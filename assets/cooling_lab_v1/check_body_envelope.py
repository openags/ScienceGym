"""Measure existing H2 source meshes at recorded poses, without new execution.

The result concerns body geometry in a prior unloaded record. It is not a
walking, reachability, manipulation, hand integration or safety test.
"""
import sys
import json
import numpy as np
import mujoco
from geometry_tools import HERE,ROOT,sha,write_json

sys.path.insert(0,str(ROOT/'simulation/humanoid_v1'))
from world import load


def build():
    folder=ROOT/'simulation/humanoid_v1/runs/nominal'
    result=json.loads((folder/'result.json').read_text())
    verification=json.loads((folder/'verification.json').read_text())
    assert verification['passed'] and verification['result_sha256']==sha(folder/'result.json')
    assert result['artifacts_sha256']['physics_trace.npz']==sha(folder/'physics_trace.npz')
    model=load(folder/'workcell.xml');data=mujoco.MjData(model)
    trace=np.load(folder/'physics_trace.npz');meshes=[]
    for g in range(model.ngeom):
        if model.geom_group[g]!=1 or model.geom_type[g]!=mujoco.mjtGeom.mjGEOM_MESH:continue
        mesh_id=int(model.geom_dataid[g]);start=model.mesh_vertadr[mesh_id]
        meshes.append((g,model.mesh_vert[start:start+model.mesh_vertnum[mesh_id]]))
    # All 0.05 s samples from the pre-existing 20 s record; no interpolated poses.
    samples=[]
    for k in range(0,len(trace['time']),10):
        data.qpos[:]=trace['qpos'][k];mujoco.mj_forward(model,data)
        points=np.concatenate([v@data.geom_xmat[g].reshape(3,3).T+data.geom_xpos[g] for g,v in meshes])
        # Measured around the free-base XY origin, not the mesh bounding-box center.
        points[:,:2]-=data.qpos[:2]
        samples.append(dict(time_s=float(trace['time'][k]),trace_index=k,free_base_position_m=data.qpos[:3].tolist(),radial_extent_m=float(np.linalg.norm(points[:,:2],axis=1).max()),bounds_m=[points.min(axis=0).tolist(),points.max(axis=0).tolist()]))
    standing=min(samples,key=lambda s:abs(s['time_s']-3));maximum=max(samples,key=lambda s:s['radial_extent_m'])
    report=dict(scope='Recorded H2 body visual-mesh envelope; exact Dex5-S Pro and carried loads absent',
        sample_period_s=.05,samples=len(samples),source_visual_meshes=len(meshes),standing=standing,maximum_sampled=maximum,
        circumscribed_turn_diameter_m=2*maximum['radial_extent_m'],
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [folder/'physics_trace.npz',folder/'workcell.xml',folder/'result.json',ROOT/'assets/unitree_h2_v1/SOURCE.json',ROOT/'simulation/humanoid_v1/world.py']],
        checker_sha256=sha(__file__),recorded_pose_envelopes=samples,
        conclusion='An initial 0.50 m radius contained the recorded 3 s body pose but missed arms-forward poses. The scene now uses 0.65 m plus an authored 0.10 m margin. This covers the sampled body geometry only; selected hands, walking and carried loads still require their own envelopes.',
        exact_selected_hands_present=False,all_joint_configurations_tested=False,walking_validated=False,
        carried_load_tested=False,full_humanoid_space_accepted=False)
    assert standing['radial_extent_m']<.5 and maximum['radial_extent_m']>.5
    write_json(HERE/'body_envelope.json',report)
    print(json.dumps(dict(standing_radius_m=standing['radial_extent_m'],maximum_sampled_radius_m=maximum['radial_extent_m'],samples=len(samples)),indent=2))


if __name__=='__main__':build()
