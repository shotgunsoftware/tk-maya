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
import pprint
import maya.cmds as cmds
import maya.mel as mel
import sgtk
from sgtk.util.filesystem import copy_file
import traceback

HookBaseClass = sgtk.get_hook_baseclass()


class MayaSessionGeometryPublishPlugin(HookBaseClass):
    """
    Plugin for publishing an open maya session.
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
            "publish.png"
        )

    @property
    def name(self):
        """
        One line display name describing the plugin
        """
        return "Publish to Shotgun"

    @property
    def description(self):
        """
        Verbose, multi-line description of what the plugin does. This can
        contain simple html for formatting.
        """

        loader_url = "https://support.shotgunsoftware.com/hc/en-us/articles/219033078"

        return """
        Publishes the session's geometry to Shotgun. A <b>Publish</b> entry will be
        created in Shotgun which will include a reference to the file's current
        path on disk. If templates are configured and the work file template
        matches the current session path, the work file will be copied to the
        publish file template path which will be the file that is published.
        Other users will be able to access the published file via the
        <b><a href='%s'>Loader</a></b> so long as they have access to the file's
        location on disk.

        If the session has no geometry nothing will be exported or published.

        <h3>File versioning</h3>
        The version number, will be derived from the session's project file
        version number and will be incremented in sync with it.

        The <code>version</code> field of the resulting <b>Publish</b> in
        Shotgun will also reflect the version number identified in the filename.
        The basic worklfow recognizes the following version formats by default:

        <ul>
        <li><code>filename.v###.ext</code></li>
        <li><code>filename_v###.ext</code></li>
        <li><code>filename-v###.ext</code></li>
        </ul>

        If templates are configured, the version will be determined from the
        "{version}" token.

        <br><br><i>NOTE: any amount of version number padding is supported. for
        non-template based workflows.</i>

        <h3>Overwriting an existing publish</h3>
        In non-template workflows, a file can be published multiple times,
        however only the most recent publish will be available to other users.
        Warnings will be provided during validation if there are previous
        publishes.
        """ % (loader_url,)

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
        return {
            "Publish Type": {
                "type": "shotgun_publish_type",
                "default": "Alembic Cache",
                "description": "SG publish type to associate publishes with."
            },
            "Publish file Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                               "correspond to a template defined in "
                               "templates.yml."
            }
        }

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["maya.*", "file.maya"]
        """
        return ["maya.session.geometry"]

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
        publish_template = self._get_template("Publish file Template", settings)
        if not publish_template and not item.parent.properties["work_file_template"]:
            accepted = False

        # check that the AbcExport command is available!
        if not mel.eval("exists \"AbcExport\""):
            accepted = False
            self.logger.warn("Item not accepted because export command AbcExport is not available.")
        
        return {
            "accepted": accepted,
            "checked": True
        }

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

        # check that there is still geometry in the scene:
        if not cmds.ls(geometry=True, noIntermediate=True):
            self.logger.warn("Validation failed because there is no geometry in the scene to be exported")
            return False

        publisher = self.parent

        # ensure we have an updated project root
        project_root = cmds.workspace(q=True, rootDirectory=True)
        item.properties["project_root"] = project_root

        # get the configured work file template
        work_template = item.parent.properties["work_file_template"]
        publish_template = self._get_template("Publish file Template", settings)

        # get the current scene path and extract fields from it
        # using the work template:
        scene_path = os.path.abspath(cmds.file(query=True, sn=True))
        #scene_file_name = os.path.basename(scene_path)
        scene_file_name = publisher.util.get_publish_name(scene_path)
        scene_file_name_root, scene_file_name_ext = os.path.splitext(scene_file_name)
        fields = work_template.get_fields(scene_path) #{ "asset_root": project_root, "name": scene_file_name_root, "version": 0 }
                
        # create the publish path by applying the fields 
        # with the publish template:
        publish_path = publish_template.apply_fields(fields)
        
        # ensure the publish folder exists:
        publish_folder = os.path.dirname(publish_path)
        self.parent.ensure_folder_exists(publish_folder)

        # get the path in a normalized state. no trailing separator,
        # separators are appropriate for current os, no double separators,
        # etc.
        path = sgtk.util.ShotgunPath.normalize(publish_path)

        # determine the publish path, version, type, and name
        publish_info = self._get_publish_info(path, settings)

        publish_name = publish_info["name"]

        # see if there are any other publishes of this path with a status.
        # Note the name, context, and path *must* match the values supplied to
        # register_publish in the publish phase in order for this to return an
        # accurate list of previous publishes of this file.
        publishes = publisher.util.get_conflicting_publishes(
            item.context,
            path,
            publish_name,
            filters=["sg_status_list", "is_not", None]
        )

        if publishes:
            conflict_info = (
                "If you continue, these conflicting publishes will no longer "
                "be available to other users via the loader:<br>"
                "<pre>%s</pre>" % (pprint.pformat(publishes),)
            )
            self.logger.warn(
                "Found %s conflicting publishes in Shotgun" %
                (len(publishes),),
                extra={
                    "action_show_more_info": {
                        "label": "Show Conflicts",
                        "tooltip": "Show the conflicting publishes in Shotgun",
                        "text": conflict_info
                    }
                }
            )

        # store the session path since this is guaranteed to run just before
        # the publish itself
        item.properties["publish_file_path"] = path

        # store the publish info in the properties
        item.properties["publish_info"] = publish_info

        self.logger.info("A Publish will be created in Shotgun and linked to:")
        self.logger.info("  %s" % (path,))

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

        # get the work file path stored during validation
        path = item.properties["publish_file_path"]

        # get all the publish info extracted during validation
        publish_info = item.properties["publish_info"]
        version_number = publish_info["version"]
        publish_path = publish_info["path"]
        publish_name = publish_info["name"]
        publish_type = publish_info["type"]

        # set the alembic args that make the most sense when working with Mari.  These flags
        # will ensure the export of an Alembic file that contains all visible geometry from
        # the current scene together with UV's and face sets for use in Mari.
        alembic_args = ["-renderableOnly",   # only renderable objects (visible and not templated)
                        "-writeFaceSets",    # write shading group set assignments (Maya 2015+)
                        "-uvWrite"           # write uv's (only the current uv set gets written)
                        ]        

        # find the animated frame range to use:
        start_frame, end_frame = self._find_scene_animation_range()
        if start_frame and end_frame:
            alembic_args.append("-fr %d %d" % (start_frame, end_frame))

        # Set the output path: 
        # Note: The AbcExport command expects forward slashes!
        alembic_args.append("-file %s" % publish_path.replace("\\", "/"))

        # build the export command.  Note, use AbcExport -help in Maya for
        # more detailed Alembic export help
        abc_export_cmd = ("AbcExport -j \"%s\"" % " ".join(alembic_args))

        # ...and execute it:
        try:
            self.parent.log_debug("Executing command: %s" % abc_export_cmd)
            mel.eval(abc_export_cmd)
        except Exception, e:
            self.logger.error("Failed to export Geometry: %s" % e)
            return

        # arguments for publish registration
        self.logger.info("Registering publish...")
        publish_data = {
            "tk": publisher.sgtk,
            "context": item.context,
            "comment": item.description,
            "path": publish_path,
            "name": publish_name,
            "version_number": version_number,
            "thumbnail_path": item.get_thumbnail_as_path(),
            "published_file_type": publish_type,
            "dependency_paths": [],
        }

        # log the publish data for debugging
        self.logger.debug(
            "Populated Publish data...",
            extra={
                "action_show_more_info": {
                    "label": "Publish Data",
                    "tooltip": "Show the complete Publish data dictionary",
                    "text": "<pre>%s</pre>" % (pprint.pformat(publish_data),)
                }
            }
        )

        # create the publish and stash it in the item properties for other
        # plugins to use.
        item.properties["sg_publish_data"] = sgtk.util.register_publish(
            **publish_data)

        # inject the publish path such that children can refer to it when
        # updating dependency information
        item.properties["sg_publish_path"] = publish_path

        self.logger.info("Publish registered!")

    def finalize(self, settings, item):
        """
        Execute the finalization pass. This pass executes once all the publish
        tasks have completed, and can for example be used to version up files.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """

        publisher = self.parent

        # get the data for the publish that was just created in SG
        publish_data = item.properties["sg_publish_data"]

        # ensure conflicting publishes have their status cleared
        publisher.util.clear_status_for_conflicting_publishes(
            item.context, publish_data)

        self.logger.info(
            "Cleared the status of all previous, conflicting publishes")

        publish_path = item.properties["publish_info"]["path"]

        path = item.properties["publish_file_path"]

        self.logger.info(
            "Publish created for file: %s" % (publish_path,),
            extra={
                "action_show_in_shotgun": {
                    "label": "Show Publish",
                    "tooltip": "Open the Publish in Shotgun.",
                    "entity": publish_data
                }
            }
        )

    def _get_publish_info(self, path, settings):
        """
        This method encompasses the logic for extracting the publish path,
        version, type, and name given the path to the current session.

        If templates are configured they will be used to identify the publish
        path. If templates are not configured, the publish-in-place logic will
        be used.

        :param str path: The path to the current session
        :param dict settings: Configured publish settings

        :return: A dictionary of the form::

            {
                "publish_path": "/path/to/file/to/publish/caches/filename.v0001.abc",
                "publish_name": "filename.abc",
                "publish_version": 1,
                "publish_type": "Alembic Cache"
            }
        """

        publisher = self.parent

        # by default, extract the version number from the work file for
        # publishing. use 1 if no version in path
        version_number = publisher.util.get_version_number(path) or 1

        # publish in place by default
        publish_path = path

        # the configured publish type
        publish_type = settings["Publish Type"].value

        # ---- Check to see if templates are configured

        publish_template = self._get_template("Publish file Template", settings)

        if publish_template:

            self.logger.debug("Work and publish templates are defined")

            # templates are defined, see if the session path matches the work
            # file template
            fields = publish_template.validate_and_get_fields(path)

            self.logger.debug("Fields extracted from file: %s" % (fields,))

            if fields:

                # scene path matches the work file template. execute the
                # "classic" toolkit behavior of constructing the output publish
                # path and copying the work file to that location
                fields["TankType"] = publish_type

                # construct the publish path
                publish_path = publish_template.apply_fields(fields)

                self.logger.debug("Publish path: %s" % (publish_path,))

                # if version number is one of the fields, use it to populate the
                # publish information, else fall back to the default version,
                # extracted from the work file above
                version_number = fields.get("version", version_number)

                self.logger.debug("Version number: %s" % (version_number,))

        # get the publish name for the publish file. this will ensure we get a
        # consistent name across version publishes of this file.
        publish_name = publisher.util.get_publish_name(publish_path)

        return {
            "path": publish_path,
            "name": publish_name,
            "version": version_number,
            "type": publish_type,
        }

    def _get_template(self, template_name, settings):
        """Return the configured template for the supplied name.

        TODO: should publish2 populate "settings" with the configured template?
              currently it just stores the name.
        """

        publisher = self.parent
        template_name = settings[template_name].value

        # NOTE: we're using `get_template_by_name` here since the settings are
        # not configured at the app level.
        return publisher.get_template_by_name(template_name)

    def _find_scene_animation_range(self):
        """
        Find the animation range from the current scene.
        """
        # look for any animation in the scene:
        animation_curves = cmds.ls(typ="animCurve")
        
        # if there aren't any animation curves then just return
        # a single frame:
        if not animation_curves:
            return (1, 1)
        
        # something in the scene is animated so return the
        # current timeline.  This could be extended if needed
        # to calculate the frame range of the animated curves.
        start = int(cmds.playbackOptions(q=True, min=True))
        end = int(cmds.playbackOptions(q=True, max=True))        
        
        return (start, end)


