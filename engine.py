# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
A Maya engine for Tank.

"""

import tank
import sys
import traceback
import time
import os
import maya.OpenMaya as OpenMaya
import pymel.core as pm
import maya.cmds as cmds

###############################################################################################
# methods to support the state when the engine cannot start up
# for example if a non-tank file is loaded in maya


class SceneEventWatcher(object):
    """
    Encapsulates event handling for multiple scene events and routes them
    into a single callback.

    This uses OpenMaya.MSceneMessage rather than scriptJobs as the former
    can safely be removed from inside of the callback itself

    Specifying run_once=True in the constructor causes all events to be
    cleaned up after the first one has triggered
    """
    def __init__(self, cb_fn,
                 scene_events = [OpenMaya.MSceneMessage.kAfterOpen,
                                 OpenMaya.MSceneMessage.kAfterSave,
                                 OpenMaya.MSceneMessage.kAfterNew],
                 run_once=False):
        """
        Constructor.

        :param cb_fn: Callcack to invoke everytime a scene event happens.
        :param scene_events: List of scene events to watch for. Defaults to new, open and save.
        :param run_once: If True, the watcher will notify only on the first event. Defaults to False.
        """
        self.__message_ids = []
        self.__cb_fn = cb_fn
        self.__scene_events = scene_events
        self.__run_once=run_once

        # register scene event callbacks:
        self.start_watching()

    def start_watching(self):
        """
        Starts watching for scene events.
        """
        # if currently watching then stop:
        self.stop_watching()

        # now add callbacks to watch for some scene events:
        for ev in self.__scene_events:
            try:
                msg_id = OpenMaya.MSceneMessage.addCallback(ev, SceneEventWatcher.__scene_event_callback, self);
            except Exception:
                # report warning...
                continue
            self.__message_ids.append(msg_id);

        # create a callback that will be run when Maya
        # exits so we can do some clean-up:
        msg_id = OpenMaya.MSceneMessage.addCallback(OpenMaya.MSceneMessage.kMayaExiting, SceneEventWatcher.__maya_exiting_callback, self)
        self.__message_ids.append(msg_id);

    def stop_watching(self):
        """
        Stops watching the Maya scene.
        """
        for msg_id in self.__message_ids:
            OpenMaya.MMessage.removeCallback(msg_id)
        self.__message_ids = []

    @staticmethod
    def __scene_event_callback(watcher):
        """
        Called on a scene event:
        """
        if watcher.__run_once:
            watcher.stop_watching()
        watcher.__cb_fn()

    @staticmethod
    def __maya_exiting_callback(watcher):
        """
        Called on Maya exit - should clean up any existing calbacks
        """
        watcher.stop_watching()

def refresh_engine(engine_name, prev_context, menu_name):
    """
    refresh the current engine
    """
    current_engine = tank.platform.current_engine()

    # first make sure that the disabled menu is removed, if it exists...
    menu_was_disabled = remove_sgtk_disabled_menu()

    # determine the tk instance and ctx to use:
    tk = current_engine.sgtk
    ctx = prev_context
    if pm.sceneName() == "":
        # if the scene opened is actually a file->new, then maintain the current
        # context/engine.
        if not menu_was_disabled:
            # just return the current engine - no need to restart it!
            return current_engine
    else:
        # loading a scene file
        new_path = pm.sceneName().abspath()

        # this file could be in another project altogether, so create a new
        # API instance.
        try:
            tk = tank.tank_from_path(new_path)
        except tank.TankError, e:
            OpenMaya.MGlobal.displayInfo("Shotgun: Engine cannot be started: %s" % e)
            # build disabled menu
            create_sgtk_disabled_menu(menu_name)
            return current_engine

        # and construct the new context for this path:
        ctx = tk.context_from_path(new_path, prev_context)

    if current_engine:
        # if context is unchanged and the menu was not previously disabled
        # then no need to rebuild the same engine again!
        if ctx == prev_context and not menu_was_disabled:
            return current_engine

        # tear down existing engine
        current_engine.log_debug("Ready to switch to context because of scene event !")
        current_engine.log_debug("Prev context: %s" % prev_context)
        current_engine.log_debug("New context: %s" % ctx)
        current_engine.destroy()

    # start new engine
    new_engine = None
    try:
        new_engine = tank.platform.start_engine(engine_name, tk, ctx)
    except tank.TankEngineInitError, e:
        OpenMaya.MGlobal.displayInfo("Shotgun: Engine cannot be started: %s" % e)
        # build disabled menu
        create_sgtk_disabled_menu(menu_name)
    else:
        new_engine.log_debug("Launched new engine for context!")

    return new_engine


def on_scene_event_callback(engine_name, prev_context, menu_name):
    """
    Callback that's run whenever a scene is saved or opened.
    """
    new_engine = None
    try:
        new_engine = refresh_engine(engine_name, prev_context, menu_name)
    except Exception:
        (exc_type, exc_value, exc_traceback) = sys.exc_info()
        message = ""
        message += "Message: Shotgun encountered a problem starting the Engine.\n"
        message += "Please contact support@shotgunsoftware.com\n\n"
        message += "Exception: %s - %s\n" % (exc_type, exc_value)
        message += "Traceback (most recent call last):\n"
        message += "\n".join( traceback.format_tb(exc_traceback))
        OpenMaya.MGlobal.displayError(message)
        new_engine = None

    if not new_engine:
        # don't have an engine but still want to watch for
        # future scene events:
        cb_fn = lambda en=engine_name, pc=prev_context, mn=menu_name:on_scene_event_callback(en, pc, mn)
        SceneEventWatcher(cb_fn, run_once=True)


def sgtk_disabled_message():
    """
    Explain why tank is disabled.
    """
    msg = ("Shotgun integration is disabled because it cannot recognize "
           "the currently opened file.  Try opening another file or restarting "
           "Maya.")

    cmds.confirmDialog( title="Sgtk is disabled",
                message=msg,
                button=["Ok"],
                defaultButton="Ok",
                cancelButton="Ok",
                dismissString="Ok" )


def create_sgtk_disabled_menu(menu_name):
    """
    Render a special "shotgun is disabled" menu
    """
    if cmds.about(batch=True):
        # don't create menu in batch mode
        return

    if pm.menu("ShotgunMenu", exists=True):
        pm.deleteUI("ShotgunMenu")

    sg_menu = pm.menu("ShotgunMenuDisabled", label=menu_name, parent=pm.melGlobals["gMainWindow"])
    pm.menuItem(label="Sgtk is disabled.", parent=sg_menu,
                command=lambda arg: sgtk_disabled_message())


def remove_sgtk_disabled_menu():
    """
    Remove the special "shotgun is disabled" menu if it exists

    :returns: True if the menu existed and was deleted
    """
    if cmds.about(batch=True):
        # don't create menu in batch mode
        return False

    if pm.menu("ShotgunMenuDisabled", exists=True):
        pm.deleteUI("ShotgunMenuDisabled")
        return True

    return False

###############################################################################################
# The Tank Maya engine

# for debug logging with time stamps
g_last_message_time = 0


class MayaEngine(tank.platform.Engine):
    """
    Toolkit engine for Maya.
    """

    ##########################################################################################
    # init and destroy

    def pre_app_init(self):
        """
        Runs after the engine is set up but before any apps have been initialized.
        """
        # unicode characters returned by the shotgun api need to be converted
        # to display correctly in all of the app windows
        from tank.platform.qt import QtCore
        # tell QT to interpret C strings as utf-8
        utf8 = QtCore.QTextCodec.codecForName("utf-8")
        QtCore.QTextCodec.setCodecForCStrings(utf8)
        self.log_debug("set utf-8 codec for widget text")

    def init_engine(self):
        """
        Initializes the Maya engine.
        """
        self.log_debug("%s: Initializing..." % self)

        # check that we are running an ok version of maya
        current_os = cmds.about(operatingSystem=True)
        if current_os not in ["mac", "win64", "linux64"]:
            raise tank.TankError("The current platform is not supported! Supported platforms "
                                 "are Mac, Linux 64 and Windows 64.")

        maya_ver = cmds.about(version=True)
        if maya_ver.startswith("Maya "):
            maya_ver = maya_ver[5:]
        if maya_ver.startswith(("2012", "2013", "2014", "2015", "2016")):
            self.log_debug("Running Maya version %s" % maya_ver)
        else:
            # show a warning that this version of Maya isn't yet fully tested with Shotgun:
            msg = ("The Shotgun Pipeline Toolkit has not yet been fully tested with Maya %s.  "
                   "You can continue to use Toolkit but you may experience bugs or instability."
                   "\n\nPlease report any issues to: support@shotgunsoftware.com"
                   % (maya_ver))

            # determine if we should show the compatibility warning dialog:
            show_warning_dlg = self.has_ui and "SGTK_COMPATIBILITY_DIALOG_SHOWN" not in os.environ
            if show_warning_dlg:
                # make sure we only show it once per session:
                os.environ["SGTK_COMPATIBILITY_DIALOG_SHOWN"] = "1"

                # split off the major version number - accomodate complex version strings and decimals:
                major_version_number_str = maya_ver.split(" ")[0].split(".")[0]
                if major_version_number_str and major_version_number_str.isdigit():
                    # check against the compatibility_dialog_min_version setting:
                    if int(major_version_number_str) < self.get_setting("compatibility_dialog_min_version"):
                        show_warning_dlg = False

            if show_warning_dlg:
                # Note, title is padded to try to ensure dialog isn't insanely narrow!
                title = "Warning - Shotgun Pipeline Toolkit Compatibility!                          " # padded!
                cmds.confirmDialog(title = title, message = msg, button = "Ok")

            # always log the warning to the script editor:
            self.log_warning(msg)

        self._maya_version = maya_ver

        if self.context.project is None:
            # must have at least a project in the context to even start!
            raise tank.TankError("The engine needs at least a project in the context "
                                 "in order to start! Your context: %s" % self.context)

        # Set the Maya project based on config
        self._set_project()

        # add qt paths and dlls
        self._init_pyside()

        # default menu name is Shotgun but this can be overriden
        # in the configuration to be Sgtk in case of conflicts
        self._menu_name = "Shotgun"
        if self.get_setting("use_sgtk_as_menu_name", False):
            self._menu_name = "Sgtk"

        # need to watch some scene events in case the engine needs rebuilding:
        cb_fn = lambda en=self.instance_name, pc=self.context, mn=self._menu_name:on_scene_event_callback(en, pc, mn)
        self.__watcher = SceneEventWatcher(cb_fn)
        self.log_debug("Registered open and save callbacks.")

    def post_app_init(self):
        """
        Called when all apps have initialized
        """
        # detect if in batch mode
        if self.has_ui:
            self._menu_handle = pm.menu("ShotgunMenu", label=self._menu_name, parent=pm.melGlobals["gMainWindow"])
            # create our menu handler
            tk_maya = self.import_module("tk_maya")
            self._menu_generator = tk_maya.MenuGenerator(self, self._menu_handle)
            # hook things up so that the menu is created every time it is clicked
            self._menu_handle.postMenuCommand(self._menu_generator.create_menu)

    def destroy_engine(self):
        """
        Stops watching scene events and tears down menu.
        """
        self.log_debug("%s: Destroying..." % self)

        # stop watching scene events:
        self.__watcher.stop_watching()

        # clean up UI:
        if self.has_ui and pm.menu(self._menu_handle, exists=True):
            pm.deleteUI(self._menu_handle)

    def _init_pyside(self):
        """
        Handles the pyside init
        """

        # first see if pyside2 is present
        try:
            from PySide2 import QtGui
        except:
            # fine, we don't expect PySide2 to be present just yet
            self.log_debug("PySide2 not detected - trying for PySide now...")
        else:
            # looks like pyside2 is already working! No need to do anything
            self.log_debug("PySide2 detected - the existing version will be used.")
            return

        # then see if pyside is present
        try:
            from PySide import QtGui
        except:
            # must be a very old version of Maya.
            self.log_debug("PySide not detected - it will be added to the setup now...")
        else:
            # looks like pyside is already working! No need to do anything
            self.log_debug("PySide detected - the existing version will be used.")
            return

        if sys.platform == "darwin":
            pyside_path = os.path.join(self.disk_location, "resources","pyside112_py26_qt471_mac", "python")
            self.log_debug("Adding pyside to sys.path: %s" % pyside_path)
            sys.path.append(pyside_path)

        elif sys.platform == "win32" and self._maya_version.startswith("2013"):
            # special 2013 version of pyside
            pyside_path = os.path.join(self.disk_location, "resources","pyside113_py26_qt471maya2013_win64", "python")
            self.log_debug("Adding pyside to sys.path: %s" % pyside_path)
            sys.path.append(pyside_path)
            dll_path = os.path.join(self.disk_location, "resources","pyside113_py26_qt471maya2013_win64", "lib")
            path = os.environ.get("PATH", "")
            path += ";%s" % dll_path
            os.environ["PATH"] = path

        elif sys.platform == "win32":
            # default windows version of pyside for 2011 and 2012
            pyside_path = os.path.join(self.disk_location, "resources","pyside111_py26_qt471_win64", "python")
            self.log_debug("Adding pyside to sys.path: %s" % pyside_path)
            sys.path.append(pyside_path)
            dll_path = os.path.join(self.disk_location, "resources","pyside111_py26_qt471_win64", "lib")
            path = os.environ.get("PATH", "")
            path += ";%s" % dll_path
            os.environ["PATH"] = path

        elif sys.platform == "linux2":
            pyside_path = os.path.join(self.disk_location, "resources","pyside112_py26_qt471_linux", "python")
            self.log_debug("Adding pyside to sys.path: %s" % pyside_path)
            sys.path.append(pyside_path)

        else:
            self.log_error("Unknown platform - cannot initialize PySide!")

        # now try to import it
        try:
            from PySide import QtGui
        except Exception, e:
            self.log_error("PySide could not be imported! Apps using pyside will not "
                           "operate correctly! Error reported: %s" % e)

    def _get_dialog_parent(self):
        """
        Get the QWidget parent for all dialogs created through
        show_dialog & show_modal.
        """
        # Find a parent for the dialog - this is the Maya mainWindow()
        from tank.platform.qt import QtGui
        import maya.OpenMayaUI as OpenMayaUI

        try:
            import shiboken
        except ImportError:
            import shiboken2 as shiboken

        ptr = OpenMayaUI.MQtUtil.mainWindow()
        parent = shiboken.wrapInstance(long(ptr), QtGui.QMainWindow)

        return parent

    @property
    def has_ui(self):
        """
        Detect and return if maya is running in batch mode
        """
        if cmds.about(batch=True):
            # batch mode or prompt mode
            return False
        else:
            return True

    ##########################################################################################
    # logging

    def log_debug(self, msg):
        """
        Log debug to the Maya script editor

        :param msg: The message to log
        """
        global g_last_message_time

        # get the time stamps
        prev_time = g_last_message_time
        current_time = time.time()

        # update global counter
        g_last_message_time = current_time

        if not self.get_setting("debug_logging", False):
            return

        msg = "Shotgun Debug [%0.3fs]: %s" % ((current_time-prev_time), msg)
        self.async_execute_in_main_thread(OpenMaya.MGlobal.displayInfo, msg)

    def log_info(self, msg):
        """
        Log info to the Maya script editor

        :param msg: The message to log
        """
        msg = "Shotgun: %s" % msg
        self.async_execute_in_main_thread(OpenMaya.MGlobal.displayInfo, msg)

    def log_warning(self, msg):
        """
        Log warning to the Maya script editor

        :param msg: The message to log
        """
        msg = "Shotgun: %s" % msg
        self.async_execute_in_main_thread(OpenMaya.MGlobal.displayWarning, msg)

    def log_error(self, msg):
        """
        Log error to the Maya script editor

        :param msg: The message to log
        """
        msg = "Shotgun: %s" % msg
        self.async_execute_in_main_thread(OpenMaya.MGlobal.displayError, msg)

    ##########################################################################################
    # scene and project management

    def _set_project(self):
        """
        Set the maya project
        """
        setting = self.get_setting("template_project")
        if setting is None:
            return

        tmpl = self.tank.templates.get(setting)
        fields = self.context.as_template_fields(tmpl)
        proj_path = tmpl.apply_fields(fields)
        self.log_info("Setting Maya project to '%s'" % proj_path)
        pm.mel.setProject(proj_path)

    ##########################################################################################
    # panel support

    def show_panel(self, panel_id, title, bundle, widget_class, *args, **kwargs):
        """
        Docks an app widget in a maya panel.

        :param panel_id: Unique identifier for the panel, as obtained by register_panel().
        :param title: The title of the panel
        :param bundle: The app, engine or framework object that is associated with this window
        :param widget_class: The class of the UI to be constructed. This must derive from QWidget.

        Additional parameters specified will be passed through to the widget_class constructor.

        :returns: the created widget_class instance
        """
        from tank.platform.qt import QtCore, QtGui

        tk_maya = self.import_module("tk_maya")

        self.log_debug("Begin showing panel %s" % panel_id)

        # The general approach below is as follows:
        #
        # 1. First create our qt tk app widget using QT.
        #    parent it to the maya main window to give it
        #    a well established parent. If the widget already
        #    exists, don't create it again, just retrieve its
        #    handle
        #
        # 2. Now create a native maya window and layout and
        #    attach our QT control to this. For this, we use
        #    the QT objectname property to do the bind. Note that
        #    the window won't show in the UI, this is all just
        #    setting up the hiearchy.
        #
        # 3. If a panel already exists, delete it. The panel
        #    no longer has the tk widget inside it, since that is
        #    parented to the window that was just created
        #
        # 4. Create a new panel using the dockControl command and
        #    pass our maya window in as the object to dock.
        #
        # 5. Lastly, since our widgets won't get notified about
        #    when the parent dock is closed (and sometimes when it
        #    needs redrawing), attach some QT event watchers to it
        #
        #
        # Note: It is possible that the close event and some of the
        #       refresh doesn't propagate down to the widget because
        #       of a misaligned parenting: The tk widget exists inside
        #       the pane layout but is still parented to the main
        #       maya window. It's possible that by setting up the parenting
        #       explicitly, the missing signals we have to compensate for
        #       may start to work. I tried a bunch of stuff but couldn't get
        #       it to work and instead resorted to the event watcher setup.

        # make a unique id for the app widget based off of the panel id
        widget_id = "wdgt_%s" % panel_id

        # create a maya window and layout
        window = pm.window()
        self.log_debug("Created window: %s" % window)
        maya_layout = pm.formLayout(parent=window)
        self.log_debug("Created layout %s" % maya_layout)

        if pm.control(widget_id, query=1, exists=1):
            self.log_debug("Toolkit widget already exists. Reparenting it...")
            # find the widget for later use
            for widget in QtGui.QApplication.allWidgets():
                if widget.objectName() == widget_id:
                    widget_instance = widget
                    break

        else:
            self.log_debug("Toolkit widget does not exist - creating it...")
            # parent the UI to the main maya window
            parent = self._get_dialog_parent()
            widget_instance = widget_class(*args, **kwargs)
            widget_instance.setParent(parent)
            # set its name - this means that it can also be found via the maya API
            widget_instance.setObjectName(widget_id)
            self.log_debug("Created %s (Object Name '%s')" % (widget_instance, widget_id))
            # apply external stylesheet
            self._apply_external_styleshet(bundle, widget_instance)

        # now reparent the widget instance to the layout
        # we can now refer to the QT widget via the widget name
        self.log_debug("Parenting widget %s to temporary window %s..." % (widget_id, maya_layout))
        pm.control(widget_id, edit=True, parent=maya_layout)

        # now attach our widget in all four corners to the maya layout so that it fills
        # the entire panel space
        pm.formLayout(maya_layout,
                      edit=True,
                      attachForm=[(widget_id, 'top', 1),
                                  (widget_id, 'left', 1),
                                  (widget_id, 'bottom', 1),
                                  (widget_id, 'right', 1)] )

        if pm.control(panel_id, query=1, exists=1):
            # exists already - delete it
            self.log_debug("Panel exists. Deleting it.")
            pm.deleteUI(panel_id)

        # lastly, move the maya window into a dock
        pm.dockControl(panel_id, area="right", content=window, label=title)
        self.log_debug("Created panel %s" % panel_id)

        # just like nuke, maya doesn't give us any hints when a panel is being closed.
        # QT widgets contained within this panel are just unparented and the floating
        # around, taking up memory.
        #
        # the visibleChangeCommand callback offered by the dockControl command
        # doesn't seem to work
        #
        # instead, install a QT event watcher to track when the parent
        # is closed and make sure that the tk widget payload is closed and
        # deallocated at the same time.
        #
        # Also, there are some obscure issues relating to UI refresh. These are also
        # resolved by looking at the stream of event and force triggering refreshes at the
        # right locations
        #
        tk_maya.install_callbacks(panel_id, widget_id)

        return widget_instance
