# Copyright (c) 2017 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import glob
import os
import maya.cmds as cmds
import maya.mel as mel
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class MayaSessionCollector(HookBaseClass):
    """
    Collector that operates on the maya session. Should inherit from the basic
    collector hook.
    """

    @property
    def settings(self):
        """
        Dictionary defining the settings that this collector expects to receive
        through the settings parameter in the process_current_session and
        process_file methods.

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

        # grab any base class settings
        collector_settings = super(MayaSessionCollector, self).settings or {}

        # settings specific to this collector
        maya_session_settings = {
            "Work Template": {
                "type": "template",
                "default": None,
                "description": "Template path for artist work files. Should "
                               "correspond to a template defined in "
                               "templates.yml. If configured, is made available"
                               "to publish plugins via the collected item's "
                               "properties. ",
            },
        }

        # update the base settings with these settings
        collector_settings.update(maya_session_settings)

        return collector_settings

    def process_current_session(self, settings, parent_item):
        """
        Analyzes the current session open in Maya and parents a subtree of
        items under the parent_item passed in.

        :param dict settings: Configured settings for this collector
        :param parent_item: Root item instance

        """

        # create an item representing the current maya session
        item = self.collect_current_maya_session(settings, parent_item)
        project_root = item.properties["project_root"]

        # look at the render layers to find rendered images on disk
        self.collect_rendered_images(item)

        # if we can determine a project root, collect other files to publish
        if project_root:

            self.logger.info(
                "Current Maya project is: %s." % (project_root,),
                extra={
                    "action_button": {
                        "label": "Change Project",
                        "tooltip": "Change to a different Maya project",
                        "callback": lambda: mel.eval('setProject ""')
                    }
                }
            )

            self.collect_playblasts(item, project_root)
            self.collect_alembic_caches(item, project_root)
        else:

            self.logger.info(
                "Could not determine the current Maya project.",
                extra={
                    "action_button": {
                        "label": "Set Project",
                        "tooltip": "Set the Maya project",
                        "callback": lambda: mel.eval('setProject ""')
                    }
                }
            )

        if cmds.ls(geometry=True, noIntermediate=True):
            self._collect_session_geometry(item)

    def collect_current_maya_session(self, settings, parent_item):
        """
        Creates an item that represents the current maya session.

        :param parent_item: Parent Item instance

        :returns: Item of type maya.session
        """

        publisher = self.parent

        # get the path to the current file
        path = cmds.file(query=True, sn=True)

        # determine the display name for the item
        if path:
            file_info = publisher.util.get_file_path_components(path)
            display_name = file_info["filename"]
        else:
            display_name = "Current Maya Session"

        # create the session item for the publish hierarchy
        session_item = parent_item.create_item(
            "maya.session",
            "Maya Session",
            display_name
        )

        # get the icon path to display for this item
        icon_path = os.path.join(
            self.disk_location,
            os.pardir,
            "icons",
            "maya.png"
        )
        session_item.set_icon_from_path(icon_path)

        # discover the project root which helps in discovery of other
        # publishable items
        project_root = cmds.workspace(q=True, rootDirectory=True)
        session_item.properties["project_root"] = project_root

        # if a work template is defined, add it to the item properties so
        # that it can be used by attached publish plugins
        work_template_setting = settings.get("Work Template")
        if work_template_setting:

            work_template = publisher.engine.get_template_by_name(
                work_template_setting.value)

            # store the template on the item for use by publish plugins. we
            # can't evaluate the fields here because there's no guarantee the
            # current session path won't change once the item has been created.
            # the attached publish plugins will need to resolve the fields at
            # execution time.
            session_item.properties["work_template"] = work_template
            self.logger.debug("Work template defined for Maya collection.")

        self.logger.info("Collected current Maya scene")

        return session_item

    def collect_alembic_caches(self, parent_item, project_root):
        """
        Creates items for alembic caches

        Looks for a 'project_root' property on the parent item, and if such
        exists, look for alembic caches in a 'cache/alembic' subfolder.

        :param parent_item: Parent Item instance
        :param str project_root: The maya project root to search for alembics
        """

        # ensure the alembic cache dir exists
        cache_dir = os.path.join(project_root, "cache", "alembic")
        if not os.path.exists(cache_dir):
            return

        self.logger.info(
            "Processing alembic cache folder: %s" % (cache_dir,),
            extra={
                "action_show_folder": {
                    "path": cache_dir
                }
            }
        )

        # look for alembic files in the cache folder
        for filename in os.listdir(cache_dir):
            cache_path = os.path.join(cache_dir, filename)

            # do some early pre-processing to ensure the file is of the right
            # type. use the base class item info method to see what the item
            # type would be.
            item_info = self._get_item_info(filename)
            if item_info["item_type"] != "file.alembic":
                continue

            # allow the base class to collect and create the item. it knows how
            # to handle alembic files
            super(MayaSessionCollector, self)._collect_file(
                parent_item,
                cache_path
            )

    def _collect_session_geometry(self, parent_item):
        """
        Creates items for session geometry to be exported.

        :param parent_item: Parent Item instance
        """

        geo_item = parent_item.create_item(
            "maya.session.geometry",
            "Geometry",
            "All Session Geometry"
        )

        # get the icon path to display for this item
        icon_path = os.path.join(
            self.disk_location,
            os.pardir,
            "icons",
            "geometry.png"
        )

        geo_item.set_icon_from_path(icon_path)

    def collect_playblasts(self, parent_item, project_root):
        """
        Creates items for quicktime playblasts.

        Looks for a 'project_root' property on the parent item, and if such
        exists, look for movie files in a 'movies' subfolder.

        :param parent_item: Parent Item instance
        :param str project_root: The maya project root to search for playblasts
        """

        movie_dir_name = None

        # try to query the file rule folder name for movies. This will give
        # us the directory name set for the project where movies will be
        # written
        if "movie" in cmds.workspace(fileRuleList=True):
            # this could return an empty string
            movie_dir_name = cmds.workspace(fileRuleEntry='movie')

        if not movie_dir_name:
            # fall back to the default
            movie_dir_name = "movies"

        # ensure the movies dir exists
        movies_dir = os.path.join(project_root, movie_dir_name)
        if not os.path.exists(movies_dir):
            return

        self.logger.info(
            "Processing movies folder: %s" % (movies_dir,),
            extra={
                "action_show_folder": {
                    "path": movies_dir
                }
            }
        )

        # look for movie files in the movies folder
        for filename in os.listdir(movies_dir):

            # do some early pre-processing to ensure the file is of the right
            # type. use the base class item info method to see what the item
            # type would be.
            item_info = self._get_item_info(filename)
            if item_info["item_type"] != "file.video":
                continue

            movie_path = os.path.join(movies_dir, filename)

            # allow the base class to collect and create the item. it knows how
            # to handle movie files
            item = super(MayaSessionCollector, self)._collect_file(
                parent_item,
                movie_path
            )

            # the item has been created. update the display name to include
            # the an indication of what it is and why it was collected
            item.name = "%s (%s)" % (item.name, "playblast")

    def collect_rendered_images(self, parent_item):
        """
        Creates items for any rendered images that can be identified by
        render layers in the file.

        :param parent_item: Parent Item instance
        :return:
        """

        # iterate over defined render layers and query the render settings for
        # information about a potential render
        for layer in cmds.ls(type="renderLayer"):

            self.logger.info("Processing render layer: %s" % (layer,))

            # use the render settings api to get a path where the frame number
            # spec is replaced with a '*' which we can use to glob
            (frame_glob,) = cmds.renderSettings(
                genericFrameImageName="*",
                fullPath=True,
                layer=layer
            )

            # see if there are any files on disk that match this pattern
            rendered_paths = glob.glob(frame_glob)

            if rendered_paths:
                # we only need one path to publish, so take the first one and
                # let the base class collector handle it
                item = super(MayaSessionCollector, self)._collect_file(
                    parent_item,
                    rendered_paths[0],
                    frame_sequence=True
                )

                # the item has been created. update the display name to include
                # the an indication of what it is and why it was collected
                item.name = "%s (Render Layer: %s)" % (item.name, layer)
