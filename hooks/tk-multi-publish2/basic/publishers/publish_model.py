"""Model publish action for tk-multi-publish2 Maya at the Netherlands Film Academy

Written by Mervin van Brakel, 2024.
"""

from pathlib import Path

import interface.data_structures
import sgtk
import six
from maya import cmds, mel

HookBaseClass = sgtk.get_hook_baseclass()

import sys

# Sketchy workaround to import our own modules within tk-multi-publish2
sys.path.append(str(Path(__file__).parent.parent))
import interface


class MayaSessionModelPublisherPlugin(HookBaseClass):
    @property
    def item_filters(self):
        return ["maya.session.model"]

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
            interface.data_structures.PublisherType.MODEL
        )

    def accept(self, settings, item):
        """"""
        return {"accepted": True, "checked": True}

    def validate(self, settings, item):
        """"""
        model_publish = interface.maya_interfacing.get_publish_settings(
            interface.data_structures.PublisherType.MODEL
        )

        for publish_data in model_publish:
            if publish_data.selection == "":
                error = (
                    f"No selection found for model publish item {publish_data.name}."
                )
                raise ValueError(error)

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
        """Exports the model to disk and publishes the file to the ShotGrid database.

        Args:
            settings: The stored settings for the plugin.
            item: The item that is being published.
        """
        model_publish_data = interface.maya_interfacing.get_publish_settings(
            interface.data_structures.PublisherType.MODEL
        )

        for publish_data in model_publish_data:
            self.configure_item(settings, item, publish_data)
            self.ensure_publish_folder_exists(item.properties["path"])
            if (
                publish_data.publisher
                == interface.data_structures.ModelPublisher.ALEMBIC
            ):
                self.export_and_publish_model_as_alembic(publish_data, settings, item)
            elif publish_data.publisher == interface.data_structures.ModelPublisher.FBX:
                self.export_and_publish_model_as_fbx(publish_data, settings, item)

    def ensure_publish_folder_exists(self, publish_path: str) -> None:
        """Ensures that the publish folder exists. If it doesn't, it will be created.

        Args:
            publish_path: The path to the publish folder.
        """
        publish_folder = Path(publish_path).parent
        self.parent.ensure_folder_exists(str(publish_folder))

    def export_and_publish_model_as_alembic(
        self, publish_data: interface.data_structures.PublishData, settings, item
    ) -> None:
        """Exports the model as an Alembic file and calls base class publish.

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
            "-file '{}'".format(item.properties["path"].replace("\\", "/")),
        ]
        abc_export_cmd = f'AbcExport -j "{" ".join(alembic_args)}"'
        self.parent.log_debug(f"Executing command: {abc_export_cmd}")
        mel.eval(abc_export_cmd)

        super().publish(settings, item)

    def export_and_publish_model_as_fbx(
        self, publish_data: interface.data_structures.PublishData, settings, item
    ) -> None:
        """Exports the model as an FBX file and calls base class publish.

        Args:
            publish_data: The data that needs to be published.
            settings: The stored settings for the plugin.
            item: The item that is being published.
        """
        cmds.select(clear=True)
        cmds.select(publish_data.selection, replace=True)
        fbx_export_cmd = 'FBXExport -f "{}" -s'.format(
            item.properties["path"].replace("\\", "/")
        )
        self.parent.log_debug(f"Executing command: {fbx_export_cmd}")
        mel.eval(fbx_export_cmd)

        super().publish(settings, item)

    def finalize(self, settings, item):
        """Skipped lol."""
