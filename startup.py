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
import re
import glob
import subprocess

from xml.etree import ElementTree

import sgtk
from sgtk import TankError
from sgtk.platform import SoftwareLauncher, SoftwareVersion, LaunchInformation

class MayaLauncher(SoftwareLauncher):
    """
    Handles launching Maya executables. Automatically starts up
    a tk-maya engine with the current context in the new session
    of Maya.
    """

    @property
    def minimum_supported_version(self):
        """
        The minimum software version that is supported by the launcher.
        """
        return "2016"

    def prepare_launch(self, exec_path, args, file_to_open=None):
        """
        Prepares an environment to launch Maya in that will automatically
        load Toolkit and the tk-maya engine when Maya starts.

        :param str exec_path: Path to Maya executable to launch.
        :param str args: Command line arguments as strings.
        :param str file_to_open: (optional) Full path name of a file to open on launch.
        :returns: :class:`LaunchInformation` instance
        """
        required_env = {}

        # Run the engine's userSetup.py file when Maya starts up
        # by appending it to the env PYTHONPATH.
        startup_path = os.path.join(self.disk_location, "startup")
        sgtk.util.append_path_to_env_var("PYTHONPATH", startup_path)
        required_env["PYTHONPATH"] = os.environ["PYTHONPATH"]

        # Check the engine settings to see whether any plugins have been
        # specified to load.
        load_plugins = self.get_setting("launch_builtin_plugin") or None
        if load_plugins:
            # Parse the specified comma-separated list of plugins
            find_plugins = [p.strip() for p in load_plugins.split(",") if p.strip()]
            self.logger.debug(
                "Plugins found from 'launch_builtin_plugins' string value "
                "split by ',': %s" % find_plugins
            )

            # Keep track of the specific list of Toolkit plugins to load when
            # launching Maya. This list is passed through the environment and
            # used by the startup/userSetup.py file.
            load_maya_plugins = []

            # Add Toolkit plugins to load to the MAYA_MODULE_PATH environment
            # variable so the Maya loadPlugin command can find them.
            maya_module_paths = os.environ.get("MAYA_MODULE_PATH") or []
            if maya_module_paths:
                maya_module_paths = maya_module_paths.split(os.pathsep)

            for find_plugin in find_plugins:
                load_plugin = os.path.join(
                    self.disk_location, "plugins", find_plugin
                )
                if os.path.exists(load_plugin):
                    # If the plugin path exists, add it to the list of MAYA_MODULE_PATHS
                    # so Maya can find it and to the list of SGTK_LOAD_MAYA_PLUGINS so
                    # the startup's userSetup.py file knows what plugins to load.
                    self.logger.debug("Preparing to launch builtin plugin '%s'" % load_plugin)
                    load_maya_plugins.append(load_plugin)
                    if load_plugin not in maya_module_paths:
                        maya_module_paths.append(load_plugin)
                else:
                    # Report the missing plugin directory
                    self.logger.warning("Resolved plugin path '%s' does not exist!" %
                        load_plugin
                    )

            # Add MAYA_MODULE_PATH and SGTK_LOAD_MAYA_PLUGINS to the launch
            # environment.
            required_env["MAYA_MODULE_PATH"] = os.pathsep.join(maya_module_paths)
            required_env["SGTK_LOAD_MAYA_PLUGINS"] = os.pathsep.join(load_maya_plugins)

            # Add context and site info
            std_env = self.get_standard_plugin_environment()
            required_env.update(std_env)

        else:
            # Prepare the launch environment with variables required by the
            # classic bootstrap approach.
            self.logger.info("Preparing Maya Launch via Toolkit Classic methodology ...")
            required_env["SGTK_ENGINE"] = self.engine_name
            required_env["SGTK_CONTEXT"] = sgtk.context.serialize(self.context)

        if file_to_open:
            # Add the file name to open to the launch environment
            required_env["SGTK_FILE_TO_OPEN"] = file_to_open

        return LaunchInformation(exec_path, args, required_env)

    ##########################################################################################
    # private methods

    def _icon_from_executable(self, exec_path):
        """
        Find the application icon based on the executable path and
        current platform.

        :param exec_path: Full path to the executable.

        :returns: Full path to application icon as a string or None.
        """
        self.logger.debug(
            "Looking for Application icon for executable '%s' ..." %
            exec_path
        )
        icon_base_path = ""
        if sys.platform == "darwin" and "Maya.app" in exec_path:
            # e.g. /Applications/Autodesk/maya2016.5/Maya.app/Contents
            icon_base_path = os.path.join(
                "".join(exec_path.partition("Maya.app")[0:2]),
                "Contents"
            )

        elif sys.platform in ["win32", "linux2"] and "bin" in exec_path:
            # e.g. C:\Program Files\Autodesk\Maya2017\  or
            #      /usr/autodesk/maya2017/
            icon_base_path = "".join(exec_path.partition("bin")[0:1])

        if not icon_base_path:
            # If no base path, no icon
            self.logger.debug(
                "Could not resolve icon base path for executable '%s'." %
                exec_path
            )
            return None

        # Append the standard icon to the base path and
        # return that path if it exists, else None.
        icon_path = os.path.join(icon_base_path, "icons", "mayaico.png")
        if not os.path.exists(icon_path):
            self.logger.debug(
                "Icon path '%s' resolved from executable '%s' does not exist!" %
                (icon_path, exec_path)
            )
            return None

        # Record what the resolved icon path was.
        self.logger.debug("Resolved icon path '%s' from input executable '%s'." %
            (icon_path, exec_path)
        )
        return icon_path

    def _resolve_path_for_platform(self, exec_path):
        """
        In some cases, the resolved path to an executable won't launch properly
        as is. Identify those cases here and modify the input executable path
        into something that will launch correctly on the current platform.

        :param str exec_path: Full path to a Maya executable

        :returns: Full path to a Maya executable that will properly launch
                  on the current platform.
        """
        if not exec_path:
            # Nothing to check
            return exec_path

        if sys.platform == "darwin" and "Maya.app" in exec_path:
            # There seems to be an anomoly with launching Maya from the
            # full executable path on MacOS. Everything behaves nicer if
            # Maya is launched from the bundle Maya.app directory instead.
            exec_path = "".join(exec_path.partition("Maya.app")[0:2])

        elif sys.platform == "linux2" and exec_path.endswith("maya.bin"):
            # Specifying the .bin suffix when launching sometimes results
            # in linked libraries not getting loaded correctly. Stripping
            # off the .bin suffix seems to resolve that issue.
            path_parts = exec_path.split(os.path.sep)
            path_parts[-1] = path_parts[-1].replace("maya.bin", "maya")
            exec_path = os.path.sep.join(path_parts)

        return exec_path

    def _scan_software(self):
        """
        Creates SoftwareVersion instances based on the path values used
        in the default configuration paths.yml environment.

        :returns: List of :class:`SoftwareVersion` instances
        """
        # Determine a list of paths to search for Maya executables based
        # on default installation path(s) for the current platform
        search_paths = []
        exec_paths = []
        if sys.platform == "darwin":
            search_paths = glob.glob("/Applications/Autodesk/maya*")

        elif sys.platform == "win32":
            search_paths = glob.glob("C:\Program Files\Autodesk\Maya*")

        elif sys.platform == "linux2":
            exec_paths.append("maya")

        if search_paths:
            for search_path in search_paths:
                # Construct the expected executable name for this path.
                # If it exists, add it to the list of exec_paths to check.
                exec_path = None
                if sys.platform == "darwin":
                    exec_path = os.path.join(search_path, "Maya.app", "Contents", "bin", "maya")

                elif sys.platform == "win32":
                    exec_path = os.path.join(search_path, "bin", "maya.exe")

                if exec_path and os.path.exists(exec_path):
                    exec_paths.append(exec_path)

        sw_versions = []

        default_product = "Maya"

        if exec_paths:
            for exec_path in exec_paths:
                # Check to see if the version number can be parsed from the path name.
                path_sw_versions = [p.lower() for p in exec_path.split(os.path.sep)
                    if re.match("maya[0-9]+[.0-9]*$", p.lower()) is not None
                ]
                if path_sw_versions:
                    # Use this sub dir to determine the default product name
                    # and version for the SoftwareVersion to be created.
                    exec_dir = path_sw_versions[0]
                    default_version = exec_dir.replace("maya", "")
                    self.logger.debug(
                        "Resolved version '%s' from executable '%s'." %
                        (default_version, exec_path)
                    )
                else:
                    try:
                        # This works, but makes the Desktop project window disappear
                        # for some reason, which isn't very nice. Therefore, use as a
                        # last resort.
                        version_output = subprocess.check_output([exec_path, "-v"])
                    except OSError:
                        self.logger.exception(
                            "Could not retrieve version information from default "
                            "executable path '%s'." % exec_path
                        )
                        continue

                    # Display and version information are contained before the first ','
                    # in the output version string.
                    display_info = version_output[0:version_output.find(",")]

                    # Update known oddball display values to "nicer" version numbers.
                    if "2016 Extension 2 SP1" in display_info:
                        display_info = display_info.replace("2016 Extension 2 SP1", "2016.5")

                    # Parse the default version from the display name determined from
                    # the version output.
                    default_version = display_info.lower().replace("maya", "").strip()
                    self.logger.debug(
                        "Resolved version '%s' from version output '%s'" %
                        (default_version, version_output)
                    )

                # Create a SoftwareVersion using the information from executable
                # path(s) found in default locations.
                exec_path = self._resolve_path_for_platform(exec_path)
                self.logger.debug("Creating SoftwareVersion for executable '%s'." % exec_path)
                sw_versions.append(SoftwareVersion(
                    default_version,
                    default_product,
                    exec_path,
                    self._icon_from_executable(exec_path)
                ))

        return sw_versions

