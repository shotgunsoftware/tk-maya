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
import sgtk
import xml.etree.ElementTree as XET

from sgtk.platform import SoftwareLauncher, SoftwareVersion, LaunchInformation

class MayaLauncher(SoftwareLauncher):
    """
    Handles launching Maya in an engine-agnostic manner.
    """

    def synergy_paths(self):
        """
        Override base class definition to restrict list of Synergy
        Config files to be Maya-specific
        """
        if self._synergy_paths is None:
            # Let the parent class deal with finding the files
            all_paths = SoftwareLauncher.synergy_paths(self)
            # Now pick out the specific ones for Maya.
            self._synergy_paths = [
                p for p in all_paths if os.path.basename(p).startswith("Maya")
            ]
        return self._synergy_paths

    def scan_software(self, versions=None):
        """
        Performs a scan for software installations.

        :param versions: List of strings representing versions
                         to search for. If set to None, search
                         for all versions. A version string is
                         DCC-specific but could be something
                         like "2017", "6.3v7" or "1.2.3.52"
        :returns: List of :class:`SoftwareVersion` instances
        """
        sw_versions = []
        for synergy_cfg in self.synergy_paths():
            swv = self._software_version_from_synergy(synergy_cfg)
            if not swv:
                self.logger.debug(
                    "Could not create SoftwareVersion from Synergy config '%s'" %
                    (synergy_cfg)
                )
                continue
            if versions and isinstance(versions, list) and str(swv.version) not in versions:
                self.logger.debug(
                    "Resolved version for Synergy config '%s' [%s] not found "
                    "in specified list of versions : %s" %
                    (synergy_cfg, swv.version, versions)
                )
                continue
            sw_versions.append(swv)

        [self._customize_software_version(swv) for swv in sw_versions]

        return sw_versions

    def resolve_software(self, sw_path):
        """
        Resolve a software instance for a given DCC path

        :param path:
        :returns: SoftwareVersion instance
        """
        synergy_data = self._synergy_data_from_executable(sw_path)
        if not synergy_data:
            return None

        sw_version = self._sofware_version_from_synergy(syn_data=synergy_data)
        return self._customize_software_version(sw_version)

    def prepare_launch(self, software_version, args, options, file_to_open=None):
        """
        Prepares the given software for launch

        :param software_version: Software Version to launch
        :param args: Command line arguments as strings
        :param options: DCC specific options to pass
        :param file_to_open: (Optional) Full path name of a file to open on launch
        :returns: LaunchInformation instance
        """
        clean_env = os.environ.copy()
        startup_path = os.path.join(self.disk_location, "startup")
        sgtk.util.append_path_to_env_var("PYTHONPATH", startup_path)
        os.environ["TANK_ENGINE"] = self.engine_name
        os.environ["TANK_CONTEXT"] = sgtk.context.serialize(self.context)
        if file_to_open:
            os.environ["TANK_FILE_TO_OPEN"] = file_to_open

        launch_info = LaunchInformation(
            software_version.path, args, os.environ.copy(),
        )
        os.environ.clear()
        os.environ.update(clean_env)

        return launch_info

    def _icon_from_executable(self, exec_path):
        """
        Find the application icon based on the executable path and
        current platform.

        :param exec_path: Full path to the executable
        :returns: Full path to application icon as a string or None.
        """
        icon_base_path = ""
        if sys.platform == "darwin" and "Maya.app" in exec_path:
            icon_base_path = os.path.join(
                "".join(exec_path.partition("Maya.app")[0:2]),
                "Contents"
            )

        elif sys.platform in ["win32", "linux2"] and "bin" in exec_path:
            icon_base_path = "".join(exec_path.partition("bin")[0:1])

        icon_path = os.path.join(icon_base_path, "icons", "mayaico.png")
        return icon_path if os.path.exists(icon_path) else None

    def _customize_software_version(self, sw_version):
        """
        Update SoftwareVersions retrieved from the parent class
        with Maya specific information.

        :param sw_version: SoftwareVersion instance to be updated.
        """
        if not sw_version:
            # There's nothing to do
            return sw_version

        # Set the default icon
        sw_version.icon = self._icon_from_executable(sw_version.path)

        if sys.platform  == "darwin" and "Maya.app" in sw_version.path:
            # There seems to be an anomoly with launching Maya from the
            # full executable path on MacOS. Everything behaves nicer if
            # Maya is launched from the bundle Maya.app directory instead.
            sw_version.path = "".join(sw_version.path.partition("Maya.app")[0:2])

