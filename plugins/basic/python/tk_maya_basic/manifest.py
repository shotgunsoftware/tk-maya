# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import sys
import pprint

class Manifest(object):
    """
    General class that can be used in different plugin environments.

    Given a plugin root path, this method will load up the manifest data
    and wrap it in various accessors
    """

    def __init__(self, root_path):
        """
        :param root_path: Plugin root path.
        """
        # a core is always located in this location
        core_path = os.path.join(root_path, "bundle_cache", "tk-core", "python")
        if core_path not in sys.path:
            sys.path.insert(0, core_path)
        # import yaml parser
        from tank_vendor import yaml

        self._root_path = root_path
        self._manifest_file = os.path.join(root_path, "info.yml")
        if not os.path.exists(self._manifest_file):
            raise RuntimeError("Cannot find plugin manifest '%s'" % self._manifest_file)

        with open(self._manifest_file) as stream:
            self._manifest_data = yaml.load(stream)

    def __repr__(self):
        """
        String representation showing the path and contents
        """
        repr = "Toolkit Plugin manifest '%s':\n" % self._manifest_file
        repr += pprint.pformat(self._manifest_data)
        return repr

    @property
    def bundle_cache_root(self):
        """
        The full path to the bundle cache root
        """
        return os.path.join(self._root_path, "bundle_cache")

    @property
    def plugin_core_path(self):
        """
        The full path to the toolkit core API suitable for the plugin
        """
        return os.path.join(self._root_path, "bundle_cache", "tk-core", "python")

    def get_setting(self, settings_name):
        """
        Return the value for a particular setting in the
        'configuration' section of the manifest. If the setting hasn't been
        defined, ``None`` will be returned.

        :param settings_name: Name of setting to retrieve
        :returns: Settings value or None if not defined
        """
        return self._manifest_data["configuration"].get(settings_name)

    @property
    def base_configuration(self):
        """
        The base configuration dict or uri
        """
        if "base_configuration" not in self._manifest_data:
            raise RuntimeError("No base configuration defined in the plugin manifest.")
        return self._manifest_data.get("base_configuration")

    @property
    def entry_point(self):
        """
        The entry point for this plugin.
        See http://developer.shotgunsoftware.com/tk-core/bootstrap.html#sgtk.bootstrap.ToolkitManager.entry_point
        """
        if "entry_point" not in self._manifest_data:
            raise RuntimeError("No entry point defined in the plugin manifest.")
        return self._manifest_data.get("entry_point")

    @property
    def name(self):
        """
        The plugin display name
        """
        return self._manifest_data.get("name") or "Unnamed Plugin"

    @property
    def description(self):
        """
        The plugin description
        """
        return self._manifest_data.get("description") or "No information available"

    @property
    def author(self):
        """
        The plugin author
        """
        return self._manifest_data.get("author") or ""

    @property
    def organization(self):
        """
        The plugin organization
        """
        return self._manifest_data.get("organization") or ""

    @property
    def contact(self):
        """
        The plugin organization
        """
        return self._manifest_data.get("contact") or ""

    @property
    def url(self):
        """
        Associated url
        """
        return self._manifest_data.get("url") or ""

    @property
    def version(self):
        """
        Version string
        """
        return self._manifest_data.get("version") or ""

    @property
    def build_information(self):
        """
        Build information string
        """
        return self._manifest_data.get("version") or ""


