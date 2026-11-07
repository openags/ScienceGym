"""Build a separate, mechanically explicit Cary sample-clamp candidate.

No laboratory asset or accepted playback is replaced here. The saved asset is
at the installed reference thickness (14 mm); dynamic states are generated
from cary_clamp.py. Neither force retention nor robot access is qualified.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
import trimesh
from cary_clamp import PARTS, MAX_GAP, solids, solid_mesh, meshes
from source_geometry import ROOT, ASSETS

HERE = Path(__file__).resolve().parent
OUT = ROOT/'assets/cary_internal_dra_2500_v1/revisions/working_clamp'
MANUAL = 'https://mmrc.caltech.edu/Cary%20UV-Vis%20Int.Sphere/manuals/Cary%20manuals/4000_5000_6000i_Internal%20DRA.pdf'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    asset = ASSETS['dra']
    path = ROOT/asset['geometry']
    assert sha(path) == asset['geometry_sha256']
    original = trimesh.load(path, force='scene', process=False)
    normal = np.array(asset['normalization_matrix'])
    before = {n:(original.graph[n][0].copy(),
                 original.geometry[original.graph[n][1]].vertices.copy())
              for n in original.graph.nodes_geometry}
    rigid = {n:solid_mesh(s) for n,s in solids().items()}
    named = dict(reference_closed=(.014, 0.), witness_closed=(.000611, 0.),
                 pulled_clear=(MAX_GAP, 0.), parked_for_zero=(MAX_GAP, np.pi/2))
    for state, (gap, angle) in named.items():
        working = meshes(gap, angle, rigid)
        preview = trimesh.Scene()
        for name, mesh in working.items():
            assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0, name
            _, key = original.graph[name]
            mesh.visual = trimesh.visual.TextureVisuals(material=original.geometry[key].visual.material.copy())
            preview.add_geometry(mesh, node_name=name)
        (OUT/(state+'.glb')).write_bytes(preview.export(file_type='glb'))
    for name, mesh in meshes(.014, rigid=rigid).items():
        node, key = original.graph[name]
        mesh.visual = trimesh.visual.TextureVisuals(material=original.geometry[key].visual.material.copy())
        mesh.apply_transform(np.linalg.inv(node) @ normal)
        original.geometry[key] = mesh
    output = OUT/'prepared_dra_candidate.glb'
    output.write_bytes(original.export(file_type='glb'))
    after = trimesh.load(output, force='scene', process=False)
    assert set(after.graph.nodes_geometry) == set(before)
    errors = {}
    for name,(node,vertices) in before.items():
        if name in PARTS:
            continue
        new_node, key = after.graph[name]
        a = trimesh.transform_points(vertices, node)
        b = trimesh.transform_points(after.geometry[key].vertices, new_node)
        assert a.shape == b.shape
        errors[name] = float(np.max(np.abs(a-b)))
    assert max(errors.values()) < 1e-6
    report = dict(scope=__doc__, status='candidate_not_integrated',
        manufacturer_CAD=False, contact_qualified=False,
        manufacturer_source=dict(url=MANUAL,
            cached_pdf_sha256='d5a5f26ba53b9c00418e18ab34eb670e7584b0a273c9fad4b573fb11db07330a',
            evidence=['Standard sample-holder kit identifies a spring clip and round post.',
                      'Installation step 9 places the clamp on the post in the sphere cap.',
                      'Reflectance operation requires a retained reference, then a retained flat sample.',
                      'Zero baseline uses the uncovered reflectance port inside the closed extension.']),
        diagnosis=['The existing installed reference clamp has a static 19 mm offset; its pad reaches the 14 mm reference backing.',
                   'Its spring, guide bore, closing travel and clear-port parking motion were unresolved.',
                   'The old spring between cap and slider would push an unlatched compression slider away from the sample.'],
        inference=dict(guide_radius_m=.003, bore_radius_m=.00315,
            travel_m=MAX_GAP, parked_angle_rad=float(np.pi/2),
            spring_wire_radius_m=.00035, spring_mean_radius_m=.0042,
            spring_turns=6, spring_position='between distal fixed stop and slider',
            slider_arm_connection='fixed overlapping welded/attached joint; not a sliding collision',
            reference_gap_m=.014, witness_backing_gap_m=.000611,
            witness_basis='Existing optical carrier bottom is 1 um outside port; copper rear face is 0.61 mm from carrier bottom.',
            limits='Local dimensions, bearing fit, spring section, rotation and available actuation clearance are reconstruction choices, not manufacturer specifications.'),
        unchanged_source_parts=len(errors), maximum_unchanged_vertex_error_m=max(errors.values()),
        source_geometry=str(path.relative_to(ROOT)), source_geometry_sha256=sha(path),
        candidate_geometry=str(output.relative_to(ROOT)), candidate_geometry_sha256=sha(output),
        generator_sha256={n:sha(HERE/n) for n in ['cary_clamp.py','build_cary_clamp_candidate.py']},
        geometry_review='mechanism_review.json (generated separately by review_cary_clamp.py)',
        remaining=['Robot hand grasp and bimanual reference/specimen exchange',
                   'Full compartment/lid clearance', 'Retention force, friction and dynamic qualification',
                   'Protective storage for removed PTFE reference', 'Complete optical acquisition sequence'])
    (OUT/'revision.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['status','unchanged_source_parts','maximum_unchanged_vertex_error_m','candidate_geometry_sha256']}))


if __name__ == '__main__':
    main()
