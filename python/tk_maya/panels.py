# Copyright (c) 2015 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Panel support utilities for Maya
"""
import os
import sys
import sgtk
from sgtk.platform.qt import QtCore, QtGui

def install_callbacks(panel_id, widget_id):
    """
    Helper method to assist in the panel creation process.
    This will iterate over all QT widgets and look for a panel_id
    widget. Once found, it will install an event filter on this panel
    to monitor its close event, so that we can gracefully handle close,
    refresh and deallocation of the embedded tk widget when this happens.
    
    :param panel_id: Object name for panel
    :param widget_id: Object name for tk widget
    """
    widget = _find_widget(panel_id)
    if widget:
        filter = CloseEventFilter(widget)
        filter.set_associated_widget(widget_id)
        filter.parent_closed.connect(_on_parent_closed_callback)
        filter.parent_dirty.connect(_on_parent_refresh_callback)
        widget.installEventFilter(filter)

def _find_widget(widget_name):
    """
    Given a name, return the first corresponding
    QT widget that is found.
    
    :param widget_name: QT object name to look for
    :returns: QWidget object or None if nothing was found
    """ 
    for widget in QtGui.QApplication.allWidgets():
        if widget.objectName() == widget_name:
            return widget
    return None

def _on_parent_closed_callback(widget_id):
    """
    Callback which fires when a panel is closed.
    This will locate the widget with the given id
    and close and delete this.
    
    :param widget_id: Object name of widget to close
    """
    widget = _find_widget(widget_id)
    if widget:
        widget.close()
        # delete later since we are inside a slot
        widget.deleteLater()
    
def _on_parent_refresh_callback(widget_id):
    """
    Callback which fires when a UI refresh is needed.
    
    :param widget_id: Object name of widget to refresh
    """
    widget = _find_widget(widget_id)
    if widget:
        # this is a pretty blunt tool, but right now I cannot
        # come up with a better solution - it seems the internal
        # window parenting in maya is a little off - and/or I am
        # not parenting up the QT widgets correctly, and I think
        # this is the reason the UI refresh isn't working correctly.
        # the only way to ensure a fully refreshed UI is to repaint 
        # the entire window.
        widget.window().update()

class CloseEventFilter(QtCore.QObject):
    """
    Event filter which emits a parent_closed signal whenever
    the monitored widget closes.
    """
    parent_closed = QtCore.Signal(str)
    parent_dirty = QtCore.Signal(str)
     
    def set_associated_widget(self, widget_id):
        """
        Set the widget that should be closed
        
        :param widget_id: Object name of widget to close
        """
        self._widget_id = widget_id
     
    def eventFilter(self, obj, event):
        """
        QT Event filter callback
        
        :param obj: The object where the event originated from
        :param event: The actual event object
        :returns: True if event was consumed, False if not
        """
        # peek at the message
        if event.type() == QtCore.QEvent.Close:
            # make sure the associated widget is still a descendant of the object
            parent = _find_widget(self._widget_id)
            while parent:
                if parent == obj:
                    # re-broadcast the close event
                    self.parent_closed.emit(self._widget_id)
                    break
                parent = parent.parent()
        
        if event.type() == QtCore.QEvent.LayoutRequest:
            # this event seems to be fairly representatative
            # (without too many false positives) of when a tab
            # needs to trigger a UI redraw of content
            self.parent_dirty.emit(self._widget_id)
        
        # pass it on!
        return False

