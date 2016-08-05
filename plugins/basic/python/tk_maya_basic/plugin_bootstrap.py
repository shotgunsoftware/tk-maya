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

import sgtk_plugin

from . import plugin_logging

# Maya module root directory path.
MODULE_ROOT_PATH = os.environ.get("TK_MAYA_BASIC_ROOT")

def bootstrap_toolkit():
    """
    Bootstraps the Shotgun toolkit and its Maya engine, using the plug-in configuration data
    to drive some bootstrap options.

    :raises: ValueError when the plug-in 'tk-core' directory does not contain a single version directory.
    :raises: KeyError when a required key is missing in the plug-in configuration file.
    """
    # Use a standalone logger to display messages in Maya script editor
    # before the Shotgun toolkit has been imported and its logging enabled.
    standalone_logger = plugin_logging.get_standalone_logger(sgtk_plugin.manifest.name)

    standalone_logger.info("Importing the Shotgun toolkit.")
    import sgtk

    # Use a custom logging handler to display messages in Maya script editor
    # before the Maya engine takes over logging.
    plugin_logging_handler = plugin_logging.PluginLoggingHandler(sgtk_plugin.manifest.name)

    sgtk.LogManager().initialize_base_file_handler("tk-maya")
    sgtk.LogManager().initialize_custom_handler(plugin_logging_handler)

    if sgtk_plugin.manifest.debug_logging:
        sgtk.LogManager().global_debug = True

    sgtk_logger = sgtk.LogManager.get_logger(sgtk_plugin.manifest.name)

    sgtk_logger.debug("Booting up plugin with manifest %s" % sgtk_plugin.manifest.BUILD_INFO)

    # create boostrap manager
    toolkit_mgr = sgtk.bootstrap.ToolkitManager()
    toolkit_mgr.entry_point = sgtk_plugin.manifest.entry_point
    toolkit_mgr.base_configuration = sgtk_plugin.manifest.base_configuration
    toolkit_mgr.bundle_cache_fallback_paths = [os.path.join(MODULE_ROOT_PATH, "bundle_cache_root")]

    sgtk_logger.info("Starting the Maya engine.")

    # Remove the custom logging handler now that the Maya engine will take over logging.
    sgtk.LogManager().root_logger.removeHandler(plugin_logging_handler)

    # Ladies and Gentlemen, start your engines!
    maya.cmds.waitCursor(state=True)
    try:
        maya_engine = toolkit_mgr.bootstrap_engine("tk-maya", entity=None)
    finally:
        # Make sure Maya wait cursor is turned off.
        maya.cmds.waitCursor(state=False)


def shutdown_toolkit():
    """
    Shutdown the Shotgun toolkit and its Maya engine.
    """
    import sgtk

    sgtk_logger = sgtk.LogManager.get_logger(sgtk_plugin.manifest.name)

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
