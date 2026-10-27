"""Extend the measurement scene with the same movable gold-reference identity."""
import numpy as np
import trimesh
from ftir_measurement_scene import FTIRMeasurementScene, translation
from source_geometry import ROOT, ASSETS


class FTIRProcedureScene(FTIRMeasurementScene):
    def __init__(self):
        super().__init__()
        asset=ASSETS['pike'];source=trimesh.load(ROOT/asset['geometry'],force='scene',process=False)
        self.reference_rest={}
        for name in ['gold_reference_holder','gold_reference_shoulder','diffuse_gold_reference_face']:
            local,_=source.graph[name]
            installed=np.array(self.setup['parts']['pike'][name]['matrix'])
            self.reference_rest[name]=translation(asset['position_m'])@installed@local

    def set_reference(self, delta):
        for name,rest in self.reference_rest.items():
            self.obstacles.set_transform('pike::'+name,np.array(delta)@rest)
