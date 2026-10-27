"""Tighten the existing cover grip without changing its arm or hinge path.

Only index and thumb flexion are adjusted. The source mesh remains unchanged;
opening, closure approach and withdrawal are screened against the instrument.
This improves geometric contact and does not qualify gripping forces.
"""
import argparse
import hashlib
import itertools
import json
import time
from collections import defaultdict
import fcl
import numpy as np
import trimesh
from scipy.spatial.transform import Rotation
from cary_distal_hand import distal_hand_manager
from source_geometry import ROOT, ASSETS, KIN, set_hand
from optical_choreography import HERE


def translation(xyz):
    m=np.eye(4);m[:3,3]=xyz;return m


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--trial',default='01');args=parser.parse_args()
    out=HERE/'previews'/('ftir_cover_contact_'+args.trial);out.mkdir(exist_ok=False)
    names=['refine_ftir_cover_contact.py','cary_distal_hand.py','source_geometry.py','grasp_profile.json','optical_setup.json']
    pins={}
    for name in names:
        data=(HERE/name).read_bytes();dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(data);pins[name]=hashlib.sha256(data).hexdigest()
    profile=json.loads((HERE/'grasp_profile.json').read_text())['ftir_cover']
    setup=json.loads((HERE/'optical_setup.json').read_text())
    interfaces=json.loads((ROOT/'assets/nicolet_6700_v1/interfaces.json').read_text())
    obstacles=trimesh.collision.CollisionManager();rest={}
    for identity in ['nicolet','pike']:
        asset=ASSETS[identity];source=trimesh.load(ROOT/asset['geometry'],force='scene',process=False)
        for name in source.graph.nodes_geometry:
            local,key=source.graph[name];installed=np.array(setup['parts'].get(identity,{}).get(name,{}).get('matrix',np.eye(4)))
            pose=translation(asset['position_m'])@installed@local;label=identity+'::'+name
            obstacles.add_object(label,source.geometry[key],pose);rest[label]=pose
    hand=distal_hand_manager('right');pivot=np.array(profile['hinge_m']);initial_palm=translation(profile['handle_center_m'])@np.array(profile['palm_matrix'])
    graph=defaultdict(list)
    for j in KIN['joints']:
        w=int(j['type']=='revolute');graph[j['parent']].append((j['id'],w));graph[j['id']].append((j['parent'],w))
    adjacent=set()
    for link in hand._objs:
        stack=[(link,None,0)]
        while stack:
            name,parent,depth=stack.pop()
            if depth>1:continue
            if name in hand._objs:adjacent.add(tuple(sorted((link,name))))
            stack.extend((child,name,depth+w) for child,w in graph[name] if child!=parent)
    def gap(digit):
        target=obstacles._objs['nicolet::lid_handle_bar']['obj'];values=[]
        for name in hand._objs:
            if digit not in name:continue
            result=fcl.DistanceResult();fcl.distance(hand._objs[name]['obj'],target,fcl.DistanceRequest(),result)
            values.append(float(result.min_distance))
        return min(values)
    started=time.monotonic();choices={}
    for digit,joint,values in [('index','right_index_1_joint',np.linspace(.72,.80,801)),
                              ('thumb','right_thumb_2_joint',np.linspace(.15,.42,2701))]:
        found=[]
        for value in values:
            q={**profile['q'],joint:float(value)};set_hand(hand,'right',q,initial_palm);distance=gap(digit)
            if .00002<=distance<=.00020:found.append(dict(value=float(value),gap_m=distance))
        choices[joint]=sorted(found,key=lambda v:v['gap_m'])[:10]
        print('choices',digit,len(found),flush=True)
    accepted=[];failures=[]
    for i,t in itertools.product(*choices.values()):
        correction={'right_index_1_joint':i['value'],'right_thumb_2_joint':t['value']}
        rows=[];failure=None
        states=[(angle,1.) for angle in np.linspace(0.,profile['open_angle_rad'],131)]
        states += [(angle,c) for angle in [0.,profile['open_angle_rad']] for c in np.linspace(0.,1.,51)]
        for angle,closed in states:
            rotate=np.eye(4);rotate[:3,:3]=Rotation.from_euler('x',angle).as_matrix()
            delta=translation(pivot)@rotate@translation(-pivot)
            for name in interfaces['cover_parts']:obstacles.set_transform('nicolet::'+name,delta@rest['nicolet::'+name])
            q={**profile['q'],**correction}
            for name in ['right_index_1_joint','right_thumb_2_joint']:q[name]*=closed
            palm=delta@initial_palm;palm[:3,3]+=np.array(profile['approach_offset_m'])*(1-closed)
            set_hand(hand,'right',q,palm)
            hit,pairs=hand.in_collision_other(obstacles,return_names=True)
            if hit:failure=dict(angle_rad=float(angle),closed=float(closed),environment=sorted(pairs));break
            _,pairs=hand.in_collision_internal(return_names=True)
            bad=[p for p in pairs if tuple(sorted(p)) not in adjacent]
            if bad:failure=dict(angle_rad=float(angle),closed=float(closed),self_intersections=sorted(bad));break
            distances={digit:gap(digit) for digit in ['index','thumb']} if closed==1 else {}
            if closed==1 and not all(1e-6<d<.00025 for d in distances.values()):
                failure=dict(angle_rad=float(angle),closed=float(closed),grip_gaps=distances);break
            rows.append(dict(angle_rad=float(angle),closed=float(closed),q=q,palm=palm.tolist(),grip_gaps_m=distances))
        if failure:failures.append(dict(correction=correction,failure=failure))
        else:
            accepted.append(dict(old_q={n:profile['q'][n] for n in correction},new_q=correction,rows=rows));break
    report=dict(scope=__doc__,passed=bool(accepted),candidates=accepted,choices=choices,failures=failures,
                source_sha256=pins,seconds=time.monotonic()-started,
                limitations=['Local hand/wrist and instrument geometry only; independent full-body composition must be rerun.',
                             'Hinge retention and grip force remain inferred, without physical qualification.'])
    (out/'fit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],candidates=len(accepted),failures=len(failures),seconds=report['seconds'])),flush=True)


if __name__=='__main__':main()
