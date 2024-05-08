# Copyright (c) 2024 Autodesk Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk Inc.


import maya.OpenMaya as OpenMaya
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

try:
    import sys

    sys.path.append("C:\\python_libs")
    import ptvsd

    ptvsd.enable_attach()
    ptvsd.wait_for_attach()
except:
    pass


class MayaSceneOperationsHook(HookBaseClass):
    """Hook class that sets up Maya events to update the Data Validation App."""

    def __init__(self, *args, **kwargs):
        super(MayaSceneOperationsHook, self).__init__(*args, **kwargs)
        self.__callback_ids = []

    def register_scene_events(self, reset_callback, change_callback):
        """
        Register events for when the scene has changed.

        The function reset_callback provided will reset the current Data Validation App,
        when called. The function change_callback provided will display a warning in the
        Data Validation App UI that the scene has changed and the current validatino state
        may be stale.

        :param reset_callback: Callback function to reset the Data Validation App.
        :type reset_callback: callable
        :param change_callback: Callback function to handle the changes to the scene.
        :type change_callback: callable
        """

        if self.__callback_ids:
            return  # Scene events already registered

        # Register Maya scene events.
        scene_message_events = [
            (OpenMaya.MSceneMessage.kAfterOpen, lambda x: reset_callback()),
            (OpenMaya.MSceneMessage.kAfterNew, lambda x: reset_callback()),
            (
                OpenMaya.MSceneMessage.kAfterImport,
                lambda x: change_callback(text="File imported"),
            ),
            (
                OpenMaya.MSceneMessage.kAfterImportReference,
                lambda x: change_callback(text="Reference imported"),
            ),
            (
                OpenMaya.MSceneMessage.kAfterCreateReference,
                lambda x: change_callback(text="Reference created"),
            ),
            (
                OpenMaya.MSceneMessage.kAfterRemoveReference,
                lambda x: change_callback(text="Reference removed"),
            ),
            (
                OpenMaya.MSceneMessage.kSceneUpdate,
                lambda x: change_callback(text="Scene updated"),
            ),
        ]
        for maya_msg, callback in scene_message_events:
            callback_id = OpenMaya.MSceneMessage.addCallback(maya_msg, callback)
            self.__callback_ids.append(callback_id)

        # Register Maya graph node events.
        self.__callback_ids.append(
            OpenMaya.MDGMessage.addNodeAddedCallback(
                lambda n, c: change_callback(text="Node added")
            )
        )
        self.__callback_ids.append(
            OpenMaya.MDGMessage.addNodeRemovedCallback(
                lambda n, c: change_callback(text="Node removed")
            )
        )

    def unregister_scene_events(self):
        """Unregister the scene events."""

        for callback_id in self.__callback_ids:
            OpenMaya.MMessage.removeCallback(callback_id)
        self.__callback_ids = []
