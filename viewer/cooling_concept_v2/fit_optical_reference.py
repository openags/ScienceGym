"""Find source-hand grasps of the installed IntegratIR reference holder."""
import argparse,itertools,json,time
from pathlib import Path
import fcl,numpy as np,trimesh
from scipy.spatial.transform import Rotation
from source_geometry import ROOT,ASSETS,fk,hand_manager,set_hand

HERE=Path(__file__).resolve().parent

def search(side='right'):
    setup=json.loads((HERE/'optical_setup.json').read_text())
    hand=hand_manager(side);obstacles=trimesh.collision.CollisionManager()
    reference=trimesh.collision.CollisionManager();target=[]
    nicolet=json.loads((ROOT/'assets/nicolet_6700_v1/interfaces.json').read_text())
    for identity in ['nicolet','pike']:
        asset=ASSETS[identity];scene=trimesh.load(ROOT/asset['geometry'],force='scene',process=False)
        base=np.eye(4);base[:3,3]=asset['position_m']
        for name in scene.graph.nodes_geometry:
            transform,key=scene.graph[name];record=setup['parts'].get(identity,{}).get(name)
            if record:transform=np.asarray(record['matrix'])@transform
            if identity=='nicolet' and name in nicolet['cover_parts']:
                hinge=np.asarray(nicolet['interfaces'][4]['pivot_m'])+np.asarray(asset['normalization_matrix'])[:3,3]
                r=np.eye(4);r[:3,:3]=Rotation.from_euler('x',-65*np.pi/180).as_matrix();r[:3,3]=hinge-r[:3,:3]@hinge;transform=r@transform
            transform=base@transform
            is_reference=identity=='pike' and name in ['gold_reference_holder','gold_reference_shoulder','diffuse_gold_reference_face']
            (reference if is_reference else obstacles).add_object(name,scene.geometry[key],transform)
            if is_reference:
                mesh=scene.geometry[key].copy();mesh.apply_transform(transform);target.append(mesh)
    combined=trimesh.util.concatenate(target);reference_center=np.array(setup['ports']['ftir_sample']['position_m'])+np.array([0,0,.0215])
    obj=trimesh.collision.CollisionManager();obj.add_object('reference',combined)
    ref_obj=obj._objs['reference']['obj'];results=[];tested=0;start=time.monotonic()
    for index,thumb2 in itertools.product(np.linspace(.2,.8,9),np.linspace(.1,.5,11)):
        q={f'{side}_{f}_1_joint':1.1 for f in ['middle','ring','little']}
        q.update({f'{side}_index_1_joint':float(index),f'{side}_thumb_1_joint':1.1641,f'{side}_thumb_2_joint':float(thumb2)})
        world=fk(q);inverse=np.linalg.inv(world[side+'_palm_force_sensor'])
        i=(inverse@world[side+'_index_force_sensor_3'])[:3,3];th=(inverse@world[side+'_thumb_force_sensor_4'])[:3,3]
        middle=(i+th)/2;gap=th-i;gap/=np.linalg.norm(gap)
        toward=middle-gap*(middle@gap);toward/=np.linalg.norm(toward);local=np.column_stack([gap,toward,np.cross(gap,toward)])
        for tilt,yaw,bias in itertools.product(np.linspace(-.6,.6,5),[-.35,0,.35,np.pi-.35,np.pi,np.pi+.35],[-.003,0,.003]):
            normal=np.array([np.cos(yaw),np.sin(yaw),0]);direction=np.array([normal[1]*np.sin(tilt),-normal[0]*np.sin(tilt),-np.cos(tilt)])
            rotation=np.column_stack([normal,direction,np.cross(normal,direction)])@local.T
            palm=np.eye(4);palm[:3,:3]=rotation;palm[:3,3]=reference_center-rotation@middle+normal*bias
            set_hand(hand,side,q,palm);tested+=1
            if hand.in_collision_other(reference) or hand.in_collision_other(obstacles):continue
            _,pairs=hand.in_collision_internal(return_names=True)
            if any(('thumb' in a and any(f in b for f in ['index','middle','ring','little'])) or ('thumb' in b and any(f in a for f in ['index','middle','ring','little'])) for a,b in pairs):continue
            def nearest(link):
                result=fcl.DistanceResult();fcl.distance(hand._objs[link]['obj'],ref_obj,fcl.DistanceRequest(enable_nearest_points=True),result)
                return float(result.min_distance),np.asarray(result.nearest_points[1])
            a=min([(link,*nearest(link)) for link in hand._objs if 'index' in link],key=lambda x:x[1])
            b=min([(link,*nearest(link)) for link in hand._objs if 'thumb' in link],key=lambda x:x[1])
            if max(a[1],b[1])>.005:continue
            x=a[2][:2]-reference_center[:2];y=b[2][:2]-reference_center[:2]
            dot=float(x@y/max(1e-12,np.linalg.norm(x)*np.linalg.norm(y)))
            if dot>-.5:continue
            local_palm=palm.copy();local_palm[:3,3]-=np.array(setup['ports']['ftir_sample']['position_m'])
            results.append(dict(q=q,palm_matrix=local_palm.tolist(),finger_gap_m=a[1],thumb_gap_m=b[1],opposition_dot=dot,tilt_rad=float(tilt),yaw_rad=float(yaw),bias_m=float(bias)))
    results.sort(key=lambda c:max(c['finger_gap_m'],c['thumb_gap_m']))
    report=dict(scope=__doc__,side=side,cover_angle_rad=-65*np.pi/180,tested=tested,seconds=time.monotonic()-start,candidates=results)
    (HERE/f'previews/optical_reference_{side}_search.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(tested=tested,candidates=len(results),best=results[:2],seconds=report['seconds'])),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--side',choices=['left','right'],default='right');args=parser.parse_args();search(args.side)
