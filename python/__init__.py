# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

# flake8: noqa

from tank import LogManager

logger = LogManager.get_logger(__name__)

from . import tk_maya


try:
    from . import flowam
except ImportError as exc:
    logger.error(
        "tk-maya: There was an error importing the 'flowam' module.\n"
        "This is likely due to Flow AM features being unavailable in the "
        "current version of tk-core - i.e. it is missing the Flow Integration SDK "
        "('tank_vendor.flow_integration_sdk' / 'tank.flowam').\n"
        "This is safe to ignore if you are not working on a Flow AM project. "
        f"Upgrade tk-core to enable Flow AM publishing.\n(ImportError: {exc})"
    )
