"""Build a source-surface SDF plugin with exact triangle distances.

The occupancy test is justified only for the pinned convex outer panel with
one polygonal through-bore. Geometry tests must pass before runtime adoption.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
from scipy.spatial import ConvexHull
import trimesh

from build_tool_station import absolve_assets, sha


def c_array(array):
    array = np.asarray(array)
    if array.ndim == 0:
        return format(float(array), '.17g')
    return '{'+','.join(c_array(x) for x in array)+'}'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    source, out = a.source.resolve(), a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, out/Path(__file__).name)
    cpp = Path(__file__).with_name('pike_surface_sdf.cc')
    shutil.copyfile(cpp, out/cpp.name)
    world = source/'world.xml'
    xml = ET.parse(world).getroot()
    absolve_assets(xml, world)
    geom = xml.find(".//geom[@name='source_panel_visual']")
    mesh_path = Path(xml.find(".//mesh[@name='"+geom.get('mesh')+"']").get('file'))
    mesh = trimesh.load(mesh_path, force='mesh', process=True)
    if not mesh.is_volume:
        raise ValueError('Source panel must be a closed surface')
    outer = ConvexHull(mesh.vertices)
    xy = mesh.vertices[:, :2]
    radius = np.linalg.norm(xy-[.04, -.01], axis=1)
    bore_points = np.unique(xy[abs(radius-.009) < 1e-7], axis=0)
    bore = ConvexHull(bore_points)
    difference_volume = outer.volume-bore.volume*np.ptp(mesh.vertices[:, 2])
    if abs(difference_volume-mesh.volume) > mesh.volume*1e-6:
        raise ValueError('Source solid differs from the declared convex shell minus through bore')
    baseline = mujoco.MjModel.from_xml_path(str(world))
    data = mujoco.MjData(baseline); mujoco.mj_kinematics(baseline, data)
    gid = baseline.geom('source_panel_visual').id
    rotation = data.geom_xmat[gid].reshape(3, 3)
    translation = data.geom_xpos[gid]
    triangles = (mesh.triangles-translation)@rotation
    normals = mesh.face_normals@rotation
    if np.any(mesh.area_faces < 1e-18):
        raise ValueError('Degenerate source triangle')
    ordered = []; nodes = []

    def split(ids):
        points = triangles[ids].reshape(-1, 3)
        node = dict(lo=points.min(axis=0), hi=points.max(axis=0), left=-1, right=-1, first=-1, count=0)
        index = len(nodes); nodes.append(node)
        if len(ids) <= 8:
            node.update(first=len(ordered), count=len(ids)); ordered.extend(ids)
        else:
            centers = triangles[ids].mean(axis=1)
            axis = int(np.argmax(np.ptp(centers, axis=0)))
            order = np.argsort(centers[:, axis], kind='stable'); half = len(order)//2
            node['left'] = split(ids[order[:half]])
            node['right'] = split(ids[order[half:]])
        return index

    split(np.arange(len(triangles)))
    name = 'sciencegym.sdf.pike_panel_'+sha(mesh_path)[:12]
    header = 'static constexpr char kPluginName[]="'+name+'";\n'
    header += 'static constexpr Vec kTriangles[][3]='+c_array(triangles[ordered])+';\n'
    header += 'static constexpr Vec kFaceNormals[]='+c_array(normals[ordered])+';\n'
    header += 'static constexpr double kRotation[3][3]='+c_array(rotation)+';\n'
    header += 'static constexpr double kTranslation[3]='+c_array(translation)+';\n'
    header += 'static constexpr double kOuterPlanes[][4]='+c_array(outer.equations)+';\n'
    header += 'static constexpr double kBorePlanes[][3]='+c_array(bore.equations)+';\n'
    header += 'static constexpr Node kNodes[]={'+','.join(
        '{'+c_array(n['lo'])+','+c_array(n['hi'])+','+','.join(str(n[k]) for k in ['left','right','first','count'])+'}'
        for n in nodes)+'};\n'
    hp = out/'pike_surface_geometry.h'; hp.write_text(header)
    package = Path(mujoco.__file__).parent
    libraries = list(package.glob('libmujoco.so.*'))
    if len(libraries) != 1:
        raise ValueError('Engine library is ambiguous')
    library = out/'libsciencegym_pike_surface.so'
    command = ['g++', '-std=c++17', '-O3', '-shared', '-fPIC', '-Wall', '-Wextra',
               '-I'+str(package/'include'), str(out/cpp.name), str(libraries[0]),
               '-Wl,-rpath,'+str(package), '-o', str(library)]
    compile_result = subprocess.run(command, capture_output=True, text=True)
    (out/'build.log').write_text(compile_result.stdout+compile_result.stderr)
    compile_result.check_returncode()
    mujoco.mj_loadPluginLibrary(str(library))
    extension = xml.find('extension')
    if extension is None:
        extension = ET.SubElement(xml, 'extension')
    plugin = ET.SubElement(extension, 'plugin', plugin=name)
    ET.SubElement(plugin, 'instance', name='source_panel_exact_surface')
    ET.SubElement(geom, 'plugin', instance='source_panel_exact_surface')
    ET.indent(xml)
    ET.ElementTree(xml).write(out/'world.xml', encoding='unicode')
    compiled = mujoco.MjModel.from_xml_path(str(out/'world.xml'))
    for field in ['body_mass', 'body_inertia', 'body_ipos', 'body_iquat', 'qpos0']:
        if not np.array_equal(getattr(compiled, field), getattr(baseline, field)):
            raise ValueError('Plugin unexpectedly changed '+field)
    if not np.allclose(compiled.geom_pos[compiled.geom('source_panel_visual').id], baseline.geom_pos[gid], atol=1e-14, rtol=0):
        raise ValueError('Plugin changed the panel coordinate frame')
    receipt = dict(scope=__doc__, plugin_name=name, library=str(library), library_sha256=sha(library),
        world_sha256=sha(out/'world.xml'), source_world_sha256=sha(world), source_mesh_sha256=sha(mesh_path),
        source_triangles=len(triangles), bvh_nodes=len(nodes),
        exact_source_volume_m3=float(mesh.volume), occupancy_volume_m3=float(difference_volume),
        source_vertices_and_faces_unchanged=True, inertial_parameters_unchanged=True,
        source_to_compiled_rotation=rotation.tolist(), source_to_compiled_translation=translation.tolist(),
        source_sha256={x.name: sha(x) for x in [out/Path(__file__).name, out/cpp.name, hp]},
        build_command=command, compiler_version=subprocess.check_output(['g++','--version'],text=True).splitlines()[0],
        mujoco_version=mujoco.__version__, engine_sha256=sha(libraries[0]),
        qualified_surface_accuracy=False, qualified_support=False, qualified_robot_handling=False)
    (out/'plugin.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps({k:receipt[k] for k in ['plugin_name','source_triangles','bvh_nodes','library_sha256']}))


if __name__ == '__main__':
    main()
