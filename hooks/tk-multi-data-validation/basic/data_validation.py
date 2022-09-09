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

    DEFAULT_MATERIALS = ["lambert1", "standardSurface1", "particleCloud1"]
    DEFAULT_CAMERAS = ["persp", "top", "front", "side"]
    ROOT_NODE_NAME = "ROOT"

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
                "fix_func": self.delete_items,
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
                    {
                        "name": "Delete",
                        "callback": lambda item: cmds.delete(item),
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
                    {
                        "name": "Delete",
                        "callback": lambda item: cmds.delete(item),
                    },
                ],
            },
            "shader_unused": {
                "name": "Delete Unused Shaders",
                "description": """Check: Unused shaders<br/>
                                Fix: Delete (default shaders are not affected)""",
                "error_msg": "Found unused shaders",
                "check_func": self.check_unused_shaders,
                "fix_func": self.delete_items,
                "fix_name": "Delete All",
                "fix_tooltip": "Delete Unused Shaders",
                "item_actions": [
                    {
                        "name": "Select",
                        "callback": lambda item: cmds.select(item, r=True),
                    },
                    {
                        "name": "Delete",
                        "callback": lambda item: cmds.delete(item),
                    },
                ],
            },
            "one_top_node": {
                "name": "One top-node only",
                "description": """Check: Only one top-node<br/>
                                Fix: Select top-nodes""",
                "error_msg": "Found more than one top-node",
                "check_func": self.check_only_one_top_node,
                "fix_func": self.create_root_node,
                "fix_name": "Create",
                "fix_tooltip": "Select top-nodes",
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
        }

    # ---------------------------------------------------------------------------
    # Check methods
    # ---------------------------------------------------------------------------

    def check_unknown_nodes(self):
        """
        Check if there are unknown nodes in the current Maya session.
        """

        unknown_nodes = cmds.ls(type="unknown")
        return _get_check_result(unknown_nodes)

    def check_sg_references(self):
        """
        Check that all the references correspond to a ShotGrid Published File.
        """

        bad_references = []

        # get the path to the references without the copy number and remove the duplicate paths
        ref_paths = list(
            dict.fromkeys(cmds.file(q=True, reference=True, withoutCopyNumber=True))
        )

        # find the matching published files in ShotGrid
        sg_publishes = sgtk.util.find_publish(
            self.sgtk, ref_paths, only_current_project=False
        )

        # list all the references which doesn't have a corresponding Published File
        for ref in cmds.file(q=True, reference=True):
            node_name = cmds.referenceQuery(ref, referenceNode=True)
            ref_path = cmds.referenceQuery(ref, filename=True, withoutCopyNumber=True)
            if ref_path not in sg_publishes:
                bad_references.append(node_name)

        return _get_check_result(bad_references)

    def check_only_one_top_node(self):
        """
        Check that there is only one top node in the scene hierarchy.
        """

        top_nodes = [
            n for n in cmds.ls(assemblies=True) if n not in self.DEFAULT_CAMERAS
        ]
        top_nodes = [] if len(top_nodes) == 1 else top_nodes

        return _get_check_result(top_nodes)

    def check_unused_shaders(self):
        """
        Check that all the materials are in used.
        """

        unassigned_materials = []

        materials = cmds.ls(mat=True)
        for m in materials:
            if m in self.DEFAULT_MATERIALS:
                continue

            # get the shading engine(s) the material belongs to
            # if the shading engine doesn't have an empty set, this means that the shader is assigned to something
            shading_engines = cmds.listConnections(
                m, d=True, et=True, t="shadingEngine"
            )
            if not shading_engines:
                continue
            is_assigned = False
            for se in shading_engines:
                if cmds.sets(se, q=True):
                    is_assigned = True
                    break
            if not is_assigned:
                unassigned_materials.append(m)

        return _get_check_result(unassigned_materials)

    # ---------------------------------------------------------------------------
    # Fix and actions methods
    # ---------------------------------------------------------------------------

    def create_root_node(self, errors):
        """
        Create a root top node and group all the previous top nodes under it.
        """
        top_nodes = [item["id"] for item in errors]
        cmds.group(top_nodes, name=self.ROOT_NODE_NAME)

    def delete_items(self, errors):
        """
        Delete a list of items.
        """
        for item in errors:
            cmds.delete(item["id"])

    def select_items(self, errors=None):
        """
        Select a list of items.
        """
        # clear the previous selection before selecting the items
        cmds.select(cl=True)
        for item in errors:
            if isinstance(item, dict):
                cmds.select(item["id"], add=True)
            else:
                cmds.select(item, add=True)


def _get_check_result(error_items):
    """ """

    return {"is_valid": not error_items, "errors": _format_maya_objects(error_items)}


def _format_maya_objects(objects):
    """ """

    formatted_objects = []

    for obj in objects:
        formatted_objects.append({"id": obj, "name": obj, "type": cmds.objectType(obj)})

    return formatted_objects
