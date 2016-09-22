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


# List of all the custom Maya commands defined by the plug-in.
PLUGIN_CMD_LIST = []


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
        maya.utils.executeDeferred(cmds.unloadPlugin, "shotgun.py")
        # Use the plug-in version to indicate that uninitialization should not be done when unloading it,
        # while keeping in mind that this version can be displayed in Maya Plug-in Information window.
        OpenMaya2.MFnPlugin(mobject, version="Unknown")
        # Return to Maya without further initializing the plug-in.
        return

    # Make sure the Shotgun toolkit has not been loaded by a custom setup
    # brought forth by Shotgun Desktop or another pipeline tool.
    if "TK_MAYA_BASIC_SGTK" not in os.environ and "tank" in sys.modules:
        msg = "The Shotgun plug-in cannot be loaded because Shotgun Toolkit is already running. " \
              "Maya was launched from Shotgun Desktop or a custom Shotgun Toolkit setup."
        OpenMaya2.MGlobal.displayError(msg)
        # Ask Maya to unload the plug-in after returning from here.
        maya.utils.executeDeferred(cmds.unloadPlugin, "shotgun.py")
        # Use the plug-in version to indicate that uninitialization should not be done when unloading it,
        # while keeping in mind that this version can be displayed in Maya Plug-in Information window.
        OpenMaya2.MFnPlugin(mobject, version="Unknown")
        # Return to Maya without futher initializing the plug-in.
        return

    # Retrieve the plug-in root directory path.
    plugin_root_path = os.environ.get("TK_MAYA_BASIC_ROOT")

    # Prepend the plug-in python package path to the python module search path.
    plugin_python_path = os.path.join(plugin_root_path, "python")
    if plugin_python_path not in sys.path:
        sys.path.insert(0, plugin_python_path)

    from sgtk_plugin_basic_maya import manifest

    # Retrieve the Shotgun toolkit core included with the plug-in and
    # prepend its python package path to the python module search path.
    tkcore_python_path = manifest.get_sgtk_pythonpath(plugin_root_path)
    if tkcore_python_path not in sys.path:
        sys.path.insert(0, tkcore_python_path)

    # Set the plug-in root directory path constant of the plug-in python package.
    import tk_maya_basic
    tk_maya_basic.PLUGIN_ROOT_PATH = plugin_root_path

    # Set the plug-in vendor name and version number to display in Maya Plug-in Information window
    # alongside the plug-in name set by Maya from the name of this file minus its '.py' extension.
    plugin = OpenMaya2.MFnPlugin(
                 mobject,
                 vendor="%s, %s" % (manifest.author, manifest.organization),
                 version=manifest.version
             )

    # Register all the plug-in custom commands.
    for cmd_class in PLUGIN_CMD_LIST:
        try:
            plugin.registerCommand(cmd_class.CMD_NAME, createCmdFunc=cmd_class)
        except:
            OpenMaya2.MGlobal.displayError("Failed to register command %s." % cmd_class.CMD_NAME)

    # Bootstrap the plug-in logic once Maya has settled.
    from tk_maya_basic import plugin_logic
    maya.utils.executeDeferred(plugin_logic.bootstrap)

    # Keep a tag in the environment to remember that the plug-in imported the Shotgun toolkit core.
    os.environ["TK_MAYA_BASIC_SGTK"] = tkcore_python_path


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

    # Deregister all the plug-in custom commands.
    for cmd_class in PLUGIN_CMD_LIST:
        try:
            plugin.deregisterCommand(cmd_class.CMD_NAME)
        except:
            OpenMaya2.MGlobal.displayError("Failed to deregister command %s." % cmd_class.CMD_NAME)
