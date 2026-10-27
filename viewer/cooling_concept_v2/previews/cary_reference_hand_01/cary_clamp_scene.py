"""Installed Cary clamp and retained reference in the actual access scene.

The candidate's guide, spring and travel are inferred reconstruction choices.
This scene supplies geometry for planning; it does not supply grasp forces or
permit an unsupported reference to count as a completed robot operation.
"""
import json
import numpy as np
import trimesh
from cary_access_scene import CaryAccessScene, translation
from cary_clamp import PARTS, MOVING, MAX_GAP, moving_transform, spring_mesh
from source_geometry import ROOT, ASSETS


CANDIDATE = 'assets/cary_internal_dra_2500_v1/revisions/working_clamp/prepared_dra_candidate.glb'
REFERENCE = ('large_reference_holder', 'large_PTFE_reference')


def object_pose(record):
    obj = record['obj']
    pose = np.eye(4)
    pose[:3, :3] = obj.getRotation()
    pose[:3, 3] = obj.getTranslation()
    return pose


class CaryClampScene(CaryAccessScene):
    def __init__(self, local_only=False):
        super().__init__(local_only=local_only, cover_candidate=True)
        self.dra_source = trimesh.load(ROOT/CANDIDATE, force='scene', process=False)
        asset = ASSETS['dra']
        normal = np.array(asset['normalization_matrix'])
        self.raw_to_world = (translation(asset['position_m']) @
            np.array(self.setup['parts']['dra']['sphere_housing']['matrix']) @ normal)
        self.clamp_meshes = {}
        self.clamp_poses = {}
        self.clamp = trimesh.collision.CollisionManager()
        self.reference = trimesh.collision.CollisionManager()
        self.reference_rest = {}
        self.reference_meshes = {}
        for name in PARTS:
            node, key = self.dra_source.graph[name]
            mesh = self.dra_source.geometry[key].copy()
            mesh.apply_transform(np.linalg.inv(normal) @ node)
            if name in MOVING:
                mesh.apply_transform(np.linalg.inv(moving_transform(.014)))
            self.clamp_meshes[name] = mesh
            # Remove the old authored +19 mm slider offset. Candidate rigid
            # parts are in raw module coordinates and already include travel.
            self.obstacles.remove_object('dra::'+name)
            self.obstacles.add_object('dra::'+name, mesh, self.raw_to_world)
            self.clamp.add_object('dra::'+name, mesh, self.raw_to_world)
        for name in REFERENCE:
            _, key = self.dra_source.graph[name]
            mesh = self.dra_source.geometry[key]
            rest = object_pose(self.obstacles._objs['dra::'+name])
            self.reference_rest[name] = rest
            self.reference_meshes[name] = mesh
            self.reference.add_object('dra::'+name, mesh, rest)
        self.gap = None
        self.set_clamp(.014)
        self.set_reference(np.eye(4))

    def set_clamp(self, gap, angle=0.):
        if not 0 <= angle <= np.pi/2:
            raise ValueError('Clamp angle outside selected parked configuration')
        pose = self.raw_to_world @ moving_transform(gap, angle)
        if self.gap != gap:
            mesh = spring_mesh(gap)
            self.clamp_meshes['sample_clamp_spring'] = mesh
            for manager in (self.obstacles, self.clamp):
                manager.remove_object('dra::sample_clamp_spring')
                manager.add_object('dra::sample_clamp_spring', mesh, self.raw_to_world)
        for name in PARTS:
            world = pose if name in MOVING else self.raw_to_world
            self.clamp_poses[name] = world
            self.obstacles.set_transform('dra::'+name, world)
            self.clamp.set_transform('dra::'+name, world)
        self.gap, self.angle = float(gap), float(angle)

    def set_reference(self, delta):
        self.reference_delta = np.asarray(delta)
        for name, rest in self.reference_rest.items():
            for manager in (self.obstacles, self.reference):
                manager.set_transform('dra::'+name, self.reference_delta @ rest)

    def local_obstacles(self):
        manager = trimesh.collision.CollisionManager()
        for name, record in self.obstacles._objs.items():
            if not name.startswith(('cary::', 'dra::')):
                continue
            identity, part = name.split('::', 1)
            if identity == 'dra' and part in PARTS:
                mesh = self.clamp_meshes[part]
            else:
                source = self.cary_source if identity == 'cary' else self.dra_source
                _, key = source.graph[part]
                mesh = source.geometry[key]
            manager.add_object(name, mesh, object_pose(record))
        return manager

    def clamp_clearance(self):
        """Check the installed actuator against itself and the whole scene."""
        names = ['dra::'+name for name in PARTS]
        _, _, internal = self.clamp.in_collision_internal(return_names=True, return_data=True)
        for name in names:
            self.obstacles.remove_object(name)
        try:
            _, _, external = self.clamp.in_collision_other(self.obstacles, return_names=True, return_data=True)
        finally:
            for part in PARTS:
                self.obstacles.add_object('dra::'+part, self.clamp_meshes[part], self.clamp_poses[part])
        fixed = {
            frozenset(('dra::sample_clamp_arm', 'dra::sample_clamp_slider')),
            frozenset(('dra::sample_clamp_post', 'dra::sphere_cap_carrier')),
        }
        backing_pair = frozenset(('dra::sample_clamp_contact', 'dra::large_reference_holder'))
        failures, bounded = {}, {}
        for contact in [*internal, *external]:
            pair = frozenset(contact.names)
            if pair in fixed:
                continue
            depth = abs(float(contact.depth))
            row = dict(parts=sorted(pair), maximum_reported_depth_m=depth)
            if pair == backing_pair:
                pad = trimesh.transform_points(self.clamp_meshes['sample_clamp_contact'].vertices,
                                                self.clamp_poses['sample_clamp_contact'])
                backing = trimesh.transform_points(self.reference_meshes['large_reference_holder'].vertices,
                    self.reference_delta @ self.reference_rest['large_reference_holder'])
                # The initial reference backing plane is perpendicular to Y.
                # Only classify nominal seating at its unrotated installed pose.
                if np.max(abs(self.reference_delta[:3, :3]-np.eye(3))) < 1e-9:
                    overlap = float(min(pad[:, 1].max(), backing[:, 1].max()) -
                                    max(pad[:, 1].min(), backing[:, 1].min()))
                    if overlap <= 1e-6:
                        row['normal_overlap_m'] = overlap
                        bounded[tuple(sorted(pair))] = row
                        continue
            if depth > 1e-7:
                key = tuple(sorted(pair))
                if depth > failures.get(key, {}).get('maximum_reported_depth_m', -1):
                    failures[key] = row
        self.last_clamp_bounded_contacts = list(bounded.values())
        return list(failures.values())

    def reference_clearance(self):
        names = ['dra::'+name for name in REFERENCE]
        for name in names:
            self.obstacles.remove_object(name)
        try:
            _, _, contacts = self.reference.in_collision_other(self.obstacles, return_names=True, return_data=True)
        finally:
            for name in REFERENCE:
                self.obstacles.add_object('dra::'+name, self.reference_meshes[name],
                    self.reference_delta @ self.reference_rest[name])
        failures = {}
        for contact in contacts:
            depth = abs(float(contact.depth))
            if depth > 1e-7:
                key = tuple(sorted(contact.names))
                if depth > failures.get(key, {}).get('maximum_reported_depth_m', -1):
                    failures[key] = dict(parts=list(key), maximum_reported_depth_m=depth)
        return list(failures.values())
