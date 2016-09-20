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
import maya.mel as mel
import maya.utils


# Make sure the plug-in is running in Maya 2014 or later.
maya_version = mel.eval("getApplicationVersionAsFloat()")
if maya_version < 2014:
    msg = "Shotgun plug-in is not compatible with version %s of Maya; it requires Maya 2014 or later."
    OpenMaya2.MGlobal.displayError(msg % maya_version)
    sys.exit()


# Plug-in root directory path.
PLUGIN_ROOT_PATH = os.environ.get("TK_MAYA_BASIC_ROOT")

# Prepend the plug-in python package path to the python module search path.
plugin_python_path = os.path.join(PLUGIN_ROOT_PATH, "python")
if plugin_python_path not in sys.path:
    sys.path.insert(0, plugin_python_path)

# Set the plug-in root directory path constant of the plug-in python package.
import tk_maya_basic
tk_maya_basic.PLUGIN_ROOT_PATH = PLUGIN_ROOT_PATH

# Module manifest is required later to get the sgtk python package path.
from sgtk_plugin_basic import manifest

# Retrieve the Shotgun toolkit core included with the plug-in and
# prepend its python package path to the python module search path.
tkcore_python_path = manifest.get_sgtk_pythonpath(PLUGIN_ROOT_PATH)
if tkcore_python_path not in sys.path:
    sys.path.insert(0, tkcore_python_path)

# Module plugin_logic needs the sgtk python package path set previously.
from tk_maya_basic import plugin_logic


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

    # The name of this file minus its '.py' extension will be the plug-in name
    # displayed in Maya Plug-in Information window.

    # Set the plug-in vendor name and version number to display in Maya Plug-in Information window.
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
    maya.utils.executeDeferred(plugin_logic.bootstrap)


def uninitializePlugin(mobject):
    """
    Deregisters the plug-in services with Maya when this plug-in is unloaded.

    :param mobject: Maya plug-in MObject.
    :raises: Exception raised by maya.api.OpenMaya.MFnPlugin deregisterCommand method.
    """

    # Shutdown the plug-in logic.
    plugin_logic.shutdown()

    plugin = OpenMaya2.MFnPlugin(mobject)

    # Deregister all the plug-in custom commands.
    for cmd_class in PLUGIN_CMD_LIST:
        try:
            plugin.deregisterCommand(cmd_class.CMD_NAME)
        except:
            OpenMaya2.MGlobal.displayError("Failed to deregister command %s." % cmd_class.CMD_NAME)
