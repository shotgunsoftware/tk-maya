# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.


# Maya Module Installation
#
# In your Maya.env file, set environment variable MAYA_MODULE_PATH
# to the full path of your tk-plugin-mayabasic directory.
#
# For example, on Linux and Mac OS X:
#     MAYA_MODULE_PATH=$HOME/my_maya_modules/tk-plugin-mayabasic
#
# For example, on Windows:
#     MAYA_MODULE_PATH=%HOME%\my_maya_modules\tk-plugin-mayabasic
#
# Search Maya Help for details about environment variables and the Maya.env file.
#
# Caveats:
# - This Maya module file can only be processed by Maya 2013 and up.
# - No blank lines allowed between the module description line and its environment variable line.

+ tk-maya-basic 1.0.0 .
TK_MAYA_BASIC_ROOT:=.
