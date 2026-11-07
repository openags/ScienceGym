"""Stage long forceps on an ordinary tray rim at the Cary bench's free left side.

An additional ordinary tray uses the existing tray's source geometry. The tip
rests on the bench and the heel meets its 50 mm rim. This inferred initial
staging is checked against the real tool and hand meshes; friction and support
forces are not qualified by these geometry checks.
"""
import argparse
import hashlib
import json
import numpy as np
import trimesh
from scipy.optimize import brentq
from scipy.spatial.transform import Rotation
from cary_distal_hand import distal_hand_manager
from optical_choreography import HERE
from source_geometry import ROOT,ASSETS,robot_meshes,fk,set_hand
from long_forceps import meshes


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--trial',default='01')
    parser.add_argument('--tray-y-offset',type=float,default=0.)
    parser.add_argument('--profile',default='previews/long_forceps_closure_03/profile.json');args=parser.parse_args()
    out=HERE/'previews'/('long_forceps_staging_'+args.trial);out.mkdir(exist_ok=False)
    names=['fit_long_forceps_staging.py','cary_distal_hand.py','long_forceps.py','source_geometry.py',args.profile]
    pins={}
    for name in names:
        data=(HERE/name).read_bytes();dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);pins[name]=hashlib.sha256(data).hexdigest()
    profile=json.loads((HERE/args.profile).read_text());assert profile['passed']
    opened=meshes(0.);vertices=np.vstack([m.vertices for m in opened.values()]);heel=opened['joined_heel'].vertices
    def rotation(angle):return Rotation.from_euler('y',-angle).as_matrix()@Rotation.from_euler('x',np.pi/2).as_matrix()
    def rise(angle):
        r=rotation(angle);return float((heel@r[2]).min()-(vertices@r[2]).min())
    angle=brentq(lambda a:rise(a)-.050001,.05,.8)
    def pose_at(value):
        pose=np.eye(4);pose[:3,:3]=rotation(value)
        pose[:3,3]=[1.65,8.22,.850001-(vertices@pose[2,:3]).min()];return pose
    pose=pose_at(angle);heel_world=trimesh.transform_points(heel,pose)
    lowest=heel_world[heel_world[:,2]<heel_world[:,2].min()+1e-8]
    tray_position=[float(lowest[:,0].mean()+.1494),float(heel_world[:,1].mean()+args.tray_y_offset),.850001]
    source=trimesh.load(ROOT/ASSETS['tray_white']['geometry'],force='scene',process=False)
    tray=trimesh.collision.CollisionManager();tray_pose=np.eye(4);tray_pose[:3,3]=tray_position
    for n in source.graph.nodes_geometry:
        local,key=source.graph[n];tray.add_object(n,source.geometry[key],tray_pose@local)
    tool=trimesh.collision.CollisionManager()
    for n,m in opened.items():tool.add_object(n,m,pose)
    def place(value):
        result=pose_at(value)
        for n in tool._objs:tool.set_transform(n,result)
        return result
    low,high=angle,angle+.10;place(high)
    assert not tool.in_collision_other(tray),'No clear upper support orientation'
    for _ in range(36):
        mid=(low+high)/2;place(mid)
        if tool.in_collision_other(tray):low=mid
        else:high=mid
    pose=place(high+1e-6);support_gap=float(tool.min_distance_other(tray))
    body=robot_meshes();hand=distal_hand_manager('right',body);palm=pose@np.array(profile['palm_matrix'])
    rows=[]
    for item in profile['rows']:
        closure=item['closure'];geometry=meshes(closure);tool=trimesh.collision.CollisionManager()
        for n,m in geometry.items():tool.add_object(n,m,pose)
        set_hand(hand,'right',item['q'],palm)
        _,hand_tool=hand.in_collision_other(tool,return_names=True)
        _,hand_tray=hand.in_collision_other(tray,return_names=True)
        _,tool_tray=tool.in_collision_other(tray,return_names=True)
        world=fk(item['q']);base=palm@np.linalg.inv(world['right_palm_force_sensor'])
        hand_floor=min(float(trimesh.transform_points(body[n].vertices,base@world[n])[:,2].min()) for n in hand._objs)
        tool_floor=min(float(trimesh.transform_points(m.vertices,pose)[:,2].min()) for m in geometry.values())
        rows.append(dict(closure=closure,hand_tool_intersections=sorted(hand_tool),hand_tray_intersections=sorted(hand_tray),
            tool_tray_intersections=sorted(tool_tray),minimum_hand_z_m=hand_floor,minimum_tool_z_m=tool_floor,
            passed=not(hand_tool or hand_tray or tool_tray) and hand_floor>.85001 and tool_floor>=.85))
    passed=all(r['passed'] for r in rows) and support_gap<2e-6
    report=dict(scope=__doc__,passed=passed,tool_world_matrix=pose.tolist(),tray_position_m=tray_position,
        tray_geometry=ASSETS['tray_white']['geometry'],tray_geometry_sha256=ASSETS['tray_white']['geometry_sha256'],
        tray_instance_id='cary_tool_tray',tool_tray_gap_m=support_gap,palm_matrix=palm.tolist(),rows=rows,
        source_sha256=pins,profile=args.profile,tray_y_offset_m=args.tray_y_offset,
        limitations=['Ordinary additional tray instance proposed; not yet installed in the live scene.',
                     'No whole-lab obstacle, full-body reach, open-hand approach or force/stability qualification.'])
    (out/'staging.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=passed,gap=support_gap,failed_states=sum(not r['passed'] for r in rows),first_failure=next((r for r in rows if not r['passed']),None))),flush=True)


if __name__=='__main__':main()
