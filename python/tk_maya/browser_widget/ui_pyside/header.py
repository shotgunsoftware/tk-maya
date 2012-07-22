# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'header.ui'
#
# Created: Tue Jul 10 22:11:45 2012
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Header(object):
    def setupUi(self, Header):
        Header.setObjectName("Header")
        Header.resize(399, 32)
        self.verticalLayout = QtGui.QVBoxLayout(Header)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setContentsMargins(2, 2, 2, 2)
        self.verticalLayout.setObjectName("verticalLayout")
        self.background = ClickBubblingGroupBox(Header)
        self.background.setTitle("")
        self.background.setObjectName("background")
        self.horizontalLayout = QtGui.QHBoxLayout(self.background)
        self.horizontalLayout.setContentsMargins(2, 2, 2, 2)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtGui.QLabel(self.background)
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.verticalLayout.addWidget(self.background)

        self.retranslateUi(Header)
        QtCore.QMetaObject.connectSlotsByName(Header)

    def retranslateUi(self, Header):
        Header.setWindowTitle(QtGui.QApplication.translate("Header", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Header", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))

from .clickbubbling_groupbox import ClickBubblingGroupBox
from . import resources_rc
