# -
# *****************************************************************************
# Copyright 2026 Autodesk, Inc. All rights reserved.
#
# These coded instructions, statements, and computer programs contain
# unpublished proprietary information written by Autodesk, Inc. and are
# protected by Federal copyright law. They may not be disclosed to third
# parties or copied or duplicated in any form, in whole or in part, without
# the prior written consent of Autodesk, Inc.
# *****************************************************************************
#

import os

from tank import LogManager
from tank.flowam.host import FlowHost
from tank_vendor.flow_integration_sdk.dependency import DependencyData
from tank_vendor.flow_integration_sdk.utils import (
    cleanpath,
    fileext,
    trace,
)

from maya import cmds, mel, OpenMaya


class MayaHost(FlowHost):
    """Maya implementation of FlowHost interface.
    This is a collection of required capabilities to support Flow AM integration.
    """

    logger = LogManager.get_logger("MayaHost")

    #: The schema name associated with Maya workfiles
    WORKFILE_TYPE = "type.workfile.maya"
    #: Maya file extensions
    FILE_TYPES = ["ma", "mb"]
    #: Export file types
    EXPORT_TYPES = ["abc"]
    #: Maya save types
    SAVE_TYPES = {
        "ma": "mayaAscii",
        "mb": "mayaBinary",
    }
    #: Maya file mime types
    MIME_TYPES = {
        "ma": "application/vnd.maya.ma",
        "mb": "application/vnd.maya.mb",
    }

    # ------------------------------------------
    # BASE CLASS INTERFACE
    # ------------------------------------------

    def __init__(self, context):

        self.logger.info("Doing MayaHost initialization...")

        super().__init__(context)

        # Add callbacks for relevant Maya events
        OpenMaya.MSceneMessage.addCallback(
            OpenMaya.MSceneMessage.kAfterNew, self._on_new_scene
        )
        OpenMaya.MSceneMessage.addCallback(
            OpenMaya.MSceneMessage.kAfterOpen, self._on_open_scene
        )

    @trace
    def current_file(self) -> str:
        """Return current open file path in dcc."""
        return cleanpath(cmds.file(query=True, sceneName=True))

    @trace
    def new_scene(self, force: bool = False) -> bool:
        """Start new scene in Maya.

        Args:
            force: If true, force action even if there are unsaved changes.

        Returns:
            True if new scene is opened, False if operation is cancelled.
        """
        if not force:
            if not self._check_unsaved_changes():
                # Operation cancelled by user
                return False
        # Force new scene
        OpenMaya.MFileIO.newFile(True)
        return True

    @trace
    def open_file(self, file_path: str) -> bool:
        """Open given file path in Maya.

        Args:
            file_path: Full path to Maya scene file to be opened.

        Returns:
            True if file is opened, False on error or if operation is cancelled.
        """
        if not self._check_unsaved_changes():
            # Operation cancelled by user
            return False
        cmds.file(file_path, open=True, force=True)
        return True

    @trace
    def save_file(self, file_path: str):
        """Save the current scene to the specified file path.

        Args:
            file_path: Absolute local path to save file.

        Raises:
            ValueError
        """
        ext = fileext(file_path)
        if ext not in self.FILE_TYPES:
            raise ValueError(f'Invalid native file extension "{ext}" provided.')

        OpenMaya.MFileIO.saveAs(file_path, self.SAVE_TYPES[ext])

    @trace
    def export(self, file_path: str) -> None:
        """Export current scene to file path specified and file type
        designated by file extension.

        Args:
            file_path: Absolute local path to export file.

        Raises:
            ValueError
        """
        ext = fileext(file_path)
        if ext not in self.EXPORT_TYPES:
            raise ValueError(f'Export type "{ext}" is not supported.')

        if ext == "abc":
            self._export_alembic(file_path)

    @trace
    def dialog(
        self,
        title: str,
        msg: str,
        buttons: list[str] | None = None,
        default: int = 0,
        cancel: int | None = None,
        no_ui_option: int | None = None,
    ) -> int:
        """Pop up a dialog in the dcc.

        Args:
            title: Title of dialog window.
            msg: Message to be displayed.
            buttons: List of strings denoting buttons to be added to dialog.
            default: Index of default button.
            cancel: Index of cancel button. If not specified, and multiple choices are
                    available, user will not be able to press escape or close to exit the dialog.
            no_ui_option: If Maya is running without UI, this option will automatically be returned.
                          If None, use default value.

        Returns:
            The index of the button selected by user. Value of -1 indicates dismissed dialog.
        """
        maya_state = OpenMaya.MGlobal.mayaState()
        if maya_state in [OpenMaya.MGlobal.kBatch, OpenMaya.MGlobal.kLibraryApp]:
            # Maya is running without UI, return default behaviour
            return no_ui_option if no_ui_option is not None else default

        buttons = buttons or ["OK"]
        kwargs = {
            "title": title,
            "message": msg,
            "button": buttons,
        }
        if default < len(buttons):
            kwargs["defaultButton"] = buttons[default]
        if cancel is not None and cancel < len(buttons):
            kwargs["cancelButton"] = buttons[cancel]
        result = cmds.confirmDialog(**kwargs)
        if result == "dismiss":
            return -1
        if not buttons:
            return 0
        return buttons.index(result)

    @trace
    def file_dialog(
        self,
        title: str,
        starting_dir: str = "",
        folder_mode: bool = False,
        file_type: str = "",
        multi_select: bool = False,
    ) -> list[str]:
        """Invoke a file dialog for selecting one or more file paths.

        Args:
            title: Title of dialog.
            starting_dir: Starting location of dialog.
            folder_mode: If True, dialog will browse folders instead of files.
            file_filter: Extension of file type to filter for.
                         Applicable only when browsing files.
            multi_select: If True, allow multiple selection of files.
                          Applicable only when browsing files.

        Returns:
            A list of file/directory paths.
            If multi_select = False, the return value will be a list of size 1.
            If user cancels or dialog couldn't be shown, list will be empty.
            If Maya is running without a GUI, empty list is returned.
        """
        maya_state = OpenMaya.MGlobal.mayaState()
        if maya_state in [OpenMaya.MGlobal.kBatch, OpenMaya.MGlobal.kLibraryApp]:
            # Maya is running without UI
            return []

        if folder_mode:
            file_mode = 3  # single existing directory
        elif multi_select:
            file_mode = 4  # one or more existing files
        else:
            file_mode = 1  # single existing file

        file_filter = f"*.{file_type.strip('.')}"
        result = cmds.fileDialog2(
            caption=title,
            okCaption="Select",
            startingDirectory=starting_dir,
            fileMode=file_mode,
            fileFilter=file_filter,
        )
        return result or []

    @trace
    def copy_to_clipboard(self, text: str) -> bool:
        """Copy given text to clipboard.

        Args:
            text: Text to be copied.

        Returns:
            True on success.
        """
        from tank.platform.qt import QtGui as qtg

        qtg.QApplication.instance().clipboard().setText(text)
        return True

    @trace
    def get_dependency_tree(self, must_exist: bool = True) -> DependencyData:
        """Return a DependencyData object which is the root of the
        dependency tree for the scene.

        Args:
            must_exist: Only return dependencies that can be found on disk.
        """
        dependencies = self._get_maya_dependencies(must_exist=must_exist)
        dependencies.sort()
        root = DependencyData(dependencies=dependencies)
        for d in dependencies:
            d.parent = root
        return root

    @trace
    def update_dependency(
        self,
        dep: DependencyData,
        file_path: str,
    ) -> DependencyData:
        """Update an existing dependency to point to given file in current scene.

        Args:
            dep: DependencyData node which identifies the dependency to be updated.
            file_path: New path to set dependency to.

        Returns:
            DependencyData object describing new state of dependency.
            NOTE: This will be an isolated node, not including sub-dependency info.

        Raises:
            RuntimeError
            ValueError
        """

        node_handle = dep.node_handle
        attribute = dep.attribute

        if not cmds.ls([node_handle]):
            msg = "Error updating dependency. "
            msg += f"Invalid node handle provided: {node_handle}."
            raise RuntimeError(msg)

        if attribute:
            # Change an attribute on a Maya node to point to new path
            self._update_attribute_dep(node_handle, attribute, file_path)

        else:
            # Change Maya reference node
            self._update_reference_dep(node_handle, attribute, file_path)

        updated_dep = DependencyData(
            dep_type=dep.dep_type,
            node_handle=dep.node_handle,
            node_type=dep.node_type,
            attribute=dep.attribute,
            file_path=self._resolve_path(file_path),
            raw_path=file_path,
        )

        self.logger.info(
            f'Dependency node "{node_handle}" updated to point to file "{file_path}".'
        )
        return updated_dep

    # ------------------------------------------
    # ADDITIONAL SUBCLASS FUNCTIONS
    # ------------------------------------------

    @trace
    def create_reference(self, file_path: str, namespace: str) -> DependencyData:
        """Create a native maya reference.

        Args:
            file_path: Path to be referenced into Maya.
            namespace: Namespace to be added to reference node.

        Returns:
            DependencyData object with all pertinent info about asset reference created.

        Raises:
            ValueError
        """
        # Check file type
        ext = fileext(file_path)
        if ext not in self.FILE_TYPES:
            msg = f'File type "{ext}" not supported for referencing in Maya.'
            raise ValueError(msg)

        # Create the reference in maya
        res = cmds.file(file_path, reference=True, namespace=namespace)
        node_name = cmds.referenceQuery(res, referenceNode=True, topReference=True)

        msg = f'Reference node "{node_name}" created pointing to file "{file_path}".'
        self.logger.info(msg)

        return DependencyData(
            node_handle=node_name,
            node_type="reference",
            file_path=self._resolve_path(file_path),
            raw_path=file_path,
        )

    def _resolve_path(self, path: str):
        """Given a maya dependency file path, resolve against current maya project."""
        if cmds.file(path, q=True, exists=True):
            path = cmds.file(path, q=True, loc=True)
        return cleanpath(cmds.workspace(expandName=path))

    def _get_maya_dependencies(
        self,
        filter_nodes: set[str] | None = None,
        ignore_nodes: set[str] | None = None,
        must_exist: bool = True,
    ) -> list[DependencyData]:
        """Returns all references to external files in the current scene.
        Examples include textures, geometry caches and other maya scene files.

        Args:
            filter_nodes: Optionally provide a list of filter nodes.
                          Return the subset of these nodes that are dependencies.
            ignore_nodes: Optionally provide a list of nodes to ignore.
            must_exist: Only return dependencies that can be found on disk.

        Returns:
            List of DependencyData objects containing all pertinent information
            related to a file dependency.
        """
        # Get list of external files and references (querying the attributes,
        # which is "node.attribute", or just "node" for references)
        cmds.filePathEditor(refresh=True)  # force refresh of file path editor
        node_attributes = cmds.filePathEditor(
            query=True, listFiles="", attributeOnly=True
        )

        if not node_attributes:
            return []

        # Get list of AM references (so we can skip them and their nodes)
        if ignore_nodes is None:
            ignore_nodes = set()

        deps: list[DependencyData] = []
        # Bit of a hack, but we want to ensure we visit parent reference nodes
        # before visiting sub references. Leverage sorting to achieve this.
        # NOTE: "namespaceRN" will always be alphabetically after "namespace:..."
        node_attributes.sort()
        node_attributes.reverse()
        for node_attr in node_attributes:
            node_type = cmds.filePathEditor(node_attr, query=True, attributeType=True)
            if node_type == "mayaUsdProxyShape.filePath":
                # This case is handled by get_usd_dependencies()
                continue
            if node_attr in ignore_nodes:
                continue
            if filter_nodes and node_attr.split(".")[0] not in filter_nodes:
                continue
            self._get_dependency_info(node_attr, deps, ignore_nodes, must_exist)

        return deps

    def _get_dependency_info(
        self,
        node_attr: str,
        deps: list[DependencyData],
        ignore_nodes: set[str],
        must_exist,
        node_type: str | None = None,
    ):
        """Add dependency associated with node attribute to list."""

        if node_type is None:
            node_type = cmds.filePathEditor(node_attr, query=True, attributeType=True)
        sub_deps: list[DependencyData] = []  # sub dependencies

        if node_type == "reference":
            # For references the node_attr will be just the reference node (without attribute)
            node, attr = node_attr, ""
            file_path = cmds.referenceQuery(node, filename=True, withoutCopyNumber=True)
            raw_path = cmds.referenceQuery(
                node, filename=True, unresolvedName=True, withoutCopyNumber=True
            )
            ref_nodes = cmds.referenceQuery(node, nodes=True)
            if ref_nodes:
                sub_deps = self._get_maya_dependencies(
                    ref_nodes, ignore_nodes, must_exist
                )
                sub_deps.sort()
                ignore_nodes.update(ref_nodes)
        else:
            # Here the node_attr will be of the format node.attribute
            node, attr = node_attr.split(".", 1)
            # Sometimes file path will be empty, so we need to check for that
            file_path = cmds.getAttr(node_attr, expandEnvironmentVariables=True)
            raw_path = cmds.getAttr(node_attr)
            ignore_nodes.add(node_attr)
            if not file_path:
                return
            file_path = cleanpath(file_path)

        # Get absolute path
        resolved_file_path = self._resolve_path(file_path)

        if must_exist and not os.path.isfile(resolved_file_path):
            self.logger.warning(f"Could not find dependency file: {resolved_file_path}")
            return

        cur_dep = DependencyData(
            node_handle=node,
            node_type=node_type,
            attribute=attr,
            file_path=resolved_file_path,
            raw_path=raw_path,
            dependencies=sub_deps,
        )
        cur_dep.identify_component()
        cur_dep.set_type()

        for d in sub_deps:
            d.parent = cur_dep

        deps.append(cur_dep)

    def _update_attribute_dep(self, node_handle: str, attribute: str, file_path: str):
        """Update attribute type dependency to new file. (e.g. texture path)"""

        # Check attribute exists
        attribute_handle = f"{node_handle}.{attribute}"
        if not cmds.attributeQuery(attribute, node=node_handle, exists=True):
            msg = "Error updating attribute dependency. "
            msg += f'Invalid attribute provided "{attribute_handle}".'
            raise RuntimeError(msg)

        # Check if new path is different
        orig_path = cleanpath(cmds.getAttr(attribute_handle))
        if file_path == orig_path:
            return

        # Update maya attribute
        cmds.setAttr(f"{node_handle}.{attribute}", file_path, type="string")

    def _update_reference_dep(self, node_handle: str, attribute: str, file_path: str):
        """Update Maya reference to new file."""

        # Check that file type is valid
        file_ext = fileext(file_path)
        if file_ext not in self.FILE_TYPES:
            msg = "Error updating reference dependency. "
            msg += f"Invalid file type provided: {file_ext}."
            raise ValueError(msg)

        # Check if new path is different
        orig_path = cmds.referenceQuery(
            node_handle, filename=True, withoutCopyNumber=True
        )
        if file_path == cleanpath(orig_path):
            return

        # Remember load state so we can preserve it because
        # changing a reference path always loads it
        loaded = cmds.referenceQuery(node_handle, isLoaded=True)
        # Update and load the reference
        cmds.file(file_path, loadReference=node_handle)
        if not loaded:
            cmds.file(unloadReference=node_handle)

        # NOTE: ignoring namespace changes for now. Assuming that
        #       dependency updates apply only to different versions of same asset.

    @trace
    def _check_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes in scene and warn user
        with pop-up dialog.

        Offer the following options:
            * save and continue
            * discard and continue
            * cancel

        Returns:
            True if user chooses to continue.
            False if user chooses to cancel current operation.
        """
        # Check if there are unsaved changes
        maya_dirty = cmds.file(q=True, modified=True)
        if not maya_dirty:
            return True

        msg = "There are unsaved changes in your current scene.\n"
        msg += "How would you like to proceed?"
        result = self.dialog(
            "Unsaved Changes",
            msg,
            buttons=["Save and continue", "Discard and continue", "Cancel"],
            default=0,
            cancel=2,
            no_ui_option=1,
        )

        if result == 0:
            # Option 1: save and continue
            # The save dialog won't return a value here if the user cancels.
            # So we need to check if the scene is still dirty to catch a cancel
            # action.
            mel.eval("SaveSceneAs")
            maya_dirty = cmds.file(q=True, modified=True)
            if maya_dirty:
                # If the user did cancel, cancel the whole operation.
                return False
            return True
        elif result == 1:
            # Option 2: discard and continue
            return True
        else:
            # Option 3: cancel operation
            return False

    def _on_new_scene(self, client_data=None):
        """Clear the asset context whenever a blank scene is started."""
        self.context.clear_flow_context()

    def _on_open_scene(self, client_data=None):
        """Set the asset context as appropriate when a new file is opened."""
        file_path = self.current_file()
        self.context.set_flow_context(file_path)

    def _export_alembic(self, file_path: str):
        """Export current scene to alembic file."""

        # Load alembic plugin if necessary
        if not cmds.pluginInfo("AbcExport", query=True, loaded=True):
            if not cmds.loadPlugin("AbcExport"):
                raise RuntimeError("Alembic plugin could not be loaded.")

        # Use scene start and end frame range
        start_frame = cmds.playbackOptions(query=True, minTime=True)
        end_frame = cmds.playbackOptions(query=True, maxTime=True)

        # Export all with default settings
        args = f'-frameRange {start_frame} {end_frame} -file "{file_path}"'
        self.logger.info(f"Exporting to alembic with args: {args}")
        try:
            cmds.AbcExport(j=args)
        except Exception as exc:  # pylint: disable=broad-except
            raise RuntimeError("Alembic export failed.") from exc
        self.logger.info("Alembic export complete!")
