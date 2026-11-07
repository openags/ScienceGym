"""Plan a Dex3 approach from encoders, native depth and a public room map.

No posed instrument model, physical object state or stored path is consumed.
The sampled clearance screen does not certify unseen surfaces or execution.
"""
import mujoco
import numpy as np
import trimesh

from dex3_ftir_hand import Dex3PointingHand
from ftir_hand import ArmIK
from joint_rrt import plan as plan_rrt
from robot_source_meshes import robot_source_meshes, source_adjacency
from source_proximity import SourceClearance
from tool_approach_planning import depth_surface


class ObservedKeyApproach:
    def __init__(self, model, estimated, depth):
        self.m, self.d = model, mujoco.MjData(model)
        self.d.qpos[:] = estimated.qpos
        mujoco.mj_forward(model, self.d)
        self.initial = self.d.qpos.copy()
        self.ik = ArmIK(model)
        self.hand = Dex3PointingHand(model)
        self.source = robot_source_meshes(model, visual_groups=(1, 2))
        self.robot = trimesh.collision.CollisionManager()
        for name, mesh in self.source.items():
            body = self.d.body(name)
            transform = np.eye(4)
            transform[:3, :3], transform[:3, 3] = body.xmat.reshape(3, 3), body.xpos
            self.robot.add_object(name, mesh, transform)
        self.environment = trimesh.collision.CollisionManager()
        meshes = {}
        for g in range(model.ngeom):
            if model.body(model.geom_bodyid[g]).name != 'lab_architecture' or model.geom_group[g] != 2:
                continue
            mid = model.geom_dataid[g]
            va, vn = model.mesh_vertadr[mid], model.mesh_vertnum[mid]
            fa, fn = model.mesh_faceadr[mid], model.mesh_facenum[mid]
            mesh = trimesh.Trimesh(vertices=model.mesh_vert[va:va+vn],
                                  faces=model.mesh_face[fa:fa+fn], process=False)
            transform = np.eye(4)
            transform[:3, :3] = self.d.geom_xmat[g].reshape(3, 3)
            transform[:3, 3] = self.d.geom_xpos[g]
            points = mesh.vertices @ transform[:3, :3].T + transform[:3, 3]
            if np.any(points.max(0) < self.initial[:3]-1.3) or np.any(points.min(0) > self.initial[:3]+1.3):
                continue
            name = 'architecture::'+model.geom(g).name
            meshes[name] = mesh
            self.environment.add_object(name, mesh, transform)
        camera = model.camera('head_depth').id
        transform = np.eye(4)
        transform[:3, :3] = self.d.cam_xmat[camera].reshape(3, 3)
        transform[:3, 3] = self.d.cam_xpos[camera]
        surface = depth_surface(depth, transform, float(model.cam_fovy[camera]))
        points = surface.vertices
        keep = np.all(abs(points-self.initial[:3]) < 1.2, axis=1) & (points[:, 2] > .82)
        faces = surface.faces[np.all(keep[surface.faces], axis=1)]
        if not len(faces):
            raise ValueError('No observed instrument surface')
        surface = trimesh.Trimesh(vertices=points, faces=faces, process=False)
        surface.remove_unreferenced_vertices()
        meshes['observed_depth_surface'] = surface
        self.environment.add_object('observed_depth_surface', surface)
        self.observed_faces = len(faces)
        self.clearance = SourceClearance(model, self.d, self.robot, self.source,
            self.environment, meshes, list(self.ik.joints), source_adjacency(model, self.source),
            check_fixed_environment=False)
        self.last_clearance = None

    def valid(self, arm):
        self.d.qpos[:] = self.initial
        self.d.qpos[self.ik.qa] = arm
        mujoco.mj_kinematics(self.m, self.d)
        mujoco.mj_comPos(self.m, self.d)
        self.last_clearance = self.clearance.check(.002)
        return self.last_clearance['clear']

    def build(self, detection, label='BACKGROUND'):
        normal = np.asarray(detection['outward_normal'])
        center = np.asarray(detection['buttons'][label])
        home = self.initial[self.ik.qa].copy()
        rows = []
        if not self.valid(home):
            return dict(planned=False, reason='initial_arm_clearance', detail=self.last_clearance)
        for lean in [.8, .6, .4]:
            for roll in [np.pi, np.pi-.3, np.pi+.3, 0.]:
                self.valid(home)
                contact_wrist, rotation, point = self.hand.at_surface(
                    center, normal, detection['row_direction'], lean, roll)
                target = contact_wrist+.03*normal
                arm, pe, re = self.ik.solve(self.d, target, rotation, home)
                row = dict(lean_rad=lean, roll_rad=roll, position_error_m=pe, rotation_error_rad=re)
                rows.append(row)
                if pe > .001 or re > .025:
                    row['failure'] = 'endpoint_ik'
                    continue
                if not self.valid(arm):
                    row.update(failure='endpoint_clearance', detail=self.last_clearance)
                    continue
                path, metrics = plan_rrt(home, arm, self.ik.low, self.ik.high,
                    self.valid, seed=7363, iterations=3000)
                row['rrt'] = metrics
                if path is None:
                    continue
                return dict(planned=True, label=label, arm_path_rad=[q.tolist() for q in path],
                    surface_m=center.tolist(), normal=normal.tolist(),
                    contact_wrist_m=contact_wrist.tolist(), wrist_rotation=rotation.tolist(),
                    wrist_local_contact_m=point.tolist(), lean_rad=lean, roll_rad=roll,
                    attempts=rows, observed_faces=self.observed_faces,
                    clearance_metrics=self.clearance.metrics(), physical_execution=False,
                    unobserved_free_space_certified=False)
        return dict(planned=False, attempts=rows, observed_faces=self.observed_faces)
