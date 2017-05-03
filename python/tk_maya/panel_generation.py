# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import maya.cmds as cmds
import maya.mel as mel
import maya.utils

from . import panel_util


# Prefix prepended to the Shotgun app panel unique identifier to create
# the name given to the Qt widget at the root of the Shotgun app panel.
SHOTGUN_APP_PANEL_PREFIX = "panel_"

# Prefix prepended to the Shotgun app panel name to create the name
# given to the Maya panel embedding the Shotgun app panel widget.
MAYA_PANEL_PREFIX = "maya_"


def restore_panels(engine):
    """
    Restores the persisted Shotgun app panels into their visible
    Maya workspace controls in the active Maya window.

    .. note:: This function is only meaningful for Maya 2017 and later,
              and does nothing for previous versions of Maya.

    :param engine: :class:`MayaEngine` instance running in Maya.
    """

    # Only restore Shotgun app panels in Maya 2017 and later.
    if mel.eval("getApplicationVersionAsFloat()") < 2017:
        return

    # Search for the Shotgun app panels that need to be restored
    # among the panels registered with the engine.
    for panel_id in engine.panels:

        # Recreate a Maya panel name with the Shotgun app panel unique identifier.
        maya_panel_name = MAYA_PANEL_PREFIX + SHOTGUN_APP_PANEL_PREFIX + panel_id

        # When the current Maya workspace contains the Maya panel workspace control,
        # the Shotgun app panel needs to be recreated and docked.
        if cmds.workspaceControl(maya_panel_name, exists=True):

            # Once Maya will have completed its UI update and be idle,
            # recreate and dock the Shotgun app panel.
            maya.utils.executeDeferred(engine.panels[panel_id]["callback"])


def dock_panel(engine, shotgun_panel, title):
    """
    Docks a Shotgun app panel into a new Maya panel in the active Maya window.

    In Maya 2016 and before, the panel is docked into a new tab of Maya Channel Box dock area.
    In Maya 2017 and after, the panel is docked into a new workspace area in the active Maya workspace.

    :param engine: :class:`MayaEngine` instance running in Maya.
    :param shotgun_panel: Qt widget at the root of the Shotgun app panel.
                          This Qt widget is assumed to be child of Maya main window.
                          Its name can be used in standard Maya commands to reparent it under a Maya panel.
    :param title: Title to give to the new dock tab.
    :returns: Name of the newly created Maya panel.
    """

    # Retrieve the Shotgun app panel name.
    shotgun_panel_name = shotgun_panel.objectName()

    # Create a Maya panel name.
    maya_panel_name = MAYA_PANEL_PREFIX + shotgun_panel_name

    # Use the proper Maya panel docking method according to the Maya version.
    if mel.eval("getApplicationVersionAsFloat()") < 2017:

        import pymel.core as pm

        # When the Maya panel already exists, it can be deleted safely since its embedded
        # Shotgun app panel has already been reparented under Maya main window.
        if pm.control(maya_panel_name, query=True, exists=True):
            engine.logger.debug("Deleting existing Maya panel %s.", maya_panel_name)
            pm.deleteUI(maya_panel_name)

        # Create a new Maya window.
        maya_window = pm.window()
        engine.logger.debug("Created Maya window %s.", maya_window)

        # Add a layout to the Maya window.
        maya_layout = pm.formLayout(parent=maya_window)
        engine.logger.debug("Created Maya layout %s.", maya_layout)

        # Reparent the Shotgun app panel under the Maya window layout.
        engine.logger.debug("Reparenting Shotgun app panel %s under Maya layout %s.", shotgun_panel_name, maya_layout)
        pm.control(shotgun_panel_name, edit=True, parent=maya_layout)

        # Keep the Shotgun app panel sides aligned with the Maya window layout sides.
        pm.formLayout(maya_layout,
                      edit=True,
                      attachForm=[(shotgun_panel_name, 'top', 1),
                                  (shotgun_panel_name, 'left', 1),
                                  (shotgun_panel_name, 'bottom', 1),
                                  (shotgun_panel_name, 'right', 1)]
        )

        # Dock the Maya window into a new tab of Maya Channel Box dock area.
        engine.logger.debug("Creating Maya panel %s.", maya_panel_name)
        pm.dockControl(maya_panel_name, area="right", content=maya_window, label=title)

        # Since Maya does not give us any hints when a panel is being closed,
        # install an event filter on Maya dock control to monitor its close event
        # in order to gracefully close and delete the Shotgun app panel widget.
        # Some obscure issues relating to UI refresh are also resolved by the event filter.
        panel_util.install_event_filter_by_name(maya_panel_name, shotgun_panel_name)

        # Once Maya will have completed its UI update and be idle,
        # raise (with "r=True") the new dock tab to the top.
        maya.utils.executeDeferred("import maya.cmds as cmds\n" \
                                   "cmds.dockControl('%s', edit=True, r=True)" % maya_panel_name)

    else:  # Maya 2017 and later

        import uuid

        # When the current Maya workspace contains our Maya panel workspace control,
        # embed the Shotgun app panel into this workspace control.
        # This can happen when the engine has just been started and the Shotgun app panel is
        # displayed for the first time around, or when the user reinvokes a displayed panel.
        if cmds.workspaceControl(maya_panel_name, exists=True):

            engine.logger.debug("Restoring Maya workspace panel %s.", maya_panel_name)

            # Set the Maya default parent to be our Maya panel workspace control.
            cmds.setParent(maya_panel_name)

            # Embed the Shotgun app panel into the Maya panel workspace control.
            build_workspace_control_ui(shotgun_panel_name)

            if cmds.control(maya_panel_name, query=True, isObscured=True):
                # When the panel is not visible, raise it to the top of its workspace area.
                engine.logger.debug("Raising workspace panel %s.", maya_panel_name)
                cmds.workspaceControl(maya_panel_name, edit=True, r=True)
            else:
                # When the panel is visible, use a workaround to force Maya 2017 to refresh the panel size.
                # We encased this workaround in a try/except since we cannot be sure
                # that it will still work without errors in future versions of Maya.
                try:
                    engine.logger.debug("Forcing Maya to refresh workspace panel %s size.", maya_panel_name)

                    # Create a new empty workspace control tab.
                    name = cmds.workspaceControl(uuid.uuid4().hex,
                                                 tabToControl=(maya_panel_name, -1),  # -1 to append a new tab
                                                 uiScript="",
                                                 r=True)  # raise at the top of its workspace area
                    # Delete the empty workspace control.
                    cmds.deleteUI(name)
                    # Delete the empty workspace control state that was created
                    # when deleting the empty workspace control.
                    cmds.workspaceControlState(name, remove=True)
                except:
                    engine.logger.debug("Cannot force Maya to refresh workspace panel %s size.", maya_panel_name)

            return maya_panel_name

        # Retrieve the Channel Box dock area, with error reporting turned off.
        # This MEL function is declared in Maya startup script file UIComponents.mel.
        # It returns an empty string when a dock area cannot be found, but Maya will
        # retrieve the Channel Box dock area even when it is not shown in the current workspace.
        dock_area = mel.eval('getUIComponentDockControl("Channel Box / Layer Editor", false)')
        engine.logger.debug("Retrieved Maya dock area %s.", dock_area)

        # This UI script will be called to build the UI of the new dock tab.
        # It will embed the Shotgun app panel into a Maya workspace control.
        # Since Maya 2017 expects this script to be passed in as a string,
        # not as a function pointer, it must retrieve the current module in order
        # to call function build_workspace_control_ui() that actually builds the UI.
        # Note that this script will be saved automatically with the workspace control state
        # in the Maya layout preference file when the user quits Maya, and will be executed
        # automatically when Maya is restarted later by the user.
        ui_script = "import sys\n" \
                    "import maya.api.OpenMaya\n" \
                    "import maya.utils\n" \
                    "for m in sys.modules:\n" \
                    "    if 'tk_maya.panel_generation' in m:\n" \
                    "        try:\n" \
                    "            sys.modules[m].build_workspace_control_ui('%(panel_name)s')\n" \
                    "        except Exception, e:\n" \
                    "            msg = 'Shotgun: Cannot restore %(panel_name)s: %%s' %% e\n" \
                    "            fct = maya.api.OpenMaya.MGlobal.displayError\n" \
                    "            maya.utils.executeInMainThreadWithResult(fct, msg)\n" \
                    "        break\n" \
                    "else:\n" \
                    "    msg = 'Shotgun: Cannot restore %(panel_name)s: Shotgun is not currently running'\n" \
                    "    fct = maya.api.OpenMaya.MGlobal.displayError\n" \
                    "    maya.utils.executeInMainThreadWithResult(fct, msg)\n" \
                    % {"panel_name": shotgun_panel_name}

        # Dock the Shotgun app panel into a new workspace control in the active Maya workspace.
        engine.logger.debug("Creating Maya workspace panel %s.", maya_panel_name)

        kwargs = {"uiScript": ui_script,
                  "retain": False,  # delete the dock tab when it is closed
                  "label": title,
                  "r": True}  # raise at the top of its workspace area

        # When we are in a Maya workspace where the Channel Box dock area can be found,
        # dock the Shotgun app panel into a new tab of this Channel Box dock area
        # since the user was used to this behaviour in previous versions of Maya.
        # When we are in a Maya workspace where the Channel Box dock area can not be found,
        # let Maya embed the Shotgun app panel into a floating workspace control window.
        kwargs["tabToControl"] = (dock_area, -1)  # -1 to append a new tab

        cmds.workspaceControl(maya_panel_name, **kwargs)

    return maya_panel_name


def build_workspace_control_ui(shotgun_panel_name):
    """
    Embeds a Shotgun app panel into the calling Maya workspace control.

    This function will be called in two cases:
    - When the workspace control is being created by Maya command workspaceControl;
    - When the workspace control is being restored from a workspace control state
      created by Maya when this workspace control was previously closed and deleted.

    .. note:: This function is only for Maya 2017 and later.

    :param shotgun_panel_name: Name of the Qt widget at the root of a Shotgun app panel.
    """

    from maya.OpenMayaUI import MQtUtil

    # In the context of this function, we know that we are running in Maya 2017 and later
    # with the newer versions of PySide and shiboken.
    from PySide2 import QtWidgets
    from shiboken2 import wrapInstance

    import sgtk.platform

    # Retrieve the Maya engine.
    engine = sgtk.platform.current_engine()

    # Retrieve the calling Maya workspace control.
    ptr = MQtUtil.getCurrentParent()
    workspace_control = wrapInstance(long(ptr), QtWidgets.QWidget)

    # Search for the Shotgun app panel widget.
    for widget in QtWidgets.QApplication.allWidgets():
        if widget.objectName() == shotgun_panel_name:

            maya_panel_name = workspace_control.objectName()

            engine.logger.debug("Reparenting Shotgun app panel %s under Maya workspace panel %s.",
                                shotgun_panel_name, maya_panel_name)

            # When possible, give a minimum width to the workspace control;
            # otherwise, it will use the width of the currently displayed tab.
            # Note that we did not use the workspace control "initialWidth" and "minimumWidth"
            # to set the minimum width to the initial width since these values are not
            # properly saved by Maya 2017 in its layout preference files.
            # This minimum width behaviour is consistent with Maya standard panels.
            size_hint = widget.sizeHint()
            if size_hint.isValid():
                # Use the widget recommended width as the workspace control minimum width.
                minimum_width = size_hint.width()
                engine.logger.debug("Setting Maya workspace panel %s minimum width to %s.",
                                    maya_panel_name, minimum_width)
                workspace_control.setMinimumWidth(minimum_width)
            else:
                # The widget has no recommended size.
                engine.logger.debug("Cannot set Maya workspace panel %s minimum width.", maya_panel_name)

            # Reparent the Shotgun app panel widget under Maya workspace control.
            widget.setParent(workspace_control)

            # Add the Shotgun app panel widget to the Maya workspace control layout.
            workspace_control.layout().addWidget(widget)

            # Install an event filter on Maya workspace control to monitor
            # its close event in order to reparent the Shotgun app panel widget
            # under Maya main window for later use.
            engine.logger.debug("Installing a close event filter on Maya workspace panel %s.", maya_panel_name)
            panel_util.install_event_filter_by_widget(workspace_control, shotgun_panel_name)

            # Delete any leftover workspace control state to avoid a spurious deletion
            # of our workspace control when the user switches to another workspace and back.
            if cmds.workspaceControlState(maya_panel_name, exists=True):
                # Once Maya will have completed its UI update and be idle,
                # delete the leftover workspace control state.
                engine.logger.debug("Deleting leftover Maya workspace control state %s.", maya_panel_name)
                maya.utils.executeDeferred(cmds.workspaceControlState, maya_panel_name, remove=True)

            break
    else:
        # The Shotgun app panel widget was not found and needs to be recreated.

        # Search for the Shotgun app panel that needs to be restored
        # among the panels registered with the engine.
        for panel_id in engine.panels:

            # The name of the Qt widget at the root of the Shotgun app panel
            # was constructed by prepending to the panel unique identifier.
            if shotgun_panel_name.endswith(panel_id):

                # Once Maya will have completed its UI update and be idle,
                # recreate and dock the Shotgun app panel.
                maya.utils.executeDeferred(engine.panels[panel_id]["callback"])

                break
        else:
            # The Shotgun app panel that needs to be restored is not in the context configuration.
            engine.logger.error("Cannot restore %s: Shotgun app panel not found. " \
                             "Make sure the app is in the context configuration. ", shotgun_panel_name)
