"""Review nonadjacent source robot-link surface intersections.

Links separated by zero or one revolute joint are excluded as mechanical
neighbors. The source ankle housings have a separately bounded joint-region
exception. Every other intersecting pair is retained for review.
"""
import argparse,gzip,hashlib,json
from collections import defaultdict
from pathlib import Path
import numpy as np
import trimesh,fcl
from source_geometry import KIN,robot_meshes

def audit(folder):
    folder=Path(folder);meshes=robot_meshes();manager=trimesh.collision.CollisionManager();graph=defaultdict(list)
    for name,mesh in meshes.items():manager.add_object(name,mesh)
    for j in KIN['joints']:
        weight=int(j['type']=='revolute');graph[j['parent']].append((j['id'],weight));graph[j['id']].append((j['parent'],weight))
    adjacent=set()
    for link in meshes:
        stack=[(link,None,0)]
        while stack:
            name,parent,distance=stack.pop()
            if distance>1:continue
            if name in meshes:adjacent.add(tuple(sorted((link,name))))
            stack.extend((child,name,distance+weight) for child,weight in graph[name] if child!=parent)
    summary={};frames=[];count=0;bounded_ankle_contacts=0;maximum_ankle_contact_radius=0
    with gzip.open(folder/'frames.jsonl.gz','rt') as stream:
        for line in stream:
            frame=json.loads(line);count+=1
            for name in meshes:manager.set_transform(name,np.asarray(frame['links'][name]).reshape(4,4).T)
            _,pairs=manager.in_collision_internal(return_names=True);unexpected=[]
            for pair in pairs:
                if tuple(sorted(pair)) in adjacent:continue
                housing_side=next((side for side in ['left','right'] if set(pair)=={side+'_knee_link',side+'_ankle_roll_link'}),None)
                if housing_side:
                    result=fcl.CollisionResult();fcl.collide(manager._objs[pair[0]]['obj'],manager._objs[pair[1]]['obj'],fcl.CollisionRequest(num_max_contacts=10000,enable_contact=True),result)
                    pivot=np.asarray(frame['links'][housing_side+'_ankle_pitch_link']).reshape(4,4).T[:3,3]
                    radius=max((float(np.linalg.norm(contact.pos-pivot)) for contact in result.contacts),default=float('inf'))
                    maximum_ankle_contact_radius=max(maximum_ankle_contact_radius,radius)
                    # These two source housings surround the ankle gimbal. Bound
                    # the exception to the 50 mm joint region, never the full leg.
                    if radius<=.05 and len(result.contacts)<10000:bounded_ankle_contacts+=1;continue
                unexpected.append(sorted(pair))
            if unexpected:
                frames.append(dict(time_s=frame['time_s'],phase=frame['phase'],pairs=unexpected))
                for pair in unexpected:
                    key=' / '.join(pair);item=summary.setdefault(key,dict(samples=0,phases=[]));item['samples']+=1
                    if frame['phase'] not in item['phases']:item['phases'].append(frame['phase'])
            if count%200==0:print('self_checked',count,flush=True)
    report=dict(passed=not frames,scope=__doc__,samples=count,intersection_frames=frames,contact_pairs=summary,excluded_mechanical_neighbor_pairs=sorted(adjacent),ankle_housing_exception=dict(bound_radius_m=.05,maximum_observed_radius_m=maximum_ankle_contact_radius,pair_samples=bounded_ankle_contacts,basis='Source knee and foot housings surround the two-axis ankle gimbal; all intersection points must lie within the bounded joint region'),verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (folder/'self_contact_review.json').write_text(json.dumps(report,indent=2)+'\n');print('self_review',count,len(frames),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder');args=parser.parse_args();audit(args.folder)
