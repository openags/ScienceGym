"""Screen source-hand entry and closure at the supported Cary forceps pose.

The ordinary tray and worktop retain the proposed staging geometry. Include
the terminal wrist housing and all nonadjacent hand parts. This local screen
does not establish whole-body reach, pickup, friction or support stability.
"""
import argparse
from collections import defaultdict
import hashlib
import itertools
import json
import time
import numpy as np
import trimesh
from cary_distal_hand import distal_hand_manager
from long_forceps import meshes
from optical_choreography import HERE
from source_geometry import ROOT,KIN,robot_meshes,set_hand,fk


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--trial',default='01')
    parser.add_argument('--staging',default='previews/long_forceps_staging_07/staging.json')
    args=parser.parse_args();out=HERE/'previews'/('long_forceps_approach_'+args.trial);out.mkdir(exist_ok=False)
    staging=json.loads((HERE/args.staging).read_text());assert staging['passed']
    profile=json.loads((HERE/staging['profile']).read_text());assert profile['passed']
    names=['fit_long_forceps_approach.py','cary_distal_hand.py','long_forceps.py','source_geometry.py',args.staging,staging['profile']]
    pins={}
    for name in names:
        data=(HERE/name).read_bytes();dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);pins[name]=hashlib.sha256(data).hexdigest()
    assert hashlib.sha256((ROOT/staging['tray_geometry']).read_bytes()).hexdigest()==staging['tray_geometry_sha256']
    body=robot_meshes();hand=distal_hand_manager('right',body)
    tool=trimesh.collision.CollisionManager();pose=np.array(staging['tool_world_matrix']);target=np.array(staging['palm_matrix'])
    for n,m in meshes(0.).items():tool.add_object(n,m,pose)
    tray=trimesh.collision.CollisionManager();tray_pose=np.eye(4);tray_pose[:3,3]=staging['tray_position_m']
    source=trimesh.load(ROOT/staging['tray_geometry'],force='scene',process=False)
    for n in source.graph.nodes_geometry:
        local,key=source.graph[n];tray.add_object(n,source.geometry[key],tray_pose@local)
    graph=defaultdict(list)
    for j in KIN['joints']:
        weight=int(j['type']=='revolute');graph[j['parent']].append((j['id'],weight));graph[j['id']].append((j['parent'],weight))
    adjacent=set()
    for link in hand._objs:
        stack=[(link,None,0)]
        while stack:
            n,parent,depth=stack.pop()
            if depth>1:continue
            if n in hand._objs:adjacent.add(tuple(sorted((link,n))))
            stack.extend((child,n,depth+weight) for child,weight in graph[n] if child!=parent)
    def check(q,palm):
        set_hand(hand,'right',q,palm)
        _,pairs=hand.in_collision_internal(return_names=True)
        failures={}
        unexpected=sorted(p for p in pairs if tuple(sorted(p)) not in adjacent)
        if unexpected:failures['self']=unexpected
        for label,manager in [('tool',tool),('tray',tray)]:
            _,pairs=hand.in_collision_other(manager,return_names=True)
            if pairs:failures[label]=sorted(pairs)
        world=fk(q);base=palm@np.linalg.inv(world['right_palm_force_sensor'])
        low=min(float(trimesh.transform_points(body[n].vertices,base@world[n])[:,2].min()) for n in hand._objs)
        if low<=.85001:failures['worktop_z_m']=low
        return failures
    closed=profile['rows'][0]['q'];failures=[];candidates=[];started=time.monotonic()
    for index,thumb in itertools.product([.1,.2,.3],[.1,.2,.3]):
        opened=dict(closed);opened['right_index_1_joint']-=index;opened['right_thumb_2_joint']-=thumb
        closure=[]
        for u in np.linspace(0.,1.,41):
            q={n:opened[n]*(1-u)+closed[n]*u for n in closed};failure=check(q,target)
            if failure:
                failures.append(dict(stage='close_hand',index_delta=index,thumb_delta=thumb,fraction=float(u),failure=failure));break
            closure.append(dict(fraction=float(u),q=q,palm=target.tolist()))
        else:
            for offset in [[0,-.06,.06],[0,0,.06],[-.06,-.04,.04],[.04,-.06,.06],[0,-.08,0],[-.06,0,0]]:
                approach=[]
                for u in np.linspace(0.,1.,41):
                    palm=target.copy();palm[:3,3]+=np.array(offset)*(1-u);failure=check(opened,palm)
                    if failure:
                        failures.append(dict(stage='approach',index_delta=index,thumb_delta=thumb,offset=offset,fraction=float(u),failure=failure));break
                    approach.append(dict(fraction=float(u),q=dict(opened),palm=palm.tolist()))
                else:
                    candidates.append(dict(open_hand=opened,closed_hand=closed,offset_m=offset,approach=approach,closure=closure))
                    print('accepted',index,thumb,offset,flush=True)
    report=dict(scope=__doc__,staging=args.staging,candidates=candidates,failures=failures,
        source_sha256=pins,seconds=time.monotonic()-started,
        limitations=['Local hand/tool/tray/worktop only; full robot and room checks remain required.',
                     'No spring forces, stability, sensor-control or actual pickup qualification.'])
    (out/'approaches.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(candidates=len(candidates),failures=len(failures),seconds=report['seconds'])),flush=True)


if __name__=='__main__':main()
