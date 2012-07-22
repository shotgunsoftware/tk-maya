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



class MenuGenerator(object):
    """
    Menu generation functionality for Maya
    """

    def __init__(self, engine):
        self._engine = engine
        self._dialogs = []
        engine_root_dir = self._engine.disk_location
        self.tank_logo = os.path.abspath(os.path.join(engine_root_dir, "resources", "logo_gray_22.png"))

    ##########################################################################################
    # public methods

    def create_menu(self):
        """
        Render the entire Tank menu.
        """
        # create main menu
        nuke_menu = nuke.menu("Nuke")
        self._menu_handle = nuke_menu.addMenu("Tank") 
        # the right click menu that is displayed when clicking on a pane 
        self._pane_menu = nuke.menu("Pane") 
        # create tank side menu
        self._node_menu_handle = nuke.menu("Nodes").addMenu("Tank", icon=self.tank_logo)

        # slight hack here but first ensure that the menu is empty
        self._menu_handle.clearMenu()
    
    
        
        # now add the context item on top of the main menu
        self._context_menu = self._add_context_menu()
        self._menu_handle.addSeparator()


        # now add favourites
        for fav in self._engine.get_setting("menu_favourites"):
            app_instance_name = fav["app_instance"]
            menu_name = fav["name"]
            
            # scan through all menu items
            for (cmd_name, cmd_details) in self._engine.commands.items():
                 cmd = AppCommand(cmd_name, cmd_details)
                 if cmd.get_app_instance_name() == app_instance_name and cmd.name == menu_name:
                     # found our match!
                     cmd.add_command_to_menu(self._menu_handle)

        self._menu_handle.addSeparator()
        
        
        # now go through all of the menu items.
        # separate them out into various sections
        commands_by_app = {}
        
        for (cmd_name, cmd_details) in self._engine.commands.items():
            cmd = AppCommand(cmd_name, cmd_details)
            
            if cmd.get_type() == "node":
                # add to the node menu
                # get icon if specified - default to tank icon if not specified
                icon = cmd.properties.get("icon", self.tank_logo)
                self._node_menu_handle.addCommand(cmd.name, cmd.callback, icon=icon)
                
            elif cmd.get_type() == "custom_pane":
                # custom pane
                # add to the std pane menu in nuke
                self._pane_menu.addCommand(cmd.name, cmd.callback)
                # also register the panel so that a panel restore command will
                # properly register it on startup or panel profile restore.
                nukescripts.registerPanel(cmd.properties.get("panel_id", "undefined"), cmd.callback)
                
            elif cmd.get_type() == "context_menu":
                # context menu!
                self._context_menu.addCommand(cmd.name, cmd.callback)
                
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
            
            
    def destroy_menu(self):
        
            self._menu_handle.clearMenu()
            self._node_menu_handle.clearMenu()
        
    ##########################################################################################
    # context menu and UI

    def _add_context_menu(self):
        """
        Adds a context menu which displays the current context
        """        
        
        ctx = self._engine.context
        
        if ctx.entity is None:
            # project-only!
            ctx_name = "[%s]" % ctx.project["name"]
        
        elif ctx.step is None and ctx.task is None:
            # entity only
            # e.g. [Shot ABC_123]
            ctx_name = "[%s %s]" % (ctx.entity["type"], ctx.entity["name"])

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
        ctx_menu = self._menu_handle.addMenu(ctx_name)
        ctx_menu.addCommand("View Context Details", self._show_context_ui)
        ctx_menu.addSeparator()
        
        return ctx_menu
                        
    
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
                app_menu = self._menu_handle.addMenu(app_name)
                for cmd in commands_by_app[app_name]:
                    cmd.add_command_to_menu(app_menu)
            
            else:
                # this app only has a single entry. 
                # display that on the menu
                # todo: Should this be labelled with the name of the app 
                # or the name of the menu item? Not sure.
                cmd_obj = commands_by_app[app_name][0]
                cmd_obj.add_command_to_menu(self._menu_handle)
                                
        
        
    
            
class AppCommand(object):
    """
    Wraps around a single command that you get from engine.commands
    """
    
    def __init__(self, name, command_dict):        
        self.name = name
        self.properties = command_dict["properties"]
        self.callback = command_dict["callback"]
        
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
        # std shotgun menu
        menu.addCommand(self.name, self.callback) 














    
