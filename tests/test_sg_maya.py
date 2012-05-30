"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------
"""
import os
import unittest2 as unittest

from mock import Mock

import pymel.core as pm
import maya.cmds as cmds

from tank_test.tank_test_base import TankTestBase, setUpModule
import tank
from engine import MayaEngine


class MayaEngineTestBase(TankTestBase):
    def setUp(self):
        super(MayaEngineTestBase, self).setUp()
        self.mock_dialogs()

        # set up a project 
        self.setup_standard_config()

        self.cfg_folder = os.path.join(self.project_config, "engines", "sg_maya")
        # set up project data
        self.sequence = {"type":"Sequence", "id":6, "name": "Seq", "project":self.project, "code":"Seq"}
        self.seq_path = os.path.join(self.project_root, "sequences", "Seq")
        self.add_production_path(self.seq_path, self.sequence)

        self.shot = {"type":"Shot", "id":2, "name":"shot_2"}
        self.shot_path = os.path.join(self.seq_path, "shot_2")
        self.add_production_path(self.shot_path, self.shot)

        self.step = {"type":"Step", "id":3, "name":"step_name", "short_name":"step_name", "code":"step_code"}
        self.step_path = os.path.join(self.shot_path, "step_name")
        self.add_production_path(self.step_path, self.step)

        # add work path
        work_path = os.path.join(self.step_path, "work")
        os.mkdir(work_path)

        self.engine = self.start_engine(project_root=self.project_root,
                                        entity = self.shot,
                                        step = self.step)

    def start_engine(self, **kws):
        """
        Instantiates an engine with a context reflecting context
        related keywords passed.
        """
        if tank.platform.current_engine():
            tank.platform.current_engine().destroy()
        ctx = tank.platform.Context(**kws)
        return MayaEngine(ctx)

    def mock_dialogs(self):
        """Mock dialogs used in apps."""
        class MockDialog(Mock):
            def __init__(self, *args, **kws):
                super(MockDialog, self).__init__(*args, **kws)
                #self.dialog_type = dialog_type

            def last_message(self):
                kws = self.call_args[1]
                return kws.get("message", "")

        self.confirm_dailog_mock = MockDialog(cmds.confirmDialog)
        cmds.confirmDialog = self.confirm_dailog_mock
        self.prompt_dailog_mock = MockDialog(cmds.promptDialog)
        cmds.promptDialog = self.prompt_dailog_mock
        self.layout_dailog_mock = MockDialog(cmds.layoutDialog)
        cmds.layoutDialog = self.layout_dailog_mock
        self.layout_dailog_mock = MockDialog(cmds.layoutDialog)
        cmds.layoutDialog = self.layout_dailog_mock


class TestMayaEngine(MayaEngineTestBase):

    def test_engine(self):
        self.assertIsInstance(self.engine, tank.platform.engine.Engine)

    def test_create_folders(self):
        """Tests that if path for given context does not yet exist, it is created during engine initialization."""
        shot = {"type":"Shot", "id":3, "name":"shot_3", "project":self.project, "code":"shot_3", "sg_sequence":self.sequence}
        self.add_to_sg_mock_db(shot)
        shot_path = os.path.join(self.seq_path, "shot_3")
        step_path = os.path.join(shot_path, "step_name")

        # expected work path
        work_path = os.path.join(step_path, "work")
        self.assertFalse(os.path.exists(work_path))

        engine = self.start_engine(project_root=self.project_root,
                                   entity = shot,
                                   step = self.step)
        self.assertTrue(os.path.exists(work_path))

if __name__ == "__main__":
    unittest.main()
