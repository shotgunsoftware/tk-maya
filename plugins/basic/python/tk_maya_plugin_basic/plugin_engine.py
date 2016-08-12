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

# For now, import the Shotgun toolkit core included with the plug-in,
# but also re-import it later to ensure usage of a swapped in version.
import sgtk as tk_core

from sgtk_plugin_basic import manifest
import plugin_logging

from . import PLUGIN_ROOT_PATH


def bootstrap(sg_user):
    """
    Bootstraps the engine using the plug-in configuration data to drive some bootstrap options.

    :param sg_user: A :class:`sgtk.authentication.ShotgunUser` instance providing the logged in user credentials.
    :raises: KeyError when a required key is missing in the plug-in configuration file.
    """

    # Needed global to re-import the toolkit core later.
    global tk_core

    # Use a custom logging handler to display messages in Maya script editor before the engine takes over logging.
    plugin_logging_handler = plugin_logging.PluginLoggingHandler(manifest.name)

    tk_core.LogManager().initialize_base_file_handler(manifest.engine_name)
    tk_core.LogManager().initialize_custom_handler(plugin_logging_handler)

    tk_core.LogManager().global_debug = bool(manifest.debug_logging)

    logger = tk_core.LogManager.get_logger(manifest.name)

    logger.debug("Bootstraping with manifest '%s'." % manifest.BUILD_INFO)

    # Retrieve the plug-in bundle cache path in order to set a fallback path for the bootstrap.
    bundle_cache_path = os.path.join(PLUGIN_ROOT_PATH, "bundle_cache")

    # Create a boostrap manager for the logged in user with the plug-in configuration data.
    toolkit_mgr = tk_core.bootstrap.ToolkitManager(sg_user)
    toolkit_mgr.entry_point                 = manifest.entry_point
    toolkit_mgr.base_configuration          = manifest.base_configuration
    toolkit_mgr.bundle_cache_fallback_paths = [bundle_cache_path]

    logger.info("Starting the %s engine." % manifest.engine_name)

    # Remove the custom logging handler now that the engine will take over logging.
    tk_core.LogManager().root_logger.removeHandler(plugin_logging_handler)

    # Ladies and Gentlemen, start your engines!
    # Before bootstrapping the engine for the first time around,
    # the toolkit manager may swap the toolkit core to its latest version.
    toolkit_mgr.bootstrap_engine(manifest.engine_name)

    # Re-import the toolkit core to ensure usage of a swapped in version.
    import sgtk as tk_core


def shutdown():
    """
    Shuts down the running engine.
    """

    logger = tk_core.LogManager.get_logger(manifest.name)

    engine = tk_core.platform.current_engine()
    if engine:

        logger.info("Stopping the %s engine." % manifest.engine_name)

        # Turn off your engine! Step away from the car!
        engine.destroy()

    else:
        logger.warning("The %s engine is already stopped!" % manifest.engine_name)
