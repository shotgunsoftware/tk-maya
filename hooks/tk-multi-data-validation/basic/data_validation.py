# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

import sgtk

import maya.cmds as cmds

HookBaseClass = sgtk.get_hook_baseclass()


class MayaDataValidationHook(HookBaseClass):
    """
    Hook to define Alias scene validation functionality.
    """

    def get_validation_data(self):
        """
        Return the validation rule data set to validate an Alias scene.
        This method will retrieve the default validation rules returned by
        :meth:`AliasSceneDataValidator.get_validation_data`. To customize the default
        validation rules, override this hook method to modify the returned data dictionary.
        The dictionary returned by this function should be formated such that it can be passed
        to the :class:`~tk-multi-data-validation:api.data.ValidationRule` class constructor to
        create a new validation rule object.
        :return: The validation rules data set.
        :rtype: dict
        """

        return {
            "unknown_nodes": {
                "name": "Delete Unknown Nodes",
                "description": """Check: Unknown nodes<br/>
                                Fix: Delete""",
                "error_msg": "Found unknown nodes",
                "check_func": self.check_unknown_nodes,
                "fix_func": self.fix_unknown_nodes,
                "fix_name": "Delete All",
                "fix_tooltip": "Delete Unknown Nodes.",
                "actions": [
                    {"name": "Select All", "callback": self.select_items},
                ],
                "item_actions": [
                    {
                        "name": "Select",
                        "callback": lambda item: cmds.select(item, r=True),
                    },
                ],
            },
            "sg_references": {
                "name": "ShotGrid Published Files References only",
                "description": """Check: References which aren't SG Published Files<br/>
                                Fix: Select references""",
                "error_msg": "Found references which doesn't match a SG Published File",
                "check_func": self.check_sg_references,
                "fix_func": self.select_items,
                "fix_name": "Select All",
                "fix_tooltip": "Select references which are not SG Published Files",
                "item_actions": [
                    {
                        "name": "Select",
                        "callback": lambda item: cmds.select(item, r=True),
                    },
                ],
            },
        }

    # ---------------------------------------------------------------------------
    # Check methods
    # ---------------------------------------------------------------------------

    def check_unknown_nodes(self):
        """ """

        unknown_nodes = cmds.ls(type="unknown")
        return _get_check_result(unknown_nodes)

    def check_sg_references(self):
        """ """

        bad_references = []

        # get the path to the references without the copy number and remove the duplicate paths
        ref_paths = list(
            dict.fromkeys(cmds.file(q=True, reference=True, withoutCopyNumber=True))
        )
        sg_publishes = sgtk.util.find_publish(
            self.sgtk, ref_paths, only_current_project=False
        )

        for ref in cmds.file(q=True, reference=True):
            node_name = cmds.referenceQuery(ref, referenceNode=True)
            ref_path = cmds.referenceQuery(ref, filename=True, withoutCopyNumber=True)
            if ref_path not in sg_publishes:
                bad_references.append(node_name)

        return _get_check_result(bad_references)

    # ---------------------------------------------------------------------------
    # Fix methods
    # ---------------------------------------------------------------------------

    def fix_unknown_nodes(self, errors=None):
        """ """
        for item in errors:
            cmds.delete(item["id"])

    # ---------------------------------------------------------------------------
    # Action methods
    # ---------------------------------------------------------------------------

    def select_items(self, errors=None):
        """ """
        cmds.select(cl=True)
        for item in errors:
            if isinstance(item, dict):
                cmds.select(item["id"], add=True)
            else:
                cmds.select(item, add=True)

    def select_references(self, errors=None):
        """ """
        pass


def _get_check_result(error_items):
    """ """

    return {"is_valid": not error_items, "errors": _format_maya_objects(error_items)}


def _format_maya_objects(objects):
    """ """

    formatted_objects = []

    for obj in objects:
        formatted_objects.append({"id": obj, "name": obj, "type": cmds.objectType(obj)})

    return formatted_objects
