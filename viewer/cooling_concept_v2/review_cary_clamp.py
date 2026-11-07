"""Check clamp travel, guide clearance, sample contact and clear-port parking.

Uses the source module and the existing reference/witness meshes. This is a
mechanism geometry review, not a robot trajectory or force-retention test.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
import trimesh
from scipy.spatial.transform import Rotation
from cary_clamp import PARTS, MAX_GAP, solids, solid_mesh, meshes
from source_geometry import ROOT, ASSETS

HERE = Path(__file__).resolve().parent
OUT = ROOT/'assets/cary_internal_dra_2500_v1/revisions/working_clamp'


def translation(xyz):
    m = np.eye(4)
    m[:3, 3] = xyz
    return m


def main():
    asset = ASSETS['dra']
    source = trimesh.load(ROOT/asset['geometry'], force='scene', process=False)
    raw = {}
    for n in source.graph.nodes_geometry:
        node, key = source.graph[n]
        raw[n] = source.geometry[key].copy()
        raw[n].apply_transform(np.linalg.inv(asset['normalization_matrix']) @ node)
    references = ['large_reference_holder', 'large_PTFE_reference']
    fixed = trimesh.collision.CollisionManager()
    for n,mesh in raw.items():
        if n not in PARTS and n not in references:
            fixed.add_object(n, mesh)
    # Installed reference: optical face at the front of the reflectance port.
    turn = np.eye(4)
    turn[:3, :3] = Rotation.from_euler('z', np.pi).as_matrix()
    place = translation([0,-.122,.084]) @ turn @ translation([-.125,.085,-.034])
    reference = trimesh.collision.CollisionManager()
    for n in references:
        reference.add_object(n, raw[n], place)
    witness = trimesh.collision.CollisionManager()
    specimen = trimesh.load(ROOT/'assets/cooling_optical_specimens_v1/witness_white.glb', force='scene', process=False)
    place_witness = translation([0,-.122001,.084])
    place_witness[:3,:3] = Rotation.from_euler('x',np.pi/2).as_matrix()
    for n in specimen.graph.nodes_geometry:
        node,key = specimen.graph[n]
        witness.add_object(n, specimen.geometry[key], place_witness @ node)
    rigid = {n:solid_mesh(s) for n,s in solids().items()}
    exported = trimesh.load(OUT/'prepared_dra_candidate.glb',force='scene',process=False)
    reference_meshes = meshes(.014,rigid=rigid)
    export_error = 0.
    for n in PARTS:
        node,key = exported.graph[n]
        points = trimesh.transform_points(exported.geometry[key].vertices,
                   np.linalg.inv(asset['normalization_matrix']) @ node)
        assert points.shape == reference_meshes[n].vertices.shape
        export_error = max(export_error,float(np.max(abs(points-reference_meshes[n].vertices))))
    beam = trimesh.collision.CollisionManager()
    # A finite cylinder occupies the complete 16 mm aperture in front of the
    # cap; triangle edges/faces are tested, not just vertex radial distances.
    beam_mesh = trimesh.creation.cylinder(radius=.008, height=.070, sections=96)
    beam_pose = translation([0,-.150,.084])
    beam_pose[:3,:3] = Rotation.from_euler('x',np.pi/2).as_matrix()
    beam.add_object('reflectance_beam_corridor',beam_mesh,beam_pose)
    rows = []
    # The reference is retained until the clamp is withdrawn; parking follows
    # after it is supported by a hand. This review does not model that hand.
    cases = [('reference_release', gap, 0., reference) for gap in np.linspace(.014, MAX_GAP, 31)]
    cases += [('empty_park', MAX_GAP, a, None) for a in np.linspace(0,np.pi/2,46)]
    cases += [('witness_close', gap, 0., witness) for gap in np.linspace(MAX_GAP, .000611, 61)]
    for phase,gap,angle,sample in cases:
        current = meshes(float(gap), float(angle), rigid)
        moving = trimesh.collision.CollisionManager()
        for n,m in current.items():
            moving.add_object(n,m)
        _,pairs,contacts = moving.in_collision_internal(return_names=True,return_data=True)
        # The slider/arm is a fixed attached assembly. Pad/arm, coil/slider,
        # and coil/stop may touch at their explicit interface surfaces only.
        fixed_join = frozenset(['sample_clamp_arm','sample_clamp_slider'])
        allowed_touch = {frozenset(p) for p in [('sample_clamp_arm','sample_clamp_contact'),
                         ('sample_clamp_slider','sample_clamp_spring'),
                         ('sample_clamp_post','sample_clamp_spring')]}
        internal = []
        for c in contacts:
            pair = frozenset(c.names)
            if pair == fixed_join:
                continue
            if pair in allowed_touch and abs(float(c.depth)) <= 1e-7:
                continue
            internal.append(dict(parts=sorted(pair),depth_m=float(c.depth)))
        _,pairs,contacts = moving.in_collision_other(fixed,return_names=True,return_data=True)
        module = []
        for c in contacts:
            pair = frozenset(c.names)
            if pair == frozenset(['sample_clamp_post','sphere_cap_carrier']):
                # Threaded mounting into the fixed cap, not actuator clearance.
                continue
            module.append(dict(parts=sorted(pair),depth_m=float(c.depth)))
        sample_hits = []
        sample_gap = None
        if sample:
            _,pairs,contacts = moving.in_collision_other(sample,return_names=True,return_data=True)
            for c in contacts:
                pair = frozenset(c.names)
                backing = 'large_reference_holder' if phase=='reference_release' else 'copper_witness'
                if pair == frozenset(['sample_clamp_contact',backing]) and abs(float(c.depth)) <= 1e-7:
                    continue
                sample_hits.append(dict(parts=sorted(pair),depth_m=float(c.depth)))
            pad = trimesh.collision.CollisionManager()
            pad.add_object('pad', current['sample_clamp_contact'])
            sample_gap = float(pad.min_distance_other(sample))
        # Orthographic beam corridor through the 16 mm port must be unobscured
        # in the parked state; all moving vertices are outside its XZ radius.
        radial_min = min(float(np.hypot(m.vertices[:,0],m.vertices[:,2]-.084).min()) for m in current.values())
        pitch = (.033-gap-.0007)/6
        beam_hit = bool(moving.in_collision_other(beam)) if phase=='empty_park' and abs(angle-np.pi/2)<1e-9 else None
        rows.append(dict(phase=phase,gap_m=float(gap),angle_rad=float(angle),
            internal_intersections=internal,module_intersections=module,
            sample_intersections=sample_hits,pad_sample_gap_m=sample_gap,
            minimum_vertex_radius_about_port_m=radial_min,coil_pitch_m=float(pitch),parked_beam_obstructed=beam_hit))
    defects = [r for r in rows if any(r[k] for k in ['internal_intersections','module_intersections','sample_intersections'])]
    checks = dict(no_unexpected_intersections=not defects,
                  exported_reference_state_matches=export_error<1e-7,
                  reference_pad_reaches_backing=0<=rows[0]['pad_sample_gap_m']<1e-6,
                  specimen_pad_reaches_backing=0<=rows[-1]['pad_sample_gap_m']<1e-6,
                  reference_release_clearance=rows[30]['pad_sample_gap_m']>.0129,
                  parked_aperture_is_clear=rows[76]['parked_beam_obstructed'] is False,
                  coil_pitch_exceeds_wire_diameter=min(r['coil_pitch_m'] for r in rows)>.0007)
    report = dict(scope=__doc__,passed=all(checks.values()),checks=checks,maximum_export_vertex_error_m=export_error,
        source_geometry_sha256=hashlib.sha256((ROOT/asset['geometry']).read_bytes()).hexdigest(),
        candidate_geometry_sha256=hashlib.sha256((OUT/'prepared_dra_candidate.glb').read_bytes()).hexdigest(),
        samples=len(rows),failed_samples=len(defects),rows=rows,
        limitations=['Generated-state geometry only; exact mesh sweeps between samples not proved.',
                     'Spring stiffness, friction, retention, rotation control and hand access are unqualified.',
                     'The complete compartment and G1 are not included in this mechanism review.'],
        source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['cary_clamp.py','review_cary_clamp.py']})
    (OUT/'mechanism_review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],samples=len(rows),failed_samples=len(defects),first_failures=defects[:2])),flush=True)


if __name__ == '__main__':
    main()
