"""Fit source Inspire fingers to the Cary pull and extension-cover handle.

Opposed index/thumb contact must remain on the selected handle segment, with
all other hand geometry clear of the installed instrument and accessory.
This is a grasp geometry search; retention forces are not established.
"""
import argparse,hashlib,itertools,json,time
import fcl,numpy as np
from cary_access_scene import CaryAccessScene
from optical_choreography import HERE
from source_geometry import hand_manager,set_hand,fk


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--part',choices=['lid','cover'],required=True);args=parser.parse_args();started=time.monotonic()
    snapshot=HERE/'previews'/('cary_access_fit_source_03_'+args.part);snapshot.mkdir(exist_ok=True)
    sources={n:(HERE/n).read_bytes() for n in ['cary_access_scene.py','fit_cary_access.py']}
    for n,data in sources.items():(snapshot/n).write_bytes(data)
    scene=CaryAccessScene(local_only=True)
    if args.part=='cover':scene.set_access(lid=.305)
    obstacles=scene.local_obstacles();hand=hand_manager('right')
    center=scene.lid_handle if args.part=='lid' else scene.cover_handle
    name='sample_lid_pull' if args.part=='lid' else 'extension_pull_bar'
    target=obstacles._objs['cary::'+name]['obj'];candidates=[];tested=0
    for index,thumb in itertools.product(np.linspace(.45,1.05,9),np.linspace(.1,.6,11)):
        q={f'right_{f}_1_joint':1.1 for f in ['middle','ring','little']}
        q.update(right_index_1_joint=float(index),right_thumb_1_joint=1.1641,right_thumb_2_joint=float(thumb))
        world=fk(q);inv=np.linalg.inv(world['right_palm_force_sensor'])
        i=(inv@world['right_index_force_sensor_3'])[:3,3];th=(inv@world['right_thumb_force_sensor_4'])[:3,3]
        middle=(i+th)/2;gap=th-i;gap/=np.linalg.norm(gap)
        forward=middle-gap*(middle@gap);forward/=np.linalg.norm(forward)
        local=np.column_stack([gap,forward,np.cross(gap,forward)])
        for tilt,sign,bias,up in itertools.product([-.6,0,.6],[1,-1],[-.002,0,.002],[.004,.007,.01,.013]):
            normal=np.array([0,sign,0]);direction=np.array([np.sin(tilt),0,-np.cos(tilt)])
            rotation=np.column_stack([normal,direction,np.cross(normal,direction)])@local.T
            palm=np.eye(4);palm[:3,:3]=rotation;palm[:3,3]=center+[0,0,up]-rotation@middle+normal*bias
            set_hand(hand,'right',q,palm);tested+=1
            if hand.in_collision_other(obstacles):continue
            _,pairs=hand.in_collision_internal(return_names=True)
            if any(('thumb' in a and any(f in b for f in ['index','middle','ring','little'])) or ('thumb' in b and any(f in a for f in ['index','middle','ring','little'])) for a,b in pairs):continue
            def nearest(link):
                r=fcl.DistanceResult();fcl.distance(hand._objs[link]['obj'],target,fcl.DistanceRequest(enable_nearest_points=True),r)
                return float(r.min_distance),np.array(r.nearest_points[1])
            a=min([(n,*nearest(n)) for n in hand._objs if 'index' in n],key=lambda row:row[1]);b=min([(n,*nearest(n)) for n in hand._objs if 'thumb' in n],key=lambda row:row[1])
            if max(a[1],b[1])>.002:continue
            if args.part=='lid' and max(abs(a[2][1]-center[1]),abs(b[2][1]-center[1]))>.009:continue
            x=a[2][1:]-center[1:];y=b[2][1:]-center[1:]
            dot=float(x@y/max(1e-12,np.linalg.norm(x)*np.linalg.norm(y)))
            if args.part=='cover' and dot>-.5:continue
            if args.part=='lid' and (a[2][1]-center[1])*(b[2][1]-center[1])>=-.005**2:continue
            relative=palm.copy();relative[:3,3]-=center
            candidates.append(dict(q=q,palm_matrix=relative.tolist(),finger_gap_m=a[1],thumb_gap_m=b[1],finger_part=a[0],thumb_part=b[0],opposition_dot=dot,tilt_rad=tilt,normal_sign=sign,bias_m=bias,offset_z_m=up))
        if tested%4680==0:print(args.part,'tested',tested,'candidates',len(candidates),flush=True)
    candidates.sort(key=lambda c:max(c['finger_gap_m'],c['thumb_gap_m']))
    report=dict(scope=__doc__,part=args.part,handle_center_m=center.tolist(),tested=tested,candidates=candidates,seconds=time.monotonic()-started,source_snapshot=str(snapshot.relative_to(HERE)),source_sha256={n:hashlib.sha256(data).hexdigest() for n,data in sources.items()})
    (HERE/'previews'/('cary_'+args.part+'_grasps.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(part=args.part,tested=tested,candidates=len(candidates),seconds=report['seconds'],best=candidates[:1])),flush=True)


if __name__=='__main__':main()
