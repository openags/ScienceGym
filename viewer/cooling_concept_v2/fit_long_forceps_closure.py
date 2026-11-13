"""Fit a continuous source-hand closure profile on the ordinary long forceps.

Both opposing blade contacts and all nonadjacent hand/tool/self collisions
are checked, including interpolated joint states between fitted knots.
This does not model spring force, friction or whole-body tool pickup.
"""
import argparse
from collections import defaultdict
import hashlib
import json
import fcl
import numpy as np
import trimesh
from scipy.optimize import least_squares
from long_forceps import meshes,OUT
from optical_choreography import HERE,JOINTS
from source_geometry import KIN,set_hand
from cary_distal_hand import distal_hand_manager


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--trial',default='01')
    parser.add_argument('--grip-index',type=int,default=0)
    parser.add_argument('--unused-fold',type=float,default=1.4)
    args=parser.parse_args();out=HERE/'previews'/('long_forceps_closure_'+args.trial);out.mkdir(exist_ok=False)
    inputs=['fit_long_forceps_closure.py','long_forceps.py','source_geometry.py','cary_distal_hand.py',
            'previews/long_forceps_grips_02/grasps.json']
    pins={}
    for name in inputs:
        data=(HERE/name).read_bytes();dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        pins[name]=hashlib.sha256(data).hexdigest()
    candidate=json.loads((HERE/inputs[-1]).read_text())['candidates'][args.grip_index]
    q=dict(candidate['q']);palm=np.array(candidate['palm_matrix'])
    for finger in ['middle','ring','little']:
        n=f'right_{finger}_1_joint';limits=JOINTS[n]['limits']
        assert limits['lower']<=args.unused_fold<=limits['upper'];q[n]=args.unused_fold
    hand=distal_hand_manager('right');graph=defaultdict(list)
    for j in KIN['joints']:
        weight=int(j['type']=='revolute');graph[j['parent']].append((j['id'],weight));graph[j['id']].append((j['parent'],weight))
    adjacent=set()
    for link in hand._objs:
        stack=[(link,None,0)]
        while stack:
            n,parent,d=stack.pop()
            if d>1:continue
            if n in hand._objs:adjacent.add(tuple(sorted((link,n))))
            stack.extend((child,n,d+w) for child,w in graph[n] if child!=parent)
    names=['right_index_1_joint','right_thumb_2_joint']
    limits=np.array([[JOINTS[n]['limits']['lower'],JOINTS[n]['limits']['upper']] for n in names])
    contacts=[candidate['index_contact'],candidate['thumb_contact']]
    def tool_at(closure):
        tool=trimesh.collision.CollisionManager()
        for name,mesh in meshes(float(closure)).items():tool.add_object(name,mesh)
        return tool
    def distances(q,tool):
        set_hand(hand,'right',q,palm);gaps=[]
        for c in contacts:
            result=fcl.DistanceResult()
            fcl.distance(hand._objs[c[3]]['obj'],tool._objs[c[1]]['obj'],fcl.DistanceRequest(),result)
            gaps.append(float(result.min_distance))
        return gaps
    def inspect(closure,q,tool):
        gaps=distances(q,tool)
        _,tool_pairs=hand.in_collision_other(tool,return_names=True)
        _,self_pairs=hand.in_collision_internal(return_names=True)
        unexpected=sorted(p for p in self_pairs if tuple(sorted(p)) not in adjacent)
        return dict(closure=float(closure),q={n:float(v) for n,v in q.items()},gaps_m=gaps,
            hand_tool_intersections=sorted(tool_pairs),self_intersections=unexpected,
            passed=not tool_pairs and not unexpected and min(gaps)>1e-6 and max(gaps)<=.00025)
    rows=[]
    for closure in np.linspace(1.,0.,51):
        tool=tool_at(closure)
        def residual(values):
            return np.array(distances({**q,**dict(zip(names,values))},tool))-.000125
        fit=least_squares(residual,[q[n] for n in names],bounds=(limits[:,0],limits[:,1]),
            diff_step=1e-4,max_nfev=80,ftol=1e-12,xtol=1e-12,gtol=1e-12)
        q.update(dict(zip(names,map(float,fit.x))));row=inspect(closure,q,tool);rows.append(row)
        if not row['passed']:print('rejected fitted knot',closure,row,flush=True)
    rows.reverse();interpolated=[]
    for a,b in zip(rows,rows[1:]):
        for u in [.25,.5,.75]:
            closure=(1-u)*a['closure']+u*b['closure'];state={n:(1-u)*a['q'][n]+u*b['q'][n] for n in q}
            interpolated.append(inspect(closure,state,tool_at(closure)))
    passed=all(r['passed'] for r in rows+interpolated)
    report=dict(scope=__doc__,passed=passed,grip_index=args.grip_index,unused_fold_rad=args.unused_fold,
        palm_matrix=palm.tolist(),contacts=contacts,rows=rows,interpolated_checks=interpolated,
        source_sha256=pins,asset_revision_sha256=hashlib.sha256((OUT/'revision.json').read_bytes()).hexdigest(),
        limitations=['No spring stiffness, pinch force, friction or retention qualification.',
                     'No approach, tool resting support or whole-body pickup path.'])
    (out/'profile.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=passed,knots=len(rows),interpolated=len(interpolated),
        failures=sum(not r['passed'] for r in rows+interpolated))),flush=True)


if __name__=='__main__':main()
