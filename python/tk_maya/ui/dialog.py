# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dialog.ui'
#
# Created: Sun Jul 22 19:25:58 2012
#      by: PyQt4 UI code generator 4.8.6
#
# WARNING! All changes made in this file will be lost!

try:
    from PySide import QtCore, QtGui
except:
    from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(811, 487)
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Your Current Context", None, QtGui.QApplication.UnicodeUTF8))
        self.horizontalLayout = QtGui.QHBoxLayout(Dialog)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.context_overview_tab_widget = QtGui.QTabWidget(Dialog)
        self.context_overview_tab_widget.setTabPosition(QtGui.QTabWidget.South)
        self.context_overview_tab_widget.setObjectName(_fromUtf8("context_overview_tab_widget"))
        self.tab = QtGui.QWidget()
        self.tab.setObjectName(_fromUtf8("tab"))
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.tab)
        self.verticalLayout_4.setObjectName(_fromUtf8("verticalLayout_4"))
        self.context_browser = ContextBrowserWidget(self.tab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.context_browser.sizePolicy().hasHeightForWidth())
        self.context_browser.setSizePolicy(sizePolicy)
        self.context_browser.setMinimumSize(QtCore.QSize(380, 0))
        self.context_browser.setObjectName(_fromUtf8("context_browser"))
        self.verticalLayout_4.addWidget(self.context_browser)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/res/icon_task.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.context_overview_tab_widget.addTab(self.tab, icon, _fromUtf8(""))
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName(_fromUtf8("tab_2"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.tab_2)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.label_2 = QtGui.QLabel(self.tab_2)
        self.label_2.setText(QtGui.QApplication.translate("Dialog", "You can double click on an app to jump to its documentation.", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout_2.addWidget(self.label_2)
        self.app_browser = AppBrowserWidget(self.tab_2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.app_browser.sizePolicy().hasHeightForWidth())
        self.app_browser.setSizePolicy(sizePolicy)
        self.app_browser.setMinimumSize(QtCore.QSize(380, 0))
        self.app_browser.setObjectName(_fromUtf8("app_browser"))
        self.verticalLayout_2.addWidget(self.app_browser)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8(":/res/logo_color_16.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.context_overview_tab_widget.addTab(self.tab_2, icon1, _fromUtf8(""))
        self.tab_3 = QtGui.QWidget()
        self.tab_3.setObjectName(_fromUtf8("tab_3"))
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.tab_3)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.label_3 = QtGui.QLabel(self.tab_3)
        self.label_3.setText(QtGui.QApplication.translate("Dialog", "The environment file contains all the settings and configuration for the currently running Tank Apps. The Tank Engine provides core services such as menu management and app startup.", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setWordWrap(True)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.verticalLayout_3.addWidget(self.label_3)
        self.environment_browser = EnvironmentBrowserWidget(self.tab_3)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.environment_browser.sizePolicy().hasHeightForWidth())
        self.environment_browser.setSizePolicy(sizePolicy)
        self.environment_browser.setMinimumSize(QtCore.QSize(380, 0))
        self.environment_browser.setObjectName(_fromUtf8("environment_browser"))
        self.verticalLayout_3.addWidget(self.environment_browser)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(_fromUtf8(":/res/cog_white.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.context_overview_tab_widget.addTab(self.tab_3, icon2, _fromUtf8(""))
        self.horizontalLayout.addWidget(self.context_overview_tab_widget)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setSpacing(5)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(Dialog)
        self.label.setText(_fromUtf8(""))
        self.label.setPixmap(QtGui.QPixmap(_fromUtf8(":/res/tank_logo.png")))
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.jump_to_fs = QtGui.QPushButton(Dialog)
        self.jump_to_fs.setText(QtGui.QApplication.translate("Dialog", "Jump to the File System", None, QtGui.QApplication.UnicodeUTF8))
        self.jump_to_fs.setObjectName(_fromUtf8("jump_to_fs"))
        self.verticalLayout.addWidget(self.jump_to_fs)
        self.platform_docs = QtGui.QPushButton(Dialog)
        self.platform_docs.setText(QtGui.QApplication.translate("Dialog", "Platform Documentation", None, QtGui.QApplication.UnicodeUTF8))
        self.platform_docs.setObjectName(_fromUtf8("platform_docs"))
        self.verticalLayout.addWidget(self.platform_docs)
        self.support = QtGui.QPushButton(Dialog)
        self.support.setText(QtGui.QApplication.translate("Dialog", "Help Desk and Support", None, QtGui.QApplication.UnicodeUTF8))
        self.support.setObjectName(_fromUtf8("support"))
        self.verticalLayout.addWidget(self.support)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.close = QtGui.QPushButton(Dialog)
        self.close.setText(QtGui.QApplication.translate("Dialog", "Close", None, QtGui.QApplication.UnicodeUTF8))
        self.close.setObjectName(_fromUtf8("close"))
        self.verticalLayout.addWidget(self.close)
        self.horizontalLayout.addLayout(self.verticalLayout)

        self.retranslateUi(Dialog)
        self.context_overview_tab_widget.setCurrentIndex(0)
        QtCore.QObject.connect(self.close, QtCore.SIGNAL(_fromUtf8("clicked()")), Dialog.accept)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        self.context_overview_tab_widget.setTabText(self.context_overview_tab_widget.indexOf(self.tab), QtGui.QApplication.translate("Dialog", "Current Context", None, QtGui.QApplication.UnicodeUTF8))
        self.context_overview_tab_widget.setTabText(self.context_overview_tab_widget.indexOf(self.tab_2), QtGui.QApplication.translate("Dialog", "Active Apps", None, QtGui.QApplication.UnicodeUTF8))
        self.context_overview_tab_widget.setTabText(self.context_overview_tab_widget.indexOf(self.tab_3), QtGui.QApplication.translate("Dialog", "Environment", None, QtGui.QApplication.UnicodeUTF8))

from ..context_browser import ContextBrowserWidget
from ..environment_browser import EnvironmentBrowserWidget
from ..app_browser import AppBrowserWidget
from . import resources_rc
