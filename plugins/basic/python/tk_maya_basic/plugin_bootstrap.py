# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import sys

import maya.cmds

from . import plugin_logging
from . import Manifest

# Maya module root directory path.
MODULE_ROOT_PATH = os.environ.get("TK_MAYA_BASIC_ROOT")

def bootstrap_toolkit():
    """
    Bootstraps the Shotgun toolkit and its Maya engine, using the plug-in configuration data
    to drive some bootstrap options.

    :raises: ValueError when the plug-in 'tk-core' directory does not contain a single version directory.
    :raises: KeyError when a required key is missing in the plug-in configuration file.
    """
    # get our settings and config options
    manifest = Manifest(MODULE_ROOT_PATH)

    # Use a standalone logger to display messages in Maya script editor
    # before the Shotgun toolkit has been imported and its logging enabled.
    standalone_logger = plugin_logging.get_standalone_logger(manifest.name)

    # Retrieve the Shotgun toolkit core python directory path
    # and prepend it to the python module search path.
    if manifest.plugin_core_path not in sys.path:
        sys.path.insert(0, manifest.plugin_core_path)

    standalone_logger.info("Importing the Shotgun toolkit.")
    import sgtk

    # Use a custom logging handler to display messages in Maya script editor
    # before the Maya engine takes over logging.
    plugin_logging_handler = plugin_logging.PluginLoggingHandler(manifest.name)

    sgtk.LogManager().initialize_base_file_handler("tk-maya")
    sgtk.LogManager().initialize_custom_handler(plugin_logging_handler)

    if manifest.get_setting("debug_logging"):
        sgtk.LogManager().global_debug = True

    sgtk_logger = sgtk.LogManager.get_logger(manifest.name)

    sgtk_logger.debug("Booting up plugin with manifest %s" % manifest)

    # create boostrap manager
    toolkit_mgr = sgtk.bootstrap.ToolkitManager()
    toolkit_mgr.entry_point = manifest.entry_point
    toolkit_mgr.base_configuration = manifest.base_configuration
    toolkit_mgr.bundle_cache_fallback_paths = [manifest.bundle_cache_root]

    sgtk_logger.info("Starting the Maya engine.")

    # Remove the custom logging handler now that the Maya engine will take over logging.
    sgtk.LogManager().root_logger.removeHandler(plugin_logging_handler)

    # Ladies and Gentlemen, start your engines!
    maya.cmds.waitCursor(state=True)
    try:
        maya_engine = toolkit_mgr.bootstrap_engine("tk-maya", entity=None)
        maya_engine.register_command("log out", logout_callback)



    finally:
        # Make sure Maya wait cursor is turned off.
        maya.cmds.waitCursor(state=False)


def logout_callback():

    # tare down the engine
    # log out
    # turn the simple menu back on



def shutdown_toolkit():
    """
    Shutdown the Shotgun toolkit and its Maya engine.
    """
    import sgtk

    # get our settings and config options
    manifest = Manifest(MODULE_ROOT_PATH)

    sgtk_logger = sgtk.LogManager.get_logger(manifest.name)

    # Turn off your engine! Step away from the car!
    maya_engine = sgtk.platform.current_engine()
    if maya_engine:
        sgtk_logger.info("Stopping the Maya engine.")
        maya.cmds.waitCursor(state=True)
        try:
            maya_engine.destroy()
        finally:
            # Make sure Maya wait cursor is turned off.
            maya.cmds.waitCursor(state=False)
