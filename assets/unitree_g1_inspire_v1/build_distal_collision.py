"""Conforming right distal-finger collision exteriors from official CAD meshes.

Visual meshes, body inertia and joint limits are unchanged. A sealed internal
void may be filled for collision only after proving at least 1 mm of external
wall separation. Index-2 receives 1 micrometre bounded simplification before
tetrahedralization. Auxiliary faces and measured surface deviation are screened
within 2 micrometres. The candidates still require compiled contact review.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import trimesh
import fcl
import manifold3d

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'simulation/g1_cooling_demo'))
from convex_cells import clean, decompose


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def surface_distance(mesh,points):
    # Trimesh's absolute triangle tolerances misclassify small CAD triangles
    # at metre scale (even identity samples). Millimetre evaluation retains
    # the geometry and returns distances in metres.
    scaled=mesh.copy();scaled.apply_scale(1000.)
    return trimesh.proximity.closest_point(scaled,np.asarray(points)*1000.)[1]/1000.


def build(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);records=[]
    for link in ['right_thumb_4','right_index_2']:
        source=HERE/'vendor/unitree_ros/meshes'/(link+'.STL')
        raw=trimesh.load(source,force='mesh');mesh=clean(raw);components=mesh.split(only_watertight=False)
        solids=[p for p in components if p.is_watertight and len(p.faces)>20 and abs(p.volume)>1e-10]
        auxiliary=[p for p in components if all(p is not q for q in solids)]
        external=[p for p in solids if p.volume>0]
        if len(external)!=1:raise ValueError('Expected one closed exterior shell: '+link)
        exterior=external[0];sealed=[]
        for p in solids:
            if p.volume>=0:continue
            manager=trimesh.collision.CollisionManager();manager.add_object('outer',exterior);manager.add_object('inner',p)
            result=fcl.DistanceResult();fcl.distance(manager._objs['outer']['obj'],manager._objs['inner']['obj'],fcl.DistanceRequest(),result)
            gap=float(result.min_distance)
            if gap<.001 or not exterior.contains(p.vertices).all():raise ValueError('An inner shell is not safely sealed below the collision exterior')
            sealed.append(dict(surface_gap_to_exterior_m=gap,void_volume_m3=float(-p.volume),faces=len(p.faces)))
        tolerance=1e-6 if link=='right_index_2' else 0.
        core=exterior.copy()
        if tolerance:
            solid=manifold3d.Manifold(manifold3d.Mesh64(vert_properties=np.asarray(core.vertices),tri_verts=np.asarray(core.faces,dtype=np.uint64)))
            simplified=solid.simplify(tolerance).to_mesh64()
            core=trimesh.Trimesh(np.asarray(simplified.vert_properties)[:,:3],np.asarray(simplified.tri_verts),process=False)
        if not core.is_volume:raise ValueError('Collision exterior is not a closed solid: '+link)
        points=np.vstack([p.vertices for p in auxiliary]) if auxiliary else np.empty((0,3))
        distance=surface_distance(core,points) if len(points) else np.array([])
        outside=distance[~core.contains(points)] if len(points) else np.array([])
        maximum=float(max(outside,default=0.))
        if maximum>2e-6:raise ValueError('Auxiliary source surface is outside the retained shells')
        if abs(core.volume-exterior.volume)>max(1e-14,abs(exterior.volume)*2e-6):raise ValueError('Exterior volume changed excessively')
        deviations=[]
        for first,second in [(exterior,core),(core,exterior)]:
            samples=np.vstack([first.vertices,first.triangles_center,first.vertices[first.edges_unique].mean(axis=1)])
            deviations.append(float(surface_distance(second,samples).max()))
        if max(deviations)>2e-6:raise ValueError('Measured exterior deviation exceeds 2 micrometres')
        print('decompose',link,'faces',len(core.faces),'sealed_voids',len(sealed),'surface_deviation_m',deviations,flush=True)
        cells=decompose(core);dest=out/link;dest.mkdir();pieces=[];volume=0.
        for i,cell in enumerate(cells):
            path=dest/f'{i:05d}.stl';cell.export(path)
            compiled=trimesh.load(path,force='mesh').convex_hull
            if not compiled.is_volume:raise ValueError('Serialized cell is not a solid')
            compiled.export(path);volume+=compiled.volume
            pieces.append(dict(path=str(path.relative_to(HERE)),sha256=sha(path)))
        error=abs(volume-core.volume)/core.volume
        if error>2e-5:raise ValueError('Serialized cell volume differs from the source solid')
        records.append(dict(link=link,source_path=str(source.relative_to(HERE)),source_sha256=sha(source),
                            source_volume_m3=float(mesh.volume),source_exterior_volume_m3=float(exterior.volume),collision_volume_m3=float(core.volume),
                            cell_volume_sum_m3=float(volume),relative_serialized_volume_error=float(error),
                            sealed_voids_filled_for_collision_only=sealed,simplification_tolerance_m=tolerance,
                            maximum_sampled_bidirectional_exterior_deviation_m=deviations,auxiliary_components=len(auxiliary),
                            maximum_omitted_surface_outside_distance_m=maximum,pieces=pieces))
        print('packaged',link,'pieces',len(pieces),flush=True)
    report=dict(schema_version=1,method='Source exterior PLC, sealed interior-void fill, optional micrometre simplification, and volume-preserving convex-cell merging',
                items=records,builder_sha256=sha(__file__),decomposer_sha256=sha(HERE.parents[1]/'simulation/g1_cooling_demo/convex_cells.py'),
                visual_geometry_changed=False,body_inertias_changed=False,joint_limits_changed=False,
                omitted_auxiliary_surface_tolerance_m=2e-6,physical_contact_qualified=False,scope=__doc__)
    (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();build(a.out)
