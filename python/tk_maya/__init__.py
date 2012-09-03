"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

"""
import maya.OpenMayaUI as OpenMayaUI

from .menu_generation import MenuGenerator

_qt_widgets = {}
def _wrap_qt_widget(widget_cls, widget_id):
    '''
    This function is used to wrap up the widget_cls in
    a new subclass to take control of the widget's
    close function.  This lets us close our parent_widget
    when the child widget close is called as well as
    remove the child widget from our tracking dictionary.
    '''
    # Define the close method we'll use in
    # the Qt TankWrapper class we'll create
    # below.  This allows us to ensure our
    # parent wrapper widget we've created
    # is closed when it need's to be.
    #
    def close(self):
        widget_cls.close(self)
        self.parentWidget().close()
        
        # This is needed for dock widgets.
        #
        self.parentWidget().deleteLater()
        
        # Pop this widget out of our dict tracking the
        # widgets that we've created so far.
        #
        self._tk_maya_engine_qt_widgets.pop(widget_id)

    # Create a TankWrapper class that is a subclass of
    # the widget_class that came in.  This lets us
    # override the close method but still call the 
    # original widget_cls close method.  We pass in
    # the close method and our widget tracking dict.
    # The new class is instantiated and added to
    # our parent_widget's layout.
    #
    return type('%sTankWrapper' % widget_cls.__name__, 
                (widget_cls, ), 
                {
                   'close':close, 
                   '_tk_maya_engine_qt_widgets':_qt_widgets
                })

def new_qt_widget(widget_cls, widget_id, app_settings={}, **kwargs):
    '''
    If the widget is a QMainWindow or inherits from
    QMainWindow then we just set the Maya window object
    as the parent and return.

    If the widget is another type of QWidget then we either
    create a dock widget if dock=True is passed in or
    create a QDialog and parent the widget to one of these
    objects.  If modal=True and we are creating a QDialog,
    then the QDialog is set as modal.

    app_settings let's seperate settings per software.

    An example would be: 
    app_settings = {
                     'maya':{
                             'dock':True,
                             'floating':True
                            },
                     'nuke':{
                             'dock':True,
                             'pane':'Properties.1'
                            }
                   }
    '''

    from PySide import QtGui, QtCore
    from PySide import shiboken
    
    # Get a pointer to the main maya window.
    #
    ptr = OpenMayaUI.MQtUtil.mainWindow()
    maya_window_qwidget = shiboken.wrapInstance(long(ptr), QtGui.QMainWindow)
    
    parent_widget = None
    widget = None
    
    # get the app specific settings
    #
    app_settings = app_settings.pop('maya', {})

    # If the instance is already a QMainWindow
    # just parent it to the maya window and
    # move on with life.
    #
    if QtGui.QMainWindow in widget_cls.__bases__:
        widget = widget_cls(maya_window_qwidget)
        parent_widget = widget
    else:
        # Default layout used for both the dock
        # and dialog wrapper methods.
        #
        wrapped_widget_cls = _wrap_qt_widget(widget_cls, widget_id)
        widget = wrapped_widget_cls()
        if app_settings.pop('dock', False):
            # The user has requested a dock widget be created
            #
            parent_widget = QtGui.QDockWidget('', maya_window_qwidget)
            dock_area = app_settings.pop('dock_area', QtCore.Qt.RightDockWidgetArea)
            maya_window_qwidget.addDockWidget(dock_area, parent_widget)
            
            # If floating hasn't been requested, dock to the area
            # the user has provided.  Maya uses TabBars for the dock
            # areas so we do some funky stuff to take care of that.
            #
            if not app_settings.pop('floating', False):
                docks = maya_window_qwidget.findChildren(QtGui.QDockWidget)
                for dock in docks:
                    if maya_window_qwidget.dockWidgetArea(dock) == dock_area:
                        if dock.isVisible():
                            maya_window_qwidget.tabifyDockWidget(dock, parent_widget)
                            break
            else:
                parent_widget.setFloating(True)
            parent_widget.setWidget(widget)
        else:
            # Dock wasn't requested so we create a QDialog
            # to wrap the passed in widget with.
            #
            parent_widget = QtGui.QDialog(maya_window_qwidget)
            parent_widget.setModal(app_settings.pop('modal', False))

            layout = QtGui.QVBoxLayout()
            layout.setSpacing(0)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(widget)
            parent_widget.setLayout(layout)
        
        # Set the new parent widget's size and title to match
        # the passed in widget.
        #
        parent_widget.resize(widget.width(), widget.height())
        window_title = widget.windowTitle() or widget_id
        parent_widget.setWindowTitle(window_title)
        widget.setParent(parent_widget)
    
    # Add the widget to our dict of widgets.
    #
    # If we have already created a widget with the
    # same window title as this widget, close
    # the old one before creating a new one.
    #
    if _qt_widgets.get(widget_id):
        _qt_widgets.get(widget_id).close()
    
    _qt_widgets[widget_id] = widget

    return parent_widget