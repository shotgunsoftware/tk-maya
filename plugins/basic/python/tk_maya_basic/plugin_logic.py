# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import logging

import maya.utils
import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as OpenMayaUI
import maya.mel as mel
import maya.cmds as cmds

try:
    import shiboken2 as shiboken
except ImportError:
    import shiboken

# For now, import the Shotgun toolkit core included with the plug-in,
# but also re-import it later to ensure usage of a swapped in version.
import sgtk

# Knowing that the plug-in is only loaded for Maya 2014 and later,
# import PySide packages without having to worry about the version to use
# (PySide in Maya 2014-2015-2016 and PySide2 in Maya 2017 and later).
from sgtk.util.qt_importer import QtImporter

qt_importer = QtImporter()
QtCore = qt_importer.QtCore
QtGui = qt_importer.QtGui

from . import plugin_engine

MENU_LOGIN = "ShotGridMenuLogin"
MENU_LABEL = "ShotGrid"

logger = sgtk.LogManager.get_logger(__name__)


class ProgressHandler(QtCore.QObject):
    """
    An object that wraps a QTimer that is used to periodically check
    for updates that need to be made to the progress bar in Maya. This
    will always execute progress updates on the main thread.
    """

    PROGRESS_INTERVAL = 150  # milliseconds

    def __init__(self):
        ptr = OpenMayaUI.MQtUtil.mainWindow()
        parent = shiboken.wrapInstance(int(ptr), QtGui.QMainWindow)

        super(ProgressHandler, self).__init__(parent=parent)

        self._progress_value = None
        self._message = None
        self._timer = QtCore.QTimer(parent=self)

        self._timer.timeout.connect(self._update_progress)
        self._timer.start(self.PROGRESS_INTERVAL)

    @property
    def timer(self):
        """
        The QTimer instance that's updating progress.
        """
        return self._timer

    def _update_progress(self):
        """
        Sets progress. Must be run from the main thread!
        """
        if self._message is not None and self._progress_value is not None:
            _show_progress_bar(self._progress_value, self._message)
            self._message = None
            self._progress_value = None

    def _handle_bootstrap_progress(self, progress_value, message):
        """
        Callback function that reports back on the toolkit and engine bootstrap progress.

        .. note:: This method is, and must remain, thread safe. It will be called from
            a non-main thread.

        :param progress_value: Current progress value, ranging from 0.0 to 1.0.
        :param message: Progress message to report.
        """

        logger.debug("Bootstrapping ShotGrid: %s" % message)

        # Set some state that will trigger our timer to update the progress bar.
        self._progress_value = progress_value
        self._message = message


progress_handler = ProgressHandler()


def bootstrap():
    """
    Bootstraps the plug-in logic handling user login and logout.
    """
    if sgtk.authentication.ShotgunAuthenticator().get_default_user():
        # When the user is already authenticated, automatically log him/her in.
        _login_user()
    else:
        # When the user is not yet authenticated, display a login menu.
        _create_login_menu()


def shutdown():
    """
    Shutdowns the plug-in logic handling user login and logout.
    """

    if sgtk.platform.current_engine():
        # When the user is logged in with a running engine, shut down the engine.
        plugin_engine.shutdown()
    else:
        # When the user is logged out, delete the displayed login menu.
        _delete_login_menu()


def _login_user():
    """
    Logs in the user to Shotgun and starts the engine.
    """

    try:
        # When the user is not yet authenticated,
        # pop up the Shotgun login dialog to get the user's credentials,
        # otherwise, get the cached user's credentials.
        user = sgtk.authentication.ShotgunAuthenticator().get_user()

    except sgtk.authentication.AuthenticationCancelled:
        # When the user cancelled the Shotgun login dialog,
        # keep around the displayed login menu.
        OpenMaya.MGlobal.displayInfo("SG login was cancelled by the user.")
        return

    # Get rid of the displayed login menu since the engine menu will take over.
    # We need to make sure the Shotgun login dialog closing events have been
    # processed before deleting the menu to avoid a crash in Maya 2017.
    maya.utils.executeDeferred(_delete_login_menu)

    OpenMaya.MGlobal.displayInfo("Loading SG integration...")

    # Show a progress bar, and set its initial value and message.
    _show_progress_bar(0.0, "Loading...")

    # Before bootstrapping the engine for the first time around,
    # the toolkit manager may swap the toolkit core to its latest version.
    try:
        plugin_engine.bootstrap(
            user,
            progress_callback=progress_handler._handle_bootstrap_progress,
            completed_callback=_handle_bootstrap_completed,
            failed_callback=_handle_bootstrap_failed,
        )
    except Exception as e:
        # return to normal state
        _handle_bootstrap_failed(phase=None, exception=e)
        # also print the full call stack
        logger.exception("SG reported the following exception during startup:")


def _handle_bootstrap_completed(engine):
    """
    Callback function that handles cleanup after successful completion of the bootstrap.

    This function is executed in the main thread by the main event loop.

    :param engine: Launched :class:`sgtk.platform.Engine` instance.
    """
    progress_handler.timer.stop()

    # Needed global to re-import the toolkit core.
    global sgtk

    # Re-import the toolkit core to ensure usage of a swapped in version.
    import sgtk

    # Hide the progress bar.
    _hide_progress_bar()

    # Report completion of the bootstrap.
    logger.debug("Maya Plugin bootstrapped.")

    # Add a logout menu item to the engine context menu, but only if
    # running as a standalone plugin
    if sgtk.platform.current_engine().context.project is None:
        sgtk.platform.current_engine().register_command(
            "Log Out of ShotGrid", _logout_user, {"type": "context_menu"}
        )


def _handle_bootstrap_failed(phase, exception):
    """
    Callback function that handles cleanup after failed completion of the bootstrap.

    This function is executed in the main thread by the main event loop.

    :param phase: Bootstrap phase that raised the exception,
                  ``ToolkitManager.TOOLKIT_BOOTSTRAP_PHASE`` or ``ToolkitManager.ENGINE_STARTUP_PHASE``.
    :param exception: Python exception raised while bootstrapping.
    """
    progress_handler.timer.stop()

    # Needed global to re-import the toolkit core.
    global sgtk

    if phase is None or phase == sgtk.bootstrap.ToolkitManager.ENGINE_STARTUP_PHASE:
        # Re-import the toolkit core to ensure usage of a swapped in version.
        import sgtk

    # Hide the progress bar.
    _hide_progress_bar()

    # Report the encountered exception.
    # the message displayed last will be the one visible in the script editor,
    # so make sure this is the error message summary.
    OpenMaya.MGlobal.displayError(
        "An exception was raised during SG startup: %s" % exception
    )
    OpenMaya.MGlobal.displayError(
        "For details, see log files in %s" % sgtk.LogManager().log_folder
    )
    OpenMaya.MGlobal.displayError("Error loading SG integration.")

    # Clear the user's credentials to log him/her out.
    sgtk.authentication.ShotgunAuthenticator().clear_default_user()

    # Re-display the login menu.
    _create_login_menu()


def _logout_user():
    """
    Shuts down the engine and logs out the user of Shotgun.
    """

    # Shutting down the engine also get rid of the engine menu.
    plugin_engine.shutdown()

    # Clear the user's credentials to log him/her out.
    sgtk.authentication.ShotgunAuthenticator().clear_default_user()

    # Re-display the login menu.
    _create_login_menu()


def _show_progress_bar(progress_value, message):
    """
    Shows a non-interruptable progress bar, and sets its value and message.

    :param progress_value: Current progress value, ranging from 0.0 to 1.0.
    :param message: Progress message to report.
    """

    # Show the main progress bar (normally in the Help Line) making sure it uses
    # the bootstrap progress configuration (since it might have been taken over by another process).
    cmds.progressBar(
        _get_main_progress_bar_name(),
        edit=True,
        beginProgress=True,
        isMainProgressBar=True,
        isInterruptable=False,
        progress=int(progress_value * 100.0),
        status="ShotGrid: %s" % message,
    )


def _hide_progress_bar():
    """
    Hides the progress bar.
    """

    # Hide the main progress bar (normally in the Help Line).
    cmds.progressBar(_get_main_progress_bar_name(), edit=True, endProgress=True)


def _get_main_progress_bar_name():
    """
    Gets and returns the name of the main progress bar in Maya.
    :return:
    """
    return mel.eval("$retvalue = $gMainProgressBar;")


def _create_login_menu():
    """
    Creates and displays a Shotgun user login menu.
    """

    # Creates the menu entry in the application menu bar.
    menu = cmds.menu(
        MENU_LOGIN,
        label=MENU_LABEL,
        # Get the mel global variable value for main window.
        # In order to get the global variable in mel.eval we have to assign it to another temporary value
        # so that it returns the result.
        parent=mel.eval("$retvalue = $gMainWindow;"),
    )

    # Add the login menu item.
    cmds.menuItem(
        parent=menu, label="Log In to ShotGrid...", command=Callback(_login_user)
    )

    cmds.menuItem(parent=menu, divider=True)

    # Add the website menu items.
    cmds.menuItem(
        parent=menu,
        label="Learn about ShotGrid...",
        command=Callback(_jump_to_website),
    )
    cmds.menuItem(
        parent=menu,
        label="Try SG for Free...",
        command=Callback(_jump_to_signup),
    )


def _delete_login_menu():
    """
    Deletes the displayed Shotgun user login menu.
    """
    if cmds.menu(MENU_LOGIN, exists=True):
        cmds.deleteUI(MENU_LOGIN)


def _jump_to_website():
    """
    Jumps to the Shotgun website in the default web browser.
    """
    QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://www.shotgridsoftware.com"))


def _jump_to_signup():
    """
    Jumps to the Shotgun signup page in the default web browser.
    """
    QtGui.QDesktopServices.openUrl(
        QtCore.QUrl("https://www.shotgridsoftware.com/trial")
    )


class Callback(object):
    def __init__(self, callback):
        self.callback = callback

    def __call__(self, *_):
        """
        Execute the callback deferred to avoid potential problems with the command resulting in the menu
        being deleted, e.g. if the context changes resulting in an engine restart! - this was causing a
        segmentation fault crash on Linux.

        :param _: Accepts any args so that a callback might throw at it.
        For example a menu callback will pass the menu state. We accept these and ignore them.
        """
        # note that we use a single shot timer instead of cmds.evalDeferred as we were experiencing
        # odd behaviour when the deferred command presented a modal dialog that then performed a file
        # operation that resulted in a QMessageBox being shown - the deferred command would then run
        # a second time, presumably from the event loop of the modal dialog from the first command!
        #
        # As the primary purpose of this method is to detach the executing code from the menu invocation,
        # using a singleShot timer achieves this without the odd behaviour exhibited by evalDeferred.

        # This logic is borrowed from the menu_generation.py Callback class.

        QtCore.QTimer.singleShot(0, self._execute_within_exception_trap)

    def _execute_within_exception_trap(self):
        """
        Execute the callback and log any exception that gets raised which may otherwise have been
        swallowed by the deferred execution of the callback.
        """
        try:
            self.callback()
        except Exception:
            current_engine = sgtk.platform.current_engine()
            current_engine.logger.exception("An exception was raised from a menu item:")
