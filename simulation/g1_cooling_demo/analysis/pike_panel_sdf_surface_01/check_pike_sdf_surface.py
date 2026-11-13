"""Compare the native panel SDF against its source triangle surface.

Read-only queries to the public MuJoCo C API. No collision callbacks, force
changes, state edits during dynamics, or modified distance coefficients.
Finite surface samples do not qualify arbitrary robot trajectories.
"""
import argparse
import ctypes as ct
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
import trimesh

from build_tool_station import sha


class SDF(ct.Structure):
    # mjplugin.h: mjSDF. The current installed public ABI uses double mjtNum.
    _fields_ = [('plugin', ct.POINTER(ct.c_void_p)), ('id', ct.POINTER(ct.c_int)),
                ('type', ct.c_int), ('relpos', ct.POINTER(ct.c_double)),
                ('relmat', ct.POINTER(ct.c_double)), ('geomtype', ct.POINTER(ct.c_int))]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('world', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    world, out = args.world.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, out/Path(__file__).name)
    model = mujoco.MjModel.from_xml_path(str(world))
    data = mujoco.MjData(model)
    mujoco.mj_kinematics(model, data)
    gid = model.geom('source_panel_visual').id
    mid = int(model.geom_dataid[gid])
    if model.geom_type[gid] != int(mujoco.mjtGeom.mjGEOM_SDF) or model.mesh_octadr[mid] < 0:
        raise ValueError('Expected a compiled native mesh SDF')
    xml = ET.parse(world).getroot()
    geom = xml.find(".//geom[@name='source_panel_visual']")
    mesh_path = Path(xml.find(".//mesh[@name='"+geom.get('mesh')+"']").get('file'))
    if not mesh_path.is_absolute():
        mesh_path = world.parent/mesh_path
    source = trimesh.load(mesh_path, force='mesh', process=True)
    if not source.is_volume:
        raise ValueError('Signed distance oracle requires a closed source surface')
    if geom.get('pos', '0 0 0') != '0 0 0' or geom.get('quat', '1 0 0 0') != '1 0 0 0':
        raise ValueError('This source-coordinate audit expects the untransformed component panel')
    libraries = list(Path(mujoco.__file__).parent.glob('libmujoco.so.*'))
    if len(libraries) != 1:
        raise ValueError('Cannot uniquely identify the loaded engine library')
    library = ct.CDLL(str(libraries[0]))
    library.mjc_distance.argtypes = [ct.c_void_p, ct.c_void_p, ct.POINTER(SDF), ct.POINTER(ct.c_double)]
    library.mjc_distance.restype = ct.c_double
    library.mjc_gradient.argtypes = [ct.c_void_p, ct.c_void_p, ct.POINTER(SDF),
                                    ct.POINTER(ct.c_double), ct.POINTER(ct.c_double)]
    library.mjc_gradient.restype = None
    plugins = (ct.c_void_p*1)(None)
    ids = (ct.c_int*1)(mid)
    types = (ct.c_int*1)(int(mujoco.mjtGeom.mjGEOM_SDF))
    sdf = SDF(plugins, ids, int(mujoco.mjtSDFType.mjSDFTYPE_SINGLE), None, None, types)
    rotation = data.geom_xmat[gid].reshape(3, 3)
    translation = data.geom_xpos[gid]
    rng = np.random.default_rng(20261106)
    faces = rng.choice(len(source.faces), 512, p=source.area_faces/source.area)
    u = np.sqrt(rng.random(512)); v = rng.random(512)
    weights = np.c_[1-u, u*(1-v), u*v]
    surface = np.einsum('ni,nij->nj', weights, source.triangles[faces])
    points = []; labels = []
    for delta in [-.0001, -.000025, -.000005, .000005, .000025, .0001]:
        points.extend(surface+delta*source.face_normals[faces])
        labels.extend(['surface_offset_'+str(delta)]*len(surface))
    top, bottom = source.bounds[1, 2], source.bounds[0, 2]
    for radius in [0., .004, .0085, .0095, .011, .020, .024]:
        for angle in np.linspace(0., 2*np.pi, 32, endpoint=False):
            for z in [(top+bottom)/2, top-.00002, top+.00002]:
                points.append([.04+radius*np.cos(angle), -.01+radius*np.sin(angle), z])
                labels.append('bore' if radius <= .0085 else 'annulus')
    points = np.asarray(points)
    exact = -trimesh.proximity.signed_distance(source, points)
    native = []; gradients = []
    for point in points:
        local = np.ascontiguousarray((point-translation)@rotation, dtype=np.float64)
        gradient = np.empty(3, dtype=np.float64)
        distance = library.mjc_distance(model._address, data._address, ct.byref(sdf),
            local.ctypes.data_as(ct.POINTER(ct.c_double)))
        library.mjc_gradient(model._address, data._address, ct.byref(sdf),
            gradient.ctypes.data_as(ct.POINTER(ct.c_double)),
            local.ctypes.data_as(ct.POINTER(ct.c_double)))
        native.append(distance); gradients.append(rotation@gradient)
    native = np.asarray(native); gradients = np.asarray(gradients)
    error = np.abs(native-exact)
    away = abs(exact) > .000005
    mismatched = away & (np.sign(native) != np.sign(exact))
    bore = np.asarray(labels) == 'bore'
    checks = dict(finite=bool(np.isfinite(native).all() and np.isfinite(gradients).all()),
        source_surface_error_below_five_micrometres=bool(np.max(error) <= .000005),
        signs_match_away_from_boundary=not bool(np.any(mismatched)),
        source_aperture_remains_open=bool(np.all(native[bore] > 0)))
    np.savez_compressed(out/'samples.npz', world_points=points, exact_distances_m=exact,
        native_distances_m=native, gradients=gradients, labels=np.asarray(labels))
    worst = np.argsort(error)[-12:][::-1]
    report = dict(scope=__doc__, passed_sampled_surface=all(checks.values()), checks=checks,
        sample_count=len(points), maximum_distance_error_m=float(np.max(error)),
        sign_mismatch_count=int(np.sum(mismatched)), bore_sample_count=int(np.sum(bore)),
        minimum_bore_clearance_m=float(np.min(native[bore])),
        worst_samples=[dict(point_m=points[i].tolist(), label=labels[i],
            source_distance_m=float(exact[i]), native_distance_m=float(native[i]),
            absolute_error_m=float(error[i])) for i in worst],
        world_sha256=sha(world), source_mesh_sha256=sha(mesh_path), samples_sha256=sha(out/'samples.npz'),
        engine_version=mujoco.__version__, engine_library_sha256=sha(libraries[0]),
        public_header_sha256={n: sha(Path(mujoco.__file__).parent/'include/mujoco'/n)
                             for n in ['mujoco.h', 'mjplugin.h', 'mjtype.h']},
        script_sha256=sha(__file__), qualified_robot_handling=False)
    (out/'review.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ['passed_sampled_surface', 'sample_count',
        'maximum_distance_error_m', 'sign_mismatch_count', 'minimum_bore_clearance_m']}), flush=True)
    if not report['passed_sampled_surface']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
