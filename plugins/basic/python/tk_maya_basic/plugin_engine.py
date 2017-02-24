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

from . import constants
from . import plugin_logging

from . import __name__ as PLUGIN_PACKAGE_NAME


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
    plugin_logging_handler = plugin_logging.PluginLoggingHandler()
    sgtk.LogManager().initialize_custom_handler(plugin_logging_handler)

    logger = sgtk.LogManager.get_logger(PLUGIN_PACKAGE_NAME)

    # Create a boostrap manager for the logged in user with the plug-in configuration data.
    toolkit_mgr = sgtk.bootstrap.ToolkitManager(sg_user)
    toolkit_mgr.base_configuration = constants.BASE_CONFIGURATION
    toolkit_mgr.plugin_id = constants.PLUGIN_ID
    plugin_root_path = os.environ.get("TK_MAYA_BASIC_ROOT")
    toolkit_mgr.bundle_cache_fallback_paths = [os.path.join(plugin_root_path, "bundle_cache")]

    # Retrieve the Shotgun entity type and id when they exist in the environment.
    entity = toolkit_mgr.get_entity_from_environment()
    logger.debug("Will launch the engine with entity: %s" % entity)

    # Install the bootstrap progress reporting callback.
    toolkit_mgr.progress_callback = progress_callback

    # install a callback that turns off logging just before the
    # engine starts up its own logging
    callback = lambda ctx, log_handler=plugin_logging_handler: _pre_engine_start_callback(ctx, log_handler)
    toolkit_mgr.pre_engine_start_callback = callback

    # Bootstrap a toolkit instance asynchronously in a background thread,
    # followed by launching the engine synchronously in the main application thread.
    # Before bootstrapping the engine for the first time around,
    # the toolkit manager may swap the toolkit core to its latest version.
    toolkit_mgr.bootstrap_engine_async(
        "tk-maya",
        entity,
        completed_callback=completed_callback,
        failed_callback=failed_callback
    )


def _pre_engine_start_callback(ctx, log_handler):
    """
    Called just before the engine starts during bootstrap.

    :param ctx: Toolkit context we are bootstrapping into.
    :type ctx: :class:`sgtk.Context`
    :param log_handler: log handler for plugin
    """
    # Remove the custom logging handler now that the engine will take over logging.
    # This ensures that there is minimal gap in logging between the bootstrapper
    # and the engine.
    import sgtk
    sgtk.LogManager().root_logger.removeHandler(log_handler)


def shutdown():
    """
    Shuts down the running engine.
    """

    # Re-import the toolkit core to ensure usage of a swapped in version.
    import sgtk
    logger = sgtk.LogManager.get_logger(PLUGIN_PACKAGE_NAME)
    engine = sgtk.platform.current_engine()

    if engine:
        logger.info("Stopping the Shotgun engine.")
        # Close the various windows (dialogs, panels, etc.) opened by the engine.
        engine.close_windows()
        # Turn off your engine! Step away from the car!
        engine.destroy()

    else:
        logger.debug("The Shotgun engine was already stopped!")
