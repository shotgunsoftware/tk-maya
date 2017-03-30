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

    logger = sgtk.LogManager.get_logger(__name__)

    # get information about this plugin (plugin id & base config)
    plugin_info = _get_plugin_info()

    # Create a boostrap manager for the logged in user with the plug-in configuration data.
    toolkit_mgr = sgtk.bootstrap.ToolkitManager(sg_user)
    toolkit_mgr.base_configuration = plugin_info["base_configuration"]
    toolkit_mgr.plugin_id = plugin_info["plugin_id"]
    plugin_root_path = os.environ.get("TK_MAYA_BASIC_ROOT")
    toolkit_mgr.bundle_cache_fallback_paths = [os.path.join(plugin_root_path, "bundle_cache")]

    # Retrieve the Shotgun entity type and id when they exist in the environment.
    entity = toolkit_mgr.get_entity_from_environment()
    logger.debug("Will launch the engine with entity: %s" % entity)

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


def _get_plugin_info():
    """
    Returns a dictionary of information about the plugin of the form:

        {
            plugin_id: <plugin id>,
            base_configuration: <config descriptor>
        }
    """

    try:
        # first, see if we can get the info from the manifest. if we can, no
        # need to parse info.yml
        from sgtk_plugin_basic_maya import manifest
        plugin_id = manifest.plugin_id
        base_configuration = manifest.base_configuration
    except ImportError:
        # no manifest, running in situ from the engine. just parse the info.yml
        # file to get at the info we need.

        # import the yaml parser
        from tank_vendor import yaml

        # build the path to the info.yml file
        plugin_info_yml = os.path.abspath(
            os.path.join(
                __file__,
                "..",
                "..",
                "..",
                "info.yml"
            )
        )

        # open the yaml file and read the data
        with open(plugin_info_yml, "r") as plugin_info_fh:
            info_yml = yaml.load(plugin_info_fh)
            plugin_id = info_yml["plugin_id"]
            base_configuration = info_yml["base_configuration"]

    # return a dictionary with the required info
    return dict(
        plugin_id=plugin_id,
        base_configuration=base_configuration,
    )


def shutdown():
    """
    Shuts down the running engine.
    """

    # Re-import the toolkit core to ensure usage of a swapped in version.
    import sgtk
    logger = sgtk.LogManager.get_logger(__name__)
    engine = sgtk.platform.current_engine()

    if engine:
        logger.info("Stopping the Shotgun engine.")
        # Close the various windows (dialogs, panels, etc.) opened by the engine.
        engine.close_windows()
        # Turn off your engine! Step away from the car!
        engine.destroy()

    else:
        logger.debug("The Shotgun engine was already stopped!")
