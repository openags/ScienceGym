"""Conforming right distal-finger contact solids from the official CAD meshes.

Visual meshes, body inertia and joint limits are unchanged. Closed outer and
inner shells are retained; degenerate auxiliary faces must lie inside or
within 2 micrometres of those shells before they can be omitted from the PLC.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import trimesh

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'simulation/g1_cooling_demo'))
from convex_cells import clean, decompose


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);records=[]
    for link in ['right_thumb_4','right_index_2']:
        source=HERE/'vendor/unitree_ros/meshes'/(link+'.STL')
        raw=trimesh.load(source,force='mesh');mesh=clean(raw);components=mesh.split(only_watertight=False)
        solids=[p for p in components if p.is_watertight and len(p.faces)>20 and abs(p.volume)>1e-10]
        auxiliary=[p for p in components if all(p is not q for q in solids)]
        core=trimesh.util.concatenate(solids)
        if not core.is_volume:raise ValueError('Source shells are not a closed solid: '+link)
        points=np.vstack([p.vertices for p in auxiliary]) if auxiliary else np.empty((0,3))
        distance=trimesh.proximity.closest_point(core,points)[1] if len(points) else np.array([])
        outside=distance[~core.contains(points)] if len(points) else np.array([])
        maximum=float(max(outside,default=0.))
        if maximum>2e-6:raise ValueError('Auxiliary source surface is outside the retained shells')
        if abs(core.volume-mesh.volume)>max(1e-14,abs(mesh.volume)*1e-7):raise ValueError('Source volume changed during shell selection')
        holes=[];outer=trimesh.util.concatenate([p for p in solids if p.volume>0])
        rng=np.random.default_rng(846)
        for p in solids:
            if p.volume>=0:continue
            candidates=rng.uniform(p.bounds[0],p.bounds[1],size=(4096,3))
            candidates=candidates[p.contains(candidates)]
            candidates=candidates[outer.contains(candidates)]
            if not len(candidates):raise ValueError('No proved point inside both the hole shell and outer solid')
            depth=trimesh.proximity.closest_point(p,candidates)[1]
            holes.append(candidates[np.argmax(depth)].tolist())
        print('decompose',link,'faces',len(core.faces),'holes',len(holes),flush=True)
        cells=decompose(core,holes=holes);dest=out/link;dest.mkdir();pieces=[];volume=0.
        for i,cell in enumerate(cells):
            path=dest/f'{i:05d}.stl';cell.export(path)
            compiled=trimesh.load(path,force='mesh').convex_hull
            if not compiled.is_volume:raise ValueError('Serialized cell is not a solid')
            compiled.export(path);volume+=compiled.volume
            pieces.append(dict(path=str(path.relative_to(HERE)),sha256=sha(path)))
        error=abs(volume-core.volume)/core.volume
        if error>2e-5:raise ValueError('Serialized cell volume differs from the source solid')
        records.append(dict(link=link,source_path=str(source.relative_to(HERE)),source_sha256=sha(source),
                            source_volume_m3=float(mesh.volume),retained_solid_volume_m3=float(core.volume),
                            cell_volume_sum_m3=float(volume),relative_serialized_volume_error=float(error),
                            inner_shell_hole_points_m=holes,auxiliary_components=len(auxiliary),
                            maximum_omitted_surface_outside_distance_m=maximum,pieces=pieces))
        print('packaged',link,'pieces',len(pieces),flush=True)
    report=dict(schema_version=1,method='TetGen PLC with explicit interior holes and volume-preserving convex-cell merging',
                items=records,builder_sha256=sha(__file__),decomposer_sha256=sha(HERE.parents[1]/'simulation/g1_cooling_demo/convex_cells.py'),
                visual_geometry_changed=False,body_inertias_changed=False,joint_limits_changed=False,
                omitted_auxiliary_surface_tolerance_m=2e-6,physical_contact_qualified=False,scope=__doc__)
    (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();build(a.out)
