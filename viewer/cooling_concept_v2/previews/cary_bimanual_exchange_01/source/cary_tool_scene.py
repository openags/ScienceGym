"""Cary planning scene with a separately sourced long forceps in the right hand."""
import numpy as np
import trimesh
from cary_clamp_scene import CaryClampScene
from long_forceps import meshes
from source_geometry import fk


class CaryToolScene(CaryClampScene):
    def __init__(self, tool_grip, reference_grip):
        super().__init__()
        self.palm_T_tool=np.linalg.inv(np.array(tool_grip))
        self.reference_grasp=np.array(reference_grip)
        self.long_tool_closure=None

    def state(self,base,q,tool_held=True,closure=1.,reference_held=False,**options):
        if self.long_tool_closure!=closure:
            self.tool=trimesh.collision.CollisionManager()
            for name,mesh in meshes(closure).items():self.tool.add_object(name,mesh)
            self.long_tool_closure=closure
        # Let the existing body/specimen code place the custom tool, keeping
        # its ordinary short-tweezer mesh generator out of this scene.
        self.last_closure=closure
        result=super().state(base,q,tool_held=tool_held,closure=closure,**options)
        if reference_held:
            self.set_reference(base@fk(q)['left_palm_force_sensor']@np.linalg.inv(self.reference_grasp))
        return result
