"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------
"""
import os
import sys

from PyQt4 import QtCore, QtGui 

class ClickBubblingGroupBox(QtGui.QGroupBox):

    def __init__(self, parent=None):
        QtGui.QGroupBox.__init__(self, parent)

    def mousePressEvent(self, event):
        event.setAccepted(False)
        
    def mouseDoubleClickEvent(self, event):
        event.setAccepted(False)
        



