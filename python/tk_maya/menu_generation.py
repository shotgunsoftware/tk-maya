"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

Menu handling for Maya

"""

import tank
import sys
import os
import unicodedata
import maya.OpenMaya as OpenMaya
import pymel.core as pm
import maya.cmds as cmds
import maya
from tank.platform.qt import QtGui, QtCore
from pymel.core import Callback


class MenuGenerator(object):
    """
    Menu generation functionality for Maya
    """

    def __init__(self, engine, menu_handle):
        self._engine = engine
        self._menu_handle = menu_handle
        self._dialogs = []

    ##########################################################################################
    # public methods

    def create_menu(self, *args):
        """
        Render the entire Tank menu.
        In order to have commands enable/disable themselves based on the enable_callback, 
        re-create the menu items every time.
        """
        self._menu_handle.deleteAllItems()
        
        # now add the context item on top of the main menu
        self._context_menu = self._add_context_menu()
        pm.menuItem(divider=True, parent=self._menu_handle)


        # now enumerate all items and create menu objects for them
        menu_items = []
        for (cmd_name, cmd_details) in self._engine.commands.items():
             menu_items.append( AppCommand(cmd_name, cmd_details) )

        # now add favourites
        for fav in self._engine.get_setting("menu_favourites"):
            app_instance_name = fav["app_instance"]
            menu_name = fav["name"]
            # scan through all menu items
            for cmd in menu_items:                 
                 if cmd.get_app_instance_name() == app_instance_name and cmd.name == menu_name:
                     # found our match!
                     cmd.add_command_to_menu(self._menu_handle)
                     # mark as a favourite item
                     cmd.favourite = True

        pm.menuItem(divider=True, parent=self._menu_handle)
        
        # now go through all of the menu items.
        # separate them out into various sections
        commands_by_app = {}
        
        for cmd in menu_items:

            if cmd.get_type() == "context_menu":
                # context menu!
                cmd.add_command_to_menu(self._context_menu)             
                
            else:
                # normal menu
                app_name = cmd.get_app_name()
                if app_name is None:
                    # un-parented app
                    app_name = "Other Items" 
                if not app_name in commands_by_app:
                    commands_by_app[app_name] = []
                commands_by_app[app_name].append(cmd)
        
        # now add all apps to main menu
        self._add_app_menu(commands_by_app)
        
    ##########################################################################################
    # context menu and UI

    def _add_context_menu(self):
        """
        Adds a context menu which displays the current context
        """        
        
        ctx = self._engine.context
        ctx_name = str(ctx)        
        
        # create the menu object
        ctx_menu = pm.subMenuItem(label=ctx_name, parent=self._menu_handle)
        
        # link to UI
        pm.menuItem(label="Jump to Shotgun", 
                    parent=ctx_menu, 
                    command=Callback(self._jump_to_sg))
        pm.menuItem(label="Jump to File System", 
                    parent=ctx_menu, 
                    command=Callback(self._jump_to_fs))


        # divider (apps may register entries below this divider)
        pm.menuItem(divider=True, parent=ctx_menu)
        
        return ctx_menu
                        
                        
    def _jump_to_sg(self):
        """
        Jump to shotgun, launch web browser
        """        
        url = self._engine.context.shotgun_url
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
        
        
    def _jump_to_fs(self):
        """
        Jump from context to FS
        """
        # launch one window for each location on disk        
        paths = self._engine.context.filesystem_locations
        for disk_location in paths:
                
            # get the setting        
            system = sys.platform
            
            # run the app
            if system == "linux2":
                cmd = 'xdg-open "%s"' % disk_location
            elif system == "darwin":
                cmd = 'open "%s"' % disk_location
            elif system == "win32":
                cmd = 'cmd.exe /C start "Folder" "%s"' % disk_location
            else:
                raise Exception("Platform '%s' is not supported." % system)
            
            exit_code = os.system(cmd)
            if exit_code != 0:
                self._engine.log_error("Failed to launch '%s'!" % cmd)
        
                        
    ##########################################################################################
    # app menus
        
        
    def _add_app_menu(self, commands_by_app):
        """
        Add all apps to the main menu, process them one by one.
        """
        for app_name in sorted(commands_by_app.keys()):
            
            if len(commands_by_app[app_name]) > 1:
                # more than one menu entry fort his app
                # make a sub menu and put all items in the sub menu
                app_menu = pm.subMenuItem(label=app_name, parent=self._menu_handle)                
                for cmd in commands_by_app[app_name]:
                    cmd.add_command_to_menu(app_menu)
            
            else:

                # this app only has a single entry. 
                # display that on the menu
                # todo: Should this be labelled with the name of the app 
                # or the name of the menu item? Not sure.
                cmd_obj = commands_by_app[app_name][0]
                if not cmd_obj.favourite:
                    # skip favourites since they are alreay on the menu
                    cmd_obj.add_command_to_menu(self._menu_handle)
                                
        
        
    
            
class AppCommand(object):
    """
    Wraps around a single command that you get from engine.commands
    """
    
    def __init__(self, name, command_dict):        
        self.name = name
        self.properties = command_dict["properties"]
        self.callback = command_dict["callback"]
        self.favourite = False
        
    def get_app_name(self):
        """
        Returns the name of the app that this command belongs to
        """
        if "app" in self.properties:
            return self.properties["app"].display_name
        return None
        
    def get_app_instance_name(self):
        """
        Returns the name of the app instance, as defined in the environment.
        Returns None if not found.
        """
        if "app" not in self.properties:
            return None
        
        app_instance = self.properties["app"]
        engine = app_instance.engine

        for (app_instance_name, app_instance_obj) in engine.apps.items():
            if app_instance_obj == app_instance:
                # found our app!
                return app_instance_name
            
        return None
        
    def get_documentation_url_str(self):
        """
        Returns the documentation as a str
        """
        if "app" in self.properties:
            app = self.properties["app"]
            doc_url = app.documentation_url
            # deal with nuke's inability to handle unicode. #fail
            if doc_url.__class__ == unicode:
                doc_url = unicodedata.normalize('NFKD', doc_url).encode('ascii', 'ignore')
            return doc_url

        return None
        
    def get_type(self):
        """
        returns the command type. Returns node, custom_pane or default
        """
        return self.properties.get("type", "default")
        
    def add_command_to_menu(self, menu):
        """
        Adds an app command to the menu
        """
        enabled = True
        
        if "enable_callback" in self.properties:
            enabled = self.properties["enable_callback"]()
        
        params = {
            "label": self.name,
            "command": Callback(self.callback),
            "parent": menu,
            "enable": enabled
        }
        
        if "tooltip" in self.properties:
            params["annotation"] = self.properties["tooltip"]
        
        pm.menuItem(**params)














    
        
