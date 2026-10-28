"""Continue a grasped Cary hood through grounded steps and bench placement.

Every held pose follows source palm FK. Alternating feet use fixed stance-foot
targets; this is kinematic choreography and does not establish dynamic balance
or grasp retention. Source geometry, sole height and FK are checked at knots.
"""
import argparse,hashlib,json,math,time,xml.etree.ElementTree as ET
import mujoco,numpy as np,trimesh
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from cary_access_scene import CaryAccessScene,translation
from cary_contact_ik import ContactIK
from optical_choreography import HERE,JOINTS,Space,load_json,canonical
from plan_optical_approaches import plan
from source_geometry import ROOT,KIN,fk


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--trial',default='01');args=parser.parse_args();started=time.monotonic()
    name='cary_cover_carry_'+args.trial;snapshot=HERE/'previews'/(name+'_source');snapshot.mkdir(exist_ok=True)
    sources={n:(HERE/n).read_bytes() for n in ['plan_cary_cover_carry.py','cary_contact_ik.py','cary_access_scene.py','optical_choreography.py','previews/cary_cover_release_01.json']}
    for n,content in sources.items():
        dest=snapshot/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(content)
    released=load_json('previews/cary_cover_release_01.json');assert released['passed_planning_geometry']
    scene=CaryAccessScene(cover_candidate=True);solver=ContactIK(scene);poses=load_json('motion_poses.json')
    base=np.array(released['root']);q=dict(released['contact'][-1]['q']);lid=released['contact'][-1]['lid_m']
    grasp=np.array(released['grasp_palm_world']);inverse_grasp=np.linalg.inv(grasp);rows=[];supported=None
    asset=ROOT/'assets/unitree_g1_inspire_v1';xml=ET.parse(asset/'simulation/robot.xml').getroot();xml.find('compiler').set('meshdir',str(asset));model=mujoco.MjModel.from_xml_string(ET.tostring(xml,encoding='unicode'));data=mujoco.MjData(model)
    indices={n:model.joint(n).qposadr[0] for n in JOINTS}
    legs={s:[s+'_'+n+'_joint' for n in ['hip_pitch','hip_roll','hip_yaw','knee','ankle_pitch','ankle_roll']] for s in ['left','right']}
    def record(stage,held=True,**extra):
        world=fk(q);palm=base@world['right_palm_force_sensor'];cover=palm@inverse_grasp if held else supported
        scene.set_access(lid=lid,cover=cover);failure=scene.check(base,q);mechanism=scene.access_clearance('cover')
        sole=min(float((np.array(v)@(base@world[n])[2,:3]+(base@world[n])[2,3]).min()) for n,v in poses['sole_vertices_m'].items())
        row=dict(stage=stage,root=base.tolist(),q=dict(q),held=held,cover_matrix=cover.tolist(),lid_m=lid,failure=failure,mechanism_failures=mechanism,bounded_contacts=scene.last_bounded_contacts,minimum_sole_z_m=sole,**extra);rows.append(row)
        if failure or mechanism or sole< -1e-5 or extra.get('error_m',0)>1e-7 or extra.get('rotation_error_rad',0)>1e-6:
            raise RuntimeError(json.dumps(dict(stage=stage,failure=failure,mechanism=mechanism[:2],sole=sole,extra=extra)))
        return palm,cover
    def move(stage,offset):
        nonlocal q
        initial=base@fk(q)['right_palm_force_sensor'];target=translation(offset)@grasp
        for u in np.linspace(0,1,max(2,int(np.ceil(np.linalg.norm(target[:3,3]-initial[:3,3])/.003))+1)):
            desired=initial.copy();desired[:3,3]=(1-u)*initial[:3,3]+u*target[:3,3]
            scene.set_access(lid=lid,cover=desired@inverse_grasp)
            q,error,angle=solver.solve(base,desired,q);record(stage,error_m=error,rotation_error_rad=angle)
        print(stage,'passed',len(rows),flush=True)
    def walk(stage,delta):
        nonlocal base,q
        original=base.copy();rest=dict(q);foot_local={s:fk(rest)[s+'_ankle_roll_link'] for s in legs};count=max(1,math.ceil(np.linalg.norm(delta[:2])/.20));clock=0.
        for pair in range(count):
            begin=base.copy();end=original.copy();end[:3,3]+=np.array(delta)*(pair+1)/count
            yaw=math.atan2(base[1,0],base[0,0]);lead='left' if np.array(delta[:2])@np.array([-math.sin(yaw),math.cos(yaw)])>0 else 'right';order=[lead,'right' if lead=='left' else 'left'];feet={s:begin@foot_local[s] for s in legs}
            for half,swing in enumerate(order):
                other='right' if swing=='left' else 'left';start_foot=feet[swing].copy();end_foot=end@foot_local[swing]
                for knot,u in enumerate(np.linspace(0,1,35)):
                    if knot==0 and (half or pair):continue
                    blend=u*u*(3-2*u);amount=(half+blend)/2;base=begin.copy();base[:3,3]+=(end[:3,3]-begin[:3,3])*amount;base[2,3]-=.015*math.sin(math.pi*amount)
                    data.qpos[:3]=base[:3,3]+np.array(KIN['root_matrix'])[:3,3];data.qpos[3:7]=[math.cos(yaw/2),0,0,math.sin(yaw/2)]
                    for n,v in q.items():data.qpos[indices[n]]=v
                    targets={other:feet[other].copy(),swing:start_foot.copy()};targets[swing][:3,3]=(1-blend)*start_foot[:3,3]+blend*end_foot[:3,3];targets[swing][2,3]+=.04*math.sin(math.pi*u)**2;errors={}
                    for side,names in legs.items():
                        target=targets[side];idx=[indices[n] for n in names];limits=np.array([[JOINTS[n]['limits']['lower'],JOINTS[n]['limits']['upper']] for n in names]);body=data.body(side+'_ankle_roll_link')
                        def residual(values):
                            data.qpos[idx]=values;mujoco.mj_kinematics(model,data);return np.r_[body.xpos-target[:3,3],.20*Rotation.from_matrix(target[:3,:3]@body.xmat.reshape(3,3).T).as_rotvec()]
                        result=least_squares(residual,[q[n] for n in names],bounds=(limits[:,0]+1e-6,limits[:,1]-1e-6),max_nfev=80,ftol=1e-11,xtol=1e-11,gtol=1e-11);error=residual(result.x);q.update(dict(zip(names,map(float,result.x))))
                        errors[side]=dict(position_m=float(np.linalg.norm(error[:3])),orientation_rad=float(np.linalg.norm(error[3:])/.20),stance=side==other,target=target.tolist())
                    world=fk(q);agreement=max(float(np.max(abs((base@world[s+'_ankle_roll_link'])[:3,3]-data.body(s+'_ankle_roll_link').xpos))) for s in legs)
                    if agreement>1e-8 or any(e['position_m']>1e-5 or e['orientation_rad']>1e-5 for e in errors.values()):raise RuntimeError('Source foot IK failed')
                    record(stage,time_s=clock+.85*u,feet=errors,source_fk_position_error_m=agreement)
                feet[swing]=end_foot;clock+=.85
            base=end.copy();print(stage,'pair',pair+1,'/',count,flush=True)
        assert max(abs(q[n]-rest[n]) for names in legs.values() for n in names)<1e-6
    failure=None;exit_path=[]
    try:
        record('initial_hold')
        move('lift_clear_for_steps',[0,-.025,.041])
        walk('step_back',[0,-.20,0])
        move('lower_to_carry',[0,-.225,-.115])
        walk('carry_sideways',[.943,0,0])
        # Keep the hood above the bench while approaching its front edge.
        walk('approach_support',[0,.30,0])
        move('extend_over_support',[.943,.20,-.115])
        bottom=min(trimesh.transform_points(scene.access_meshes[n].vertices,scene.access_rest[n])[:,2].min() for n in scene.cover_names)
        move('lower_onto_support',[.943,.20,.850001-float(bottom)])
        supported=rows[-1]['cover_matrix'];supported=np.array(supported)
        closed=dict(q);opened=released['grasp']['opened']
        for u in np.linspace(0,1,31):
            q={**closed,**{n:closed[n]*(1-u)+v*u for n,v in opened.items()}};record('release_on_bench',held=False)
        first=base@fk(q)['right_palm_force_sensor']
        for u in np.linspace(0,1,31):
            target=first.copy();target[:3,3]+=[0,0,.06*u]
            q,error,angle=solver.solve(base,target,q);record('withdraw_from_support',held=False,error_m=error,rotation_error_rad=angle)
        rest=canonical({**poses['poses']['rest'],**poses['poses']['stance']});space=Space(scene,base,rest,q,{},open_hand=opened)
        exit_path=[dict(root=base.tolist(),q=space.q_at(v),held=False,cover_matrix=supported.tolist(),lid_m=lid) for v in reversed(plan(space))]
    except RuntimeError as exc:failure=str(exc);print('rejected',failure,flush=True)
    report=dict(scope=__doc__,passed_planning_geometry=failure is None,independent_composed_review_pending=True,rows=rows,exit=exit_path,failure=failure,source_snapshot=str(snapshot.relative_to(HERE)),source_sha256={n:hashlib.sha256(content).hexdigest() for n,content in sources.items()},geometry=scene.cary_geometry,geometry_sha256=hashlib.sha256((ROOT/scene.cary_geometry).read_bytes()).hexdigest(),seconds=time.monotonic()-started)
    (HERE/'previews'/(name+'.json')).write_text(json.dumps(report,separators=(',',':'))+'\n');print(json.dumps(dict(passed=report['passed_planning_geometry'],states=len(rows),seconds=report['seconds'])),flush=True)
    if failure:raise RuntimeError(failure)


if __name__=='__main__':main()
