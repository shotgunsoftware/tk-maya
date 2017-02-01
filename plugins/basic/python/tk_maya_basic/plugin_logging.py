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
        """

        # Avoid using super() in order to be compatible with old-style classes found in older versions of logging.
        logging.Handler.__init__(self)

        # Set the handler to use a simple message format.
        self.setFormatter(logging.Formatter("Shotgun: %(message)s"))

    def emit(self, record):
        """
        Displays the specified logging record in Maya script editor according to its level number.

        This method is the implementation override of the 'logging.Handler' base class one.

        :param record: Logging record to display in Maya script editor.
        """

        # Give a standard format to the message:
        #     Shotgun: <message>
        # We use a simpler message format than the one used by the engine.
        if record.levelno < logging.INFO:
            msg = "Debug: %s" % self.format(record)
        else:
            msg = self.format(record)

        # Select Maya display function to use according to the logging record level.
        # We use MEL to display the message in order to have it surrounded by "//"
        # rather than "#" to go along with the messages emitted by the engine.
        if record.levelno < logging.WARNING:
            fct = OpenMaya2.MGlobal.displayInfo
        elif record.levelno < logging.ERROR:
            fct = OpenMaya2.MGlobal.displayWarning
        else:
            fct = OpenMaya2.MGlobal.displayError

        # Display the message in Maya script editor in a thread safe manner.
        maya.utils.executeInMainThreadWithResult(fct, msg)
