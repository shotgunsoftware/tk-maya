"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------
"""
import tank
import os
import sys
import datetime
import threading 

try:
    from PySide import QtCore, QtGui
except:
    from PyQt4 import QtCore, QtGui

from .browser_widget import BrowserWidget
from .browser_widget import ListItem
from .browser_widget import ListHeader

class EnvironmentBrowserWidget(BrowserWidget):

    
    def __init__(self, parent=None):
        BrowserWidget.__init__(self, parent)
    
    def get_data(self, data):
    
        # the app instance here is actually the engine...
        engine = self._app
            
        data = {}
        
        data["engine"] = {"name": engine.display_name,
                          "version": engine.version,
                          "documentation_url": engine.documentation_url,
                          "description": engine.description
                          }
        
        data["environment"] = {"name": engine.environment.get("name"),
                               "disk_location": engine.environment.get("disk_location"),
                               "description": engine.environment.get("description")
                               }
        
        return data
        

    def process_result(self, result):

        d = result["engine"]

        i = self.add_item(ListItem)
        details = []
        details.append("<b>Engine: %s</b>" % d.get("name"))
        details.append("Version: %s" % d.get("version"))
        details.append("Description: %s" % d.get("description"))    
        i.set_details("<br>".join(details))
        i.data = d
        i.setToolTip("Double click for documentation.")
        i.set_thumbnail(":/res/tank_app_logo.png")

        
        d = result["environment"]

        i = self.add_item(ListItem)
        details = []
        details.append("<b>Environment: %s</b>" % d.get("name"))
        details.append("Path: %s" % d.get("disk_location"))
        details.append("Description: %s" % d.get("description"))    
        i.set_details("<br>".join(details))
        i.data = d
        i.set_thumbnail(":/res/tank_env_logo.png")
            