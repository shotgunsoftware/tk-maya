"""Animation publish action for tk-multi-publish2 Maya at the Netherlands Film Academy.
Pretty much only the validate and publish functions do something here, the rest
of the code can be found in the interface folder.

Written by Mervin van Brakel, 2024.
"""

from pathlib import Path

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

import sys

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
    """Plugin that handles the publishing of animation data."""

    @property
    def item_filters(self):
        """Function that ShotGrid calls to check if it should show the plugin."""
        return ["maya.session"]

    def create_settings_widget(self, _):
        """Function that ShotGrid calls to create the settings widget. The widget be inserted
        into the ShotGrid tk-multi-publish2 UI."""
        return interface.user_interface.PublishUserInterface(
            interface.data_structures.PublisherType.ANIMATION
        )

    def accept(self, _, __):
        """Function that ShotGrid calls to check if the plugin should be accepted.
        We use so much custom logic that we always just accept and check lol."""
        return {"accepted": True, "checked": True}

    def validate(self, _, __):
        """Validates the stored publish data."""
        animation_publish_data = interface.maya_interfacing.get_publish_settings(
            interface.data_structures.PublisherType.ANIMATION
        )

        for publish_data in animation_publish_data:
            if publish_data.selection == "":
                error = f"No selection found for animation publish item {publish_data.name}."
                raise ValueError(error)

        return True

    def publish(self, settings, item):
        """Exports the animation to disk and publishes the file to the ShotGrid database."""
        animation_publish_data = interface.maya_interfacing.get_publish_settings(
            interface.data_structures.PublisherType.ANIMATION
        )

        for publish_data in animation_publish_data:
            if (
                publish_data.publisher
                == interface.data_structures.AnimationPublisher.USD
            ):
                interface.export_animation_as_usd()
            elif (
                publish_data.publisher
                == interface.data_structures.AnimationPublisher.ALEMBIC
            ):
                interface.export_animation_as_alembic()

        super().publish(settings, item)


def export_animation_as_usd():
    """Exports the animation as USD, then loads that USD and cleans it up."""
    raise NotImplementedError("This function is not implemented yet.")


def export_animation_as_alembic():
    """Exports the animation as an Alembic file."""
    raise NotImplementedError("This function is not implemented yet.")
