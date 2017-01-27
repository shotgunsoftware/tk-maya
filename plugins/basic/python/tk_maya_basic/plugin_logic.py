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
import pymel.core as pm

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
from . import plugin_logging
from . import __name__ as PLUGIN_PACKAGE_NAME

MENU_LOGIN = "ShotgunMenuLogin"
MENU_LABEL = "Shotgun"

# Initialize a standalone logger to display messages in Maya script editor
# when the engine is not running while the user is logged out of Shotgun.
standalone_logger = logging.getLogger(PLUGIN_PACKAGE_NAME)
# Do not propagate messages to Maya ancestor logger to avoid duplicated logs.
standalone_logger.propagate = False
# Ignore messages less severe than the info ones.
standalone_logger.setLevel(logging.INFO)
# Use a custom logging handler to display messages in Maya script editor.
standalone_logger.addHandler(plugin_logging.PluginLoggingHandler())


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
        standalone_logger.info("Shotgun login was cancelled by the user.")
        return

    # Get rid of the displayed login menu since the engine menu will take over.
    # We need to make sure the Shotgun login dialog closing events have been
    # processed before deleting the menu to avoid a crash in Maya 2017.
    maya.utils.executeDeferred(_delete_login_menu)

    standalone_logger.debug("Bootstrapping Shotgun.")

    # Show a progress bar, and set its initial value and message.
    _show_progress_bar(0.0, "Loading...")

    # Before bootstrapping the engine for the first time around,
    # the toolkit manager may swap the toolkit core to its latest version.
    try:
        plugin_engine.bootstrap(
            user,
            progress_callback=_handle_bootstrap_progress,
            completed_callback=_handle_bootstrap_completed,
            failed_callback=_handle_bootstrap_failed
        )
    except Exception, e:
        # return to normal state
        _handle_bootstrap_failed(phase=None, exception=e)
        # also print the full call stack
        standalone_logger.exception("Shotgun reported the following exception during startup:")


def _handle_bootstrap_progress(progress_value, message):
    """
    Callback function that reports back on the toolkit and engine bootstrap progress.

    This function is executed in the main thread by the main event loop.

    :param progress_value: Current progress value, ranging from 0.0 to 1.0.
    :param message: Progress message to report.
    """

    standalone_logger.debug("Bootstrapping Shotgun: %s" % message)

    # Show the progress bar, and update its value and message.
    _show_progress_bar(progress_value, message)


def _handle_bootstrap_completed(engine):
    """
    Callback function that handles cleanup after successful completion of the bootstrap.

    This function is executed in the main thread by the main event loop.

    :param engine: Launched :class:`sgtk.platform.Engine` instance.
    """

    # Needed global to re-import the toolkit core.
    global sgtk

    # Re-import the toolkit core to ensure usage of a swapped in version.
    import sgtk

    # Hide the progress bar.
    _hide_progress_bar()

    # Report completion of the bootstrap.
    standalone_logger.info("Integration loaded.")

    # Add a logout menu item to the engine context menu.
    sgtk.platform.current_engine().register_command(
        "Log Out of Shotgun",
        _logout_user,
        {"type": "context_menu"}
    )


def _handle_bootstrap_failed(phase, exception):
    """
    Callback function that handles cleanup after failed completion of the bootstrap.

    This function is executed in the main thread by the main event loop.

    :param phase: Bootstrap phase that raised the exception,
                  ``ToolkitManager.TOOLKIT_BOOTSTRAP_PHASE`` or ``ToolkitManager.ENGINE_STARTUP_PHASE``.
    :param exception: Python exception raised while bootstrapping.
    """

    # Needed global to re-import the toolkit core.
    global sgtk

    if phase is None or phase == sgtk.bootstrap.ToolkitManager.ENGINE_STARTUP_PHASE:
        # Re-import the toolkit core to ensure usage of a swapped in version.
        import sgtk

    # Hide the progress bar.
    _hide_progress_bar()

    # Report the encountered exception.
    standalone_logger.error("Initialization failed: %s" % exception)

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
    main_progress_bar = pm.ui.MainProgressBar(minValue=0, maxValue=100, interruptable=False)
    main_progress_bar.beginProgress()

    # Set the main progress bar value and message.
    main_progress_bar.setProgress(int(progress_value * 100.0))
    main_progress_bar.setStatus("Shotgun: %s" % message)


def _hide_progress_bar():
    """
    Hides the progress bar.
    """

    # Hide the main progress bar (normally in the Help Line).
    main_progress_bar = pm.getMainProgressBar()
    main_progress_bar.endProgress()


def _create_login_menu():
    """
    Creates and displays a Shotgun user login menu.
    """

    # Creates the menu entry in the application menu bar.
    menu = pm.menu(MENU_LOGIN, label=MENU_LABEL, parent=pm.melGlobals["gMainWindow"])

    # Add the login menu item.
    pm.menuItem(
        parent=menu,
        label="Log In to Shotgun...",
        command=pm.Callback(_login_user)
    )

    pm.menuItem(parent=menu, divider=True)

    # Add the website menu items.
    pm.menuItem(
        parent=menu,
        label="Learn about Shotgun...",
        command=pm.Callback(_jump_to_website)
    )
    pm.menuItem(
        parent=menu,
        label="Try Shotgun for Free...",
        command=pm.Callback(_jump_to_signup)
    )


def _delete_login_menu():
    """
    Deletes the displayed Shotgun user login menu.
    """

    if pm.menu(MENU_LOGIN, exists=True):
        pm.deleteUI(MENU_LOGIN)


def _jump_to_website():
    """
    Jumps to the Shotgun website in the default web browser.
    """
    QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://www.shotgunsoftware.com"))


def _jump_to_signup():
    """
    Jumps to the Shotgun signup page in the default web browser.
    """
    QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://www.shotgunsoftware.com/signup"))
