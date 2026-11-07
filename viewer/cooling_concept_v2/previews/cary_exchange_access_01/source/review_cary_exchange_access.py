"""Check actuator/reference clearance inside the complete existing laboratory.

The reference is geometrically held in place while the clamp withdraws and
rotates, then follows a selected withdrawal corridor. A supporting hand is a
required precondition that this probe does not implement or qualify.
"""
import argparse
import hashlib
import json
import time
import numpy as np
import trimesh
from cary_clamp_scene import CaryClampScene, CANDIDATE
from cary_clamp import PARTS, MAX_GAP
from cary_access_scene import translation
from optical_choreography import HERE
from source_geometry import ROOT, ASSETS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trial', default='01')
    args = parser.parse_args()
    folder = HERE/'previews'/f'cary_exchange_access_{args.trial}'
    folder.mkdir(exist_ok=False)
    sources = {}
    for name in ['review_cary_exchange_access.py', 'cary_clamp_scene.py', 'cary_clamp.py',
                 'cary_access_scene.py', 'optical_delivery.py', 'optical_choreography.py',
                 'source_geometry.py', 'optical_setup.json', 'previews/cary_cover_carry_03.json']:
        data = (HERE/name).read_bytes()
        target = folder/'source'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        sources[name] = hashlib.sha256(data).hexdigest()
    start = time.monotonic()
    scene = CaryClampScene()
    cover = json.loads((HERE/'previews/cary_cover_carry_03.json').read_text())['rows'][-1]['cover_matrix']
    scene.set_access(lid=.15, cover=cover)
    candidate = scene.dra_source
    initial_error = 0.
    for name in PARTS:
        node, key = candidate.graph[name]
        installed = translation(ASSETS['dra']['position_m']) @ np.array(
            scene.setup['parts']['dra']['sphere_housing']['matrix']) @ node
        expected = trimesh.transform_points(candidate.geometry[key].vertices, installed)
        actual = trimesh.transform_points(scene.clamp_meshes[name].vertices, scene.clamp_poses[name])
        assert actual.shape == expected.shape, name
        initial_error = max(initial_error, float(np.max(abs(expected-actual))))
    cases = [('withdraw_clamp', float(g), 0., 0.) for g in np.linspace(.014, MAX_GAP, 31)]
    cases += [('rotate_clamp', MAX_GAP, float(a), 0.) for a in np.linspace(0, np.pi/2, 46)]
    cases += [('withdraw_supported_reference', MAX_GAP, np.pi/2, float(y)) for y in np.linspace(0, -.06, 31)]
    rows = []
    for phase, gap, angle, offset in cases:
        scene.set_clamp(gap, angle)
        scene.set_reference(translation([0, offset, 0]))
        row = dict(phase=phase, gap_m=gap, angle_rad=angle, reference_offset_y_m=offset,
            clamp_intersections=scene.clamp_clearance(),
            reference_intersections=scene.reference_clearance(),
            nominal_clamp_seating=scene.last_clamp_bounded_contacts,
            nominal_reference_seating=scene.last_reference_bounded_contacts)
        rows.append(row)
    failures = [r for r in rows if r['clamp_intersections'] or r['reference_intersections']]
    report = dict(scope=__doc__, passed=not failures and initial_error < 1e-7,
        samples=len(rows), failed_samples=len(failures),
        initial_candidate_vertex_error_m=initial_error, lid_opening_m=.15, cover_matrix=cover,
        rows=rows, seconds=time.monotonic()-start, source_sha256=sources,
        geometry_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
                        for p in [CANDIDATE, scene.cary_geometry]},
        inherited_scene='audits/optical_exchange_01/export.json',
        inherited_scene_sha256=hashlib.sha256((HERE/'audits/optical_exchange_01/export.json').read_bytes()).hexdigest(),
        limitations=['Sampled geometric corridors; no supporting robot hands or trajectory.',
                     'No contact forces, balance, enclosure closure, measurement or complete workflow qualification.',
                     'The 150 mm operating opening is an inference, not a manufacturer travel specification.'])
    (folder/'review.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'], samples=len(rows), failed_samples=len(failures),
        maximum_initial_vertex_error_m=initial_error, first_failures=failures[:2], seconds=report['seconds'])), flush=True)
    if not report['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
