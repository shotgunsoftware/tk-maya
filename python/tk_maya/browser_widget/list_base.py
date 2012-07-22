"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------
"""
import os
import urllib
import sys

try:
    from PyQt4 import QtCore, QtGui
    USING_PYQT = True
except:
    from PySide import QtCore, QtGui
    USING_PYQT = False 


class ListBase(QtGui.QWidget):
    
    if USING_PYQT:
        clicked = QtCore.pyqtSignal(QtGui.QWidget)
        double_clicked = QtCore.pyqtSignal(QtGui.QWidget)
    else:
        clicked = QtCore.Signal(QtGui.QWidget)
        double_clicked = QtCore.Signal(QtGui.QWidget)
        
    
    def __init__(self, app, worker, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self._app = app
        self._worker = worker

    def supports_selection(self):
        return False

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            # handle this event!
            self.clicked.emit(self)

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self)

    def set_selected(self, status):
        pass
    
    def is_selected(self):
        return False
        
    def set_title(self, title):
        pass

    def set_details(self, text):
        pass
        
    def get_title(self):
        return None

    def get_details(self):
        return None

    