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
import maya.cmds
import maya.utils

# Maya module root directory path.
MODULE_ROOT_PATH = os.environ.get("TK_MAYA_BASIC_ROOT")

# prepend default plugin API location
plugin_python_path = os.path.join(MODULE_ROOT_PATH, "bundle_cache", "python")
if plugin_python_path not in sys.path:
    sys.path.insert(0, plugin_python_path)

# Prepend the plug-in python directory path to the python module search path.
plugin_python_path = os.path.join(MODULE_ROOT_PATH, "python")
if plugin_python_path not in sys.path:
    sys.path.insert(0, plugin_python_path)

# Import the required plug-in bootstrap module.
import sgtk_plugin
import tk_maya_basic.plugin_bootstrap as plugin_bootstrap

def maya_useNewAPI():
    """
    The presence of this function lets Maya know that this plug-in uses Python API 2.0 objects.
    """
    pass


class BootstrapToolkitCmd(OpenMaya2.MPxCommand):
    """
    Custom Maya command that bootstraps the Shotgun toolkit and its Maya engine.
    """

    # Custom Maya command name as known by 'maya.cmds'.
    CMD_NAME = sgtk_plugin.manifest.bootstrap_command

    def __init__(self):
        """
        Initializes an instance of the bootstrap toolkit command.
        """
        super(BootstrapToolkitCmd, self).__init__()

    def doIt(self, args):
        """
        Bootstraps the Shotgun toolkit and its Maya engine.

        This method is the implementation override of the 'OpenMaya2.MPxCommand' base class one.

        :param args: Maya MArgList of command arguments passed in by the caller.
        """
        plugin_bootstrap.bootstrap_toolkit()


class ShutdownToolkitCmd(OpenMaya2.MPxCommand):
    """
    Custom Maya command that shutdowns the Shotgun toolkit and its Maya engine.
    """

    # Custom Maya command name as known by 'maya.cmds'.
    CMD_NAME = sgtk_plugin.manifest.shutdown_command

    def __init__(self):
        """
        Initializes an instance of the shutdown toolkit command.
        """
        super(ShutdownToolkitCmd, self).__init__()

    def doIt(self, args):
        """
        Shutdowns the Shotgun toolkit and its Maya engine.

        This method is the implementation override of the 'OpenMaya2.MPxCommand' base class one.

        :param args: Maya MArgList of command arguments passed in by the caller.
        """
        plugin_bootstrap.shutdown_toolkit()


# List of all the custom Maya commands defined by this plug-in.
PLUGIN_CMD_LIST = (BootstrapToolkitCmd, ShutdownToolkitCmd)


def initializePlugin(mobject):
    """
    Registers the plug-in services with Maya when this plug-in is loaded.

    :param mobject: Maya plug-in MObject.
    :raises: Exception raised by maya.api.OpenMaya.MFnPlugin registerCommand method.
    """
    plugin = OpenMaya2.MFnPlugin(
        mobject,
        vendor="%s, %s" % (sgtk_plugin.manifest.author, sgtk_plugin.manifest.organization),
        version=sgtk_plugin.manifest.version
    )

    # Register all the plug-in custom commands.
    for cmdClass in PLUGIN_CMD_LIST:
        try:
            plugin.registerCommand(cmdClass.CMD_NAME, createCmdFunc=cmdClass)
        except:
            sys.stderr.write("Failed to register command %s.\n" % cmdClass.CMD_NAME)
            raise

    # Automatically bootstrap the Shotgun toolkit and its Maya engine once Maya has settled.
    # This is temporary until we have a proper login workflow/menu in place.
    maya.utils.executeDeferred("from maya import cmds; cmds.%s()" % BootstrapToolkitCmd.CMD_NAME)


def uninitializePlugin(mobject):
    """
    Deregisters the plug-in services with Maya when this plug-in is unloaded.

    :param mobject: Maya plug-in MObject.
    :raises: Exception raised by maya.api.OpenMaya.MFnPlugin deregisterCommand method.
    """

    # Shutdown the Shotgun toolkit and its Maya engine.
    maya.cmds.sgShutdownToolkit()

    plugin = OpenMaya2.MFnPlugin(mobject)

    # Deregister all the plug-in custom commands.
    for cmdClass in PLUGIN_CMD_LIST:
        try:
            plugin.deregisterCommand(cmdClass.CMD_NAME)
        except:
            sys.stderr.write("Failed to deregister command %s.\n" % cmdClass.CMD_NAME)
            raise
