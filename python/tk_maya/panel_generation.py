# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

def dock_panel(engine, panel_id, widget_id, title):
    """
    Docks a Shotgun app panel widget in a new panel tab of Maya Channel Box dock area.

    :param engine: :class:`MayaEngine` instance running in Maya.
    :param panel_id: Unique string identifier for the Shotgun app panel.
    :param widget_id: Unique string identifier for the Shotgun app panel widget instance.
    :param title: Title to give to the new dock tab.
    """

    # The imports are done here rather than at the module level to avoid spurious imports
    # when this module is reloaded in the context of a workspace control UI script.
    import maya.mel as mel
    import maya.utils
    import pymel.core as pm

    # Create the Maya panel name.
    maya_panel_id = "panel_%s" % panel_id

    # When the Maya panel already exists, it can be delete safely since its embedded
    # Shotgun app panel widget has already been reparented under Maya main window.
    if pm.control(maya_panel_id, query=True, exists=True):
        engine.log_debug("Deleting existing Maya panel %s." % maya_panel_id)
        pm.deleteUI(maya_panel_id)

    # Use the proper Maya panel docking method according to the Maya version.
    if mel.eval("getApplicationVersionAsFloat()") < 2017:

        # Create a new Maya window.
        maya_window = pm.window()
        engine.log_debug("Created Maya window %s." % maya_window)

        # Add a layout to the Maya window.
        maya_layout = pm.formLayout(parent=maya_window)
        engine.log_debug("Created Maya layout %s." % maya_layout)

        # Reparent the Shotgun app panel widget under the Maya window layout.
        engine.log_debug("Reparenting Shotgun app panel widget %s under Maya layout %s." % (widget_id, maya_layout))
        pm.control(widget_id, edit=True, parent=maya_layout)

        # Keep the Shotgun app panel widget sides aligned with the Maya window layout sides.
        pm.formLayout(maya_layout,
                      edit=True,
                      attachForm=[(widget_id, 'top', 1),
                                  (widget_id, 'left', 1),
                                  (widget_id, 'bottom', 1),
                                  (widget_id, 'right', 1)]
        )

        # Dock the Maya window into a new tab of Maya Channel Box dock area.
        engine.log_debug("Creating Maya panel %s." % maya_panel_id)
        pm.dockControl(maya_panel_id, area="right", content=maya_window, label=title)

        # Once Maya will have completed its UI update and be idle,
        # raise (with "r=True") the new dock tab to the top.
        maya.utils.executeDeferred("cmds.dockControl('%s', edit=True, r=True)" % maya_panel_id)

    else:  # Maya 2017 and later

        # Delete any default workspace control state that might have been automatically
        # created by Maya when a previously existing Maya panel was closed and deleted.
        if pm.workspaceControlState(maya_panel_id, exists=True):
            engine.log_debug("Deleting existing Maya workspace panel state %s." % maya_panel_id)
            pm.workspaceControlState(maya_panel_id, remove=True)

        # Retrieve the Channel Box dock area, with error reporting turned on.
        # This MEL function is declared in Maya startup script file UIComponents.mel.
        dock_area = mel.eval('getUIComponentDockControl("Channel Box / Layer Editor", true)')
        engine.log_debug("Retrieved Maya dock area %s." % dock_area)

        # This UI script will be called to build the UI of the new dock tab.
        # It will embed the Shotgun app panel widget into a Maya workspace control.
        # Maya 2017 expects this script to be passed in as a string, not as a function pointer
        # according to C++ source code method TelfWorkspaceControlCmd::handleScriptFlag().
        # See function _build_workspace_control_ui() below for a commented version of this script.
        ui_script = "import pymel.core as pm\n" \
                    "workspace_control = pm.setParent(query=True)\n" \
                    "pm.control('%s', edit=True, parent=workspace_control)" \
                    % widget_id

        # The following UI script can be used for development and debugging purposes.
        # This script has to retrieve and import the current source file in order to call
        # function _build_workspace_control_ui() below to build the workspace control UI.
        # ui_script = "import imp\n" \
        #             "panel_generation = imp.load_source('%s', '%s')\n" \
        #             "panel_generation._build_workspace_control_ui('%s')" \
        #             % (__name__, __file__.replace(".pyc", ".py"), widget_id)

        # Dock the Shotgun app panel widget into a new tab of the Channel Box dock area.
        engine.log_debug("Creating Maya workspace panel %s." % maya_panel_id)
        dock_tab = pm.workspaceControl(maya_panel_id,
                                       tabToControl=(dock_area, -1),  # -1 to append a new tab
                                       uiScript=ui_script,
                                       loadImmediately=True,
                                       retain=False,  # delete the dock tab when it is closed
                                       label=title,
                                       r=True  # raise the new dock tab to the top
                   )

        # Now that the workspace dock tab has been created, let's update its UI script.
        # This updated script will be saved automatically with the workspace control state
        # in the Maya layout preference file when the user will choose to quit Maya,
        # and will be executed automatically when Maya is restarted later by the user.

        # The script will delete the empty workspace dock tab that Maya will recreate on startup
        # when the user previously chose to quit Maya while the panel was opened.
        deferred_script = "import maya.cmds as cmds\\n" \
                          "if cmds.workspaceControl('%(id)s', exists=True):\\n" \
                          "    cmds.deleteUI('%(id)s')" \
                          % {"id": maya_panel_id}

        # The previous script will need to be executed once Maya has completed its UI update and be idle.
        ui_script = "import maya.utils\n" \
                    "maya.utils.executeDeferred(\"%s\")\n" \
                    % deferred_script

        # Update the workspace dock tab UI script.
        pm.workspaceControl(maya_panel_id, edit=True, uiScript=ui_script)


def _build_workspace_control_ui(widget_id):
    """
    Embed a Shotgun app panel widget into the calling Maya workspace control.

    :param widget_id: Unique string identifier for the Shotgun app panel widget instance.
    """

    import pymel.core as pm

    # In the context of this function, setParent() returns the calling workspace control
    # according to C++ source code method TiceSetParentCmd::doQuery().
    workspace_control = pm.setParent(query=True)

    # Reparent the Shotgun app panel widget under the workspace control.
    pm.control(widget_id, edit=True, parent=workspace_control)
