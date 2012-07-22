# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'item.ui'
#
# Created: Sun Jul 15 14:28:08 2012
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Item(object):
    def setupUi(self, Item):
        Item.setObjectName("Item")
        Item.resize(416, 100)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Item.sizePolicy().hasHeightForWidth())
        Item.setSizePolicy(sizePolicy)
        Item.setMinimumSize(QtCore.QSize(0, 100))
        self.verticalLayout = QtGui.QVBoxLayout(Item)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setContentsMargins(2, 2, 2, 2)
        self.verticalLayout.setObjectName("verticalLayout")
        self.background = ClickBubblingGroupBox(Item)
        self.background.setTitle("")
        self.background.setObjectName("background")
        self.horizontalLayout = QtGui.QHBoxLayout(self.background)
        self.horizontalLayout.setSpacing(8)
        self.horizontalLayout.setContentsMargins(2, 2, 2, 2)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.thumbnail = ThumbnailLabel(self.background)
        self.thumbnail.setMinimumSize(QtCore.QSize(130, 90))
        self.thumbnail.setMaximumSize(QtCore.QSize(130, 90))
        self.thumbnail.setText("")
        self.thumbnail.setPixmap(QtGui.QPixmap(":/res/thumb_empty.png"))
        self.thumbnail.setScaledContents(False)
        self.thumbnail.setAlignment(QtCore.Qt.AlignCenter)
        self.thumbnail.setObjectName("thumbnail")
        self.horizontalLayout.addWidget(self.thumbnail)
        self.details = QtGui.QLabel(self.background)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.details.sizePolicy().hasHeightForWidth())
        self.details.setSizePolicy(sizePolicy)
        self.details.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.details.setWordWrap(True)
        self.details.setObjectName("details")
        self.horizontalLayout.addWidget(self.details)
        self.verticalLayout.addWidget(self.background)

        self.retranslateUi(Item)
        QtCore.QMetaObject.connectSlotsByName(Item)

    def retranslateUi(self, Item):
        Item.setWindowTitle(QtGui.QApplication.translate("Item", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.details.setText(QtGui.QApplication.translate("Item", "content", None, QtGui.QApplication.UnicodeUTF8))

from .clickbubbling_groupbox import ClickBubblingGroupBox
from .thumbnail_label import ThumbnailLabel
from . import resources_rc
