"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------
"""
import os
import sys

try:
    from PyQt4 import QtCore, QtGui
    from .ui_pyqt.header import Ui_Header
    USING_PYQT = True
except:
    from PySide import QtCore, QtGui
    from .ui_pyside.header import Ui_Header
    USING_PYQT = False 

from .list_base import ListBase

class ListHeader(ListBase):
    
    def __init__(self, app, worker, parent=None):
        ListBase.__init__(self, app, worker, parent)

        # set up the UI
        self.ui = Ui_Header() 
        self.ui.setupUi(self)
        self.ui.background.setStyleSheet("background-color: #6F6F6F; border: none")

    def set_title(self, title):
        self.ui.label.setText("<big>%s</big>" % title)
        
    def get_title(self):
        return self.ui.label.text()