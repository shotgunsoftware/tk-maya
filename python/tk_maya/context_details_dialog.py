"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------
"""
import tank
import platform
import unicodedata
import os
import sys
import threading
import pymel.core as pm

try:
    from PySide import QtCore, QtGui
except:
    from PyQt4 import QtCore, QtGui

from .ui.dialog import Ui_Dialog

class ContextDetailsDialog(QtGui.QDialog):

    
    def __init__(self, app):
        QtGui.QDialog.__init__(self)
        self._app = app
        # set up the UI
        self.ui = Ui_Dialog() 
        self.ui.setupUi(self)
        
        # set platform version in title
        title = "Tank %s - Context Information" % self._app.tank.version
        self.setWindowTitle(title)
        
        # set up the browsers
        self.ui.context_browser.set_app(self._app)
        self.ui.context_browser.set_label("Your Current Work Context")
        self.ui.context_browser.enable_search(False)        
        self.ui.context_browser.action_requested.connect( self.show_in_sg )
        
        self.ui.app_browser.set_app(self._app)
        self.ui.app_browser.set_label("Currently Running Tank Apps")
        self.ui.app_browser.action_requested.connect( self.show_app_in_app_store )        

        self.ui.environment_browser.set_app(self._app)
        self.ui.environment_browser.set_label("Your current Environment")
        self.ui.environment_browser.enable_search(False)        
        self.ui.environment_browser.action_requested.connect( self.show_engine_in_app_store )
        
        self.ui.jump_to_fs.clicked.connect( self.show_in_fs )
        self.ui.support.clicked.connect( self.open_helpdesk )
        self.ui.platform_docs.clicked.connect( self.open_platform_docs )
                
        # load data from shotgun
        self.setup_context_list()
        self.setup_apps_list()
        self.setup_environment_list()
        
    ########################################################################################
    # make sure we trap when the dialog is closed so that we can shut down 
    # our threads. Nuke does not do proper cleanup on exit.
    
    def _cleanup(self):
        self.ui.context_browser.destroy()
        self.ui.app_browser.destroy()
        self.ui.environment_browser.destroy()
        
    def closeEvent(self, event):
        self._cleanup()
        # okay to close!
        event.accept()
        
    def accept(self):
        self._cleanup()
        QtGui.QDialog.accept(self)
        
    def reject(self):
        self._cleanup()
        QtGui.QDialog.reject(self)
        
    def done(self, status):
        self._cleanup()
        QtGui.QDialog.done(self, status)
        
    ########################################################################################
    # basic business logic        
                
    def setup_context_list(self): 
        self.ui.context_browser.clear()
        self.ui.context_browser.load({})
        
    def setup_apps_list(self): 
        self.ui.app_browser.clear()
        self.ui.app_browser.load({})

    def setup_environment_list(self): 
        self.ui.environment_browser.clear()
        self.ui.environment_browser.load({})

    def open_helpdesk(self):
        pm.showHelp("http://tank.zendesk.com", absolute=True)
    
    def open_platform_docs(self):        
        if self._app.tank.documentation_url:
            pm.showHelp(self._app.tank.documentation_url, absolute=True)

        else:
            QtGui.QMessageBox.critical(self, 
                                       "No Documentation found!",
                                       "Your version of the tank platform does not have documentation")
                
    def show_in_fs(self):
        """
        Jump from context to FS
        """
        
        if self._app.context.entity:
            paths = self._app.tank.paths_from_entity(self._app.context.entity["type"], 
                                                     self._app.context.entity["id"])
        else:
            paths = self._app.tank.paths_from_entity(self._app.context.project["type"], 
                                                     self._app.context.project["id"])
        
        # launch one window for each location on disk
        # todo: can we do this in a more elegant way?
        for disk_location in paths:
                
            # get the setting        
            system = platform.system()
            
            # run the app
            if system == "Linux":
                cmd = 'xdg-open "%s"' % disk_location
            elif system == "Darwin":
                cmd = 'open "%s"' % disk_location
            elif system == "Windows":
                cmd = 'cmd.exe /C start "Folder" "%s"' % disk_location
            else:
                raise Exception("Platform '%s' is not supported." % system)
            
            exit_code = os.system(cmd)
            if exit_code != 0:
                self._app.log_error("Failed to launch '%s'!" % cmd)
        
        
    def show_in_sg(self):
        """
        Jump to shotgun
        """
        curr_selection = self.ui.context_browser.get_selected_item()
        if curr_selection is None:
            return
        
        data = curr_selection.sg_data
        sg_url = "%s/detail/%s/%d" % (self._app.shotgun.base_url, data["type"], data["id"])        
        pm.showHelp(sg_url, absolute=True)
        

    def show_app_in_app_store(self):
        """
        Jump to app store
        """
        curr_selection = self.ui.app_browser.get_selected_item()
        if curr_selection is None:
            return
        
        doc_url = curr_selection.data.get("documentation_url")
        if doc_url is None:
            QtGui.QMessageBox.critical(self, 
                                       "No Documentation found!",
                                       "Sorry, this app does not have any associated documentation!")
        else:
            pm.showHelp(doc_url, absolute=True)

    def show_engine_in_app_store(self):
        """
        Jump to app store
        """
        curr_selection = self.ui.environment_browser.get_selected_item()
        if curr_selection is None:
            return
        
        doc_url = curr_selection.data.get("documentation_url")
        if doc_url:
            pm.showHelp(doc_url, absolute=True)
        