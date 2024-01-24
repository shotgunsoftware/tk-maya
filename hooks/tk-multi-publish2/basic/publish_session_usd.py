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
import maya.mel as mel
import sgtk
import tempfile
import shutil

from tank_vendor import six

HookBaseClass = sgtk.get_hook_baseclass()


class MayaSessionUSDPublishPlugin(HookBaseClass):
    """
    Plugin for publishing an open maya session.

    This hook relies on functionality found in the base file publisher hook in
    the publish2 app and should inherit from it in the configuration. The hook
    setting for this plugin should look something like this::

        hook: "{self}/publish_file.py:{engine}/tk-multi-publish2/basic/publish_session.py"

    """

    # NOTE: The plugin icon and name are defined by the base file plugin.

    @property
    def description(self):
        """
        Verbose, multi-line description of what the plugin does. This can
        contain simple html for formatting.
        """

        return """
        <div><p>This plugin will export the scene as a USD file.
        Below you will find several settings that influence your export.</p>
        <br>
        <p>Export active selection only: Only exports your active selection as a USD file.
        Note: Everything that is highlighted in green in the viewport is your active selection.</p>
        <p>Disable animations: Exports your scene without any animation data.</p>
        <p>Export current frame only: Only exports the frame you are currently viewing.</p><br></div>
        """

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
        # inherit the settings from the base publish plugin
        base_settings = super(MayaSessionUSDPublishPlugin, self).settings or {}

        # settings specific to this class
        maya_publish_settings = {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                "correspond to a template defined in "
                "templates.yml.",
            },
            "Export Active Selection Only": {
                "type": "bool",
                "default": False,
                "description": "Setting for only exporting active selection.",
            },
            "Disable Animations Export": {
                "type": "bool",
                "default": False,
                "description": "Setting for disabling animation on export.",
            },
            "Export Current Frame Only": {
                "type": "bool",
                "default": False,
                "description": "Setting for only exporting current frame.",
            },
        }

        # update the base settings
        base_settings.update(maya_publish_settings)

        return base_settings

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["maya.*", "file.maya"]
        """
        return ["maya.session.usd"]

    def create_settings_widget(self, parent):
        """
        Creates a custom widget for the given parent widget.

        :param parent: Parent widget to host the custom UI.
        :return: The QWidget containing the custom UI.
        """
        from sgtk.platform.qt import QtGui

        usd_publish_menu = QtGui.QGroupBox(parent)
        usd_publish_menu.setTitle("USD publishing")
        menu_layout = QtGui.QVBoxLayout()
        menu_layout.addStretch()

        # Description text
        description_label = QtGui.QLabel(self.description)
        description_label.setWordWrap(True)
        description_label.setOpenExternalLinks(True)
        menu_layout.addWidget(description_label)

        # Active selection
        active_selection_checkbox = QtGui.QCheckBox("Export active selection only")
        menu_layout.addWidget(active_selection_checkbox)

        # Disable animations
        disable_animation_checkbox = QtGui.QCheckBox("Disable animations")
        menu_layout.addWidget(disable_animation_checkbox)

        # Current frame
        current_frame_checkbox = QtGui.QCheckBox("Export current frame only")
        menu_layout.addWidget(current_frame_checkbox)

        usd_publish_menu.setLayout(menu_layout)

        return usd_publish_menu

    def get_ui_settings(self, widget, items=None):
        """
        Invoked by the Publisher when the selection changes. This method gathers the settings
        on the previously selected task, so that they can be later used to repopulate the
        custom UI if the task gets selected again. They will also be passed to the accept, validate,
        publish and finalize methods, so that the settings can be used to drive the publish process.

        The widget argument is the widget that was previously created by
        `create_settings_widget`.

        The method returns a dictionary, where the key is the name of a
        setting that should be updated and the value is the new value of that
        setting. Note that it is up to you how you want to store the UI's state as
        settings and you don't have to necessarily to return all the values from
        the UI. This is to allow the publisher to update a subset of settings
        when multiple tasks have been selected.

        Example::

            {
                 "setting_a": "/path/to/a/file"
            }

        :param widget: The widget that was created by `create_settings_widget`
        """
        from sgtk.platform.qt import QtGui

        checkbox_settings_list = widget.findChildren(QtGui.QCheckBox)

        for checkbox in checkbox_settings_list:
            if checkbox.text() == "Export active selection only":
                active_selection_value = checkbox.isChecked()
            elif checkbox.text() == "Disable animations":
                disable_animation_value = checkbox.isChecked()
            elif checkbox.text() == "Export current frame only":
                current_frame_value = checkbox.isChecked()

        updated_ui_settings = {
            "Export Active Selection Only": active_selection_value,
            "Disable Animations Export": disable_animation_value,
            "Export Current Frame Only": current_frame_value,
        }

        return updated_ui_settings

    def set_ui_settings(self, widget, settings, items=None):
        """
        Allows the custom UI to populate its fields with the settings from the
        currently selected tasks.

        The widget is the widget created and returned by
        `create_settings_widget`.

        A list of settings dictionaries are supplied representing the current
        values of the settings for selected tasks. The settings dictionaries
        correspond to the dictionaries returned by the settings property of the
        hook.

        Example::

            settings = [
            {
                 "seeting_a": "/path/to/a/file"
                 "setting_b": False
            },
            {
                 "setting_a": "/path/to/a/file"
                 "setting_b": False
            }]

        The default values for the settings will be the ones specified in the
        environment file. Each task has its own copy of the settings.

        When invoked with multiple settings dictionaries, it is the
        responsibility of the custom UI to decide how to display the
        information. If you do not wish to implement the editing of multiple
        tasks at the same time, you can raise a ``NotImplementedError`` when
        there is more than one item in the list and the publisher will inform
        the user than only one task of that type can be edited at a time.

        :param widget: The widget that was created by `create_settings_widget`.
        :param settings: a list of dictionaries of settings for each selected
            task.
        :param items: A list of PublishItems the selected publish tasks are parented to.
        """
        from sgtk.platform.qt import QtGui

        checkbox_settings_list = widget.findChildren(QtGui.QCheckBox)

        for checkbox in checkbox_settings_list:
            if (
                checkbox.text() == "Export active selection only"
                and settings[0]["Export Active Selection Only"]
            ):
                checkbox.toggle()
            elif (
                checkbox.text() == "Disable animations"
                and settings[0]["Disable Animations Export"]
            ):
                checkbox.toggle()
            elif (
                checkbox.text() == "Export current frame only"
                and settings[0]["Export Current Frame Only"]
            ):
                checkbox.toggle()

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

        accepted = True
        publisher = self.parent
        template_name = settings["Publish Template"].value

        # ensure a work file template is available on the parent item
        work_template = item.parent.properties.get("work_template")
        if not work_template:
            self.logger.debug(
                "A work template is required for the session item in order to "
                "publish session geometry. Not accepting session geom item."
            )
            accepted = False

        # ensure the publish template is defined and valid and that we also have
        publish_template = publisher.get_template_by_name(template_name)
        if not publish_template:
            self.logger.debug(
                "The valid publish template could not be determined for the "
                "session geometry item. Not accepting the item."
            )
            accepted = False

        # we've validated the publish template. add it to the item properties
        # for use in subsequent methods
        item.properties["publish_template"] = publish_template

        # check that the mayaUsdPlugin command is available!
        if not cmds.pluginInfo("mayaUsdPlugin", query=True, loaded=True):
            try:
                # Try to load the plugin if it is installed
                cmds.loadPlugin("mayaUsdPlugin" + ".mll")
            except:
                self.logger.debug(
                    "Item not accepted because Maya USD plugin is not installed. "
                    "You are probably using an older Maya version, currently USD is standard installed in Maya 2022+"
                    "The plugin is also available to manually install via the Maya-USD Github."
                )
                accepted = False

        # because a publish template is configured, disable context change. This
        # is a temporary measure until the publisher handles context switching
        # natively.
        item.context_change_allowed = False

        return {"accepted": accepted, "checked": True}

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish. Returns a
        boolean to indicate validity.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        :returns: True if item is valid, False otherwise.
        """

        path = _session_path()

        # ---- ensure the session has been saved

        if not path:
            # the session still requires saving. provide a save button.
            # validation fails.
            error_msg = "The Maya session has not been saved."
            self.logger.error(error_msg, extra=_get_save_as_action())
            raise Exception(error_msg)

        # get the normalized path
        path = sgtk.util.ShotgunPath.normalize(path)

        # check that there is still geometry in the scene:
        if not cmds.ls(geometry=True, noIntermediate=True):
            if not cmds.ls(cameras=True):
                error_msg = (
                    "Validation failed because there is no geometry in the scene "
                    "to be exported. You can uncheck this plugin or create "
                    "geometry to export to avoid this error."
                )
                raise Exception(error_msg)

        # check if there's a selection when selection export is enabled
        if settings["Export Active Selection Only"].value and not cmds.ls(
            selection=True
        ):
            error_msg = (
                "Validation failed because there is no active selection to export. "
                "Please make a selection in the viewport or outliner, or disable"
                "the active selection checkbox if you want to export the whole scene instead."
            )
            raise Exception(error_msg)

        # get the configured work file template
        work_template = item.parent.properties.get("work_template")
        publish_template = item.properties.get("publish_template")

        # get the current scene path and extract fields from it using the work
        # template:
        work_fields = work_template.get_fields(path)

        # ensure the fields work for the publish template
        missing_keys = publish_template.missing_keys(work_fields)
        if missing_keys:
            error_msg = (
                "Work file '%s' missing keys required for the "
                "publish template: %s" % (path, missing_keys)
            )
            self.logger.error(error_msg)
            raise Exception(error_msg)

        # create the publish path by applying the fields. store it in the item's
        # properties. This is the path we'll create and then publish in the base
        # publish plugin. Also set the publish_path to be explicit.
        item.properties["path"] = publish_template.apply_fields(work_fields)
        item.properties["publish_path"] = item.properties["path"]

        # use the work file's version number when publishing
        if "version" in work_fields:
            item.properties["publish_version"] = work_fields["version"]

        # run the base class validation
        return super(MayaSessionUSDPublishPlugin, self).validate(settings, item)

    def rename_uv(self):
        try:
            current_selection = cmds.ls(sl=True)

            # Select all geometry
            geometry = cmds.ls(geometry=True)
            geometries = cmds.listRelatives(geometry, p=True, path=True)

            for mesh in geometries:
                # Get all UV Sets
                cmds.select(mesh, r=True)
                uv_sets = cmds.polyUVSet(mesh, q=True, allUVSets=True)
                uv_count = 0

                # For all UV sets rename to uv and count with number
                if not uv_sets is None:
                    for uv in uv_sets:
                        if uv_count == 0:
                            uv_name = "uv"
                            uv_count = uv_count + 1
                        else:
                            uv_name = "uv" + str(uv_count)
                            uv_count = uv_count + 1
                        if not uv_name == uv:
                            cmds.polyUVSet(
                                rename=True,
                                perInstance=True,
                                newUVSet=uv_name,
                                uvSet=uv,
                            )

            self.parent.log_debug("Renamed all uv sets.")
            cmds.select(current_selection, r=True)

        except Exception as e:
            self.logger.debug(str(e))

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """

        publisher = self.parent

        # First make sure all the uv sets are named correctly
        self.rename_uv()

        # get the path to create and publish
        publish_path = item.properties["path"]

        # This is a quick fix to make sure directories exists before executing the usd export command
        publish_path = publish_path.replace("\\", "/")
        publish_dir = os.path.dirname(publish_path)
        publish_name = os.path.basename(publish_path)

        # ensure the publish folder exists:
        self.parent.ensure_folder_exists(publish_dir)

        start_frame, end_frame = _find_scene_animation_range()

        if settings["Export Active Selection Only"].value:
            self.logger.debug("Exporting active selection USD only.")
            export_mode = "-es"
        else:
            export_mode = "-ea"

        if settings["Disable Animations Export"].value:
            self.logger.debug("Disabling animation export.")
            animation_mode = "0"
        else:
            animation_mode = "1"

        if settings["Export Current Frame Only"].value:
            self.logger.debug("Exporting current frame only.")
            current_frame = int(cmds.currentTime(query=True))
            start_frame = current_frame
            end_frame = current_frame

        # This is the really long Maya command to export everything in the scene to USDA
        usd_command: str = (
            'file -force -options ";exportUVs=1;exportSkels=auto;exportSkin=auto;exportBlendShapes=1'
            ";exportColorSets=1;defaultMeshScheme=none;defaultUSDFormat=usda;animation="
            + animation_mode
            + ";eulerFilter"
            "=0;staticSingleSample=0;startTime="
            + str(start_frame)
            + ";endTime="
            + str(end_frame)
            + ";frameStride=1;frameSample=0.0;parentScope"
            "=;exportDisplayColor=0;shadingMode=useRegistry;convertMaterialsTo=UsdPreviewSurface"
            ';exportInstances=1;exportVisibility=1;mergeTransformAndShape=1;stripNamespaces=0" -type "USD '
            'Export" -pr ' + export_mode
        )

        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_directory:
            # Setting file name
            temp_file_path = os.path.join(temp_directory, publish_name).replace(
                os.sep, "/"
            )
            file_path = ' "' + temp_file_path + '"'

            # Setting final command
            usd_command = usd_command + file_path + ";"

            # Executing export command
            self.parent.log_debug("Executing command: %s" % usd_command)
            mel.eval(usd_command)

            # Copy directory
            shutil.copy2(temp_file_path, publish_dir)
            self.parent.log_debug("Copied file to publish path")

        # Now that the usd file has been generated and copied, hand it off to the
        super(MayaSessionUSDPublishPlugin, self).publish(settings, item)


def _find_scene_animation_range():
    """
    Find the animation range from the current scene.
    """
    # look for any animation in the scene:
    animation_curves = cmds.ls(typ="animCurve")

    # if there aren't any animation curves then just return
    # a single frame:
    if not animation_curves:
        return 1001, 1001

    # something in the scene is animated so return the
    # current timeline.  This could be extended if needed
    # to calculate the frame range of the animated curves.
    start = int(cmds.playbackOptions(q=True, min=True))
    end = int(cmds.playbackOptions(q=True, max=True))

    return start, end


def _session_path():
    """
    Return the path to the current session
    :return:
    """
    path = cmds.file(query=True, sn=True)

    if path is not None:
        path = six.ensure_str(path)

    return path


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
            "callback": callback,
        }
    }
