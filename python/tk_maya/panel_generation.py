# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from . import panel_util


def dock_panel(engine, shotgun_panel, title, new_panel):
    """
    Docks a Shotgun app panel into a new Maya panel in the active Maya window.

    In Maya 2016 and before, the panel is docked into a new tab of Maya Channel Box dock area.
    In Maya 2017 and after, the panel is docked into a new workspace area in the active Maya workspace.

    :param engine: :class:`MayaEngine` instance running in Maya.
    :param shotgun_panel: Qt widget at the root of the Shotgun app panel.
                          This Qt widget is assumed to be child of Maya main window.
                          Its name can be used in standard Maya commands to reparent it under a Maya panel.
    :param title: Title to give to the new dock tab.
    :param new_panel: True when the Shotgun app panel was just created by the calling function.
                      False when the Shotgun app panel was retrieved from under an existing Maya panel.
    :returns: Name of the newly created Maya panel.
    """

    # The imports are done here rather than at the module level to avoid spurious imports
    # when this module is reloaded in the context of a workspace control UI script.
    import maya.mel as mel

    # Retrieve the Shotgun app panel name.
    shotgun_panel_name = shotgun_panel.objectName()

    # Use the proper Maya panel docking method according to the Maya version.
    if mel.eval("getApplicationVersionAsFloat()") < 2017:

        import maya.utils
        import pymel.core as pm

        # Create a Maya panel name.
        maya_panel_name = "maya_%s" % shotgun_panel_name

        # When the Maya panel already exists, it can be deleted safely since its embedded
        # Shotgun app panel has already been reparented under Maya main window.
        if pm.control(maya_panel_name, query=True, exists=True):
            engine.log_debug("Deleting existing Maya panel %s." % maya_panel_name)
            pm.deleteUI(maya_panel_name)

        # Create a new Maya window.
        maya_window = pm.window()
        engine.log_debug("Created Maya window %s." % maya_window)

        # Add a layout to the Maya window.
        maya_layout = pm.formLayout(parent=maya_window)
        engine.log_debug("Created Maya layout %s." % maya_layout)

        # Reparent the Shotgun app panel under the Maya window layout.
        engine.log_debug("Reparenting Shotgun app panel %s under Maya layout %s." % (shotgun_panel_name, maya_layout))
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
        engine.log_debug("Creating Maya panel %s." % maya_panel_name)
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
        import maya.cmds as cmds

        # Create a Maya panel name in the current Maya workspace.
        # We need to use different names for different workspaces in order for
        # each workspace control location to be saved and restored properly
        # when the user swithces from one workspace to another.
        current_workspace = cmds.workspaceLayoutManager(query=True, current=True)
        maya_panel_name = "maya_%s_%s" % (current_workspace, shotgun_panel_name)
        # Make sure the name is a valid Maya object name.
        maya_panel_name = mel.eval('formValidObjectName("%s")' % maya_panel_name)

        # When the Maya panel already exists, it can be deleted safely since its embedded
        # Shotgun app panel has already been reparented under Maya main window.
        if cmds.workspaceControl(maya_panel_name, query=True, exists=True):
            engine.log_debug("Deleting existing Maya panel %s." % maya_panel_name)
            cmds.deleteUI(maya_panel_name)

        if cmds.workspaceControlState(maya_panel_name, exists=True):
            # We have a saved workspace control state created by Maya from a workspace control that was
            # previously closed and deleted when the user swithced to another workspace or exited Maya.
            if new_panel:
                # When the Shotgun app panel was just created by the calling function, let Maya
                # embed it into a workspace control restored from the workspace control state.
                # This case happens when the engine has just been started and the Shotgun app panel
                # is displayed for the first time around.
                # In Maya 2017, switching to another workspace then back is the only straightforward
                # way to make Maya automatically recreate the workspace control and call its UI script.
                engine.log_debug("Making Maya recreate workspace panel %s." % maya_panel_name)
                temp_workspace_name = "W%s" % uuid.uuid4().hex
                cmds.workspaceLayoutManager(saveAs=temp_workspace_name)
                cmds.workspaceLayoutManager(setCurrent=current_workspace)
                cmds.workspaceLayoutManager(delete=temp_workspace_name)
                return maya_panel_name
            else:
                # When the Shotgun app panel was retrieved from under an existing Maya panel,
                # delete the workspace control state since we want to recreate our default workspace control.
                engine.log_debug("Deleting existing Maya workspace panel state %s." % maya_panel_name)
                cmds.workspaceControlState(maya_panel_name, remove=True)

        # Retrieve the Channel Box dock area, with error reporting turned off.
        # This MEL function is declared in Maya startup script file UIComponents.mel.
        # It returns an empty string when a dock area cannot be found, but Maya will
        # retrieve the Channel Box dock area even when it is not shown in the current workspace.
        dock_area = mel.eval('getUIComponentDockControl("Channel Box / Layer Editor", false)')
        engine.log_debug("Retrieved Maya dock area %s." % dock_area)

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
        engine.log_debug("Creating Maya workspace panel %s." % maya_panel_name)

        kwargs = {"uiScript": ui_script,
                  "loadImmediately": True,
                  "retain": False,  # delete the dock tab when it is closed
                  "label": title,
                  "r": True}  # raise at the top of its workspace area

        if current_workspace == "Maya Classic":
            # We are in the default Maya workspace where the Channel Box dock area can be found.
            # Dock the Shotgun app panel into a new tab of this Channel Box dock area,
            # since the user was used to this behaviour in previous versions of Maya.
            kwargs["tabToControl"] = (dock_area, -1)  # -1 to append a new tab

        # When we are in a new Maya 2017 workspace where the Channel Box dock area might not be found,
        # let Maya embed the Shotgun app panel into a floating workspace control window.

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

    import maya.api.OpenMaya
    import maya.utils
    from maya.OpenMayaUI import MQtUtil

    # In the context of this function, we know that we are running in Maya 2017 and later
    # with the newer versions of PySide and shiboken.
    from PySide2 import QtWidgets
    from shiboken2 import wrapInstance

    # Retrieve the calling Maya workspace control.
    ptr = MQtUtil.getCurrentParent()
    workspace_control = wrapInstance(long(ptr), QtWidgets.QWidget)

    # Search for the Shotgun app panel widget.
    for widget in QtWidgets.QApplication.allWidgets():
        if widget.objectName() == shotgun_panel_name:

            # Reparent the Shotgun app panel widget under Maya workspace control.
            widget.setParent(workspace_control)

            # Add the Shotgun app panel widget to the Maya workspace control layout.
            workspace_control.layout().addWidget(widget)

            # Install an event filter on Maya workspace control to monitor
            # its close event in order to reparent the Shotgun app panel widget
            # under Maya main window for later use.
            panel_util.install_event_filter_by_widget(workspace_control, shotgun_panel_name)

            break
    else:
        msg = "Shotgun: Cannot restore %s: Shotgun app panel not found" % shotgun_panel_name
        fct = maya.api.OpenMaya.MGlobal.displayError
        maya.utils.executeInMainThreadWithResult(fct, msg)
