# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
This file is loaded automatically by Maya at startup
It sets up the Toolkit context and prepares the tk-maya engine.
"""

import os
import maya.OpenMaya as OpenMaya
import maya.cmds as cmds

def start_toolkit_classic():
    """
    Parse enviornment variables for an engine name and
    serialized Context to use to startup Toolkit and
    the tk-maya engine and environment.
    """
    import sgtk
    logger = sgtk.LogManager.get_logger(__name__)

    logger.debug("Launching toolkit in classic mode.")

    # Get the name of the engine to start from the environement
    env_engine = os.environ.get("SGTK_ENGINE")
    if not env_engine:
        OpenMaya.MGlobal.displayError(
            "Shotgun: Missing required environment variable SGTK_ENGINE."
        )
        return

    # Get the context load from the environment.
    env_context = os.environ.get("SGTK_CONTEXT")
    if not env_context:
        OpenMaya.MGlobal.displayError(
            "Shotgun: Missing required environment variable SGTK_CONTEXT."
        )
        return
    try:
        # Deserialize the environment context
        context = sgtk.context.deserialize(env_context)
    except Exception, e:
        OpenMaya.MGlobal.displayError(
            "Shotgun: Could not create context! Shotgun Pipeline Toolkit will "
            "be disabled. Details: %s" % e
        )
        return

    try:
        # Start up the toolkit engine from the environment data
        logger.debug("Launching engine instance '%s' for context %s" % (env_engine, env_context))
        engine = sgtk.platform.start_engine(env_engine, context.sgtk, context)
    except Exception, e:
        OpenMaya.MGlobal.displayError(
            "Shotgun: Could not start engine: %s" % e
        )
        return


def start_toolkit_with_plugins():
    """
    Parse environment variables for a list of plugins to load that will
    ultimately startup Toolkit and the tk-maya engine and environment.
    """
    import sgtk
    logger = sgtk.LogManager.get_logger(__name__)

    logger.debug("Launching maya in plugin mode")

    for plugin_path in os.environ["SGTK_LOAD_MAYA_PLUGINS"].split(os.pathsep):
        # Find the appropriate "plugin" sub directory. Maya will not be
        # able to find any plugins under the base directory without this.
        if os.path.isdir(os.path.join(plugin_path, "plug-ins")):
            load_path = os.path.join(plugin_path, "plug-ins")
        elif os.path.isdir(os.path.join(plugin_path, "plugins")):
            load_path = os.path.join(plugin_path, "plugins")
        else:
            load_path = plugin_path

        # Load the plugins from the resolved path individually, as the
        # loadPlugin Maya command has difficulties loading all (*) plugins
        # from a path that contains a string in the form of 'v#.#.#':
        #   loadPlugin "/shotgun/site/project/install/app_store/tk-maya/v0.7.10/plugins/basic/plug-ins/*";
        #   // Error: line 1: Plug-in, "/shotgun/site/project/install/app_store/tk-maya/v0.7.10/plugins/basic/plug-ins/*", was not found on MAYA_PLUG_IN_PATH. //
        #   loadPlugin "/shotgun/site/project/install/app_store/tk-maya-no_version/plugins/basic/plug-ins/*";
        #   // Result: shotgun //
        for plugin_filename in os.listdir(load_path):
            if not plugin_filename.endswith(".py"):
                # Skip files/directories that are not plugins
                continue

            # Construct the OS agnostic full path to the plugin
            # and attempt to load the plugin. Note that the loadPlugin
            # command always returns a list, even when loading a single plugin.
            full_plugin_path = os.path.join(load_path, plugin_filename)
            logger.debug("Loading plugin %s" % full_plugin_path)

            loaded_plugins = cmds.loadPlugin(full_plugin_path)
            # note: loadPlugin returns a list of the loaded plugins
            if not loaded_plugins:
                OpenMaya.MGlobal.displayWarning(
                    "Shotgun: Could not load plugin: %s" % full_plugin_path
                )
                continue


def start_toolkit():
    """
    Import Toolkit and start up a tk-maya engine based on
    environment variables.
    """

    # Verify sgtk can be loaded.
    try:
        import sgtk
    except Exception, e:
        OpenMaya.MGlobal.displayError(
            "Shotgun: Could not import sgtk! Disabling for now: %s" % e
        )
        return

    # start up toolkit logging to file
    sgtk.LogManager().initialize_base_file_handler("tk-maya")

    if os.environ.get("SGTK_LOAD_MAYA_PLUGINS"):
        # Plugins will take care of initalizing everything
        start_toolkit_with_plugins()
    else:
        # Rely on the classic boostrapping method
        start_toolkit_classic()

    # Check if a file was specified to open and open it.
    file_to_open = os.environ.get("SGTK_FILE_TO_OPEN")
    if file_to_open:
        OpenMaya.MGlobal.displayInfo(
            "Shotgun: Opening '%s'..." % file_to_open
        )
        cmds.file(file_to_open, force=True, open=True)

    # Clean up temp env variables.
    del_vars = [
        "SGTK_ENGINE", "SGTK_CONTEXT", "SGTK_FILE_TO_OPEN",
        "SGTK_LOAD_MAYA_PLUGINS",
    ]
    for var in del_vars:
        if var in os.environ:
            del os.environ[var]


# Fire up Toolkit and the environment engine when there's time.
cmds.evalDeferred("start_toolkit()")
