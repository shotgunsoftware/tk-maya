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

def bootstrap_sgtk():
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

    file_to_open = os.environ.get("SGTK_FILE_TO_OPEN")
    if file_to_open:
        # finally open the file
        cmds.file(file_to_open, force=True, open=True)

    # clean up temp env vars
    for var in ["SGTK_ENGINE", "SGTK_CONTEXT", "SGTK_FILE_TO_OPEN"]:
        if var in os.environ:
            del os.environ[var]


# Fire up Toolkit and the environment engine when there's time.
cmds.evalDeferred("bootstrap_sgtk()")
