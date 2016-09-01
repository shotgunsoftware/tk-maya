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

from PySide import QtGui
import pymel.core as pm

# For now, import the Shotgun toolkit core included with the plug-in,
# but also re-import it later to ensure usage of a swapped in version.
import sgtk

from sgtk_plugin_basic import manifest
import plugin_engine
import plugin_logging

from . import __name__ as PLUGIN_PACKAGE_NAME


MENU_LOGIN = "ShotgunMenuLogin"
MENU_LABEL = "Shotgun"

ITEM_LABEL_LOGIN   = "Log In to Shotgun..."
ITEM_LABEL_LOGOUT  = "Log Out of Shotgun"
ITEM_LABEL_WEBSITE = "Learn about Shotgun..."

WEBSITE_URL = "https://shotgunsoftware.com"


# Initialize a standalone logger to display messages in Maya script editor
# when the engine is not running while the user is logged out of Shotgun.
standalone_logger = logging.getLogger(PLUGIN_PACKAGE_NAME)
# Do not propagate messages to Maya ancestor logger to avoid duplicated logs.
standalone_logger.propagate = False
# Ignore messages less severe than the debug ones.
standalone_logger.setLevel(logging.DEBUG)
# Use a custom logging handler to display messages in Maya script editor.
standalone_logger.addHandler(plugin_logging.PluginLoggingHandler(manifest.name))

# Main progress bar used when bootstrapping the toolkit and engine.
main_progress_bar = None


def bootstrap():
    """
    Bootstraps the plug-in logic handling user login and logout.
    """

    if sgtk.authentication.ShotgunAuthenticator().get_default_user():
        # When the user is already authenticated, automatically log him/her in.
        login_user()
    else:
        # When the user is not yet authenticated, display a login menu.
        create_login_menu()


def shutdown():
    """
    Shutdowns the plug-in logic handling user login and logout.
    """

    if sgtk.platform.current_engine():
        # When the user is logged in with a running engine, shut down the engine.
        plugin_engine.shutdown()
    else:
        # When the user is logged out, delete the displayed login menu.
        delete_login_menu()


def login_user():
    """
    Logs in the user to Shotgun and starts the engine.
    """

    # Needed global to create the main progress bar.
    global main_progress_bar

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
    delete_login_menu()

    # Create a non-interruptable main progress bar (normally in the Help Line).
    main_progress_bar = pm.ui.MainProgressBar(minValue=0, maxValue=100, interruptable=False)
    main_progress_bar.beginProgress()

    # Before bootstrapping the engine for the first time around,
    # the toolkit manager may swap the toolkit core to its latest version.
    plugin_engine.bootstrap(user,
                            progress_callback=handle_bootstrap_progress,
                            completed_callback=handle_bootstrap_completed,
                            failed_callback=handle_bootstrap_failed)


def handle_bootstrap_progress(step_number, message, current_index, maximum_index):
    """
    Callback function that reports back on the toolkit and engine bootstrap progress.

    This function is executed in the main thread by the main event loop.

    :param step_number: Current progress step number,
                        from 1 to ``sgtk.bootstrap.ToolkitManager.MAX_PROGRESS_STEP_NUMBER``.
    :param message: Progress message to report.
    :param current_index: Optional current item number being looped over.
    :param maximum_index: Optional maximum item number being looped over.
    """

    if maximum_index and maximum_index > 1:
        message = "%s (%s of %s)" % (message, current_index+1, maximum_index+1)

    message = "Bootstrapping %s: %s" % (manifest.engine_name, message)

    standalone_logger.info(message)

    # Update the main progress bar.
    progress_value = int((step_number - 1.0) / sgtk.bootstrap.ToolkitManager.MAX_PROGRESS_STEP_NUMBER * 100.0)
    main_progress_bar.setProgress(progress_value)
    main_progress_bar.setStatus(message)

    # Force Maya to process its UI events in order to refresh the main progress bar.
    QtGui.qApp.processEvents()


def handle_bootstrap_completed(engine):
    """
    Callback function that handles cleanup after successful completion of the bootstrap.

    This function is executed in the main thread by the main event loop.

    :param engine: Launched :class:`sgtk.platform.Engine` instance.
    """

    # Needed global to re-import the toolkit core.
    global sgtk

    # Needed global to get rid of the main progress bar.
    global main_progress_bar

    # Re-import the toolkit core to ensure usage of a swapped in version.
    import sgtk

    # Get rid of the main progress bar.
    main_progress_bar.endProgress()
    main_progress_bar = None

    # Add a logout menu item to the engine context menu.
    sgtk.platform.current_engine().register_command(ITEM_LABEL_LOGOUT,
                                                    logout_user,
                                                    {"type": "context_menu"})


def handle_bootstrap_failed(step, exception):
    """
    Callback function that handles cleanup after failed completion of the bootstrap.

    This function is executed in the main thread by the main event loop.

    :param step: Bootstrap step ("sgtk" or "engine") that raised the exception.
    :param exception: Python exception raised while bootstrapping.
    """

    # Needed global to re-import the toolkit core.
    global sgtk

    # Needed global to get rid of the main progress bar.
    global main_progress_bar

    if step == "engine":
        # Re-import the toolkit core to ensure usage of a swapped in version.
        import sgtk

    # Get rid of the main progress bar.
    main_progress_bar.endProgress()
    main_progress_bar = None

    # Report the encountered exception.
    standalone_logger.info("Bootstrapping %s failed: %s" % (manifest.engine_name, exception))

    # Clear the user's credentials to log him/her out.
    sgtk.authentication.ShotgunAuthenticator().clear_default_user()

    # Re-display the login menu.
    create_login_menu()


def logout_user():
    """
    Shuts down the engine and logs out the user of Shotgun.
    """

    # Shutting down the engine also get rid of the engine menu.
    plugin_engine.shutdown()

    # Clear the user's credentials to log him/her out.
    sgtk.authentication.ShotgunAuthenticator().clear_default_user()

    # Re-display the login menu.
    create_login_menu()


def create_login_menu():
    """
    Creates and displays a Shotgun user login menu.
    """

    # Creates the menu entry in the application menu bar.
    menu = pm.menu(MENU_LOGIN, label=MENU_LABEL, parent=pm.melGlobals["gMainWindow"])

    # Add the login menu item.
    pm.menuItem(parent=menu, label=ITEM_LABEL_LOGIN, command=pm.Callback(login_user))

    # Add the website menu item.
    pm.menuItem(parent=menu, label=ITEM_LABEL_WEBSITE, command=pm.Callback(jump_to_website))


def delete_login_menu():
    """
    Deletes the displayed Shotgun user login menu.
    """

    if pm.menu(MENU_LOGIN, exists=True):
        pm.deleteUI(MENU_LOGIN)


def jump_to_website():
    """
    Jumps to the Shotgun website in the defaul web browser.
    """

    # Import Qt locally from PySide since sgtk.platform.qt only works after engine initialization.
    from PySide import QtCore, QtGui

    QtGui.QDesktopServices.openUrl(QtCore.QUrl(WEBSITE_URL))
