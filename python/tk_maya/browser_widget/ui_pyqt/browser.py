# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'browser.ui'
#
# Created: Thu Jul 19 19:12:06 2012
#      by: PyQt4 UI code generator 4.8.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Browser(object):
    def setupUi(self, Browser):
        Browser.setObjectName(_fromUtf8("Browser"))
        Browser.resize(489, 293)
        Browser.setWindowTitle(QtGui.QApplication.translate("Browser", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.verticalLayout = QtGui.QVBoxLayout(Browser)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setMargin(2)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.browser_header = QtGui.QGroupBox(Browser)
        self.browser_header.setMinimumSize(QtCore.QSize(0, 44))
        self.browser_header.setMaximumSize(QtCore.QSize(16777215, 44))
        self.browser_header.setStyleSheet(_fromUtf8("#browser_header {\n"
"border: none;\n"
"background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(97, 97, 97, 255), stop:1 rgba(49, 49, 49, 255))\n"
"}"))
        self.browser_header.setTitle(_fromUtf8(""))
        self.browser_header.setObjectName(_fromUtf8("browser_header"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.browser_header)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.label = QtGui.QLabel(self.browser_header)
        self.label.setText(QtGui.QApplication.translate("Browser", "Browser Title", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout_2.addWidget(self.label)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.search = QtGui.QLineEdit(self.browser_header)
        self.search.setMinimumSize(QtCore.QSize(150, 0))
        self.search.setMaximumSize(QtCore.QSize(150, 16777215))
        self.search.setStyleSheet(_fromUtf8("border-width: 1px; \n"
"background-image: url(:/res/search.png);\n"
"background-repeat: no-repeat;\n"
"background-position: center left;\n"
"border-style: inset; \n"
"border-color: #535353; \n"
"border-radius: 9px; \n"
"padding-left: 15px"))
        self.search.setObjectName(_fromUtf8("search"))
        self.horizontalLayout_2.addWidget(self.search)
        self.verticalLayout.addWidget(self.browser_header)
        self.scroll_area = QtGui.QScrollArea(Browser)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName(_fromUtf8("scroll_area"))
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 483, 155))
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setMargin(4)
        self.verticalLayout_4.setObjectName(_fromUtf8("verticalLayout_4"))
        self.scroll_area_layout = QtGui.QVBoxLayout()
        self.scroll_area_layout.setSpacing(0)
        self.scroll_area_layout.setObjectName(_fromUtf8("scroll_area_layout"))
        self.verticalLayout_4.addLayout(self.scroll_area_layout)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_4.addItem(spacerItem1)
        self.scroll_area.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scroll_area)
        self.message_overlay = QtGui.QGroupBox(Browser)
        self.message_overlay.setTitle(_fromUtf8(""))
        self.message_overlay.setObjectName(_fromUtf8("message_overlay"))
        self.horizontalLayout_3 = QtGui.QHBoxLayout(self.message_overlay)
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.status_message = QtGui.QLabel(self.message_overlay)
        self.status_message.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.status_message.setText(QtGui.QApplication.translate("Browser", "Sorry, no items found!", None, QtGui.QApplication.UnicodeUTF8))
        self.status_message.setAlignment(QtCore.Qt.AlignCenter)
        self.status_message.setWordWrap(True)
        self.status_message.setObjectName(_fromUtf8("status_message"))
        self.horizontalLayout_3.addWidget(self.status_message)
        self.verticalLayout.addWidget(self.message_overlay)
        self.load_overlay = QtGui.QGroupBox(Browser)
        self.load_overlay.setTitle(_fromUtf8(""))
        self.load_overlay.setObjectName(_fromUtf8("load_overlay"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.load_overlay)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.progress_bar = QtGui.QLabel(self.load_overlay)
        self.progress_bar.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.progress_bar.setText(_fromUtf8(""))
        self.progress_bar.setPixmap(QtGui.QPixmap(_fromUtf8(":/res/progress_bar_1.png")))
        self.progress_bar.setAlignment(QtCore.Qt.AlignCenter)
        self.progress_bar.setObjectName(_fromUtf8("progress_bar"))
        self.horizontalLayout.addWidget(self.progress_bar)
        self.verticalLayout.addWidget(self.load_overlay)

        self.retranslateUi(Browser)
        QtCore.QMetaObject.connectSlotsByName(Browser)

    def retranslateUi(self, Browser):
        pass

from . import resources_rc
