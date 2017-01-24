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

import maya.api.OpenMaya as OpenMaya2  # Python API 2.0
import maya.cmds as cmds
import maya.mel as mel
import maya.utils

PLUGIN_FILENAME = "shotgun.py"

def maya_useNewAPI():
    """
    The presence of this function lets Maya know that this plug-in uses Python API 2.0 objects.
    """
    pass


def initializePlugin(mobject):
    """
    Registers the plug-in services with Maya when this plug-in is loaded.

    :param mobject: Maya plug-in MObject.
    :raises: Exception raised by maya.api.OpenMaya.MFnPlugin registerCommand method.
    """
    # Make sure the plug-in is running in Maya 2014 or later.
    maya_version = mel.eval("getApplicationVersionAsFloat()")
    if maya_version < 2014:
        msg = "The Shotgun plug-in is not compatible with version %s of Maya; it requires Maya 2014 or later."
        OpenMaya2.MGlobal.displayError(msg % maya_version)
        # Ask Maya to unload the plug-in after returning from here.
        maya.utils.executeDeferred(cmds.unloadPlugin, PLUGIN_FILENAME)
        # Use the plug-in version to indicate that uninitialization should not be done when unloading it,
        # while keeping in mind that this version can be displayed in Maya Plug-in Information window.
        OpenMaya2.MFnPlugin(mobject, version="Unknown")
        # Return to Maya without further initializing the plug-in.
        return

    # We currently don't support running multiple engines
    # if an engine is already running, exit with an error.
    try:
        import sgtk

        if sgtk.platform.current_engine():
            msg = "The Shotgun plug-in cannot be loaded because Shotgun Toolkit is already running."
            OpenMaya2.MGlobal.displayError(msg)
            # Ask Maya to unload the plug-in after returning from here.
            maya.utils.executeDeferred(cmds.unloadPlugin, PLUGIN_FILENAME)
            # Use the plug-in version to indicate that uninitialization should not be done when unloading it,
            # while keeping in mind that this version can be displayed in Maya Plug-in Information window.
            OpenMaya2.MFnPlugin(mobject, version="Unknown")
            # Return to Maya without further initializing the plug-in.
            return
    except ImportError:
        # no sgtk available
        pass

    # Retrieve the plug-in root directory path, set by the module
    plugin_root_path = os.environ.get("TK_MAYA_BASIC_ROOT")

    # Prepend the plug-in python package path to the python module search path.
    plugin_python_path = os.path.join(plugin_root_path, "python")
    if plugin_python_path not in sys.path:
        sys.path.insert(0, plugin_python_path)

    # --- Import Core ---
    #
    # - If we are running the plugin built as a stand-alone unit,
    #   try to retrieve the path to sgtk core and add that to the pythonpath.
    #   When the plugin has been built, there is a sgtk_plugin_basic_maya
    #   module which we can use to retrieve the location of core and add it
    #   to the pythonpath.
    # - If we are running toolkit as part of a larger zero config workflow
    #   and not from a standalone workflow, we are running the plugin code
    #   directly from the engine folder without a bundle cache and with this
    #   configuration, core already exists in the pythonpath.

    try:
        from sgtk_plugin_basic_maya import manifest
        running_as_standalone_plugin = True
    except ImportError:
        running_as_standalone_plugin = False

    if running_as_standalone_plugin:
        # Retrieve the Shotgun toolkit core included with the plug-in and
        # prepend its python package path to the python module search path.
        tkcore_python_path = manifest.get_sgtk_pythonpath(plugin_root_path)
        sys.path.insert(0, tkcore_python_path)
        import sgtk

    else:
        # Running as part of the the launch process and as part of zero
        # config. The launch logic that started maya has already
        # added sgtk to the pythonpath.
        import sgtk

    # as early as possible, start up logging to the backend file
    sgtk.LogManager().initialize_base_file_handler("tk-maya")

    # Set the plug-in root directory path constant of the plug-in python package.
    from tk_maya_basic import constants
    from tk_maya_basic import plugin_logic

    # Set the plug-in vendor name and version number to display in Maya Plug-in Information window
    # alongside the plug-in name set by Maya from the name of this file minus its '.py' extension.
    OpenMaya2.MFnPlugin(
        mobject,
        vendor=constants.PLUGIN_AUTHOR,
        version=constants.PLUGIN_VERSION
    )

    # Bootstrap the plug-in logic once Maya has settled.
    maya.utils.executeDeferred(plugin_logic.bootstrap)


def uninitializePlugin(mobject):
    """
    Deregisters the plug-in services with Maya when this plug-in is unloaded.

    :param mobject: Maya plug-in MObject.
    :raises: Exception raised by maya.api.OpenMaya.MFnPlugin deregisterCommand method.
    """
    plugin = OpenMaya2.MFnPlugin(mobject)

    if plugin.version == "Unknown":
        # As requested earlier when initializing the plug-in,
        # return to Maya without further uninitializing it.
        return

    # Shutdown the plug-in logic.
    from tk_maya_basic import plugin_logic
    plugin_logic.shutdown()

