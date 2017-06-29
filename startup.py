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
from sgtk.platform import SoftwareLauncher, SoftwareVersion, LaunchInformation


class MayaLauncher(SoftwareLauncher):
    """
    Handles launching Maya executables. Automatically starts up
    a tk-maya engine with the current context in the new session
    of Maya.
    """

    # Named regex strings to insert into the executable template paths when
    # matching against supplied versions and products. Similar to the glob
    # strings, these allow us to alter the regex matching for any of the
    # variable components of the path in one place
    COMPONENT_REGEX_LOOKUP = {
        "version": "[\d.]+",
        "mach": "x\d+"
    }

    # This dictionary defines a list of executable template strings for each
    # of the supported operating systems. The templates are used for both
    # globbing and regex matches by replacing the named format placeholders
    # with an appropriate glob or regex string. As Side FX adds modifies the
    # install path on a given OS for a new release, a new template will need
    # to be added here.
    EXECUTABLE_TEMPLATES = {
        "darwin": [
            # /Applications/Autodesk/maya2015/Maya.app
            "/Applications/Autodesk/maya{version}/Maya.app",
        ],
        "win32": [
            # C:/Program Files/Autodesk/Maya2015/bin/maya.exe
            "C:/Program Files/Autodesk/Maya{version}/bin/maya.exe",
        ],
        "linux2": [
            # /usr/autodesk/maya2016/bin/maya
            "/usr/autodesk/maya{version}/bin/maya",
            "/usr/autodesk/maya{version}-{mach}/bin/maya",
        ]
    }

    @property
    def minimum_supported_version(self):
        """
        The minimum software version that is supported by the launcher.
        """
        return "2014"

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
        find_plugins = self.get_setting("launch_builtin_plugins")
        if find_plugins:
            # Parse the specified comma-separated list of plugins
            self.logger.debug(
                "Plugins found from 'launch_builtin_plugins': %s" % find_plugins
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
                        # Insert at beginning of list to give priority to toolkit plugins
                        # launched from the desktop app over standalone ones whose
                        # path is already part of the MAYA_MODULE_PATH env var
                        maya_module_paths.insert(0, load_plugin)
                else:
                    # Report the missing plugin directory
                    self.logger.warning(
                        "Resolved plugin path '%s' does not exist!" %
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
            self.logger.debug("Preparing Maya Launch via Toolkit Classic methodology ...")
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

        # the engine icon in case we need to use it as a fallback
        engine_icon = os.path.join(self.disk_location, "icon_256.png")

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
            # use the bundled engine icon
            self.logger.debug("Couldn't find bundled icon. Using engine icon.")
            return engine_icon

        # Append the standard icon to the base path and
        # return that path if it exists, else None.
        icon_path = os.path.join(icon_base_path, "icons", "mayaico.png")
        if not os.path.exists(icon_path):
            self.logger.debug(
                "Icon path '%s' resolved from executable '%s' does not exist!"
                "Falling back on engine icon." % (icon_path, exec_path)
            )
            return engine_icon

        # Record what the resolved icon path was.
        self.logger.debug(
            "Resolved icon path '%s' from input executable '%s'." %
            (icon_path, exec_path)
        )
        return icon_path

    def scan_software(self):
        """
        Scan the filesystem for maya executables.

        :return: A list of :class:`SoftwareVersion` objects.
        """

        self.logger.debug("Scanning for Maya executables...")

        supported_sw_versions = []
        for sw_version in self._find_software():
            (supported, reason) = self._is_supported(sw_version)
            if supported:
                supported_sw_versions.append(sw_version)
            else:
                self.logger.debug(
                    "SoftwareVersion %s is not supported: %s" %
                    (sw_version, reason)
                )

        return supported_sw_versions

    def _find_software(self):
        """
        Find executables in the default install locations.
        """

        # all the executable templates for the current OS
        executable_templates = self.EXECUTABLE_TEMPLATES.get(sys.platform, [])

        # all the discovered executables
        sw_versions = []

        for executable_template in executable_templates:

            self.logger.debug("Processing template %s.", executable_template)

            executable_matches = self._glob_and_match(
                executable_template,
                self.COMPONENT_REGEX_LOOKUP
            )

            # Extract all products from that executable.
            for (executable_path, key_dict) in executable_matches:

                # extract the matched keys form the key_dict (default to None if
                # not included)
                executable_version = key_dict.get("version")

                sw_versions.append(
                    SoftwareVersion(
                        executable_version,
                        "Maya",
                        executable_path,
                        self._icon_from_executable(executable_path)
                    )
                )

        return sw_versions
