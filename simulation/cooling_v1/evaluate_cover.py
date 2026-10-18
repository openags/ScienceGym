"""Observe actual rigid/flex support after release, including cloth strain."""
import numpy as np
import mujoco


def measure(model,data,target,support):
    bid=model.body('cover').id;vector=np.zeros(3);support_geoms=set();finger_contacts=0
    for i,c in enumerate(data.contact):
        names=[]
        for g,f in zip(c.geom,c.flex):
            if g>=0:names.append(model.body(int(model.geom_bodyid[g])).name)
            else:
                name=mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_FLEX,int(f))
                names.append('cover' if name.startswith('cover_') else name)
        if 'cover' not in names:continue
        force=np.zeros(6);mujoco.mj_contactForce(model,data,i,force)
        if {'left_finger','right_finger'}&set(names) and force[0]>.01:finger_contacts+=1
        if support not in names:continue
        sign=1 if names[1]=='cover' else -1
        vector+=(c.frame.reshape(3,3).T@force[:3])*sign
        if force[0]>.0001:
            side=names.index(support);support_geoms.add(model.geom(int(c.geom[side])).name)
    p=data.body('cover').xpos.copy();weight=float(model.body_subtreemass[bid])*9.81
    strain=float(np.max(np.abs(data.flexedge_length/model.flexedge_length0-1)))
    tilt=float(np.arccos(np.clip(data.body('cover').xmat[8],-1,1)))
    speed=float(np.linalg.norm(data.body('cover').cvel));error=float(np.linalg.norm(p-target))
    return dict(passed=bool(error<.002 and tilt<.012 and speed<.02 and strain<.01
                           and abs(vector[2]-weight)<.2*weight and not finger_contacts
                           and model.nflex==2 and not any(w.number for w in data.warning)),
                position_m=p.tolist(),error_m=error,tilt_rad=tilt,speed=speed,
                max_edge_strain=strain,vertical_support_force_n=float(vector[2]),
                weight_n=weight,support_geoms=sorted(support_geoms),finger_contacts=finger_contacts)


def evaluate(robot,checkpoints):
    data=mujoco.MjData(robot.model);rows=[]
    for item in checkpoints:
        trace=min(robot.trace,key=lambda row:abs(row[0]-item['time']))
        data.qpos[:]=trace[1];data.qvel[:]=trace[2];data.ctrl[:]=trace[3]
        mujoco.mj_forward(robot.model,data)
        rows.append(dict(time_s=trace[0],support=item['support'],**measure(robot.model,data,np.array(item['target']),item['support'])))
    return dict(passed=len(rows)==2 and all(x['passed'] for x in rows),checks=rows,whole_paper_validated=False)
