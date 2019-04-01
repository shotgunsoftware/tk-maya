import json

import sgtk

import maya.cmds

HookBaseClass = sgtk.get_hook_baseclass()


class SceneSetup(HookBaseClass):
    """
    Hook to add override for setting up the scene on engine creation and context change.
    i.e. Set the project
    """

    def execute(self, context):
        """
        Main hook entry point

        Set the maya project and render settings.

        :param context:         Context
                                The context the file operation is being
                                performed in.
        """
        self.parent.set_project()
        if not maya.cmds.pluginInfo("RenderMan_for_Maya", q=True, loaded=True):
            maya.cmds.loadPlugin("RenderMan_for_Maya")
        if not maya.cmds.objExists("rmanGlobals"):
            maya.cmds.evalDeferred('maya.cmds.createNode("rmanGlobals")', en=True)
        maya.cmds.evalDeferred('maya.cmds.setAttr("defaultRenderGlobals.currentRenderer", "renderman", type="string")', low=True)
        data = self.render_setup_data(context)
        if not data:
            return
        self.logger.debug("Render Settings: {}".format(json.dumps(data)))
        maya.cmds.evalDeferred("import maya.app.renderSetup.model.renderSettings as renderSettings; renderSettings.decode({})".format(json.dumps(data)), lp=True)

    def render_setup_data(self, context):
        """
        Create a dictionary containing all the render setup information (render paths etc).

        :param context:         Context
                                The context the file operation is being
                                performed in.

        :returns:               A dict containing settings for the renderman globals workspace destinations or None.
        """
        file_name = maya.cmds.file(query=True, sceneName=True)
        if not self.parent.apps.get("tk-multi-workfiles2"):
            return
        template = self.parent.apps["tk-multi-workfiles2"].get_template("template_work")
        if not template:
            return
        if file_name:
            fields = template.validate_and_get_fields(file_name)
        else:
            fields = context.as_template_fields(template)

        if not fields:
            return
        self.logger.debug("Fields: {}".format(json.dumps(fields)))
        keys = template.keys

        def safe_pop(dic, key, default=None):
            if key in dic:
                return dic.pop(key)
            return default

        data = {
            "renderman": {
                "defaultNodes": {},
                "defaultRendererNodes": {
                }, 
                "userData": {}
            }
        }
        # clear all User Tokens
        for idx in range(10):
            data["renderman"]["defaultRendererNodes"]["rmanGlobals.UserTokens[{}].userTokenKeys".format(idx)] = ""
            data["renderman"]["defaultRendererNodes"]["rmanGlobals.UserTokens[{}].userTokenValues".format(idx)] = ""

        safe_pop(keys, "version")
        safe_pop(keys, "extension")
        version = safe_pop(fields, "version", default=1)
        data["renderman"]["defaultRendererNodes"]["rmanGlobals.version"] = version

        for idx, name in enumerate(keys.keys()):
            value = str(fields.get(name, "unknown"))
            data["renderman"]["defaultRendererNodes"]["rmanGlobals.UserTokens[{}].userTokenKeys".format(idx)] = name
            data["renderman"]["defaultRendererNodes"]["rmanGlobals.UserTokens[{}].userTokenValues".format(idx)] = value
        name_field = {}
        if "name" in fields:
            name_field["segment_name"] = "<name>"
        image_file_format_template = self.parent.get_template("template_image_file_format")
        if image_file_format_template:
            data["renderman"]["defaultRendererNodes"]["rmanGlobals.imageFileFormat"] = image_file_format_template.apply_fields(name_field)
            data["renderman"]["defaultRendererNodes"]["rmanGlobals.imageOutputDir"] = "<ws>/renders/<layer>/<camera>/<version>"

        rib_file_format_template = self.parent.get_template("template_rib_file_format")
        if rib_file_format_template:
            data["renderman"]["defaultRendererNodes"]["rmanGlobals.ribFileFormat"] = rib_file_format_template.apply_fields(name_field)
            data["renderman"]["defaultRendererNodes"]["rmanGlobals.ribOutputDir"] = "<ws>/rib/<layer>/<camera>/<version>"

        return data