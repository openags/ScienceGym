"""Retain all official L200/M STEP solids in a local metric inspection mesh."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import tempfile

import cadquery as cq
import numpy as np
import trimesh
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.GeomAbs import GeomAbs_Cylinder
from OCP.StlAPI import StlAPI_Writer
from trimesh.visual.material import PBRMaterial

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def artifact(path):
    return dict(path=str(path.relative_to(ROOT)), sha256=sha(path))


def frame(solids):
    # Use the plate centre and bottom bearing plane, not the protruding screw's
    # asymmetric assembly bounding box. Only rotation, translation and mm->m.
    top = solids[0].BoundingBox()
    bottom = solids[1].BoundingBox()
    out = np.array([[1., 0, 0, -(top.xmin + top.xmax) / 2],
                    [0, 0, -1., (top.zmin + top.zmax) / 2],
                    [0, 1., 0, -bottom.ymin], [0, 0, 0, 1.]])
    out[:3, :] *= .001
    return out


def cylinder_features(solid, matrix):
    features = []
    for face in solid.Faces():
        surface = BRepAdaptor_Surface(face.wrapped)
        if surface.GetType() != GeomAbs_Cylinder:
            continue
        cylinder = surface.Cylinder()
        p = cylinder.Axis().Location()
        d = cylinder.Axis().Direction()
        point = matrix @ np.array([p.X(), p.Y(), p.Z(), 1])
        axis = matrix[:3, :3] @ np.array([d.X(), d.Y(), d.Z()]) * 1000
        features.append(dict(radius_m=cylinder.Radius() * .001,
                             axis_origin_m=point[:3].tolist(), axis=axis.tolist()))
    return features


def close_collinear_seams(mesh):
    """Make adjacent CAD tessellation edges conform; never cap a real hole.

    An edge A--C sometimes faces two edges A--B--C with B on the same line.
    Split the existing incident triangle at B. No vertex is added or moved.
    Noncollinear openings remain untouched and cause the caller to fail.
    """
    vertices = mesh.vertices.copy()
    area, volume = mesh.area, mesh.volume
    changes = []
    for _ in range(100):
        boundary = mesh.edges_unique[np.bincount(mesh.edges_unique_inverse) == 1]
        candidates = np.unique(boundary)
        cut = False
        for a, b in boundary:
            vector = mesh.vertices[b] - mesh.vertices[a]
            length = np.linalg.norm(vector)
            t = (mesh.vertices[candidates] - mesh.vertices[a]) @ vector / length ** 2
            distance = np.linalg.norm(mesh.vertices[candidates] - mesh.vertices[a] - t[:, None] * vector, axis=1)
            middle = candidates[(t > 1e-6) & (t < 1 - 1e-6) & (distance < 1e-7)]
            if not len(middle):
                continue
            p = int(middle[0])
            incident = np.flatnonzero((mesh.faces == a).any(axis=1) & (mesh.faces == b).any(axis=1))
            if len(incident) != 1:
                raise ValueError('Ambiguous CAD seam incidence')
            j = int(incident[0])
            face = mesh.faces[j]
            ai, bi = int(np.flatnonzero(face == a)[0]), int(np.flatnonzero(face == b)[0])
            c = int(face[(set(range(3)) - {ai, bi}).pop()])
            if (ai + 1) % 3 != bi:
                a, b = b, a
            faces = mesh.faces.tolist()
            faces[j] = [int(a), p, c]
            faces.append([p, int(b), c])
            mesh.faces = faces
            changes.append(dict(edge_vertices=[int(a), int(b)], existing_middle_vertex=p,
                                collinearity_error_mm=float(distance[np.flatnonzero(candidates == p)[0]])))
            cut = True
            break
        if not cut:
            break
    if not np.array_equal(vertices, mesh.vertices) or abs(mesh.area - area) > 1e-7 or abs(mesh.volume - volume) > 1e-6:
        raise ValueError('A seam repair changed source geometry')
    return dict(splits=len(changes), changes=changes, vertices_moved=0,
                area_delta_mm2=float(mesh.area - area), volume_delta_mm3=float(mesh.volume - volume))


def build():
    source = json.loads((HERE / 'sources.json').read_text())
    for entry in source['files']:
        path = HERE / entry['path']
        if not path.is_file():
            raise FileNotFoundError('Run assets/thorlabs_l200_v1/fetch_sources.py first: ' + str(path))
        if sha(path) != entry['sha256']:
            raise ValueError('Source revision mismatch: ' + str(path))
    source_path = HERE / source['files'][0]['path']
    solids = cq.importers.importStep(str(source_path)).val().Solids()
    if len(solids) != 86:
        raise ValueError('Unexpected official STEP solid count')
    matrix = frame(solids)
    scene = trimesh.Scene()
    rejected = trimesh.Scene()
    records = []
    with tempfile.TemporaryDirectory(prefix='sciencegym-l200-') as temporary:
        for i, solid in enumerate(solids):
            # Absolute 30 um tessellation avoids CadQuery's default relative
            # deflection. Keep the source BRep and every disconnected solid.
            mesher = BRepMesh_IncrementalMesh(solid.wrapped, .03, False, .12, False)
            mesher.Perform()
            path = Path(temporary) / f'{i}.stl'
            if not StlAPI_Writer().Write(solid.wrapped, str(path)):
                raise ValueError('STEP tessellation failed: ' + str(i))
            mesh = trimesh.load(path, force='mesh')
            raw_faces = len(mesh.faces)
            mesh.merge_vertices(digits_vertex=4)  # 0.1 um in source mm units
            mesh.update_faces(mesh.nondegenerate_faces())
            mesh.update_faces(mesh.unique_faces())
            mesh.remove_unreferenced_vertices()
            identity = f'L200_M__solid_{i:03d}'
            raw_watertight = mesh.is_watertight
            if not raw_watertight:
                failed = mesh.copy()
                failed.apply_transform(matrix)
                rejected.add_geometry(failed, node_name=identity, geom_name=identity)
            seam_repair = close_collinear_seams(mesh)
            if not mesh.is_watertight:
                raise ValueError('Nonconforming source tessellation remains: ' + identity)
            mesh.apply_transform(matrix)
            # glTF stores float32 positions; record the actual delivery geometry.
            mesh.vertices = mesh.vertices.astype(np.float32)
            group = 'upper_plate' if i == 0 else 'lower_plate' if i == 1 else 'pantograph_links' if 2 <= i <= 17 else 'adjuster' if i == 19 else 'bearing_blocks' if i in [18, 39, 40, 41] else 'pins_and_hardware'
            color = [12, 13, 16, 255] if group in ['upper_plate', 'lower_plate', 'bearing_blocks', 'pantograph_links'] else [158, 163, 170, 255]
            material = PBRMaterial(
                name='authored_' + group, baseColorFactor=color, metallicFactor=.68,
                roughnessFactor=.32 if group == 'pins_and_hardware' else .44)
            record = dict(id=identity, source_solid_index=i, display_group=group,
                          step_valid=solid.isValid(), step_volume_m3=solid.Volume() * 1e-9,
                          mesh_volume_m3=float(mesh.volume), bounds_m=mesh.bounds.tolist(),
                          faces=len(mesh.faces), raw_faces=raw_faces,
                          raw_tessellation_watertight=raw_watertight, seam_repair=seam_repair,
                          watertight=mesh.is_watertight, winding_consistent=mesh.is_winding_consistent)
            if i in [0, 1, 19]:
                record['cylindrical_faces'] = cylinder_features(solid, matrix)
            records.append(record)
            # Split render normals at hard CAD edges. Averaging hole-wall
            # normals into the flat plate makes the real plate look embossed.
            # This changes vertex sharing only; topology findings above refer
            # to the welded triangles, not these intentional shading seams.
            render_mesh = trimesh.graph.smooth_shade(mesh, angle=np.radians(25), facet_minarea=100)
            render_mesh.metadata.pop('original_components', None)
            render_mesh.visual = trimesh.visual.TextureVisuals(material=material)
            scene.add_geometry(render_mesh, node_name=identity, geom_name=identity)
    geometry = HERE / 'geometry' / 'L200_M.glb'
    geometry.parent.mkdir(exist_ok=True)
    geometry.write_bytes(scene.export(file_type='glb', include_normals=True))
    rejected_path = geometry.parent / 'L200_M_unrepaired.glb'
    rejected_path.write_bytes(rejected.export(file_type='glb'))
    # Detect genuinely repeated source geometry, not just similar nuts at
    # different placements. No source solid is silently removed or combined.
    repeats = []
    for i, a in enumerate(records):
        for j, b in enumerate(records[:i]):
            if not np.allclose(a['bounds_m'], b['bounds_m'], atol=1e-8, rtol=0):
                continue
            if abs(a['step_volume_m3'] - b['step_volume_m3']) > 1e-14:
                continue
            common = solids[i].intersect(solids[j]).Volume() * 1e-9
            if abs(common / a['step_volume_m3'] - 1) < 1e-6:
                repeats.append(dict(parts=[b['id'], a['id']], common_volume_m3=common))
    result = dict(schema_version=1, candidate=source['selected_candidate'], accepted=False,
                  scope='Official source geometry in its retracted pose; static asset inspection only',
                  geometry={**artifact(geometry), 'parts': len(records), 'bounds_m': scene.bounds.tolist(),
                            'axes': '+Z up, SI metres; plate centre XY, bottom bearing plane Z=0'},
                  source_to_scene_matrix=matrix.tolist(), source_length_unit='mm',
                  source_pose_height_m=records[0]['bounds_m'][1][2],
                  parts=records, coincident_source_solids=repeats,
                  rejected_tessellation={**artifact(rejected_path), 'parts': list(rejected.geometry),
                                         'reason': 'Collinear T-junctions in raw tessellation; retained before edge subdivision'},
                  tessellation=dict(linear_deflection_mm=.03, angular_deflection_rad=.12,
                                    vertex_weld_mm=.0001, source_shape_repaired=False,
                                    render_normal_split_degrees=25,
                                    topology_scope='Welded geometry; render-normal seams do not count as physical openings',
                                    seam_repair='Split existing edges at existing collinear vertices; no new or moved vertices, no hole filling',
                                    ocp_version=importlib.metadata.version('cadquery-ocp')),
                  inspection_groups={g: [p['id'] for p in records if p['display_group'] == g]
                                     for g in sorted({p['display_group'] for p in records})},
                  collision_or_dynamics_qualified=False, physical_installation_qualified=False,
                  limitations=source['open_requirements'],
                  source_artifacts=[artifact(p) for p in [Path(__file__), HERE / 'fetch_sources.py',
                                    HERE / 'sources.json', *[HERE / e['path'] for e in source['files']]]])
    (HERE / 'model.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(solids=len(records), faces=sum(p['faces'] for p in records),
                         open_meshes=[p['id'] for p in records if not p['watertight']],
                         coincident_source_pairs=len(repeats))))


if __name__ == '__main__':
    build()
