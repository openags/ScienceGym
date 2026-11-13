"""Existing full laboratory with movable Nicolet cover and acquisition keys."""
import json
import numpy as np
import trimesh
from scipy.spatial.transform import Rotation

from optical_delivery import DeliveryScene
from optical_choreography import HERE
from source_geometry import ROOT, ASSETS


def translation(xyz):
    result = np.eye(4)
    result[:3, 3] = xyz
    return result


class FTIRMeasurementScene(DeliveryScene):
    def __init__(self):
        super().__init__()
        self.interfaces = json.loads((ROOT / 'assets/nicolet_6700_v1/interfaces.json').read_text())
        self.source = trimesh.load(ROOT / ASSETS['nicolet']['geometry'], force='scene', process=False)
        self.interface_world = translation(ASSETS['nicolet']['position_m']) @ np.array(ASSETS['nicolet']['normalization_matrix'])
        self.cover = next(v for v in self.interfaces['interfaces'] if v['id'] == 'sample_cover')
        self.hinge = (self.interface_world @ np.r_[self.cover['pivot_m'], 1.])[:3]
        self.closed_poses = {}
        for name in self.cover['parts'] + ['scan_key_' + str(i) for i in range(4)]:
            local, _ = self.source.graph[name]
            installed = np.array(self.setup['parts'].get('nicolet', {}).get(name, {}).get('matrix', np.eye(4)))
            self.closed_poses[name] = translation(ASSETS['nicolet']['position_m']) @ installed @ local
        self.set_cover(0.)

    def set_cover(self, angle):
        rotation = np.eye(4)
        rotation[:3, :3] = Rotation.from_euler('x', angle).as_matrix()
        delta = translation(self.hinge) @ rotation @ translation(-self.hinge)
        for name in self.cover['parts']:
            self.obstacles.set_transform('nicolet::' + name, delta @ self.closed_poses[name])
        self.cover_angle = float(angle)

    def set_key(self, identity, travel):
        assert 0. <= travel <= .0003 + 1e-12
        interface = next(v for v in self.interfaces['interfaces'] if v['id'] == identity)
        axis = self.interface_world[:3, :3] @ np.array(interface['axis'])
        name = 'scan_key_' + identity.split('_')[-1]
        self.obstacles.set_transform('nicolet::' + name, translation(axis * travel) @ self.closed_poses[name])
