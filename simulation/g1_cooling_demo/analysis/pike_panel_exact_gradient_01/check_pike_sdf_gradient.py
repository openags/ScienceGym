"""Check recorded SDF normals against finite differences of the source surface."""
import argparse
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import numpy as np
import trimesh

from build_tool_station import sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('world', type=Path)
    parser.add_argument('surface_review', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    world, source, out = [p.resolve() for p in [args.world, args.surface_review, args.output]]
    review = json.loads((source/'review.json').read_text())
    assert review['passed_sampled_surface'] and sha(world) == review['world_sha256']
    assert sha(source/'samples.npz') == review['samples_sha256']
    xml = ET.parse(world).getroot()
    geom = xml.find(".//geom[@name='source_panel_visual']")
    mesh_path = Path(xml.find(".//mesh[@name='"+geom.get('mesh')+"']").get('file'))
    assert sha(mesh_path) == review['source_mesh_sha256']
    mesh = trimesh.load(mesh_path, force='mesh', process=True)
    mesh.apply_scale(1000.)
    samples = np.load(source/'samples.npz')
    labels = samples['labels']; distances = samples['exact_distances_m']
    eligible = np.flatnonzero(np.isin(labels, ['surface_offset_-2.5e-05', 'surface_offset_2.5e-05']) &
                             (abs(abs(distances)-.000025) < 1e-10))
    rng = np.random.default_rng(20261106)
    indices = rng.choice(eligible, min(96, len(eligible)), replace=False)
    points = samples['world_points'][indices]
    perturbation = 1e-7
    shifted = np.concatenate([points+sign*perturbation*np.eye(3)[axis]
                              for axis in range(3) for sign in [-1., 1.]])
    scaled = shifted*1000.
    unsigned = np.concatenate([trimesh.proximity.closest_point_naive(mesh, chunk)[1]/1000.
                               for chunk in np.array_split(scaled, 12)])
    signed = unsigned*np.where(mesh.contains(scaled), -1., 1.)
    signed = signed.reshape(3, 2, len(points))
    finite_difference = ((signed[:, 1]-signed[:, 0])/(2*perturbation)).T
    native = samples['gradients'][indices]
    errors = np.linalg.norm(finite_difference-native, axis=1)
    checks = dict(at_least_ninety_samples=len(indices) >= 90,
        finite_source_derivative=bool(np.isfinite(finite_difference).all()),
        unit_native_normal=bool(np.max(abs(np.linalg.norm(native, axis=1)-1.)) < 1e-10),
        gradient_agrees_with_source=bool(np.max(errors) < 1e-5))
    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, out/Path(__file__).name)
    np.savez_compressed(out/'samples.npz', indices=indices, points_m=points,
        source_finite_difference=finite_difference, native_gradients=native, errors=errors)
    result = dict(scope=__doc__, checks=checks, passed=all(checks.values()),
        sample_count=len(points), perturbation_m=perturbation, maximum_gradient_error=float(np.max(errors)),
        world_sha256=sha(world), source_review_sha256=sha(source/'review.json'),
        samples_sha256=sha(out/'samples.npz'), script_sha256=sha(__file__),
        qualified_robot_handling=False)
    (out/'review.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result), flush=True)
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
