"""Contact-wake diagnostic for an optionally sleeping instrument cover.

A small free sphere is added only to this diagnostic, then falls onto the
original cover under gravity. It is not a robot action or a demo asset. The
baseline and candidate use identical probe geometry and recorded motor inputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
import trimesh


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run(source, sleeping, output):
    source, sleeping, output = [Path(p).resolve() for p in [source,sleeping,output]]
    output.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(__file__,output/Path(__file__).name)
    trace = dict(np.load(source/'trace.npz'))
    model = mujoco.MjModel.from_xml_path(str(source/'world.xml'))
    data = mujoco.MjData(model);data.qpos[:]=trace['qpos'][0];mujoco.mj_forward(model,data)
    g = model.geom('lab_part_2294').id
    assert model.geom_bodyid[g] == model.body('nicolet_cover').id
    k = model.geom_dataid[g]
    v = model.mesh_vert[model.mesh_vertadr[k]:model.mesh_vertadr[k]+model.mesh_vertnum[k]].copy()
    f = model.mesh_face[model.mesh_faceadr[k]:model.mesh_faceadr[k]+model.mesh_facenum[k]].copy()
    v = v@data.geom_xmat[g].reshape(3,3).T+data.geom_xpos[g]
    mesh = trimesh.Trimesh(vertices=v,faces=f,process=False)
    ray=np.r_[np.mean(v[:,:2],axis=0),v[:,2].max()+.1]
    points,_,_=mesh.ray.intersects_location([ray],[[0.,0.,-1.]])
    assert len(points)>0
    surface=points[np.argmax(points[:,2])]
    start=surface+np.array([0.,0.,.045])
    histories,contacts,timings=[],[],[]
    for label,xml_path in [('baseline',source/'world.xml'),('candidate',sleeping/'world.xml')]:
        tree=ET.parse(xml_path).getroot()
        body=ET.SubElement(tree.find('worldbody'),'body',name='wake_diagnostic_probe',pos=' '.join(map(str,start)),sleep='never')
        ET.SubElement(body,'freejoint',name='wake_probe_free')
        ET.SubElement(body,'geom',name='wake_probe_geom',type='sphere',size='.005',mass='.02',rgba='1 0 0 1')
        ET.indent(tree);path=output/(label+'.xml');ET.ElementTree(tree).write(path,encoding='unicode')
        m=mujoco.MjModel.from_xml_path(str(path));d=mujoco.MjData(m)
        for j in range(model.njnt):
            n=model.joint(j).name
            width={0:7,1:4,2:1,3:1}[int(model.jnt_type[j])]
            d.joint(n).qpos[:]=trace['qpos'][0,model.jnt_qposadr[j]:model.jnt_qposadr[j]+width]
        mujoco.mj_forward(m,d)
        cover=m.body('nicolet_cover').id;probe=m.body('wake_diagnostic_probe').id;tid=int(m.body_treeid[cover])
        rows=[];states=[];started=time.monotonic()
        for i in range(round(.2/m.opt.timestep)):
            d.ctrl[:]=trace['ctrl'][i];mujoco.mj_step(m,d)
            load=0.
            for ci,c in enumerate(d.contact):
                if {int(m.geom_bodyid[g]) for g in c.geom}=={cover,probe}:
                    wrench=np.zeros(6);mujoco.mj_contactForce(m,d,ci,wrench);load+=max(0.,float(wrench[0]))
            rows.append([float(d.time),int(d.tree_asleep[tid]),load])
            states.append(np.r_[d.qpos,d.qvel])
        timings.append(time.monotonic()-started);histories.append(np.asarray(states));contacts.append(np.asarray(rows))
    c=contacts[1];loaded=np.flatnonzero(c[:,2]>1e-5);slept=np.flatnonzero(c[:,1]>=0)
    nq=(histories[0].shape[1]+model.nq-model.nv+1)//2
    delta=abs(histories[0]-histories[1])
    checks=dict(slept_before_impact=bool(len(loaded) and np.any(slept<loaded[0])),
        awake_during_loaded_contact=bool(len(loaded) and np.all(c[loaded,1]<0)),
        positive_probe_cover_contact=bool(len(loaded)),
        bounded_position_difference=bool(delta[:,:nq].max()<1e-5),
        bounded_velocity_difference=bool(delta[:,nq:].max()<1e-3))
    report=dict(scope=__doc__,source_model_sha256=sha(source/'world.xml'),sleep_candidate_sha256=sha(sleeping/'world.xml'),
        source_trace_sha256=sha(source/'trace.npz'),script_sha256=sha(output/Path(__file__).name),
        probe_mass_kg=.02,probe_radius_m=.005,probe_start_world_m=start.tolist(),
        surface_world_m=surface.tolist(),checks=checks,passed=all(checks.values()),
        sleeping_steps=len(slept),first_loaded_contact_s=float(c[loaded[0],0]) if len(loaded) else None,
        peak_probe_force_n=float(c[:,2].max()),maximum_position_difference=float(delta[:,:nq].max()),
        maximum_velocity_difference=float(delta[:,nq:].max()),seconds_baseline_candidate=timings,
        robot_execution_claimed=False,qualified_grasp=False)
    np.savez_compressed(output/'comparison.npz',baseline=histories[0],candidate=histories[1],
        baseline_contacts=contacts[0],candidate_contacts=contacts[1])
    (output/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('sleeping');p.add_argument('output')
    a=p.parse_args();run(a.source,a.sleeping,a.output)
