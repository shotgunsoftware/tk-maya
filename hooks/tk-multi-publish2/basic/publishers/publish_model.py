"""Model publish action for tk-multi-publish2 Maya at the Netherlands Film Academy

Written by Mervin van Brakel, 2024.
"""

from pathlib import Path

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

import sys

# Sketchy workaround to import our own modules within tk-multi-publish2
sys.path.append(str(Path(__file__).parent.parent))
import interface


class MayaSessionModelPublisherPlugin(HookBaseClass):
    @property
    def item_filters(self):
        return ["maya.session"]

    def create_settings_widget(self, parent):
        return interface.user_interface.PublishUserInterface(
            interface.data_structures.PublisherType.MODEL
        )

    def accept(self, settings, item):
        """"""
        return {"accepted": True, "checked": True}

    def validate(self, settings, item):
        """"""
        return super().validate(settings, item)

    def publish(self, settings, item):
        super().publish(settings, item)
