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
A Maya engine for Shotgun Toolkit.

"""

import sgtk
import sys
import traceback
import re
import os
import logging
import maya.OpenMaya as OpenMaya
import maya.cmds as cmds
import maya.utils
import maya.mel as mel
from sgtk.platform import Engine

# Maya versions compatibility constants
VERSION_OLDEST_COMPATIBLE = 2022
VERSION_OLDEST_SUPPORTED = 2023
VERSION_NEWEST_SUPPORTED = 2026
# Caution: make sure compatibility_dialog_min_version default value in info.yml
# is equal to VERSION_NEWEST_SUPPORTED

# Although the engine has logging already, this logger is needed for callback based logging
# where an engine may not be present.
logger = sgtk.LogManager.get_logger(__name__)

###############################################################################################
# methods to support the state when the engine cannot start up
# for example if a non-sgtk file is loaded in maya


class SceneEventWatcher(object):
    """
    Encapsulates event handling for multiple scene events and routes them
    into a single callback.

    This uses OpenMaya.MSceneMessage rather than scriptJobs as the former
    can safely be removed from inside of the callback itself

    Specifying run_once=True in the constructor causes all events to be
    cleaned up after the first one has triggered
    """

    def __init__(
        self,
        cb_fn,
        scene_events=[
            OpenMaya.MSceneMessage.kAfterOpen,
            OpenMaya.MSceneMessage.kAfterSave,
            OpenMaya.MSceneMessage.kAfterNew,
        ],
        run_once=False,
    ):
        """
        Constructor.

        :param cb_fn: Callback to invoke every time a scene event happens.
        :param scene_events: List of scene events to watch for. Defaults to new, open and save.
        :param run_once: If True, the watcher will notify only on the first event. Defaults to False.
        """
        self.__message_ids = []
        self.__cb_fn = cb_fn
        self.__scene_events = scene_events
        self.__run_once = run_once

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
                msg_id = OpenMaya.MSceneMessage.addCallback(
                    ev, SceneEventWatcher.__scene_event_callback, self
                )
            except Exception:
                # report warning...
                continue
            self.__message_ids.append(msg_id)

        # create a callback that will be run when Maya
        # exits so we can do some clean-up:
        msg_id = OpenMaya.MSceneMessage.addCallback(
            OpenMaya.MSceneMessage.kMayaExiting,
            SceneEventWatcher.__maya_exiting_callback,
            self,
        )
        self.__message_ids.append(msg_id)

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
        Called on Maya exit - should clean up any existing callbacks
        """
        watcher.stop_watching()


def maya_scene_path():
    """
    Returns the path to the current scene.
    :return: str
    """
    # This logic is borrowed from the pymel implementation of sceneName().

    # Get the name for untitled files in Maya.
    untitled_file_name = mel.eval("untitledFileName()")
    path = OpenMaya.MFileIO.currentFile()

    file_name = os.path.basename(path)
    # Don't just use cmds.file(q=1, sceneName=1)
    # because it was sometimes returning an empty string,
    # even when there was a valid file
    # Check both the OpenMaya.MFileIO.currentFile() and the cmds.file(q=1, sceneName=1)
    # so as to be sure that no file is open. This should mean that if someone does have
    # a file open and it's named after the untitledFileName we should still be able to return the path.
    if file_name.startswith(untitled_file_name) and cmds.file(q=1, sceneName=1) == "":
        return None
    return path


def refresh_engine(engine_name, prev_context, menu_name):
    """
    refresh the current engine
    """
    logger.debug("Refreshing the engine, previous context: '%r'", prev_context)
    current_engine = sgtk.platform.current_engine()

    if not current_engine:
        # If we don't have an engine for some reason then we don't have
        # anything to do.
        logger.debug(
            "No currently initialized engine found; aborting the refresh of the engine"
        )
        return

    # Get the path of the current open Maya scene file.
    new_path = maya_scene_path()

    if new_path is None:
        # This is a File->New call, so we just leave the engine in the current
        # context and move on.
        logger.debug("New file call, aborting the refresh of the engine.")
        return

    # this file could be in another project altogether, so create a new
    # API instance.
    try:
        tk = sgtk.sgtk_from_path(new_path)
        logger.debug("Extracted sgtk instance: '%r' from path: '%r'", tk, new_path)

    except sgtk.TankError as e:
        logger.exception("Could not execute sgtk_from_path('%s')" % new_path)
        OpenMaya.MGlobal.displayInfo(
            "Flow Production Tracking: Engine cannot be started: %s" % e
        )
        # build disabled menu
        create_sgtk_disabled_menu(menu_name)
        return

    # shotgun menu may have been removed, so add it back in if its not already there.
    current_engine.create_shotgun_menu()
    # now remove the shotgun disabled menu if it exists.
    remove_sgtk_disabled_menu()

    # and construct the new context for this path:
    ctx = tk.context_from_path(new_path, prev_context)
    logger.debug(
        "Given the path: '%s' the following context was extracted: '%r'", new_path, ctx
    )

    if ctx != sgtk.platform.current_engine().context:
        logger.debug("Changing the context to '%r", ctx)
        current_engine.change_context(ctx)


def on_scene_event_callback(engine_name, prev_context, menu_name):
    """
    Callback that's run whenever a scene is saved or opened.
    """
    try:
        refresh_engine(engine_name, prev_context, menu_name)
    except Exception as e:
        logger.exception("Could not refresh the engine; error: '%s'" % e)
        (exc_type, exc_value, exc_traceback) = sys.exc_info()
        message = ""
        message += "Message: PTR encountered a problem changing the Engine's context.\n"
        message += "Please contact %s\n\n" % sgtk.support_url
        message += "Exception: %s - %s\n" % (exc_type, exc_value)
        message += "Traceback (most recent call last):\n"
        message += "\n".join(traceback.format_tb(exc_traceback))
        OpenMaya.MGlobal.displayError(message)


def sgtk_disabled_message():
    """
    Explain why sgtk is disabled.
    """
    msg = (
        "PTR integration is disabled because it cannot recognize "
        "the currently opened file.  Try opening another file or restarting "
        "Maya."
    )

    cmds.confirmDialog(
        title="Sgtk is disabled",
        message=msg,
        button=["Ok"],
        defaultButton="Ok",
        cancelButton="Ok",
        dismissString="Ok",
    )


def create_sgtk_disabled_menu(menu_name):
    """
    Render a special "PTR is disabled" menu
    """
    if cmds.about(batch=True):
        # don't create menu in batch mode
        return

    # destroy any pre-existing shotgun menu - the one that holds the apps
    if cmds.menu("ShotGridMenu", exists=True):
        cmds.deleteUI("ShotGridMenu")

    # create a new shotgun disabled menu if one doesn't exist already.
    if not cmds.menu("ShotGridMenuDisabled", exists=True):
        sg_menu = cmds.menu(
            "ShotGridMenuDisabled",
            label=menu_name,
            # Get the mel global variable value for main window.
            # In order to get the global variable in mel.eval we have to assign it to another temporary value
            # so that it returns the result.
            parent=mel.eval("$retvalue = $gMainWindow;"),
        )
        cmds.menuItem(
            label="Sgtk is disabled.",
            parent=sg_menu,
            command=lambda arg: sgtk_disabled_message(),
        )


def remove_sgtk_disabled_menu():
    """
    Remove the special "PTR is disabled" menu if it exists

    :returns: True if the menu existed and was deleted
    """
    if cmds.about(batch=True):
        # don't create menu in batch mode
        return False

    if cmds.menu("ShotGridMenuDisabled", exists=True):
        cmds.deleteUI("ShotGridMenuDisabled")
        return True

    return False


###############################################################################################
# The Tank Maya engine


class MayaEngine(Engine):
    """
    Toolkit engine for Maya.
    """

    __DIALOG_SIZE_CACHE = dict()

    @property
    def context_change_allowed(self):
        """
        Whether the engine allows a context change without the need for a restart.
        """
        return True

    @property
    def host_info(self):
        """
        :returns: A dictionary with information about the application hosting this engine.

        The returned dictionary is of the following form on success:

            {
                "name": "Maya",
                "version": "2017 Update 4",
            }

        The returned dictionary is of following form on an error preventing
        the version identification.

            {
                "name": "Maya",
                "version: "unknown"
            }
        """

        host_info = {"name": "Maya", "version": "unknown"}
        try:
            # The 'about -installedVersion' Maya MEL command returns:
            # - the app name (Maya, Maya LT, Maya IO)
            # - the major version (2017, 2018)
            # - the update version when applicable (update 4)
            maya_installed_version_string = cmds.about(installedVersion=True)

            # group(0) entire match
            # group(1) 'Maya' match (name)
            # group(2) LT, IO, etc ... match (flavor)
            # group(3) 2017 ... match (version)
            matches = re.search(
                r"(maya)\s+([a-zA-Z]+)?\s*(.*)",
                maya_installed_version_string,
                re.IGNORECASE,
            )
            host_info["name"] = matches.group(1).capitalize().rstrip().lstrip()
            host_info["version"] = matches.group(3)
            if matches.group(2):
                host_info["name"] = host_info["name"] + " " + matches.group(2)

        except:
            # Fallback to 'Maya' initialized above
            pass

        return host_info

    ##########################################################################################
    # init and destroy

    def pre_app_init(self):
        """
        Runs after the engine is set up but before any apps have been initialized.
        """
        # unicode characters returned by the shotgun api need to be converted
        # to display correctly in all of the app windows
        from sgtk.platform.qt import QtCore

        # tell QT to interpret C strings as utf-8
        utf8 = QtCore.QTextCodec.codecForName("utf-8")
        QtCore.QTextCodec.setCodecForCStrings(utf8)
        self.logger.debug("set utf-8 codec for widget text")

    def init_engine(self):
        """
        Initializes the Maya engine.
        """
        self.logger.debug("%s: Initializing...", self)

        # check that we are running an ok version of maya
        current_os = cmds.about(operatingSystem=True)
        if current_os not in ["mac", "win64", "linux64"]:
            raise sgtk.TankError(
                "The current platform is not supported! Supported platforms "
                "are Mac, Linux 64 and Windows 64."
            )

        url_doc_supported_versions = "https://help.autodesk.com/view/SGDEV/ENU/?guid=SGD_si_integrations_engine_supported_versions_html"

        maya_ver = cmds.about(version=True)
        if maya_ver.startswith("Maya "):
            maya_ver = maya_ver[5:]

        try:
            maya_major_version = int(cmds.about(majorVersion=True))
        except (TypeError, ValueError):
            message = """
Flow Production Tracking is not compatible with this version of {product}.

For information regarding support engine versions, please visit this page:
{url_doc_supported_versions}.
            """.strip()

            if self.has_ui:
                try:
                    cmds.confirmDialog(
                        button="Ok",
                        icon="critical",
                        # Padding to try to prevent the dialog being insanely narrow
                        title="Error - Flow Production Tracking Compatibility!".ljust(
                            70
                        ),
                        message=message.replace(
                            # Presence of \n breaks the Rich Text Format
                            "\n",
                            "<br>",
                        ).format(
                            product="Maya",
                            url_doc_supported_versions='<a href="{u}">{u}</a>'.format(
                                u=url_doc_supported_versions,
                            ),
                        ),
                    )
                except:  # nosec B110
                    # It is unlikely that the above message will go through
                    # on old versions of Maya (Python2, Qt4, ...).
                    # But there is nothing more we can do here.
                    pass

            raise sgtk.TankError(
                message.format(
                    product="Maya",
                    url_doc_supported_versions=url_doc_supported_versions,
                )
            )

        if maya_major_version < VERSION_OLDEST_COMPATIBLE:
            # Older that the oldest known compatible version
            message = """
Flow Production Tracking is no longer compatible with {product} versions older
than {version}.

For information regarding support engine versions, please visit this page:
{url_doc_supported_versions}
            """.strip()

            if self.has_ui:
                try:
                    cmds.confirmDialog(
                        button="Ok",
                        icon="critical",
                        title="Error - Flow Production Tracking Compatibility!".ljust(
                            # Padding to try to prevent the dialog being insanely narrow
                            70
                        ),
                        message=message.replace(
                            # Presence of \n breaks the Rich Text Format
                            "\n",
                            "<br>",
                        ).format(
                            product="Maya",
                            url_doc_supported_versions='<a href="{u}">{u}</a>'.format(
                                u=url_doc_supported_versions,
                            ),
                            version=VERSION_OLDEST_COMPATIBLE,
                        ),
                    )
                except:  # nosec B110
                    # It is unlikely that the above message will go through
                    # on old versions of Maya (Python2, Qt4, ...).
                    # But there is nothing more we can do here.
                    pass

            raise sgtk.TankError(
                message.format(
                    product="Maya",
                    url_doc_supported_versions=url_doc_supported_versions,
                    version=VERSION_OLDEST_COMPATIBLE,
                )
            )

        elif maya_major_version < VERSION_OLDEST_SUPPORTED:
            # Older than the oldest supported version
            self.logger.warning(
                "Flow Production Tracking no longer supports {product} "
                "versions older than {version}".format(
                    product="Maya",
                    version=VERSION_OLDEST_SUPPORTED,
                )
            )

            if self.has_ui:
                cmds.confirmDialog(
                    button="Ok",
                    icon="warning",
                    title="Warning - Flow Production Tracking Compatibility!".ljust(
                        # Padding to try to prevent the dialog being insanely narrow
                        70
                    ),
                    message="""
Flow Production Tracking no longer supports {product} versions older than
{version}.
You can continue to use Toolkit but you may experience bugs or instabilities.

For information regarding support engine versions, please visit this page:
{url_doc_supported_versions}
                    """.strip()
                    .replace(
                        # Presence of \n breaks the Rich Text Format
                        "\n",
                        "<br>",
                    )
                    .format(
                        product="Maya",
                        url_doc_supported_versions='<a href="{u}">{u}</a>'.format(
                            u=url_doc_supported_versions,
                        ),
                        version=VERSION_OLDEST_SUPPORTED,
                    ),
                )

        elif maya_major_version <= VERSION_NEWEST_SUPPORTED:
            # Within the range of supported versions
            self.logger.debug(f"Running Maya version {maya_ver}")

        else:  # Newer than the newest supported version (untested)
            self.logger.warning(
                "Flow Production Tracking has not yet been fully tested with "
                "{product} version {version}.".format(
                    product="Maya",
                    version=maya_major_version,
                )
            )

            if (
                # determine if we should show the compatibility warning dialog
                self.has_ui
                and "SGTK_COMPATIBILITY_DIALOG_SHOWN" not in os.environ
                and maya_major_version
                >= self.get_setting("compatibility_dialog_min_version")
            ):
                # make sure we only show it once per session:
                os.environ["SGTK_COMPATIBILITY_DIALOG_SHOWN"] = "1"

                cmds.confirmDialog(
                    button="Ok",
                    icon="warning",
                    title="Warning - Flow Production Tracking Compatibility!".ljust(
                        # Padding to try to prevent the dialog being insanely narrow
                        70
                    ),
                    message="""
Flow Production Tracking has not yet been fully tested with {product} version
{version}.
You can continue to use Toolkit but you may experience bugs or instabilities.

Please report any issues to:
{support_url}
                    """.strip()
                    .replace(
                        # Presence of \n breaks the Rich Text Format
                        "\n",
                        "<br>",
                    )
                    .format(
                        product="Maya",
                        support_url='<a href="{u}">{u}</a>'.format(u=sgtk.support_url),
                        version=maya_major_version,
                    ),
                )

        # In the case of Maya Windows, we have the possility of locking
        # up if we allow the PySide shim to import QtWebEngineWidgets. We can
        # stop that happening here by setting the environment variable.
        if current_os.startswith("win"):
            self.logger.debug(
                "Maya on Windows can deadlock if QtWebEngineWidgets "
                "is imported. Setting SHOTGUN_SKIP_QTWEBENGINEWIDGETS_IMPORT=1..."
            )
            os.environ["SHOTGUN_SKIP_QTWEBENGINEWIDGETS_IMPORT"] = "1"

        # Set the Maya project based on config
        self._set_project()

        # add qt paths and dlls
        self._init_pyside()

        # default menu name is Shotgun but this can be overriden
        # in the configuration to be Sgtk in case of conflicts
        self._menu_name = "Flow Production Tracking"
        if self.get_setting("use_short_menu_name", False):
            self._menu_name = "FPTR"

        self.__watcher = None
        if self.get_setting("automatic_context_switch", True):
            # need to watch some scene events in case the engine needs rebuilding:
            cb_fn = lambda en=self.instance_name, pc=self.context, mn=self._menu_name: on_scene_event_callback(
                en, pc, mn
            )
            self.__watcher = SceneEventWatcher(cb_fn)
            self.logger.debug("Registered open and save callbacks.")

        # Initialize a dictionary of Maya panels that have been created by the engine.
        # Each panel entry has a Maya panel name key and an app widget instance value.
        self._maya_panel_dict = {}

    def create_shotgun_menu(self):
        """
        Creates the main shotgun menu in maya.
        Note that this only creates the menu, not the child actions
        :return: bool
        """

        # only create the shotgun menu if not in batch mode and menu doesn't already exist
        if self.has_ui and not cmds.menu("ShotGridMenu", exists=True):
            self._menu_path = cmds.menu(
                "ShotGridMenu",
                label=self._menu_name,
                # Get the mel global variable value for main window.
                # In order to get the global variable in mel.eval we have to assign it to another temporary value
                # so that it returns the result.
                parent=mel.eval("$retvalue = $gMainWindow;"),
            )
            # create our menu handler
            tk_maya = self.import_module("tk_maya")
            self._menu_generator = tk_maya.MenuGenerator(self, self._menu_path)
            # hook things up so that the menu is created every time it is clicked
            cmds.menu(
                self._menu_path,
                edit=True,
                postMenuCommand=self._menu_generator.create_menu,
            )

            # Restore the persisted Shotgun app panels.
            tk_maya.panel_generation.restore_panels(self)
            return True

        return False

    def post_app_init(self):
        """
        Called when all apps have initialized
        """
        self.create_shotgun_menu()

        # Run a series of app instance commands at startup.
        self._run_app_instance_commands()

    def post_context_change(self, old_context, new_context):
        """
        Runs after a context change. The Maya event watching will be stopped
        and new callbacks registered containing the new context information.

        :param old_context: The context being changed away from.
        :param new_context: The new context being changed to.
        """
        # If we have a watcher, we need to stop watching.
        # If we will be watching in the new context we need to replace it with
        # a new watcher that has a callback registered with the new context baked in.
        # This will ensure that the context_from_path call that occurs after a
        # File->Open receives an up-to-date "previous" context.
        # If we aren't watching in the new context, this ensures we've stopped.
        if self.__watcher is not None:
            self.__watcher.stop_watching()

        if self.get_setting("automatic_context_switch", True):
            cb_fn = lambda en=self.instance_name, pc=new_context, mn=self._menu_name: on_scene_event_callback(
                engine_name=en,
                prev_context=pc,
                menu_name=mn,
            )
            self.__watcher = SceneEventWatcher(cb_fn)
            self.logger.debug(
                "Registered new open and save callbacks before changing context."
            )

        # Set the Maya project to match the new context.
        self._set_project()

    def _run_app_instance_commands(self):
        """
        Runs the series of app instance commands listed in the 'run_at_startup' setting
        of the environment configuration yaml file.
        """

        # Build a dictionary mapping app instance names to dictionaries of commands they registered with the engine.
        app_instance_commands = {}
        for command_name, value in self.commands.items():
            app_instance = value["properties"].get("app")
            if app_instance:
                # Add entry 'command name: command function' to the command dictionary of this app instance.
                command_dict = app_instance_commands.setdefault(
                    app_instance.instance_name, {}
                )
                command_dict[command_name] = value["callback"]

        # Run the series of app instance commands listed in the 'run_at_startup' setting.
        for app_setting_dict in self.get_setting("run_at_startup", []):
            app_instance_name = app_setting_dict["app_instance"]
            # Menu name of the command to run or '' to run all commands of the given app instance.
            setting_command_name = app_setting_dict["name"]

            # Retrieve the command dictionary of the given app instance.
            command_dict = app_instance_commands.get(app_instance_name)

            if command_dict is None:
                self.logger.warning(
                    "%s configuration setting 'run_at_startup' requests app '%s' that is not installed.",
                    self.name,
                    app_instance_name,
                )
            else:
                if not setting_command_name:
                    # Run all commands of the given app instance.
                    # Run these commands once Maya will have completed its UI update and be idle
                    # in order to run them after the ones that restore the persisted Shotgun app panels.
                    for command_name, command_function in command_dict.items():
                        self.logger.debug(
                            "%s startup running app '%s' command '%s'.",
                            self.name,
                            app_instance_name,
                            command_name,
                        )
                        maya.utils.executeDeferred(command_function)
                else:
                    # Run the command whose name is listed in the 'run_at_startup' setting.
                    # Run this command once Maya will have completed its UI update and be idle
                    # in order to run it after the ones that restore the persisted Shotgun app panels.
                    command_function = command_dict.get(setting_command_name)
                    if command_function:
                        self.logger.debug(
                            "%s startup running app '%s' command '%s'.",
                            self.name,
                            app_instance_name,
                            setting_command_name,
                        )
                        maya.utils.executeDeferred(command_function)
                    else:
                        known_commands = ", ".join(
                            "'%s'" % name for name in command_dict
                        )
                        self.logger.warning(
                            "%s configuration setting 'run_at_startup' requests app '%s' unknown command '%s'. "
                            "Known commands: %s",
                            self.name,
                            app_instance_name,
                            setting_command_name,
                            known_commands,
                        )

    def destroy_engine(self):
        """
        Stops watching scene events and tears down menu.
        """
        self.logger.debug("%s: Destroying...", self)

        # Clear the dictionary of Maya panels to keep the garbage collector happy.
        self._maya_panel_dict = {}

        if self.get_setting("automatic_context_switch", True):
            # stop watching scene events
            self.__watcher.stop_watching()

        # clean up UI:
        if self.has_ui and cmds.menu(self._menu_path, exists=True):
            cmds.deleteUI(self._menu_path)

    def _init_pyside(self):
        """
        Handles the pyside init
        """

        # First see if pyside6 is present
        try:
            from PySide6 import QtGui
        except:
            # fine, we don't expect PySide2 to be present just yet
            self.logger.debug("PySide6 not detected - trying for PySide2 now...")
        else:
            # looks like pyside2 is already working! No need to do anything
            self.logger.debug("PySide6 detected - the existing version will be used.")
            return

        # Next, check if PySide2 is present
        try:
            from PySide2 import QtGui
        except:
            # fine, we don't expect PySide2 to be present just yet
            self.logger.debug(
                "PySide2 not detected - it will be added to the setup now..."
            )
        else:
            # looks like pyside2 is already working! No need to do anything
            self.logger.debug("PySide2 detected - the existing version will be used.")
            return

    def show_dialog(self, title, *args, **kwargs):
        """
        If on Windows or Linux, this method will call through to the base implementation of
        this method without alteration. On OSX, we'll do some additional work to ensure that
        window parenting works properly, which requires some extra logic on that operating
        system beyond setting the dialog's parent.

        :param str title: The title of the dialog.

        :returns: the created widget_class instance
        """
        if not self.has_ui:
            self.log_error(
                "Sorry, this environment does not support UI display! Cannot show "
                "the requested window '%s'." % title
            )
            return

        from sgtk.platform.qt import QtCore, QtGui

        # create the dialog:
        dialog, widget = self._create_dialog_with_widget(title, *args, **kwargs)

        if not sgtk.util.is_macos():
            window_flags = dialog.windowFlags()

            if self.get_setting("enable_dialogs_minimize_button", False):
                window_flags |= QtGui.Qt.WindowMinimizeButtonHint

            dialog.setWindowFlags(window_flags)
            dialog.show()
        else:
            # When using the recipe here to get Z-depth ordering correct we also
            # inherit another feature that results in window size and position being
            # remembered. This size/pos retention happens across app boundaries, so
            # we would end up with one app inheriting the size from a previously
            # launched app, which was weird. To counteract that, we keep track of
            # the dialog's size before Maya gets ahold of it, and then resize it
            # right after it's shown. We'll also move the dialog to the center of
            # the desktop.
            center_screen = (
                QtGui.QApplication.desktop().availableGeometry(dialog).center()
            )
            self.__DIALOG_SIZE_CACHE[title] = dialog.size()

            # TODO: Get an explanation and document why we're having to do this. It appears to be
            # a Maya-only solution, because similar problems in other integrations, namely Nuke,
            # are not resolved in the same way. This fix comes to us from the Maya dev team, but
            # we've not yet spoken with someone that can explain why it fixes the problem.
            dialog.setWindowFlags(QtCore.Qt.Window)
            dialog.setProperty("saveWindowPref", True)
            dialog.show()

            # The resize has to happen after the dialog is shown, and we need
            # to move the dialog after the resize, since center of screen will be
            # relative to the final size of the dialog.
            dialog.resize(self.__DIALOG_SIZE_CACHE[title])
            dialog.move(center_screen - dialog.rect().center())

        # lastly, return the instantiated widget
        return widget

    def _get_dialog_parent(self):
        """
        Get the QWidget parent for all dialogs created through
        show_dialog & show_modal.
        """
        # Find a parent for the dialog - this is the Maya mainWindow()
        from sgtk.platform.qt import QtGui, shiboken
        import maya.OpenMayaUI as OpenMayaUI

        ptr = OpenMayaUI.MQtUtil.mainWindow()
        parent = shiboken.wrapInstance(int(ptr), QtGui.QMainWindow)

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

    def _emit_log_message(self, handler, record):
        """
        Called by the engine to log messages in Maya script editor.
        All log messages from the toolkit logging namespace will be passed to this method.

        :param handler: Log handler that this message was dispatched from.
                        Its default format is "[levelname basename] message".
        :type handler: :class:`~python.logging.LogHandler`
        :param record: Standard python logging record.
        :type record: :class:`~python.logging.LogRecord`
        """
        # Give a standard format to the message:
        #     Shotgun <basename>: <message>
        # where "basename" is the leaf part of the logging record name,
        # for example "tk-multi-shotgunpanel" or "qt_importer".
        if record.levelno < logging.INFO:
            formatter = logging.Formatter("Debug: PTR %(basename)s: %(message)s")
        else:
            formatter = logging.Formatter("PTR %(basename)s: %(message)s")

        msg = formatter.format(record)

        # Select Maya display function to use according to the logging record level.
        if record.levelno < logging.WARNING:
            fct = OpenMaya.MGlobal.displayInfo
        elif record.levelno < logging.ERROR:
            fct = OpenMaya.MGlobal.displayWarning
        else:
            fct = OpenMaya.MGlobal.displayError

        # Display the message in Maya script editor in a thread safe manner.
        self.async_execute_in_main_thread(fct, msg)

    ##########################################################################################
    # scene and project management

    def _set_project(self):
        """
        Set the maya project
        """
        setting = self.get_setting("template_project")
        if setting is None:
            return

        tmpl = self.sgtk.templates.get(setting)
        fields = self.context.as_template_fields(tmpl)
        proj_path = tmpl.apply_fields(fields)
        self.logger.info("Setting Maya project to '%s'", proj_path)

        try:
            cmds.workspace(proj_path, openWorkspace=True)
        except RuntimeError as e:
            self.logger.error("Maya failed to open Project. Error: %s", str(e))
            raise e

        cmds.workspace(proj_path, openWorkspace=True)

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
        from sgtk.platform.qt import QtGui

        tk_maya = self.import_module("tk_maya")

        self.logger.debug("Begin showing panel %s", panel_id)

        # The general approach below is as follows:
        #
        # 1. First create our qt tk app widget using QT.
        #    parent it to the Maya main window to give it
        #    a well established parent. If the widget already
        #    exists, don't create it again, just retrieve its
        #    handle.
        #
        # 2. Now dock our QT control in a new panel tab of
        #    Maya Channel Box dock area. We use the
        #    Qt object name property to do the bind.
        #
        # 3. Lastly, since our widgets won't get notified about
        #    when the parent dock is closed (and sometimes when it
        #    needs redrawing), attach some QT event watchers to it
        #
        # Note: It is possible that the close event and some of the
        #       refresh doesn't propagate down to the widget because
        #       of a misaligned parenting: The tk widget exists inside
        #       the pane layout but is still parented to the main
        #       Maya window. It's possible that by setting up the parenting
        #       explicitly, the missing signals we have to compensate for
        #       may start to work. I tried a bunch of stuff but couldn't get
        #       it to work and instead resorted to the event watcher setup.

        # make a unique id for the app widget based off of the panel id
        widget_id = tk_maya.panel_generation.SHOTGUN_APP_PANEL_PREFIX + panel_id

        if cmds.control(widget_id, query=1, exists=1):
            self.logger.debug("Reparent existing toolkit widget %s.", widget_id)
            # Find the Shotgun app panel widget for later use.
            for widget in QtGui.QApplication.allWidgets():
                if widget.objectName() == widget_id:
                    widget_instance = widget
                    # Reparent the Shotgun app panel widget under Maya main window
                    # to prevent it from being deleted with the existing Maya panel.
                    self.logger.debug(
                        "Reparenting widget %s under Maya main window.", widget_id
                    )
                    parent = self._get_dialog_parent()
                    widget_instance.setParent(parent)
                    # The Shotgun app panel was retrieved from under an existing Maya panel.
                    break
        else:
            self.logger.debug("Create toolkit widget %s", widget_id)
            # parent the UI to the main maya window
            parent = self._get_dialog_parent()
            widget_instance = widget_class(*args, **kwargs)
            widget_instance.setParent(parent)
            # set its name - this means that it can also be found via the maya API
            widget_instance.setObjectName(widget_id)
            self.logger.debug("Created widget %s: %s", widget_id, widget_instance)
            # apply external stylesheet
            self._apply_external_styleshet(bundle, widget_instance)
            # The Shotgun app panel was just created.

        # Dock the Shotgun app panel into a new Maya panel in the active Maya window.
        maya_panel_name = tk_maya.panel_generation.dock_panel(
            self, widget_instance, title
        )

        # Add the new panel to the dictionary of Maya panels that have been created by the engine.
        # The panel entry has a Maya panel name key and an app widget instance value.
        # Note that the panel entry will not be removed from the dictionary when the panel is
        # later deleted since the added complexity of updating the dictionary from our panel
        # close callback is outweighed by the limited length of the dictionary that will never
        # be longer than the number of apps configured to be runnable by the engine.
        self._maya_panel_dict[maya_panel_name] = widget_instance

        return widget_instance

    def close_windows(self):
        """
        Closes the various windows (dialogs, panels, etc.) opened by the engine.
        """

        # Make a copy of the list of Tank dialogs that have been created by the engine and
        # are still opened since the original list will be updated when each dialog is closed.
        opened_dialog_list = self.created_qt_dialogs[:]

        # Loop through the list of opened Tank dialogs.
        for dialog in opened_dialog_list:
            dialog_window_title = dialog.windowTitle()
            try:
                # Close the dialog and let its close callback remove it from the original dialog list.
                self.logger.debug("Closing dialog %s.", dialog_window_title)
                dialog.close()
            except Exception as exception:
                self.logger.error(
                    "Cannot close dialog %s: %s", dialog_window_title, exception
                )

        # Loop through the dictionary of Maya panels that have been created by the engine.
        for maya_panel_name, widget_instance in self._maya_panel_dict.items():
            # Make sure the Maya panel is still opened.
            if cmds.control(maya_panel_name, query=True, exists=True):
                try:
                    # Reparent the Shotgun app panel widget under Maya main window
                    # to prevent it from being deleted with the existing Maya panel.
                    self.logger.debug(
                        "Reparenting widget %s under Maya main window.",
                        widget_instance.objectName(),
                    )
                    parent = self._get_dialog_parent()
                    widget_instance.setParent(parent)
                    # The Maya panel can now be deleted safely.
                    self.logger.debug("Deleting Maya panel %s.", maya_panel_name)
                    cmds.deleteUI(maya_panel_name)
                except Exception as exception:
                    self.logger.error(
                        "Cannot delete Maya panel %s: %s", maya_panel_name, exception
                    )

        # Clear the dictionary of Maya panels now that they were deleted.
        self._maya_panel_dict = {}
