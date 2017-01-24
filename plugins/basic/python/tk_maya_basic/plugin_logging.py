# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import logging

import maya.api.OpenMaya as OpenMaya2  # Python API 2.0
import maya.utils


class PluginLoggingHandler(logging.Handler):
    """
    Custom logging handler to display plug-in logging records in Maya script editor in a thread safe manner.
    """

    def __init__(self):
        """
        Initializes an instance of the plug-in logging handler.

        :param plugin_name: Plug-in name to include in the standard message format.
        """

        # Avoid using super() in order to be compatible with old-style classes found in older versions of logging.
        logging.Handler.__init__(self)

        # Set the handler to use a standard message format similar to the one used by the engine.
        logging_format = "Shotgun: %(message)s"
        self.setFormatter(logging.Formatter(logging_format))

    def emit(self, record):
        """
        Displays the specified logging record in Maya script editor according to its level number.

        This method is the implementation override of the 'logging.Handler' base class one.

        :param record: Logging record to display in Maya script editor.
        """
        # Give a standard format to the message.
        msg = self.format(record)

        # Display the message in Maya script editor in a thread safe manner.
        if record.levelno < logging.WARNING:
            fct = OpenMaya2.MGlobal.displayInfo
        elif record.levelno < logging.ERROR:
            fct = OpenMaya2.MGlobal.displayWarning
        else:
            fct = OpenMaya2.MGlobal.displayError

        maya.utils.executeInMainThreadWithResult(fct, msg)
