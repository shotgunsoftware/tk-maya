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
        current_engine = tank.platform.current_engine()
        
        # first make sure that the disabled menu is reset, if it exists...
        if pm.menu("TankMenuDisabled", exists=True):
            pm.deleteUI("TankMenuDisabled")
        
        # if the scene opened is actually a file->new, then maintain the current
        # context/engine.
        if pm.sceneName() == "":
            return
        else:
            new_path = pm.sceneName().abspath()
            
            # this file could be in another project altogether, so create a new Tank
            # API instance.
            try:
                tk = tank.tank_from_path(new_path)
            except tank.TankError, e:
                OpenMaya.MGlobal.displayInfo("Tank Engine cannot be started: %s" % e)
                # render menu
                create_tank_disabled_menu()
                return

            ctx = tk.context_from_path(new_path, prev_context)
            
            # if an engine is active right now and context is unchanged, no need to 
            # rebuild the same engine again!
            if current_engine is not None and ctx == prev_context:
                return
        
        if current_engine:
            current_engine.log_debug("Ready to switch to context because of scene event !")
            current_engine.log_debug("Prev context: %s" % prev_context)   
            current_engine.log_debug("New context: %s" % ctx)        
            # tear down existing engine
            current_engine.destroy()
    
        # create new engine
        try:
            new_engine = tank.platform.start_engine(engine_name, tk, ctx)
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
    if pm.menu("TankMenu", exists=True):
        pm.deleteUI("TankMenu")

    sg_menu = pm.menu("TankMenuDisabled", label="Tank", parent=pm.melGlobals["gMainWindow"])
    pm.menuItem(label="Tank is disabled.", parent=sg_menu, 
                command=lambda arg: tank_disabled_message())


###############################################################################################
# The Tank Maya engine

class MayaEngine(tank.platform.Engine):
    
    ##########################################################################################
    # init and destroy
            
    def init_engine(self):
        self.log_debug("%s: Initializing..." % self)
        
        # our job queue
        self._queue = []
        
        self._init_pyside()
        
        # detect if in batch mode
        if self.__is_ui_enabled():
            self._menu_handle = pm.menu("TankMenu", label="Tank", parent=pm.melGlobals["gMainWindow"])
            # create our menu handler
            from tk_maya import MenuGenerator
            self._menu_generator = MenuGenerator(self, self._menu_handle)
            # hook things up so that the menu is created every time it is clicked
            self._menu_handle.postMenuCommand(self._menu_generator.create_menu)
                    
        # Set the Maya project based on config
        self._set_project()
        
        # Watch for scene open events, we'll tear down this engine and start another one based
        # on the new context.
        cb_fn = lambda en=self.instance_name, pc=self.context: on_scene_event_cb(en, pc)
        pm.scriptJob(event=["SceneOpened", cb_fn], runOnce=True)
        pm.scriptJob(event=["SceneSaved", cb_fn], runOnce=True)
        self.log_debug("Registered open and save callbacks.")
    
    def destroy_engine(self):
        self.log_debug("%s: Destroying..." % self)
        pm.deleteUI(self._menu_handle)
    
    
    def _init_pyside(self):
        """
        Handles the pyside init
        """
        
        # first see if pyside is already present - in that case skip!
        try:
            from PySide import QtGui
        except:
            # fine, we don't expect pyside to be present just yet
            self.log_debug("PySide not detected - Tank will add it to the setup now...")
        else:
            # looks like pyside is already working! No need to do anything
            self.log_debug("PySide detected - Tank will use the existing version.")
            return
        
        
        if sys.platform == "darwin":
            pyside_path = os.path.join(self.disk_location, "resources","pyside112_py26_qt471_mac", "python")
            sys.path.append(pyside_path)
        
        elif sys.platform == "win32":
            pyside_path = os.path.join(self.disk_location, "resources","pyside111_py26_qt471_win64", "python")
            sys.path.append(pyside_path)
            
        elif sys.platform == "linux2":        
            pyside_path = os.path.join(self.disk_location, "resources","pyside112_py26_qt471_linux", "python")
            sys.path.append(pyside_path)
            dll_path = os.path.join(self.disk_location, "resources","pyside112_py26_qt471_linux", "lib")
            path = os.environ.get("PATH", "")
            path += ";%s" % dll_path
            os.environ["PATH"] = path
        
        else:
            self.log_error("Unknown platform - cannot initialize PySide!")
        
        # now try to import it
        try:
            from PySide import QtGui
        except Exception, e:
            self.log_error("PySide could not be imported! Tank Apps using pyside will not "
                           "operate correctly! Error reported: %s" % e)
    
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
        self._maya_progress_bar = maya.mel.eval('$tmp = $gMainProgressBar')
        
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
        
    def __is_ui_enabled(self):
        """
        Returns true if there is a UI present.
        """
        if cmds.about(batch=True):
            # batch mode or prompt mode
            return False
        else:
            return True        

            

  
        
        
                
