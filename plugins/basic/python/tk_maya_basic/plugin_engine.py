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
    shotgun_site = os.environ.get("SHOTGUN_SITE")
    entity_type = os.environ.get("SHOTGUN_ENTITY_TYPE")
    entity_id = os.environ.get("SHOTGUN_ENTITY_ID")

    # Check that the shotgun site (if set) matches the site we are currently
    # logged in to. If not, issue a warning and ignore the entity type/id variables
    # TODO: Handle this correctly and pop up a login dialog in case of a site mismatch
    if shotgun_site and sg_user.host != shotgun_site:
        logger.warning("You are currently logged in to site %s but the plugin has been "
                       "requested to launch with context %s %s at %s. The plugin does not "
                       "currently support switching between sites and the contents of "
                       "SHOTGUN_ENTITY_TYPE and SHOTGUN_ENTITY_ID will therefore "
                       "be ignored." % (sg_user.host, entity_type, entity_id, shotgun_site)
                       )
        entity_type = None
        entity_id = None

    if (entity_type and not entity_id) or (not entity_type and entity_id):
        logger.error("Both environment variables SHOTGUN_ENTITY_TYPE and SHOTGUN_ENTITY_ID must be provided "
                     "to set a context entity. Shotgun will be initialized in site context.")

    if entity_id:
        # The entity id must be an integer number.
        try:
            entity_id = int(entity_id)
        except ValueError:
            logger.error("Environment variable SHOTGUN_ENTITY_ID value '%s' is not an integer number. "
                         "Shotgun will be initialized in site context." % entity_id)
            entity_id = None

    if entity_type and entity_id:
        # Set the entity to launch the engine for.
        entity = {"type": entity_type, "id": entity_id}
    else:
        # Set the entity to launch the engine in site context.
        entity = None

    logger.debug("Will launch the engine with entity: %s" % entity)

    # Remove the custom logging handler now that the engine will take over logging.
    sgtk.LogManager().root_logger.removeHandler(plugin_logging_handler)

    # Install the bootstrap progress reporting callback.
    toolkit_mgr.progress_callback = progress_callback

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
        logger.debug("The maya engine was already stopped!")
