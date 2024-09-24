"""Animation publish action for tk-multi-publish2 Maya at the Netherlands Film Academy

Written by Mervin van Brakel, 2024.
"""

from pathlib import Path

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

import sys

# Sketchy workaround to import our own modules within tk-multi-publish2
sys.path.append(str(Path(__file__).parent.parent))
import interface

# TODO: DELETE THIS PART LATER:
import importlib

importlib.reload(interface)
importlib.reload(interface.data_structures)
importlib.reload(interface.maya_interfacing)
importlib.reload(interface.models)
importlib.reload(interface.view)


class MayaSessionAnimationPublisherPlugin(HookBaseClass):
    @property
    def description(self):
        return ""

    @property
    def settings(self):
        return {}

    @property
    def item_filters(self):
        return ["maya.session"]

    def create_settings_widget(self, parent):
        return interface.view.PublishUserInterface(
            interface.data_structures.PublisherType.ANIMATION
        )

    def get_ui_settings(self, widget, items=None):
        """"""
        return {}

    def set_ui_settings(self, widget, settings, items=None):
        """"""

    def accept(self, settings, item):
        """"""
        return {"accepted": True, "checked": True}

    def validate(self, settings, item):
        """"""
        return super().validate(settings, item)

    def publish(self, settings, item):
        super().publish(settings, item)
