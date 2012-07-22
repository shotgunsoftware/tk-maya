"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------
"""
import os
import sys

try:
    from PyQt4 import QtCore, QtGui
    from .ui_pyqt.browser import Ui_Browser
    USING_PYQT = True
except:
    from PySide import QtCore, QtGui
    from .ui_pyside.browser import Ui_Browser
    USING_PYQT = False 
     
from .worker import Worker

class BrowserWidget(QtGui.QWidget):
    
    ######################################################################################
    # SIGNALS
    
    # when the selection changes 
    if USING_PYQT:
        selection_changed = QtCore.pyqtSignal()
    else:
        selection_changed = QtCore.Signal()
    
    # when someone double clicks on an item
    if USING_PYQT:
        action_requested = QtCore.pyqtSignal()
    else:
        action_requested = QtCore.Signal()
    
    
    ######################################################################################
    # Init & Destruct
    
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        
        # set up the UI
        self.ui = Ui_Browser() 
        self.ui.setupUi(self)

        # hide the overlays
        self.ui.load_overlay.setVisible(False)
        self.ui.message_overlay.setVisible(False)

        self._app = None
        self._worker = None
        self._current_work_id = None
        self._selected_item = None
        self._selected_items = []
        self._dynamic_widgets = []
        self._multi_select = False
        self._search = True
        
        # spinner
        self._spin_icons = []
        self._spin_icons.append(QtGui.QPixmap(":/res/progress_bar_1.png"))
        self._spin_icons.append(QtGui.QPixmap(":/res/progress_bar_2.png"))
        self._spin_icons.append(QtGui.QPixmap(":/res/progress_bar_3.png"))
        self._spin_icons.append(QtGui.QPixmap(":/res/progress_bar_4.png")) 
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect( self._update_spinner )
        self._current_spinner_index = 0
        
        # search
        self.ui.search.textEdited.connect(self._on_search_text_changed)
        
    def enable_multi_select(self, status):
        """
        Should we enable multi select
        """
        self._multi_select = True
        
    def enable_search(self, status):
        """
        Toggle the search bar (on by default)
        """
        self.ui.search.setVisible(status)
        
    def destroy(self):
        if self._worker:
            self._worker.stop()
        
    def set_app(self, app):
        """
        associate with an app object
        """
        self._app = app
        # set up worker queue
        self._worker = Worker(app)
        self._worker.work_completed.connect( self._on_worker_signal)
        self._worker.work_failure.connect( self._on_worker_failure)
        
        self._worker.start(QtCore.QThread.LowPriority)
        
    def set_label(self, label):
        """
        Sets the text next to the search button 
        """
        self.ui.label.setText("<big>%s</big>" % label)
    ######################################################################################
    # Public Methods
    
    def load(self, data):
        """
        Loads data into the browser widget. 
        Called by outside code 
        """
        # start spinning
        self.ui.scroll_area.setVisible(False)
        self.ui.load_overlay.setVisible(True)
        self._timer.start(100)
        # queue up work
        self._current_work_id = self._worker.queue_work(self.get_data, data, asap=True)
    
    def clear(self):
        """
        Clear widget of its contents.
        """
        # hide overlays
        self.ui.load_overlay.setVisible(False)
        self.ui.message_overlay.setVisible(False)
        self.ui.scroll_area.setVisible(True)
        
        # clear search box
        self.ui.search.setText("")
        
        # also reset any jobs that are processing. No point processing them
        # if their requestors are gone.
        if self._worker:
            self._worker.clear()
            
        for x in self._dynamic_widgets:
            self.ui.scroll_area_layout.removeWidget(x)
            x.deleteLater()
        self._dynamic_widgets = []
            
    def set_message(self, message):
        """
        Replace the list of items with a single message
        """
        self.ui.load_overlay.setVisible(False)
        self.ui.message_overlay.setVisible(True)
        self.ui.scroll_area.setVisible(False)
        self.ui.status_message.setText(message)
        
    def clear_selection(self):
        """
        Clears the selection
        """
        for x in self._dynamic_widgets:
            x.set_selected(False)        
        self._selected_item = None
        self._selected_items = []
                
    def get_selected_item(self):
        """
        Gets the last selected item, None if no selection
        """
        return self._selected_item
    
    def get_selected_items(self):
        """
        Returns entire selection
        """
        return self._selected_items
        
    def get_items(self):
        return self._dynamic_widgets
        
    def select(self, item):
        self._on_item_clicked(item)
        # in order for the scroll to happen during load, first give
        # the scroll area  chance to resize it self by processing its event queue.
        QtCore.QCoreApplication.processEvents()
        # and focus on the selection
        self.ui.scroll_area.ensureWidgetVisible(item)
    
    ##########################################################################################
    # Protected stuff - implemented by deriving classes
    
    def get_data(self, data):
        """
        Needs to be implemented by subclasses
        """
        raise Exception("not implemented!")
    
    def process_result(self, result):
        """
        Needs to be implemented by subclasses
        """
        raise Exception("not implemented!")
    
    ##########################################################################################
    # Internals
    
    def _on_search_text_changed(self, text):
        """
        Cull based on search box
        """

        if text == "":
            # show all items
            for i in self._dynamic_widgets:
                i.setVisible(True)

        elif(text) > 2:
            # cull by string for strings > 2 chars
            lower_text = text.lower()
            for i in self._dynamic_widgets:
                details = i.get_details()
                if details is None: # header
                    i.setVisible(True)
                elif lower_text in details.lower():
                    i.setVisible(True)
                else:
                    i.setVisible(False)
    
    def _on_worker_failure(self, uid, msg):
        """
        The worker couldn't execute stuff
        """
        if self._current_work_id != uid:
            # not our job. ignore
            return

        # finally, turn off progress indication and turn on display
        self.ui.scroll_area.setVisible(True)
        self.ui.load_overlay.setVisible(False)        
        self._timer.stop()
    
        # show error message
        self.set_message(msg)
        

    def _on_worker_signal(self, uid, data):
        """
        Signalled whenever the worker completes something
        """
        if self._current_work_id != uid:
            # not our job. ignore
            return

        # finally, turn off progress indication and turn on display
        self.ui.scroll_area.setVisible(True)
        self.ui.load_overlay.setVisible(False)        
        self._timer.stop()
    
        # process!
        self.process_result(data)
            
    
    def _update_spinner(self):
        """
        Animate spinner icon
        """
        self.ui.progress_bar.setPixmap(self._spin_icons[self._current_spinner_index])
        self._current_spinner_index += 1
        if self._current_spinner_index == 4:
            self._current_spinner_index = 0            
        
    def _on_item_clicked(self, item):
        
        if item.supports_selection() == False:
            # not all items are selectable
            return
        
        if self._multi_select:
            if item.is_selected():
                # remove from selection
                item.set_selected(False)
                # remove it from list of selected items
                s = set(self._selected_items) - set([item])
                self._selected_items = list(s)
                if len(self._selected_items) > 0:
                    self._selected_item = self._selected_items[0]
                else:
                    self._selected_item = None 
            else:
                # add to selection
                item.set_selected(True)
                self._selected_item = item
                self._selected_items.append(item)
        else:
            # single select
            self.clear_selection()
            item.set_selected(True)
            self._selected_item = item
            self._selected_items = [item]
            
        self.selection_changed.emit()

    def _on_item_double_clicked(self, item):
        self.action_requested.emit()

    def add_item(self, item_class):
        """
        Adds a list item. Returns the created object.
        """
        widget = item_class(self._app, self._worker, self)
        self.ui.scroll_area_layout.addWidget(widget)
        self._dynamic_widgets.append(widget)   
        widget.clicked.connect( self._on_item_clicked )
        widget.double_clicked.connect( self._on_item_double_clicked )   
        return widget  




        
        
        



