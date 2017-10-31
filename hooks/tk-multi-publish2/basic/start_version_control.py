# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import maya.cmds as cmds
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class MayaStartVersionControlPlugin(HookBaseClass):
    """
    Simple plugin to insert a version number into the maya file path if one
    does not exist.
    """

    @property
    def icon(self):
        """
        Path to an png icon on disk
        """

        # look for icon one level up from this hook's folder in "icons" folder
        return os.path.join(
            self.disk_location,
            os.pardir,
            "icons",
            "version_up.png"
        )

    @property
    def name(self):
        """
        One line display name describing the plugin
        """
        return "Begin file versioning"

    @property
    def description(self):
        """
        Verbose, multi-line description of what the plugin does. This can
        contain simple html for formatting.
        """
        return """
        Adds a version number to the filename.<br><br>

        Once a version number exists in the file, the publishing will
        automatically bump the version number. For example,
        <code>filename.ext</code> will be saved to
        <code>filename.v001.ext</code>.<br><br>

        If the session has not been saved, validation will fail and a button
        will be provided in the logging output to save the file.<br><br>

        If a file already exists on disk with a version number, validation will
        fail and the logging output will include button to save the file to a
        different name.<br><br>
        """

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["maya.*", "file.maya"]
        """
        return ["maya.session"]

    @property
    def settings(self):
        """
        Dictionary defining the settings that this plugin expects to receive
        through the settings parameter in the accept, validate, publish and
        finalize methods.

        A dictionary on the following form::

            {
                "Settings Name": {
                    "type": "settings_type",
                    "default": "default_value",
                    "description": "One line description of the setting"
            }

        The type string should be one of the data types that toolkit accepts as
        part of its environment configuration.
        """
        return {}

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any
        interest to this plugin. Only items matching the filters defined via the
        item_filters property will be presented to this method.

        A publish task will be generated for each item accepted here. Returns a
        dictionary with the following booleans:

            - accepted: Indicates if the plugin is interested in this value at
                all. Required.
            - enabled: If True, the plugin will be enabled in the UI, otherwise
                it will be disabled. Optional, True by default.
            - visible: If True, the plugin will be visible in the UI, otherwise
                it will be hidden. Optional, True by default.
            - checked: If True, the plugin will be checked in the UI, otherwise
                it will be unchecked. Optional, True by default.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process

        :returns: dictionary with boolean keys accepted, required and enabled
        """

        path = _session_path()

        if path:
            version_number = self._get_version_number(path, item)
            if version_number is not None:
                self.logger.info(
                    "Maya '%s' plugin rejected the current session..." %
                    (self.name,)
                )
                self.logger.info(
                    "  There is already a version number in the file...")
                self.logger.info("  Maya file path: %s" % (path,))
                return {"accepted": False}
        else:
            # the session has not been saved before (no path determined).
            # provide a save button. the session will need to be saved before
            # validation will succeed.
            self.logger.warn(
                "The Maya session has not been saved.",
                extra=_get_save_as_action()
            )

        self.logger.info(
            "Maya '%s' plugin accepted the current session." %
            (self.name,),
            extra=_get_version_docs_action()
        )

        # accept the plugin, but don't force the user to add a version number
        # (leave it unchecked)
        return {
            "accepted": True,
            "checked": False
        }

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish.

        Returns a boolean to indicate validity.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process

        :returns: True if item is valid, False otherwise.
        """

        publisher = self.parent
        path = _session_path()

        if not path:
            # the session still requires saving. provide a save button.
            # validation fails
            error_msg = "The Maya session has not been saved."
            self.logger.error(
                error_msg,
                extra=_get_save_as_action()
            )
            raise Exception(error_msg)

        # NOTE: If the plugin is attached to an item, that means no version
        # number could be found in the path. If that's the case, the work file
        # template won't be much use here as it likely has a version number
        # field defined within it. Simply use the path info hook to inject a
        # version number into the current file path

        # get the path to a versioned copy of the file.
        version_path = publisher.util.get_version_path(path, "v001")
        if os.path.exists(version_path):
            error_msg = "A file already exists with a version number. Please " \
                        "choose another name."
            self.logger.error(
                error_msg,
                extra=_get_save_as_action()
            )
            raise Exception(error_msg)

        return True

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """

        publisher = self.parent

        # get the path in a normalized state. no trailing separator, separators
        # are appropriate for current os, no double separators, etc.
        path = sgtk.util.ShotgunPath.normalize(_session_path())

        # ensure the session is saved in its current state
        _save_session(path)

        # get the path to a versioned copy of the file.
        version_path = publisher.util.get_version_path(path, "v001")

        # save to the new version path
        _save_session(version_path)
        self.logger.info("A version number has been added to the Maya file...")
        self.logger.info("  Maya file path: %s" % (version_path,))

    def finalize(self, settings, item):
        """
        Execute the finalization pass. This pass executes once
        all the publish tasks have completed, and can for example
        be used to version up files.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """
        pass

    def _get_version_number(self, path, item):
        """
        Try to extract and return a version number for the supplied path.

        :param path: The path to the current session

        :return: The version number as an `int` if it can be determined, else
            None.

        NOTE: This method will use the work template provided by the
        session collector, if configured, to determine the version number. If
        not configured, the version number will be extracted using the zero
        config path_info hook.
        """

        publisher = self.parent
        version_number = None

        work_template = item.properties.get("work_template")
        if work_template:
            if work_template.validate(path):
                self.logger.debug(
                    "Using work template to determine version number.")
                work_fields = work_template.get_fields(path)
                if "version" in work_fields:
                    version_number = work_fields.get("version")
            else:
                self.logger.debug(
                    "Work template did not match path")
        else:
            self.logger.debug(
                "Work template unavailable for version extraction.")

        if version_number is None:
            self.logger.debug(
                "Using path info hook to determine version number.")
            version_number = publisher.util.get_version_number(path)

        return version_number

def _session_path():
    """
    Return the path to the current session
    :return:
    """
    path = cmds.file(query=True, sn=True)

    if isinstance(path, unicode):
        path = path.encode("utf-8")

    return path


def _save_session(path):
    """
    Save the current session to the supplied path.
    """

    # Maya can choose the wrong file type so we should set it here
    # explicitly based on the extension
    maya_file_type = None
    if path.lower().endswith(".ma"):
        maya_file_type = "mayaAscii"
    elif path.lower().endswith(".mb"):
        maya_file_type = "mayaBinary"

    cmds.file(rename=path)

    # save the scene:
    if maya_file_type:
        cmds.file(save=True, force=True, type=maya_file_type)
    else:
        cmds.file(save=True, force=True)


# TODO: method duplicated in all the maya hooks
def _get_save_as_action():
    """

    Simple helper for returning a log action dict for saving the session
    """

    engine = sgtk.platform.current_engine()

    # default save callback
    callback = cmds.SaveScene

    # if workfiles2 is configured, use that for file save
    if "tk-multi-workfiles2" in engine.apps:
        app = engine.apps["tk-multi-workfiles2"]
        if hasattr(app, "show_file_save_dlg"):
            callback = app.show_file_save_dlg

    return {
        "action_button": {
            "label": "Save As...",
            "tooltip": "Save the current session",
            "callback": callback
        }
    }


def _get_version_docs_action():
    """
    Simple helper for returning a log action to show version docs
    """
    return {
        "action_open_url": {
            "label": "Version Docs",
            "tooltip": "Show docs for version formats",
            "url": "https://support.shotgunsoftware.com/hc/en-us/articles/115000068574-User-Guide-WIP-#What%20happens%20when%20you%20publish"
        }
    }
