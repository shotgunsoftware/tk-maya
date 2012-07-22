# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'header.ui'
#
# Created: Thu Jul 19 19:12:05 2012
#      by: PyQt4 UI code generator 4.8.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Header(object):
    def setupUi(self, Header):
        Header.setObjectName(_fromUtf8("Header"))
        Header.resize(399, 32)
        Header.setWindowTitle(QtGui.QApplication.translate("Header", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.verticalLayout = QtGui.QVBoxLayout(Header)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setMargin(2)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.background = ClickBubblingGroupBox(Header)
        self.background.setTitle(_fromUtf8(""))
        self.background.setObjectName(_fromUtf8("background"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.background)
        self.horizontalLayout.setMargin(2)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label = QtGui.QLabel(self.background)
        self.label.setText(QtGui.QApplication.translate("Header", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setWordWrap(True)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout.addWidget(self.label)
        self.verticalLayout.addWidget(self.background)

        self.retranslateUi(Header)
        QtCore.QMetaObject.connectSlotsByName(Header)

    def retranslateUi(self, Header):
        pass

from .clickbubbling_groupbox import ClickBubblingGroupBox
from . import resources_rc
