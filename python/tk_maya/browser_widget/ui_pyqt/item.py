# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'item.ui'
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

class Ui_Item(object):
    def setupUi(self, Item):
        Item.setObjectName(_fromUtf8("Item"))
        Item.resize(416, 100)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Item.sizePolicy().hasHeightForWidth())
        Item.setSizePolicy(sizePolicy)
        Item.setMinimumSize(QtCore.QSize(0, 100))
        Item.setWindowTitle(QtGui.QApplication.translate("Item", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.verticalLayout = QtGui.QVBoxLayout(Item)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setMargin(2)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.background = ClickBubblingGroupBox(Item)
        self.background.setTitle(_fromUtf8(""))
        self.background.setObjectName(_fromUtf8("background"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.background)
        self.horizontalLayout.setSpacing(8)
        self.horizontalLayout.setMargin(2)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.thumbnail = ThumbnailLabel(self.background)
        self.thumbnail.setMinimumSize(QtCore.QSize(130, 90))
        self.thumbnail.setMaximumSize(QtCore.QSize(130, 90))
        self.thumbnail.setText(_fromUtf8(""))
        self.thumbnail.setPixmap(QtGui.QPixmap(_fromUtf8(":/res/thumb_empty.png")))
        self.thumbnail.setScaledContents(False)
        self.thumbnail.setAlignment(QtCore.Qt.AlignCenter)
        self.thumbnail.setObjectName(_fromUtf8("thumbnail"))
        self.horizontalLayout.addWidget(self.thumbnail)
        self.details = QtGui.QLabel(self.background)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.details.sizePolicy().hasHeightForWidth())
        self.details.setSizePolicy(sizePolicy)
        self.details.setText(QtGui.QApplication.translate("Item", "content", None, QtGui.QApplication.UnicodeUTF8))
        self.details.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.details.setWordWrap(True)
        self.details.setObjectName(_fromUtf8("details"))
        self.horizontalLayout.addWidget(self.details)
        self.verticalLayout.addWidget(self.background)

        self.retranslateUi(Item)
        QtCore.QMetaObject.connectSlotsByName(Item)

    def retranslateUi(self, Item):
        pass

from .clickbubbling_groupbox import ClickBubblingGroupBox
from .thumbnail_label import ThumbnailLabel
from . import resources_rc
