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


class MayaSessionPublishPlugin(HookBaseClass):
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
        Publishes the file to Shotgun. A <b>Publish</b> entry will be
        created in Shotgun which will include a reference to the file's current
        path on disk. If templates are configured and the work file template
        matches the current session path, the work file will be copied to the
        publish file template path which will be the file that is published.
        Other users will be able to access the published file via the
        <b><a href='%s'>Loader</a></b> so long as they have access to the file's
        location on disk.

        If the session has not been saved, validation will fail and a button
        will be provided in the logging output to save the file.

        <h3>File versioning</h3>
        If the filename contains a version number, the process will bump the
        file to the next version after publishing.

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

        After publishing, if a version number is detected in the work file, the
        work file will automatically be saved to the next incremental version
        number. For example, <code>filename.v001.ext</code> will be published
        and copied to <code>filename.v002.ext</code>

        If the next incremental version of the file already exists on disk, the
        validation step will produce a warning, and a button will be provided in
        the logging output which will allow saving the session to the next
        available version number prior to publishing.

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
                "default": "Maya Scene",
                "description": "SG publish type to associate publishes with."
            },
            "Work file Template": {
                "type": "template",
                "default": None,
                "description": "Template path for artist work files. Should "
                               "correspond to a template defined in "
                               "templates.yml."
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
        return ["maya.session"]

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

        path = _session_path()

        if not path:
            # the session has not been saved before (no path determined).
            # provide a save button. the session will need to be saved before
            # validation will succeed.
            self.logger.warn(
                "The Maya session has not been saved.",
                extra=_get_save_as_action()
            )

        self.logger.info(
            "Maya '%s' plugin accepted the current Maya session." %
            (self.name,)
        )
        return {
            "accepted": True,
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

        publisher = self.parent
        path = _session_path()

        if not path:
            # the session still requires saving. provide a save button.
            # validation fails.
            self.logger.error(
                "The Maya session has not been saved.",
                extra=_get_save_as_action()
            )
            return False

        # ensure we have an updated project root
        project_root = cmds.workspace(q=True, rootDirectory=True)
        item.properties["project_root"] = project_root

        # warn if no project root could be determined.
        if not project_root:
            self.logger.warning(
                "Your session is not part of a maya project.",
                extra={
                    "action_button": {
                        "label": "Set Project",
                        "tooltip": "Set the maya project",
                        "callback": lambda: mel.eval('setProject ""')
                    }
                }
            )

        # get the path in a normalized state. no trailing separator,
        # separators are appropriate for current os, no double separators,
        # etc.
        path = sgtk.util.ShotgunPath.normalize(path)

        # determine the publish path, version, type, and name
        publish_info = self._get_publish_info(path, settings)

        publish_name = publish_info["publish_name"]

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

        # check to see if the next version of the work file already exists on
        # disk. if so, warn the user and provide the ability to jump to save
        # to that version now
        (next_version_path, version) = self._get_next_version_info(
            path, settings)
        if next_version_path and os.path.exists(next_version_path):

            # determine the next available version_number. just keep asking for
            # the next one until we get one that doesn't exist.
            while os.path.exists(next_version_path):
                (next_version_path, version) = self._get_next_version_info(
                    next_version_path, settings)

            self.logger.error(
                "The next version of this file already exists on disk.",
                extra={
                    "action_button": {
                        "label": "Save to v%s" % (version,),
                        "tooltip": "Save to the next available version number, "
                                   "v%s" % (version,),
                        "callback": lambda: _save_session(next_version_path)
                    }
                }
            )
            return False

        # store the session path since this is guaranteed to run just before
        # the publish itself
        item.properties["work_file_path"] = path

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
        path = item.properties["work_file_path"]

        # ensure the session is saved
        _save_session(path)

        # get all the publish info extracted during validation
        publish_info = item.properties["publish_info"]
        version_number = publish_info["publish_version"]
        publish_path = publish_info["publish_path"]
        publish_name = publish_info["publish_name"]
        publish_type = publish_info["publish_type"]

        # if the path doesn't match the publish path, copy the file to the
        # publish path
        if path != publish_path and not os.path.exists(publish_path):
            publish_folder = os.path.dirname(publish_path)
            publisher.ensure_folder_exists(publish_folder)
            copy_file(path, publish_path)
            self.logger.debug(
                "Copied work file (%s) to publish path (%s)" %
                (path, publish_path)
            )

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
            "dependency_paths": _maya_find_additional_session_dependencies(),
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

        publish_path = item.properties["publish_info"]["publish_path"]

        path = item.properties["work_file_path"]

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

        # insert the path into the properties
        item.properties["next_version_path"] = self._bump_file_version(
            path, settings)

    def _bump_file_version(self, path, settings):
        """
        Save the supplied path to the next version on disk.
        """

        (next_version_path, version) = self._get_next_version_info(
            path, settings)

        if version is None:
            self.logger.debug(
                "No version number detected in the publish path. "
                "Skipping the bump file version step."
            )
            return None

        self.logger.info("Incrementing session file version number...")

        # nothing to do if the next version path can't be determined or if it
        # already exists.
        if not next_version_path:
            self.logger.warning("Could not determine the next version path.")
            return None
        elif os.path.exists(next_version_path):
            self.logger.warning(
                "The next version of the path already exists",
                extra={
                    "action_show_folder": {
                        "path": next_version_path
                    }
                }
            )
            return None

        # save the session to the new path
        _save_session(next_version_path)
        self.logger.info("Session saved as: %s" % (next_version_path,))

        return next_version_path

    def _get_next_version_info(self, path, settings):
        """
        Return the next version of the supplied path.

        If templates are configured, use template logic. Otherwise, fall back to
        the zero configuration, path_info hook logic.

        :param str path: A path with a version number.
        :param settings: Configured settings for this plugin.

        :return: A tuple of the form::

            # the first item is the supplied path with the version bumped by 1
            # the second item is the new version number
            (next_version_path, version)
        """

        publisher = self.parent

        # get the configured work file template
        work_template = self._get_template("Work file Template", settings)

        # set these so we can check to see if the template logic applied
        next_version_path = None
        version = None

        if work_template:
            # if the work file template matches, we'll get parsed fields
            fields = work_template.validate_and_get_fields(path)

            if fields and "version" in fields:
                # template matched. bump the version number and re-apply to
                # the template
                fields["version"] += 1
                next_version_path = work_template.apply_fields(fields)
                version = fields["version"]

        if not next_version_path and not version:
            # fall back to the "zero config" logic
            next_version_path = publisher.util.get_next_version_path(path)
            version = publisher.util.get_version_number(next_version_path)

        return (next_version_path, version)

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
                "publish_path": "/path/to/file/to/publish/filename.v0001.ma",
                "publish_name": "filename.ma",
                "publish_version": 1,
                "publish_type": "Maya Scene"
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

        # NOTE: we're using `get_template_by_name` here since the settings are
        # not configured at the app level.

        work_template = self._get_template("Work file Template", settings)
        publish_template = self._get_template("Publish file Template", settings)

        if work_template and publish_template:

            self.logger.debug("Work and publish templates are defined")

            # templates are defined, see if the session path matches the work
            # file template
            fields = work_template.validate_and_get_fields(path)

            self.logger.debug("Fields extracted from work file: %s" % (fields,))

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
            "publish_path": publish_path,
            "publish_name": publish_name,
            "publish_version": version_number,
            "publish_type": publish_type,
        }

    def _get_template(self, template_name, settings):
        """Return the configured template for the supplied name.

        TODO: should publish2 populate "settings" with the configured template?
              currently it just stores the name.
        """

        publisher = self.parent
        template_name = settings[template_name].value
        return publisher.get_template_by_name(template_name)


def _maya_find_additional_session_dependencies():
    """
    Find additional dependencies from the session
    """

    # default implementation looks for references and
    # textures (file nodes) and returns any paths that
    # match a template defined in the configuration
    ref_paths = set()

    # first let's look at maya references
    ref_nodes = cmds.ls(references=True)
    for ref_node in ref_nodes:
        # get the path:
        ref_path = cmds.referenceQuery(ref_node, filename=True)
        # make it platform dependent
        # (maya uses C:/style/paths)
        ref_path = ref_path.replace("/", os.path.sep)
        if ref_path:
            ref_paths.add(ref_path)

    # now look at file texture nodes
    for file_node in cmds.ls(l=True, type="file"):
        # ensure this is actually part of this session and not referenced
        if cmds.referenceQuery(file_node, isNodeReferenced=True):
            # this is embedded in another reference, so don't include it in
            # the breakdown
            continue

        # get path and make it platform dependent
        # (maya uses C:/style/paths)
        texture_path = cmds.getAttr(
            "%s.fileTextureName" % file_node).replace("/", os.path.sep)
        if texture_path:
            ref_paths.add(texture_path)

    return list(ref_paths)


def _session_path():
    """
    Return the path to the current session
    :return:
    """
    path = cmds.file(query=True, sn=True)

    if isinstance(path, unicode):
        path = path.encode("utf-8")

    return path


def _save_session(path):
    """
    Save the current session to the supplied path.
    """

    # Maya can choose the wrong file type so we should set it here
    # explicitly based on the extension
    maya_file_type = None
    if path.lower().endswith(".ma"):
        maya_file_type = "mayaAscii"
    elif path.lower().endswith(".mb"):
        maya_file_type = "mayaBinary"

    cmds.file(rename=path)

    # save the scene:
    if maya_file_type:
        cmds.file(save=True, force=True, type=maya_file_type)
    else:
        cmds.file(save=True, force=True)


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
            "callback": callback
        }
    }
