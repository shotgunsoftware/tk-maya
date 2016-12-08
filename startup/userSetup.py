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

print "Sourcing /shotgun/gitrepos/tk-maya/startup/userSetup.py"

def bootstrap_sgtk_from_env():
    """
    Parse enviornment variables for an engine name and
    serialized Context to use to startup a Toolkit Engine
    and environment.
    """
    # Verify sgtk can be loaded.
    try:
        import sgtk
    except Exception, e:
        OpenMaya.MGlobal.displayError(
            "Shotgun: Could not import sgtk! Disabling for now: %s" % e
        )
        return

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
        engine = sgtk.platform.start_engine(env_engine, context.sgtk, context)
    except Exception, e:
        OpenMaya.MGlobal.displayError(
            "Shotgun: Could not start engine: %s" % e
        )
        return

def load_sgtk_plugins():
    for plugin_path in os.environ["SGTK_LOAD_MAYA_PLUGINS"].split(os.pathsep):
        # Find the appropriate "plugin" sub directory. Maya will not be
        # able to find any plugins under the base directory without this.
        if os.path.isdir(os.path.join(plugin_path, "plug-ins")):
            load_path = os.path.join(plugin_path, "plug-ins")
        elif os.path.isdir(os.path.join(plugin_path, "plugins")):
            load_path = os.path.join(plugin_path, "plugins")
        else:
            load_path = plugin_path

        # Display a message indicating what path plugins are 
        # being loaded from.
        OpenMaya.MGlobal.displayInfo(
            "Shotgun: Loading plugins from '%s'" % load_path
        )

        # Load the plugins from the resolved path
        loaded_plugins = cmds.loadPlugin("%s/*" % load_path)
        if not loaded_plugins:
            OpenMaya.MGlobal.displayWarning(
                "Shotgun: No plugins loaded from '%s'" % load_path
            )
            continue

        # Set the newly loaded plugins to autoload.
        for loaded_plugin in loaded_plugins:
            cmds.pluginInfo(loaded_plugin, e=True, autoload=True)


def start_toolkit():
    OpenMaya.MGlobal.displayInfo(
        "Shotgun: Starting up Toolkit"
    )
    if os.environ.get("SGTK_LOAD_MAYA_PLUGINS"):
        OpenMaya.MGlobal.displayInfo(
            "Shotgun: Loading Toolkit plugins ..."
        )
        load_sgtk_plugins()
    else:
        OpenMaya.MGlobal.displayInfo(
            "Shotgun: Bootstrapping Toolkit from environmment variables ..."
        )
        bootstrap_sgtk_from_env()

    file_to_open = os.environ.get("SGTK_FILE_TO_OPEN")
    if file_to_open:
        # finally open the file
        OpenMaya.MGlobal.displayInfo(
            "Shotgun: Opening '%s' ..." % file_to_open
        )
        cmds.file(file_to_open, force=True, open=True)

    # clean up temp env vars
    del_vars = [
        "SGTK_ENGINE", "SGTK_CONTEXT", "SGTK_FILE_TO_OPEN",
        "SGTK_LOAD_MAYA_PLUGINS",
    ]
    for var in del_vars:
        if var in os.environ:
            del os.environ[var]


# Fire up Toolkit and the environment engine when there's time.
cmds.evalDeferred("start_toolkit()")
