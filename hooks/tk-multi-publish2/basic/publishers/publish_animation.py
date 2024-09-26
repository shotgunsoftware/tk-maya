﻿"""Animation publish action for tk-multi-publish2 Maya at the Netherlands Film Academy.
Pretty much only the validate and publish functions do something here, the rest
of the code can be found in the interface folder.

Written by Mervin van Brakel, 2024.
"""

import sys
from pathlib import Path
import os
import copy
import sgtk
from maya import cmds, mel
from tank_vendor import six

HookBaseClass = sgtk.get_hook_baseclass()


# Sketchy workaround to import our own modules within tk-multi-publish2.
# We have to do it like this because these publisher files are not imported in a "normal" way.
sys.path.append(str(Path(__file__).parent.parent))
import interface

# TODO: DELETE THIS PART LATER:
import importlib

importlib.reload(interface)
importlib.reload(interface.data_structures)
importlib.reload(interface.maya_interfacing)
importlib.reload(interface.models)
importlib.reload(interface.user_interface)


class MayaSessionAnimationPublisherPlugin(HookBaseClass):
    """Plugin that handles the publishing of animation data.
    The HookBaseClass can be found over on tk-multi-publish2/hooks/publish_file.py"""

    @property
    def item_filters(self) -> list:
        """Function that ShotGrid calls to check if it should show the plugin."""
        return ["maya.session"]

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

    def create_settings_widget(
        self, _
    ) -> interface.user_interface.PublishUserInterface:
        """Function that ShotGrid calls to create the settings widget. The widget be inserted
        into the ShotGrid tk-multi-publish2 UI.

        Returns:
            Widget for display in UI.
        """
        return interface.user_interface.PublishUserInterface(
            interface.data_structures.PublisherType.ANIMATION
        )

    def accept(self, _, __) -> dict:
        """Function that ShotGrid calls to check if the plugin should be accepted.
        We use so much custom logic that we always just accept and check lol.

        Returns:
            Dictionary with the keys "accepted" and "checked" set to True.
        """
        return {"accepted": True, "checked": True}

    def validate(self, settings, item) -> bool:
        """Validates the stored publish data and configures our paths.

        Args:
            settings: The stored settings for the plugin.
            item: The item that is being published.

        Returns:
            True if the validation is successful.
        """
        animation_publish_data = interface.maya_interfacing.get_publish_settings(
            interface.data_structures.PublisherType.ANIMATION
        )

        for publish_data in animation_publish_data:
            if publish_data.selection == "":
                error = f"No selection found for animation publish item {publish_data.name}."
                raise ValueError(error)

            new_item = self.get_configured_item(settings, item, publish_data)
            super().validate(settings, new_item)

        return True

    def get_configured_item(
        self, settings, item, publish_data: interface.data_structures.PublishData
    ):
        """Uses the ShotGrid templates to construct the publish path. The path
        is then stored on the item so the base class can use it to register a publish.
        We have to make new settings and items because they pass through all the publishers,
        which is really annoying and is kinda because I'm forcing this tk-multi-publish thing
        to do things it's not designed for but oh well.

        Args:
            settings: The stored settings for the plugin.
            item: The item that is being published.
            publish_data: The data that needs to be published.
        """
        new_item = copy.copy(item)
        file_path = six.ensure_str(cmds.file(query=True, sn=True))
        normalized_file_path = sgtk.util.ShotgunPath.normalize(file_path)

        work_template = item.properties.get("work_template")
        publish_template = self.parent.get_template_by_name(
            settings["Publish Template"].value
        )
        work_fields = work_template.get_fields(normalized_file_path)
        work_fields["publish_name"] = publish_data.name
        work_fields["publish_type"] = publish_data.publish_type.publish_type

        if publish_data.publisher == interface.data_structures.AnimationPublisher.USD:
            work_fields["publish_extension"] = "usd"
        if (
            publish_data.publisher
            == interface.data_structures.AnimationPublisher.ALEMBIC
        ):
            work_fields["publish_extension"] = "abc"

        publish_path = publish_template.apply_fields(work_fields)
        new_item.properties["path"] = publish_path
        new_item.properties["publish_path"] = publish_path

        if "version" in work_fields:
            new_item.properties["publish_version"] = work_fields["version"]

        return new_item

    def publish(self, settings, item):
        """Exports the animation to disk and publishes the file to the ShotGrid database.

        Args:
            settings: The stored settings for the plugin.
            item: The item that is being published.
        """
        animation_publish_data = interface.maya_interfacing.get_publish_settings(
            interface.data_structures.PublisherType.ANIMATION
        )

        for publish_data in animation_publish_data:
            new_item = self.get_configured_item(settings, item, publish_data)
            self.ensure_publish_folder_exists(new_item.properties["path"])
            if (
                publish_data.publisher
                == interface.data_structures.AnimationPublisher.USD
            ):
                self.export_and_publish_animation_as_usd(
                    publish_data, settings, new_item
                )
            elif (
                publish_data.publisher
                == interface.data_structures.AnimationPublisher.ALEMBIC
            ):
                self.export_and_publish_animation_as_alembic(
                    publish_data, settings, new_item
                )

    def ensure_publish_folder_exists(self, publish_path: str) -> None:
        """Ensures that the publish folder exists. If it doesn't, it will be created.

        Args:
            publish_path: The path to the publish folder.
        """
        publish_folder = Path(publish_path).parent
        self.parent.ensure_folder_exists(str(publish_folder))

    def export_and_publish_animation_as_usd(
        self, publish_data: interface.data_structures.PublishData, settings, item
    ) -> None:
        """Exports the animation as USD, then loads that USD and cleans it up."""
        super().publish(settings, item)
        raise NotImplementedError("This function is not implemented yet.")

    def export_and_publish_animation_as_alembic(
        self, publish_data: interface.data_structures.PublishData, settings, item
    ) -> None:
        """Exports the animation as an Alembic file."""
        alembic_args = [
            "-renderableOnly",
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

        print(settings)
        print(item)
        super().publish(settings, item)

    def finalize(self, settings, item):
        """Skipped lol."""
