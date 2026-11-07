"""Static sensitivity bound, using existing poses, not a new robot episode.

Triangle inequalities bound the authored hand chain at ANY joint angles.
The 30 mm wrist adapter allowance is an explicit design assumption, not a
verified H2/Dex5-S mount. Loads, walking, stopping and real hand uncertainty
outside this reconstruction are not covered.
"""
import json
import math
import sys
import numpy as np
import trimesh
import mujoco
from geometry_tools import HERE,ROOT,sha,write_json
sys.path.insert(0,str(ROOT/'simulation/humanoid_v1'))
from world import load

def build():
    hand_root=ROOT/'assets/unitree_dex5s_reconstruction_v1'
    model_record=json.loads((hand_root/'model.json').read_text());hand_bounds=[]
    for h in model_record['hands']:
        k=json.loads((ROOT/h['kinematics']).read_text());mesh=trimesh.load(ROOT/h['path'],force='scene')
        lengths={'palm':0.}
        for j in k['joints']:lengths[j['id']]=lengths[j['parent']]+float(np.linalg.norm(j['origin_m']))
        maximum=0
        for node in mesh.graph.nodes_geometry:
            transform,name=mesh.graph[node];link=k['part_links'][node]
            local=trimesh.transform_points(mesh.geometry[name].vertices,np.linalg.inv(k['bind_world'][link])@transform)
            maximum=max(maximum,lengths[link]+float(np.linalg.norm(local,axis=1).max()))
        hand_bounds.append(dict(side=h['id'],all_authored_joint_angles_radius_m=maximum))
    adapter_allowance=.030
    reserved_hand_radius=math.ceil((max(h['all_authored_joint_angles_radius_m'] for h in hand_bounds)+adapter_allowance)*100)/100
    folder=ROOT/'simulation/humanoid_v1/runs/nominal';body=load(folder/'workcell.xml');data=mujoco.MjData(body)
    trace=np.load(folder/'physics_trace.npz');samples=[]
    for index in range(0,len(trace['time']),10):
        data.qpos[:]=trace['qpos'][index];mujoco.mj_forward(body,data)
        for side in ['left','right']:
            radius=float(np.linalg.norm(data.site(side+'_wrist_reference').xpos[:2]-data.qpos[:2]))
            samples.append(dict(trace_index=index,time_s=float(trace['time'][index]),side=side,wrist_radius_m=radius))
    worst=max(samples,key=lambda r:r['wrist_radius_m'])
    body_radius=json.loads((HERE/'body_envelope.json').read_text())['maximum_sampled']['radial_extent_m']
    selected_radius=math.ceil(max(body_radius,worst['wrist_radius_m']+reserved_hand_radius)*100)/100
    sources=[hand_root/'model.json',HERE/'body_envelope.json',folder/'physics_trace.npz',folder/'workcell.xml',ROOT/'simulation/humanoid_v1/world.py']
    sources += [ROOT/h[field] for h in model_record['hands'] for field in ['path','kinematics']]
    report=dict(schema_version=1,status='bounded_design_sensitivity_not_spatial_acceptance',
      hand_bounds=hand_bounds,wrist_adapter_allowance_m=adapter_allowance,reserved_hand_radius_m=reserved_hand_radius,
      wrist_samples=len(samples),worst_sample=worst,selected_body_hand_radius_m=selected_radius,additional_route_margin_m=.10,
      minimum_required_half_width_m=selected_radius+.10,
      source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in sources],checker_sha256=sha(__file__),
      load_included=False,dynamic_motion_validated=False,actual_mount_qualified=False,full_spatial_acceptance=False,
      limitations=['Existing unloaded poses sampled every 0.05 s; no walking or new manipulation sequence',
       'Hand bound is valid for the authored chain, not proof of true hardware joint frames',
       '30 mm wrist mounting allowance is a declared design assumption requiring later qualification',
       'No carried loads, camera mount envelopes, stopping/falling or balance coverage'])
    write_json(HERE/'hand_envelope.json',report)
    print(json.dumps({'selected_radius_m':selected_radius,'required_half_width_m':selected_radius+.10,'hand_reserve_m':reserved_hand_radius}))

if __name__=='__main__':build()
