"""Camera publish action for tk-multi-publish2 Maya at the Netherlands Film Academy

Written by Mervin van Brakel, 2024.
"""

import shutil
import tempfile
from pathlib import Path

import interface.data_structures
import sgtk
import six
from maya import cmds, mel

HookBaseClass = sgtk.get_hook_baseclass()


class MayaSessionCameraPublisherPlugin(HookBaseClass):
    @property
    def item_filters(self):
        return ["maya.session.camera"]

    @property
    def settings(self) -> dict:
        """Function that ShotGrid calls to get the settings for the plugin.
        Is only used for getting the publish template setting from tk-maya.yml in the config."""
        base_settings = super().settings or {}
        animation_publish_settings = {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                "correspond to a template defined in "
                "templates.yml.",
            }
        }
        base_settings.update(animation_publish_settings)

        return base_settings

    def create_settings_widget(self, parent):
        return interface.user_interface.PublishUserInterface(
            interface.data_structures.PublisherType.CAMERA
        )

    def accept(self, settings, item):
        """"""

        return {"accepted": True, "checked": True}

    def validate(self, settings, item):
        """"""
        camera_publish_data = interface.maya_interfacing.get_publish_settings(
            interface.data_structures.PublisherType.CAMERA
        )

        for publish_data in camera_publish_data:
            if publish_data.selection == "":
                error = (
                    f"No selection found for camera publish item {publish_data.name}."
                )
                raise ValueError(error)

            # TODO: Validate if we've actually got a camera selected. Not as easy as it sounds.

            self.configure_item(settings, item, publish_data)
            super().validate(settings, item)

        return True

    def configure_item(
        self, settings, item, publish_data: interface.data_structures.PublishData
    ):
        """Uses the ShotGrid templates to construct the publish path, the path
        is then stored on the item so the base class can use it to register a publish.

        Args:
            settings: The stored settings for the plugin.
            item: The item that is being published.
            publish_data: The data that needs to be published.
        """
        file_path = six.ensure_str(cmds.file(query=True, sn=True))
        normalized_file_path = sgtk.util.ShotgunPath.normalize(file_path)

        work_template = item.parent.properties.get("work_template")
        publish_template = self.parent.get_template_by_name(
            settings["Publish Template"].value
        )
        work_fields = work_template.get_fields(normalized_file_path)
        work_fields["publish_name"] = publish_data.name
        work_fields["publish_type"] = publish_data.publish_type.publish_type
        work_fields["publish_extension"] = publish_data.publisher.value

        publish_path = publish_template.apply_fields(work_fields)
        item.properties["path"] = publish_path
        item.properties["publish_path"] = publish_path

        if "version" in work_fields:
            item.properties["publish_version"] = work_fields["version"]

    def publish(self, settings, item):
        """Exports the camera to disk and publishes the file to the ShotGrid database.

        Args:
            settings: The stored settings for the plugin.
            item: The item that is being published.
        """
        camera_publish_data = interface.maya_interfacing.get_publish_settings(
            interface.data_structures.PublisherType.CAMERA
        )

        for publish_data in camera_publish_data:
            self.configure_item(settings, item, publish_data)
            self.ensure_publish_folder_exists(item.properties["path"])
            if publish_data.publisher == interface.data_structures.CameraPublisher.USD:
                self.export_and_publish_camera_as_usd(publish_data, settings, item)
            elif (
                publish_data.publisher
                == interface.data_structures.CameraPublisher.ALEMBIC
            ):
                self.export_and_publish_camera_as_alembic(publish_data, settings, item)

    def ensure_publish_folder_exists(self, publish_path: str) -> None:
        """Ensures that the publish folder exists. If it doesn't, it will be created.

        Args:
            publish_path: The path to the publish folder.
        """
        publish_folder = Path(publish_path).parent
        self.parent.ensure_folder_exists(str(publish_folder))

    def export_and_publish_camera_as_usd(
        self, publish_data: interface.data_structures.PublishData, settings, item
    ) -> None:
        """Exports the camera as USD and calls the base class publish. We just use the
        regular ol' USD export command here because it's decent enough for cameras I guess.

        Args:
            publish_data: The data that needs to be published.
            settings: The stored settings for the plugin.
            item: The item that is being published.
        """
        cmds.select(clear=True)
        cmds.select(publish_data.selection, replace=True)
        usd_command: str = (
            'file -force -options ";exportUVs=1;exportSkels=none;exportSkin=none;exportBlendShapes=0'
            ";exportColorSets=1;defaultMeshScheme=catmullClark;defaultUSDFormat=usda;animation=1;eulerFilter"
            "=1;staticSingleSample=0;startTime="
            + str(publish_data.first_frame)
            + ";endTime="
            + str(publish_data.last_frame)
            + ";frameStride=1;frameSample=0.0;exportDisplayColor=0;shadingMode=useRegistry;"
            "exportInstances=1;exportVisibility=1;mergeTransformAndShape=1;"
            'stripNamespaces=0;parentScope=Camera" -type "USD Export" -pr -es '
        )

        # USD is written to a temporary file first, because for some reason the Maya USD
        # export just HATES our network drives.
        with tempfile.TemporaryDirectory() as temp_directory:
            temp_file = Path(temp_directory) / Path(item.properties["path"]).name
            usd_command = usd_command + '" ' + str(temp_file).replace("\\", "/") + '";'
            mel.eval(usd_command)

            shutil.copy2(str(temp_file), item.properties["path"])

        super().publish(settings, item)

    def export_and_publish_camera_as_alembic(
        self, publish_data: interface.data_structures.PublishData, settings, item
    ) -> None:
        """Exports the camera as an Alembic file and calls base class publish.

        Args:
            publish_data: The data that needs to be published.
            settings: The stored settings for the plugin.
            item: The item that is being published.
        """
        alembic_args = [
            "-writeFaceSets",
            "-uvWrite",
            "-eulerFilter",
            "-writeVisibility",
            f"-root {publish_data.selection}",
            f"-fr {publish_data.first_frame} {publish_data.last_frame}",
            "-file '{}'".format(item.properties["path"].replace("\\", "/")),
        ]
        abc_export_cmd = f'AbcExport -j "{" ".join(alembic_args)}"'
        self.parent.log_debug(f"Executing command: {abc_export_cmd}")
        mel.eval(abc_export_cmd)

        super().publish(settings, item)

    def finalize(self, settings, item):
        """Skipped lol."""
