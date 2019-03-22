
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class SceneSetup(HookBaseClass):
    """
    Hook to add override for setting up the scene on engine creation and context change.
    i.e. Set the project
    """
    def execute(self, context):
        self.parent.set_project()