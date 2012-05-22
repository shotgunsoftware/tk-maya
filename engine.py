"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

A Maya engine for Tank.

"""

import tank
import platform
import sys
import traceback
import textwrap
import os
import maya.OpenMaya as OpenMaya
import pymel.core as pm
import maya.cmds as cmds
import maya
from pymel.core import Callback

CONSOLE_OUTPUT_WIDTH = 200

###############################################################################################
# methods to support the state when the engine cannot start up
# for example if a non-tank file is loaded in maya


def on_scene_event_cb(engine_name, prev_context):
    """
    Callback which gets executed when a new scene is opened in Maya
    
    current_engine may be None if no engine is active.
    engine_name and prev_context are always populated.
    
    """
    
    try:
    
        current_engine = tank.engine()
        
        # first make sure that the disabled menu is reset, if it exists...
        if pm.menu("TankMenuDisabled", exists=True):
            pm.deleteUI("TankMenuDisabled")
        
        # if the scene opened is actually a file->new, then re-use the previous context
        # 'untitled' will never result in a context so no point trying...    
        if pm.sceneName() == "":
            # untitled scene
            ctx = prev_context
            
        else:
            # look at current file to get the context
            new_path = pm.sceneName().abspath()
            ctx = tank.system.Context.from_path(new_path)    
    
            # if an engine is active right now and context is unchanged, no need to 
            # rebuild the same engine again!
            if current_engine is not None and ctx == prev_context:
                # no need to change anything!
                return
        
        if current_engine:
            current_engine.log_debug("Ready to switch to context because of scene event !")
            current_engine.log_debug("Prev context: %s" % prev_context)   
            current_engine.log_debug("New context: %s" % ctx)        
            # tear down existing engine
            current_engine.destroy()
    
        # create new engine
        try:
            new_engine = tank.system.start_engine(engine_name, ctx)    
        
        except tank.TankEngineInitError, e:
            OpenMaya.MGlobal.displayInfo("Tank Engine cannot be started: %s" % e)
            # render menu
            create_tank_disabled_menu()
            # set up callbacks
            cb_fn = lambda en=engine_name, pc=prev_context: on_scene_event_cb(en, pc)
            pm.scriptJob(event=["SceneOpened", cb_fn], runOnce=True)
            pm.scriptJob(event=["SceneSaved", cb_fn], runOnce=True)
    
        else:
            new_engine.log_debug("Launched new engine for context!")

    except Exception, e:
        (exc_type, exc_value, exc_traceback) = sys.exc_info()
        message = ""
        message += "Message: There was a problem starting the Tank Engine.\n"
        message += "Please contact tanksupport@shotgunsoftware.com\n\n"
        message += "Exception: %s - %s\n" % (exc_type, exc_value)
        message += "Traceback (most recent call last):\n"
        message += "\n".join( traceback.format_tb(exc_traceback))
        OpenMaya.MGlobal.displayError(message)
    
def tank_disabled_message():
    """
    Explain why tank is disabled.
    """
    msg = ("Tank is disabled because it cannot recongnize the currently opened file. "
           "Try opening another file or restarting Maya.")
    
    cmds.confirmDialog( title="Tank is disabled", 
                message=msg, 
                button=["Ok"], 
                defaultButton="Ok", 
                cancelButton="Ok", 
                dismissString="Ok" )
        
    
def create_tank_disabled_menu():
    """
    Render a special "tank is disabled menu"
    """
    sg_menu = pm.menu("TankMenuDisabled", label="Tank", parent=pm.melGlobals["gMainWindow"])
    pm.menuItem(label="Tank is disabled.", parent=sg_menu, 
                command=lambda arg: tank_disabled_message())


###############################################################################################
# The Tank Maya engine

class MayaEngine(tank.system.Engine):
    
    ##########################################################################################
    # init and destroy
            
    def init_engine(self):
        self.log_debug("%s: Initializing..." % self)
        
        # our job queue
        self._queue = []
        # detect if in batch mode
        if self.in_maya_interpreter():
            self._menu_handle = pm.menu("TankMenu", label="Tank", parent=pm.melGlobals["gMainWindow"])
            self._menu_handle.postMenuCommand(self._post_menu_command)
        
        # now check that there is a location on disk which corresponds to the context
        # for the maya engine (because it for example sets the maya project)
        if len(self.context.entity_locations) == 0:
            # Try to create path for the context.
            tank.system.schema.create_filesystem_structure(self.shotgun,
                                                           self.context.project_root,
                                                           self.context.entity["type"],
                                                           self.context.entity["id"])
            if len(self.context.entity_locations) == 0:
                raise tank.TankError("No folders on disk are associated with the current context. The Maya "
                                     "engine requires a context which exists on disk in order to run "
                                     "correctly.")
                
        # Set the Maya project based on config
        self._set_project()
        
        # Watch for scene open events, we'll tear down this engine and start another one based
        # on the new context.
        cb_fn = lambda en=self.name, pc=self.context: on_scene_event_cb(en, pc)
        pm.scriptJob(event=["SceneOpened", cb_fn], runOnce=True)
        pm.scriptJob(event=["SceneSaved", cb_fn], runOnce=True)
        self.log_debug("Registered open and save callbacks.")
    
    def destroy_engine(self):
        self.log_debug("%s: Destroying..." % self)
        pm.deleteUI(self._menu_handle)
    
    ##########################################################################################
    # logging
    
    def log_debug(self, msg):
        if self.get_setting("debug_logging", False):
            msg = "%s DEBUG: %s" % (self, msg)
            for l in textwrap.wrap(msg, CONSOLE_OUTPUT_WIDTH):
                OpenMaya.MGlobal.displayInfo(l)
    
    def log_info(self, msg):
        msg = "Tank: %s" % msg
        for l in textwrap.wrap(msg, CONSOLE_OUTPUT_WIDTH):
            OpenMaya.MGlobal.displayInfo(l)
        
    def log_warning(self, msg):
        msg = "Tank: %s" % msg
        for l in textwrap.wrap(msg, CONSOLE_OUTPUT_WIDTH):
            OpenMaya.MGlobal.displayWarning(l)
    
    def log_error(self, msg):
        msg = "Tank: %s" % msg
        OpenMaya.MGlobal.displayError(msg)
    
    ##########################################################################################
    # scene and project management            
        
    def _set_project(self):
        """
        Set the maya project
        """
        tmpl = self.tank.templates.get(self.get_setting("template_project"))
        fields = self.context.as_template_fields(tmpl)
        proj_path = tmpl.apply_fields(fields)
        self.log_info("Setting Maya project to '%s'" % proj_path)        
        pm.mel.setProject(proj_path)
    
    ##########################################################################################
    # managing the menu
    
    def __add_command_to_menu(self, cmd_name, callback, properties):
        """
        Helper used to populate the menu when it is being rebuilt
        """
        enabled = True
        
        if cmd["properties"].has_key("enable_callback"):
            enabled = cmd["properties"]["enable_callback"]()
        
        params = {
            "label": cmd["name"],
            "command": Callback(cmd["callback"]),
            "parent": self._menu_handle,
            "enable": enabled
        }
        
        if cmd["properties"].has_key("tooltip"):
            params["annotation"] = cmd["properties"]["tooltip"]
        
        pm.menuItem(**params)

        
    def __add_documentation_to_menu(self):
        """
        Adds documentation items to menu based on what docs are available. 
        """
        
        # create Help menu
        pm.menuItem(divider=True, parent=self._menu_handle) 
        help_menu = pm.subMenuItem(label="Help", parent=self._menu_handle)

        for d in self.documentation:
            pm.menuItem(label=d, 
                        parent=help_menu, 
                        command=lambda arg, u=self.documentation[d]: cmds.showHelp(u, absolute=True))
            pm.menuItem(divider=True, parent=help_menu)
        
    def __launch_context_in_fs(self):
        """
        Shows the location of the project
        in a std file system browser
        """
        tmpl = self.tank.templates.get(self.get_setting("template_project"))
        fields = self.context.as_template_fields(tmpl)
        proj_path = tmpl.apply_fields(fields)
        self.log_debug("Launching file system viewer for folder %s" % proj_path)        
        
        # get the setting        
        system = platform.system()
        
        # run the app
        if system == "Linux":
            cmd = 'xdg-open "%s"' % proj_path
        elif system == "Darwin":
            cmd = 'open "%s"' % proj_path
        elif system == "Windows":
            cmd = 'cmd.exe /C start "Folder" "%s"' % proj_path
        else:
            raise Exception("Platform '%s' is not supported." % system)
        
        self.log_debug("Executing command '%s'" % cmd)
        exit_code = os.system(cmd)
        if exit_code != 0:
            self.log_error("Failed to launch '%s'!" % cmd)
        
        

    def __add_context_menu(self):
        """
        Adds a context menu which displays the current context
        """        
        ctx = self.context
        
        # try to figure out task/step, however this may not always be present
        task_step = None
        if ctx.step:
            task_step = ctx.step.get("name")
        if ctx.task:
            task_step = ctx.task.get("name")

        if task_step is None:
            # e.g. [Shot ABC_123]
            ctx_name = "[%s %s]" % (ctx.entity["type"], ctx.entity["name"])
        else:
            # e.g. [Lighting, Shot ABC_123]
            ctx_name = "[%s, %s %s]" % (task_step, ctx.entity["type"], ctx.entity["name"])
        
        # create the menu object
        ctx_menu = pm.subMenuItem(label=ctx_name, parent=self._menu_handle)
        
        # link to shotgun
        sg_url = "%s/detail/%s/%d" % (self.shotgun.base_url, ctx.entity["type"], ctx.entity["id"])
        pm.menuItem(label="Show %s in Shotgun" % ctx.entity["type"], 
                    parent=ctx_menu, 
                    command=lambda arg, u=sg_url: cmds.showHelp(u, absolute=True))
                
        # link to fs
        pm.menuItem(label="Show in File System", 
                    parent=ctx_menu, 
                    command=lambda arg: self.__launch_context_in_fs())

        pm.menuItem(divider=True, parent=self._menu_handle)
    
    def _post_menu_command(self, *args):
        """
        In order to have commands enable/disable themselves based on the enable_callback, 
        re-create the menu items every time.
        """
        self.log_debug("Recreating Tank menu contents...")
        self._menu_handle.deleteAllItems()
        
        # context
        self.__add_context_menu()
        
        # user commands
        for (cmd_name, cmd_data) in self.commands:
            self.__add_command_to_menu(cmd_name, cmd_data["callback"], cmd_data["properties"])
        
        # lastly, add the help menu
        self.__add_documentation_to_menu()
        
    ##########################################################################################
    # queue

    def add_to_queue(self, name, method, args):
        """
        Maya implementation of the engine synchronous queue. Adds an item to the queue.
        """
        qi = {}
        qi["name"] = name
        qi["method"] = method
        qi["args"] = args
        self._queue.append(qi)
    
    def report_progress(self, percent):
        """
        Callback function part of the engine queue. This is being passed into the methods
        that are executing in the queue so that they can report progress back if they like
        """
        # convert to delta value before passing to maya
        delta = percent - self._current_progress
        pm.progressBar(self._maya_progress_bar, edit=True, step=delta)
        self._current_progress = percent
    
    def execute_queue(self):
        """
        Executes all items in the queue, one by one, in a controlled fashion
        """
        self._maya_progress_bar = maya.mel.eval('$tmp = $gMainProgressBar');
        
        # execute one after the other syncronously
        while len(self._queue) > 0:
            
            # take one item off
            current_queue_item = self._queue[0]
            self._queue = self._queue[1:]

            # set up the progress bar  
            pm.progressBar( self._maya_progress_bar,
                            edit=True,
                            beginProgress=True,
                            isInterruptable=False,
                            status=current_queue_item["name"] )
            self._current_progress = 0
            
            # process it
            try:
                kwargs = current_queue_item["args"]
                # force add a progress_callback arg - this is by convention
                kwargs["progress_callback"] = self.report_progress
                # execute
                current_queue_item["method"](**kwargs)
            except:
                # error and continue
                # todo: may want to abort here - or clear the queue? not sure.
                self.log_exception("Error while processing callback %s" % current_queue_item)
            finally:
                pm.progressBar(self._maya_progress_bar, edit=True, endProgress=True)
        
    def in_maya_interpreter(self):
        """Returns true if not in batch mode."""
        try: 
            import maya.standalone             
            maya.standalone.initialize()        
        except: 
           return True
        return False

            
            
                
