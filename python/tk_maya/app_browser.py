"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------
"""
import tank
import os
import sys
import datetime
import threading 


from PyQt4 import QtCore, QtGui
from .browser_widget import BrowserWidget
from .browser_widget import ListItem
from .browser_widget import ListHeader

class AppBrowserWidget(BrowserWidget):

    
    def __init__(self, parent=None):
        BrowserWidget.__init__(self, parent)
    
    def get_data(self, data):
    
        # the app instance here is actually the engine...
        engine = self._app
        
        data = {}
        for app in engine.apps.values():
            data[app.name] = {"display_name": app.display_name,
                              "version": app.version,
                              "documentation_url": app.documentation_url,
                              "description": app.description
                              }
        return data
            

    def process_result(self, result):
        
        for app in result.values():
        
            i = self.add_item(ListItem)
            details = []
            details.append("<b>%s</b>" % app.get("display_name"))
            details.append("Version: %s" % app.get("version"))
            details.append("Description: %s" % app.get("description"))    
            i.set_details("<br>".join(details))
            i.data = app
            i.setToolTip("Double click for documentation.")
            i.set_thumbnail(":/res/tank_app_logo.png")
            