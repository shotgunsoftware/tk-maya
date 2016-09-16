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

from sgtk_plugin_basic_maya import manifest
from . import plugin_logging

from . import __name__ as PLUGIN_PACKAGE_NAME
from . import PLUGIN_ROOT_PATH


def bootstrap(sg_user, progress_callback, completed_callback, failed_callback):
    """
    Bootstraps the engine using the plug-in manifest data to drive some bootstrap options.

    :param sg_user: A :class:`sgtk.authentication.ShotgunUser` instance providing the logged in user credentials.
    :param progress_callback: Callback function that reports back on the toolkit and engine bootstrap progress.
    :param completed_callback: Callback function that handles cleanup after successful completion of the bootstrap.
    :param failed_callback: Callback function that handles cleanup after failed completion of the bootstrap.
    """

    # The first time around, import the toolkit core included with the plug-in,
    # but also re-import it later to ensure usage of a swapped in version.
    import sgtk

    # Use a custom logging handler to display messages in Maya script editor before the engine takes over logging.
    plugin_logging_handler = plugin_logging.PluginLoggingHandler(manifest.name)

    sgtk.LogManager().initialize_base_file_handler(manifest.engine_name)
    sgtk.LogManager().initialize_custom_handler(plugin_logging_handler)

    sgtk.LogManager().global_debug = bool(manifest.debug_logging)

    logger = sgtk.LogManager.get_logger(PLUGIN_PACKAGE_NAME)

    logger.debug("Bootstraping with manifest '%s'." % manifest.BUILD_INFO)

    # Create a boostrap manager for the logged in user with the plug-in configuration data.
    toolkit_mgr = sgtk.bootstrap.ToolkitManager(sg_user)

    # pass the manager to the manifest for basic init
    manifest.initialize_manager(toolkit_mgr, PLUGIN_ROOT_PATH)

    # check if the target core supports async init
    can_bootstrap_engine_async = hasattr(toolkit_mgr, "bootstrap_engine_async")
    if not can_bootstrap_engine_async:
        # Display the warning before the custom logging handler is removed.
        logger.warning("Cannot initialize Shotgun asynchronously with the loaded toolkit core version;"
                       " falling back on synchronous startup.")

    # Remove the custom logging handler now that the engine will take over logging.
    sgtk.LogManager().root_logger.removeHandler(plugin_logging_handler)

    if can_bootstrap_engine_async:

        # Install the bootstrap progress reporting callback.
        toolkit_mgr.progress_callback = progress_callback

        # Bootstrap a toolkit instance asynchronously in a background thread,
        # followed by launching the engine synchronously in the main application thread.
        # Before bootstrapping the engine for the first time around,
        # the toolkit manager may swap the toolkit core to its latest version.
        toolkit_mgr.bootstrap_engine_async(
            manifest.engine_name,
            completed_callback=completed_callback,
            failed_callback=failed_callback
        )

    else:

        # The imported version of the toolkit core is too old to provide asynchronous bootstrapping.
        # Fall back on synchronous bootstrapping of the engine in the main application thread,
        # while still calling the provided callbacks in order for the plug-in to work as expected.
        # Note that the provided progress reporting callback cannot be used since
        # this older version of the toolkit core expects a differend callback signature.

        try:

            engine = toolkit_mgr.bootstrap_engine(manifest.engine_name)

        except Exception, exception:

            # Handle cleanup after failed completion of the engine bootstrap.
            failed_callback(None, exception)

            return

        # Handle cleanup after successful completion of the engine bootstrap.
        completed_callback(engine)


def shutdown():
    """
    Shuts down the running engine.
    """

    # Re-import the toolkit core to ensure usage of a swapped in version.
    import sgtk

    logger = sgtk.LogManager.get_logger(PLUGIN_PACKAGE_NAME)

    engine = sgtk.platform.current_engine()
    if engine:

        logger.info("Stopping the %s engine." % manifest.engine_name)

        # Turn off your engine! Step away from the car!
        engine.destroy()

    else:
        logger.warning("The %s engine is already stopped!" % manifest.engine_name)
