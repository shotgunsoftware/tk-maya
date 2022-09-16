# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

import os

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
    RENDERER = {"short_name": "arnold", "name": "Arnold Renderer", "plugin": "mtoa.mll"}

    def sanitize_check_result(self, errors):
        """ """

        formatted_errors = []

        for err in errors:
            formatted_errors.append({"id": err, "name": err})

        return {"is_valid": not errors, "errors": formatted_errors}

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

        check_list = {
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
            "material_unused": {
                "name": "Delete Unused Materials",
                "description": """Check: Unused materials<br/>
                                Fix: Delete (default materials are not affected)""",
                "error_msg": "Found unused materials",
                "check_func": self.check_unused_materials,
                "fix_func": self.delete_items,
                "fix_name": "Delete All",
                "fix_tooltip": "Delete Unused Materials",
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
                                Fix: Create root top-node""",
                "error_msg": "Found more than one top-node",
                "check_func": self.check_only_one_top_node,
                "fix_func": self.create_root_node,
                "fix_name": "Create Root",
                "fix_tooltip": "Create root top-node",
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
            "top_node_pivot_position": {
                "name": "Top-node pivot position",
                "description": """Check: Top-node pivot position should be world-centered<br/>
                                Fix: Set top-node pivot position to 0,0,0""",
                "error_msg": "Top-node pivot position is not world-centered",
                "check_func": self.check_top_node_pivot_position,
                "fix_func": self.reset_top_node_pivot_position,
                "fix_name": "Reset",
                "fix_tooltip": "Reset top-node pivot position to 0,0,0",
                "dependency_ids": ["one_top_node"],
            },
            "sync_frame_range": {
                "name": "Frame Range Synchronization",
                "description": """Check: Timeline values should be synced with the values defined in ShotGrid""",
                "error_msg": "Frame Range not synced with ShotGrid",
                "check_func": self.check_frame_range,
                "fix_func": self.synch_frame_range,
                "fix_name": "Synchronize",
                "fix_tooltip": "Synchronize timeline with ShotGrid data",
            },
        }

        # ----------------------------------------------------------------
        # Modelling specific checks
        # ----------------------------------------------------------------

        if self.parent.context.step and self.parent.context.step["name"] == "Model":

            check_list.update(
                {
                    "top_node_freeze_transforms": {
                        "name": "Top-node freeze transforms",
                        "description": """Check: Top-node position should be frozen<br/>
                                        Fix: Freeze top-node position""",
                        "error_msg": "Top-node position is not frozen",
                        "check_func": self.check_top_node_freeze_tranforms,
                        "fix_func": self.freeze_transforms,
                        "fix_name": "Freeze All",
                        "fix_tooltip": "Freeze top-node position",
                        "dependency_ids": ["one_top_node"],
                    },
                    "group_node_freeze_transforms": {
                        "name": "Group nodes freeze transforms",
                        "description": """Check: Group nodes positions should be frozen<br/>
                                        Fix: Freeze group nodes positions""",
                        "error_msg": "Group nodes positions are not frozen",
                        "check_func": self.check_group_node_freeze_tranforms,
                        "fix_func": self.freeze_transforms,
                        "fix_name": "Freeze All",
                        "fix_tooltip": "Freeze group nodes positions",
                    },
                    "mesh_freeze_transforms": {
                        "name": "Meshes freeze transforms",
                        "description": """Check: Meshes positions should be frozen<br/>
                                        Fix: Freeze meshes positions""",
                        "error_msg": "Meshes positions are not frozen",
                        "check_func": self.check_mesh_freeze_tranforms,
                        "fix_func": self.freeze_transforms,
                        "fix_name": "Freeze All",
                        "fix_tooltip": "Freeze meshes positions",
                    },
                    "no_references": {
                        "name": "No References",
                        "description": """Check: No references should be used""",
                        "error_msg": "References found",
                        "check_func": self.check_references,
                        "actions": [
                            {"name": "Select All", "callback": self.select_items},
                        ],
                    },
                    "mesh_history": {
                        "name": "Mesh History",
                        "description": """Check: Meshes have history<br/>
                                        Fix: Delete mesh history""",
                        "error_msg": "Meshes have history",
                        "check_func": self.check_mesh_history,
                        "fix_func": self.delete_history,
                        "fix_name": "Delete History",
                        "fix_tooltip": "Delete mesh history",
                        "dependency_ids": ["no_references"],
                    },
                    "mesh_visibility": {
                        "name": "Mesh Visibility",
                        "description": """Check: Meshes should all be visible""",
                        "error_msg": "Some meshes are not visible",
                        "check_func": self.check_mesh_visibility,
                    },
                    "default_materials_only": {
                        "name": "Default materials only",
                        "description": """Check: Only default materials should be used""",
                        "error_msg": "Found non-default materials",
                        "check_func": self.check_default_materials,
                    },
                }
            )

        elif self.parent.context.step and self.parent.context.step["name"] in [
            "Light",
            "Texture",
        ]:

            check_list.update(
                {
                    "custom_materials_only": {
                        "name": "Custom materials only",
                        "description": """Check: Only custom materials should be used""",
                        "error_msg": "Found non-custom materials",
                        "check_func": self.check_custom_materials,
                    },
                    "render_engine": {
                        "name": "Render Engine",
                        "description": """Check: Make sure the right render engine is selected""",
                        "error_msg": "Render engine not selected",
                        "check_func": self.check_render_engine,
                        "fix_func": self.set_renderer,
                        "fix_name": "Set Renderer",
                        "fix_tooltip": "Set Renderer",
                    },
                }
            )

        return check_list

    # ---------------------------------------------------------------------------
    # Check methods
    # ---------------------------------------------------------------------------

    def check_unknown_nodes(self):
        """
        Check if there are unknown nodes in the current Maya session.
        """

        unknown_nodes = cmds.ls(type="unknown")
        return unknown_nodes

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

        return bad_references

    def check_unused_materials(self):
        """
        Check that all the materials are in used.
        """

        unassigned_materials = []

        materials = cmds.ls(mat=True)
        for m in materials:
            if m in self.DEFAULT_MATERIALS:
                continue

            # get the shading engine(s) the material belongs to
            # if the shading engine doesn't have an empty set, this means that the material is assigned to something
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

        return unassigned_materials

    def check_only_one_top_node(self):
        """
        Check that there is only one top node in the scene hierarchy.
        """

        top_nodes = [
            n for n in cmds.ls(assemblies=True) if n not in self.DEFAULT_CAMERAS
        ]
        top_nodes = [] if len(top_nodes) == 1 else top_nodes

        return top_nodes

    def check_top_node_pivot_position(self):
        """ """

        # as this check depends on check_only_one_top_node(), we can assume that we have only one top node here
        top_nodes = [
            n for n in cmds.ls(assemblies=True) if n not in self.DEFAULT_CAMERAS
        ]

        is_valid = True
        pivot_positions = cmds.xform(top_nodes[0], q=True, piv=True)
        for p in pivot_positions:
            if p != 0:
                is_valid = False
                break

        return [] if is_valid else top_nodes

    def check_top_node_freeze_tranforms(self):
        """ """

        # as this check depends on check_only_one_top_node(), we can assume that we have only one top node here
        top_nodes = [
            n for n in cmds.ls(assemblies=True) if n not in self.DEFAULT_CAMERAS
        ]

        return self.check_freeze_transforms(top_nodes)

    def check_group_node_freeze_tranforms(self):
        """ """
        group_nodes = []

        # get all the group nodes
        transform_nodes = cmds.ls(exactType="transform")
        for n in transform_nodes:
            self.logger.info(n)
            if not self.is_group_node(n):
                continue
            group_nodes.append(n)

        return self.check_freeze_transforms(group_nodes)

    def check_mesh_freeze_tranforms(self):
        """ """

        # get all the meshes
        all_shapes = cmds.ls(exactType="mesh", dag=1, ni=1, l=True)
        all_meshes = [
            cmds.ls(cmds.listRelatives(s, fullPath=True, p=True), long=True)
            for s in all_shapes
        ]

        return self.check_freeze_transforms(all_meshes)

    def check_mesh_history(self):
        """ """

        bad_meshes = []

        for shape in cmds.ls(exactType="mesh", dag=1, ni=1, sn=True):
            for mesh in cmds.ls(
                cmds.listRelatives(shape, fullPath=True, p=True), sn=True
            ):
                mesh_history = cmds.listHistory(mesh, lv=0)
                # remove the shape name from the list
                if shape in mesh_history:
                    mesh_history.remove(shape)
                if mesh_history:
                    bad_meshes.append(mesh)

        return bad_meshes

    def check_mesh_visibility(self):
        """ """

        bad_meshes = []

        # get all the meshes
        for shape in cmds.ls(exactType="mesh", dag=1, ni=1, l=True):
            for mesh in cmds.ls(cmds.listRelatives(shape, fullPath=True, p=True)):
                if not cmds.getAttr("{}.visibility".format(mesh)):
                    bad_meshes.append(mesh)

        return bad_meshes

    def check_references(self):
        """ """
        return cmds.ls(references=True)

    def check_default_materials(self):
        """ """

        custom_materials = []

        materials = cmds.ls(mat=True)
        for m in materials:
            if m not in self.DEFAULT_MATERIALS:
                custom_materials.append(m)

        return custom_materials

    def check_custom_materials(self):
        """ """

        bad_shapes = []

        for shape in cmds.ls(exactType="mesh", dag=1, ni=1):
            for shading_engine in cmds.listConnections(shape, t="shadingEngine"):
                for con in cmds.listConnections(shading_engine):
                    if con in self.DEFAULT_MATERIALS:
                        bad_shapes.append(shape)

        return bad_shapes

    def check_frame_range(self):
        """ """

        self.logger.info(self.parent.engine.apps)
        tk_multi_setframerange = self.parent.engine.apps.get("tk-multi-setframerange")
        if not tk_multi_setframerange:
            self.logger.error("Can't find tk-multi-setframerange Toolkit app")
            return []

        (sg_in, sg_out) = tk_multi_setframerange.get_frame_range_from_shotgun()
        (current_in, current_out) = tk_multi_setframerange.get_current_frame_range()

        if sg_in != current_in or sg_out != current_out:
            return [os.path.basename(cmds.file(q=True, sn=True))]

        return []

    def check_render_engine(self):
        """ """

        current_renderer = cmds.getAttr("defaultRenderGlobals.currentRenderer")
        return [] if current_renderer == self.RENDERER["name"] else [current_renderer]

    # ---------------------------------------------------------------------------
    # Fix and actions methods
    # ---------------------------------------------------------------------------

    def create_root_node(self, errors):
        """
        Create a root top node and group all the previous top nodes under it.
        """
        top_nodes = [item["id"] for item in errors]
        cmds.group(top_nodes, name=self.ROOT_NODE_NAME)

    def reset_top_node_pivot_position(self, errors):
        """ """
        top_node = errors[0]
        cmds.xform(top_node["id"], piv=(0, 0, 0))

    def freeze_transforms(self, errors):
        """ """
        for item in errors:
            cmds.makeIdentity(item["id"], apply=True)

    def delete_items(self, errors):
        """
        Delete a list of items.
        """
        for item in errors:
            cmds.delete(item["id"])

    def select_items(self, errors):
        """
        Select a list of items.
        """
        # clear the previous selection before selecting the items
        cmds.select(cl=True)
        for item in errors:
            cmds.select(item["id"], add=True)

    def delete_history(self, errors):
        """ """
        for item in errors:
            cmds.delete(item["id"], constructionHistory=True)

    def synch_frame_range(self, errors):
        """ """

        tk_multi_setframerange = self.parent.engine.apps.get("tk-multi-setframerange")
        (sg_in, sg_out) = tk_multi_setframerange.get_frame_range_from_shotgun()
        tk_multi_setframerange.set_frame_range(sg_in, sg_out)

    def set_renderer(self, errors):
        """ """

        # make sure the plugin is loaded
        if self.RENDERER["plugin"] and not cmds.pluginInfo(
            self.RENDERER["plugin"], query=True, loaded=True
        ):
            cmds.loadPlugin(self.RENDERER["plugin"])

        if not self.RENDERER["short_name"] in cmds.renderer(
            query=True, namesOfAvailableRenderers=True
        ):
            return

        cmds.setAttr("defaultRenderGlobals.currentRenderer", l=False)
        cmds.setAttr(
            "defaultRenderGlobals.currentRenderer", self.RENDERER["name"], type="string"
        )

    # ---------------------------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------------------------

    def check_freeze_transforms(self, items):
        """ """

        error_items = []

        for i in items:

            is_valid = True

            # check translation
            translation_positions = cmds.xform(i, q=True, t=True)
            for p in translation_positions:
                if p != 0:
                    is_valid = False
                    error_items.append(i)
                    break

            # check rotation
            if is_valid:
                rotation_positions = cmds.xform(i, q=True, ro=True)
                for p in rotation_positions:
                    if p != 0:
                        is_valid = False
                        error_items.append(i)
                        break

            # check scale
            if is_valid:
                scale_positions = cmds.xform(i, q=True, s=True)
                for p in scale_positions:
                    if p != 1:
                        error_items.append(i)
                        break

        return error_items

    def is_group_node(self, node):
        """ """

        children = cmds.listRelatives(node, children=True)
        if not children:
            return False

        for c in children:
            if not cmds.ls(c, transforms=True):
                return False
        return True
