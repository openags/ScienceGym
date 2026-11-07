"""Compare rejected native hull contacts with original source triangles."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import mujoco
import numpy as np
import trimesh

HERE=Path(__file__).resolve().parent;BASE=HERE.parents[1];ROOT=BASE.parents[1]
sys.path.insert(0,str(BASE))
from robot_source_meshes import robot_source_meshes


def main(folder):
    folder=Path(folder).resolve();output=HERE/(folder.name+'_contact_source_review.json')
    if output.exists():raise FileExistsError(output)
    tr=dict(np.load(folder/'trace.npz'));m=mujoco.MjModel.from_xml_path(str(folder/'world.xml'))
    d=mujoco.MjData(m);meshes=robot_source_meshes(m)
    links=['right_index_2','right_index_force_sensor_3']
    hands={name:trimesh.collision.CollisionManager() for name in links}
    for name in links:hands[name].add_object(name,meshes[name])
    parts=json.loads((folder/'laboratory_import.json').read_text())['parts']
    names={p['geom']:p['source_part'] for p in parts if p['instance']=='nicolet' and p['source_part'] in
           ['sample_access_slider_grip','sample_access_sliding_window']}
    objects={name:trimesh.collision.CollisionManager() for name in names}
    for name in names:
        gid=m.geom(name).id;mid=m.geom_dataid[gid]
        va,vn=m.mesh_vertadr[mid],m.mesh_vertnum[mid];fa,fn=m.mesh_faceadr[mid],m.mesh_facenum[mid]
        mesh=trimesh.Trimesh(vertices=m.mesh_vert[va:va+vn],faces=m.mesh_face[fa:fa+fn],process=False)
        objects[name].add_object(name,mesh)
    rows=[]
    for t in np.arange(45.,48.501,.05):
        i=int(np.argmin(abs(tr['time']-t)));d.qpos[:]=tr['qpos'][i];mujoco.mj_kinematics(m,d)
        for name,manager in hands.items():
            body=d.body(name);T=np.eye(4);T[:3,:3]=body.xmat.reshape(3,3);T[:3,3]=body.xpos
            manager.set_transform(name,T)
        for name,manager in objects.items():
            geom=d.geom(name);T=np.eye(4);T[:3,:3]=geom.xmat.reshape(3,3);T[:3,3]=geom.xpos
            manager.set_transform(name,T)
        for link,hand in hands.items():
            for name,obj in objects.items():
                intersects=bool(hand.in_collision_other(obj))
                rows.append(dict(time_s=float(tr['time'][i]),robot_source_link=link,
                    device_source_part=names[name],source_triangle_intersection=intersects,
                    source_surface_distance_m=float(hand.min_distance_other(obj))))
    report=dict(rows=rows,
        index_link_window_intersections=sum(r['source_triangle_intersection'] for r in rows
            if r['robot_source_link']=='right_index_2' and r['device_source_part']=='sample_access_sliding_window'),
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [Path(__file__),BASE/'robot_source_meshes.py',folder/'trace.npz',folder/'world.xml',folder/'laboratory_import.json']},
        scope='Retained-state source triangle diagnostics, including actual contact states. Cannot replace native dynamics review or authorize ignoring a collision.')
    output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'rows':len(rows),'index_link_window_intersections':report['index_link_window_intersections']}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder');main(p.parse_args().folder)
