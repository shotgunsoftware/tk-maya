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
import xml.etree.ElementTree as XML_ET

import sgtk
from sgtk import TankError
from sgtk.platform import SoftwareLauncher, SoftwareVersion, LaunchInformation

class MayaLauncher(SoftwareLauncher):
    """
    Handles launching Maya without having an active engine.
    """
    def scan_software(self, versions=None, display_name=None, icon=None):
        """
        Performs a scan for software installations.

        :param versions: List of strings representing versions
                         to search for. If set to None, search
                         for all versions. A version string is
                         DCC-specific but could be something
                         like "2017", "6.3v7" or "1.2.3.52"
        :param display_name: (optional) Specify label to use for all
                             SoftwareVersions found.
        :param icon: (optional) Specify icon to use for all
                     SoftwareVersions found.

        :returns: List of :class:`SoftwareVersion` instances
        """
        # First look for executables using the Autodesk Synergy registry.
        sw_versions = _synergy_software_versions(
            self.logger, versions, display_name, icon
        )
        if not sw_versions:
            # Look for executables in paths formerly specified by the
            # default configuration paths.yml file.
            sw_versions = _default_path_software_versions(
                self.logger, versions, display_name, icon
            )
        if not sw_versions:
            self.logger.info(
                "Unable to determine available SoftwareVersions for engine %s" %
                self.engine_name
            )
            return []

        return  sw_versions


    def prepare_launch(self, exec_path, args, options, file_to_open=None):
        """
        Prepares the given software for launch

        :param exec_path: Path to DCC executable to launch
        :param args: Command line arguments as strings
        :param options: DCC specific options to pass
        :param file_to_open: (Optional) Full path name of a file to open on launch

        :returns: LaunchInformation instance
        """
        required_env = {}
        startup_path = os.path.join(self.disk_location, "startup")
        sgtk.util.append_path_to_env_var("PYTHONPATH", startup_path)
        required_env["PYTHONPATH"] = os.environ["PYTHONPATH"]
        required_env["TANK_ENGINE"] = self.engine_name
        required_env["TANK_CONTEXT"] = sgtk.context.serialize(self.context)
        if file_to_open:
            required_env["TANK_FILE_TO_OPEN"] = file_to_open

        return LaunchInformation(exec_path, args, required_env)


def _icon_from_executable(exec_path):
    """
    Find the application icon based on the executable path and
    current platform.

    :param exec_path: Full path to the executable

    :returns: Full path to application icon as a string or None.
    """
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
        return None

    # Append the standard icon to the base path and
    # return that path if it exists, else None.
    icon_path = os.path.join(icon_base_path, "icons", "mayaico.png")
    return icon_path if os.path.exists(icon_path) else None


def _synergy_config_files():
    """
    Scans the local file system using a list of search paths for
    Autodesk Synergy Config files (.syncfg).

    :returns: List of path names to Synergy Config files found
              in the local environment
    """
    # Check for custom paths defined by the SYNHUB_CONFIG_PATH env var.
    env_paths = os.environ.get("SYNHUB_CONFIG_PATH")
    search_paths = []
    if isinstance(env_paths, basestring):
        # This can be a list of directories and/or files.
        search_paths = env_paths.split(os.pathsep)

    # Check the platfom-specific default installation path
    # if no paths were set in the environment
    elif sys.platform == "darwin":
        search_paths = ["/Applications/Autodesk/Synergy/"]
    elif sys.platform == "win32":
        search_paths = ["C:\\ProgramData\\Autodesk\\Synergy\\"]
    elif sys.platform == "linux2":
        search_paths = ["/opt/Autodesk/Synergy/"]
    else:
        return search_paths

    synergy_configs = []
    for search_path in search_paths:
        if os.path.isdir(search_path):
            # Get the list of *.syncfg files in this directory
            synergy_configs.extend([
                os.path.join(search_path, f) for f in os.listdir(search_path)
                if f.startswith("Maya") and f.endswith(".syncfg")
            ])

        elif os.path.isfile(search_path):
            file_name = os.path.basename(search_path)
            if file_name.find("Maya") > -1 and file_name.endswith(".syncfg"):
                # Add the specified Synergy Config file directly to the list of paths.
                synergy_configs.append(search_path)

    return synergy_configs

def _synergy_software_versions(logger, versions=None, display_name=None, icon=None):
    """
    Creates SoftwareVersion instances based on the Synergy configuration
    data from Synergy Config (.syncfg) files found in the local environment.

    :param logger: Logger instance to use to log messages.
    :param versions: (optional) Specific list of version numbers (as strings) to
                     find matching executables for.
    :param display_name: (optional) Specify label to use for all
                         SoftwareVersions found.
    :param icon: (optional) Specify icon to use for all
                 SoftwareVersions found.

    :returns: List of :class:`SoftwareVersion` SoftwareVersion instance.
    """
    # Get the list of Maya*.syncfg files in the local environment
    configs = _synergy_config_files()
    if not configs:
        logger.debug(
            "Unable to determine Autodesk Synergy paths for platform "%
            sys.platform
        )
        return []

    logger.debug("Found Autodesk Synergy Maya config files : %s" % configs)
    # Determine the list of SoftwareVersion to return from the list
    # of configurations found and the list of versions requested.
    sw_versions = []
    for config in configs:
        try:
            # Parse the Synergy Config file as XML
            doc = XML_ET.parse(config)
        except Exception, e:
            raise TankError(
                "Caught exception attempting to parse [%s] as XML.\n%s" % (config, e)
            )

        try:
            # Find the <Application> element that contains the data
            # we want.
            app_elem = doc.getroot().find("Application")
            if app_elem is None:
                logger.warning(
                    "No <Application> found in Synergy config file '%s'." % config
                )
                continue

            # Convert the element's attribute/value pairs to a dictionary
            synergy_data = dict(app_elem.items())
        except Exception, e:
            raise TankError(
                "Caught unknown exception retrieving <Application> data from %s:\n%s" %
                (config, e)
            )

        if versions and synergy_data["NumericVersion"] not in versions:
            # If this version isn't in the list of requested versions, skip it.
            logger.debug("Skipping Maya Synergy version %s ..." % synergy_data["NumericVersion"])
            continue

        exec_path = synergy_data["ExecutablePath"]
        if sys.platform == "darwin" and "Maya.app" in exec_path:
            # There seems to be an anomoly with launching Maya from the
            # full executable path on MacOS. Everything behaves nicer if
            # Maya is launched from the bundle Maya.app directory instead.
            exec_path = "".join(exec_path.partition("Maya.app")[0:2])

        # Create a SoftwareVersion from input and config data.
        logger.debug("Creating SoftwareVersion for '%s'" % exec_path)
        sw_versions.append(SoftwareVersion(
            synergy_data["Name"],
            synergy_data["NumericVersion"],
            (display_name or synergy_data["StringVersion"]),
            exec_path,
            (icon or _icon_from_executable(exec_path))
        ))

    return sw_versions


def _default_path_software_versions(logger, versions=None, display_name=None, icon=None):
    """
    Creates SoftwareVersion instances based on the path values used
    in the default configuration paths.yml environment.

    :param logger: Logger instance to use to log messages.
    :param versions: (optional) Specific list of version numbers (as strings) to
                     find matching executables for.
    :param display_name: (optional) Specify label to use for all
                         SoftwareVersions found.
    :param icon: (optional) Specify icon to use for all
                 SoftwareVersions found.

    :returns: List of :class:`SoftwareVersion` SoftwareVersion instance.
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
    sw_version_regex = "%smaya[0-9]+[.0-9]*%s" % (os.path.sep, os.path.sep)
    if exec_paths:
        for exec_path in exec_paths:
            # Check to see if the version number can be parsed from the path name.
            sw_version_search = re.search(sw_version_regex, exec_path.lower())
            if sw_version_search is not None:
                # Use this sub dir to determine the default display name
                # and version for the SoftwareVersion to be created.
                default_display = sw_version_search.group(0)[1:-1]
                default_version = default_display.replace("maya", "")
                default_display = "Maya %s" % default_version
            else:
                try:
                    # This works, but makes the Desktop project window disappear
                    # for some reason, which isn't very nice. Therefore, use as a
                    # last resort.
                    version_output = subprocess.check_output([exec_path, "-v"])
                except OSError:
                    logger.exception(
                        "Could not retrieve version information from default "
                        "executable path '%s'." % exec_path
                    )
                    continue

                # Display and version information are contained before the first ','
                # in the output version string.
                default_display = version_output[0:version_output.find(",")]
                if "2016 Extension 2 SP1" in default_display:
                    # Update the display value to know "nicer" version numbers.
                    default_display = default_display.replace("2016 Extension 2 SP1", "2016.5")

                # Parse the default version from the display name determined from
                # the version output.
                default_version = default_display.lower().replace("maya", "").strip()

            if versions and default_version not in versions:
                # If this version isn't in the list of requested versions, skip it.
                logger.debug("Skipping Maya default version %s ..." % default_version)
                continue

            if sys.platform == "darwin" and "Maya.app" in exec_path:
                # There seems to be an anomoly with launching Maya from the
                # full executable path on MacOS. Everything behaves nicer if
                # Maya is launched from the bundle Maya.app directory instead.
                exec_path = "".join(exec_path.partition("Maya.app")[0:2])

            # Create a SoftwareVersion using the information from executable path(s) found
            # in default locations.
            logger.debug("Creating SoftwareVersion for executable '%s'." % exec_path)
            sw_versions.append(SoftwareVersion(
                default_display.replace(" ", "_"),
                default_version,
                (display_name or default_display),
                exec_path,
                (icon or _icon_from_executable(exec_path))
            ))

    return sw_versions
