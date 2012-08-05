"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

Menu handling for Maya

"""

import tank
import platform
import sys
import os
import unicodedata
import maya.OpenMaya as OpenMaya
import pymel.core as pm
import maya.cmds as cmds
import maya
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
        
        if ctx.entity is None:
            # project-only!
            ctx_name = "%s" % ctx.project["name"]
        
        elif ctx.step is None and ctx.task is None:
            # entity only
            # e.g. [Shot ABC_123]
            ctx_name = "%s %s" % (ctx.entity["type"], ctx.entity["name"])

        else:
            # we have either step or task
            task_step = None
            if ctx.step:
                task_step = ctx.step.get("name")
            if ctx.task:
                task_step = ctx.task.get("name")
            
            # e.g. [Lighting, Shot ABC_123]
            ctx_name = "%s, %s %s" % (task_step, ctx.entity["type"], ctx.entity["name"])
        
        # create the menu object
        ctx_menu = pm.subMenuItem(label=ctx_name, parent=self._menu_handle)
        
        # link to UI
        pm.menuItem(label="About Tank", 
                    parent=ctx_menu, 
                    command=Callback(self._show_context_ui))
        pm.menuItem(divider=True, parent=ctx_menu)
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

        if self._engine.context.entity is None:
            # project-only!
            url = "%s/detail/%s/%d" % (self._engine.shotgun.base_url, 
                                       "Project", 
                                       self._engine.context.project["id"])
        else:
            # entity-based
            url = "%s/detail/%s/%d" % (self._engine.shotgun.base_url, 
                                       self._engine.context.entity["type"], 
                                       self._engine.context.entity["id"])
        
        pm.showHelp(url, absolute=True)        
        
        
    def _jump_to_fs(self):
        
        """
        Jump from context to FS
        """
        
        if self._engine.context.entity:
            paths = self._engine.tank.paths_from_entity(self._engine.context.entity["type"], 
                                                     self._engine.context.entity["id"])
        else:
            paths = self._engine.tank.paths_from_entity(self._engine.context.project["type"], 
                                                     self._engine.context.project["id"])
        
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
                self._engine.log_error("Failed to launch '%s'!" % cmd)
        
                        
    
    def _show_context_ui(self):
        """
        """
        from .context_details_dialog import ContextDetailsDialog
        # some QT notes here. Need to keep the dialog object from being GC-ed
        # otherwise pyside will go hara kiri. QT has its own loop to track
        # objects and destroy them and unless we store the dialog as a member
        self._dialog = ContextDetailsDialog(self._engine)
        
        # hack - pyside can crash for some reason when a dialog object is GCed
        # so keep all of them in memory. PySide FAIL
        self._dialogs.append(self._dialog)
        
        # run modal dialogue
        self._dialog.exec_()
        
        # on the mac, need to delete it - otherwise a "ghost" will remain
        # after closing has happened - on other platforms, however, this
        # double deletion crashes Nuke >.<
        if sys.platform == "darwin":
            self._dialog.deleteLater()
        
        
        
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














    
        