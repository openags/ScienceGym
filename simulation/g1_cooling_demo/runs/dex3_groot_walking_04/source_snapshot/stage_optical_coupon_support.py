"""Author a supported coupon start without the earlier two-millimetre drop.

Only the initial free-coupon pose changes. Geometry, contact parameters,
robot state, tool/tray and other free objects remain exact. This does not credit
robot placement, fabrication or manipulation and is not a runtime state reset.
"""
import argparse
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

from frozen_collision_plugins import load, sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('scene',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--gap',type=float,default=.00002)
    a=p.parse_args()
    if not 0<=a.gap<=.00002:p.error('Supported initial clearance must be 0 to 20 micrometres')
    scene,out=a.scene.resolve(),a.output.resolve()
    binding=json.loads((scene/'binding.json').read_text())
    state=json.loads((scene/'initial_state.json').read_text())
    assert sha(scene/'world.xml')==binding['world_sha256']
    assert sha(scene/'initial_state.json')==binding['initial_state_sha256']
    loader=Path(__file__).with_name('frozen_collision_plugins.py')
    load(binding['collision_plugins'],sha(loader))
    m=mujoco.MjModel.from_xml_path(str(scene/'world.xml'));d=mujoco.MjData(m)
    d.qpos[:],d.qvel[:]=state['qpos'],state['qvel'];mujoco.mj_forward(m,d)
    old=d.qpos.copy();normal=d.body('carrier_tray').xmat.reshape(3,3)[:,2].copy()
    gap=float(binding['specimen_initial_support']['initial_release_gap_m'])
    joint=d.joint('optical_witness_white_free')
    # The tray's actual upper triangle is sloped. A ray at the specimen centre
    # plus a tray-axis offset ignores the higher surface under its rim. Select
    # the source triangle under the declared location and align the copper back
    # with that plane before placing it with the small declared clearance.
    gid=m.geom(binding['specimen_initial_support']['geom']).id
    mid=int(m.geom_dataid[gid]);start,count=m.mesh_vertadr[mid],m.mesh_vertnum[mid]
    vertices=m.mesh_vert[start:start+count].astype(float)@d.geom_xmat[gid].reshape(3,3).T+d.geom_xpos[gid]
    start,count=m.mesh_faceadr[mid],m.mesh_facenum[mid]
    triangles=vertices[m.mesh_face[start:start+count]]
    origin=np.asarray(binding['specimen_initial_support']['point_work_m'])+.05*normal
    direction=-normal
    edge1=triangles[:,1]-triangles[:,0];edge2=triangles[:,2]-triangles[:,0]
    h=np.cross(np.broadcast_to(direction,edge2.shape),edge2);det=np.einsum('ij,ij->i',edge1,h)
    inv=np.zeros_like(det);valid=abs(det)>1e-15;inv[valid]=1/det[valid]
    offset=origin-triangles[:,0];u=inv*np.einsum('ij,ij->i',offset,h)
    q=np.cross(offset,edge1);v=inv*(q@direction);distance=inv*np.einsum('ij,ij->i',edge2,q)
    valid &= (u>=-1e-10)&(v>=-1e-10)&(u+v<=1+1e-10)&(distance>=0)
    if not np.any(valid):raise ValueError('No source support triangle below declared specimen position')
    face=int(np.flatnonzero(valid)[np.argmin(distance[valid])]);point=origin+distance[face]*direction
    support_normal=np.cross(edge1[face],edge2[face]);support_normal/=np.linalg.norm(support_normal)
    if support_normal@normal<0:support_normal=-support_normal
    angle=float(np.arccos(np.clip(normal@support_normal,-1.,1.)))
    if angle>np.deg2rad(5):raise ValueError('Selected support plane exceeds bounded staging inclination')
    axis=np.cross(normal,support_normal)
    align=Rotation.from_rotvec(axis/np.linalg.norm(axis)*angle).as_matrix() if np.linalg.norm(axis)>1e-12 else np.eye(3)
    body=m.body('optical_witness_white').id
    old_position=d.xpos[body].copy();old_rotation=d.xmat[body].reshape(3,3).copy()
    rotation=align@old_rotation
    local=[]
    for own in np.flatnonzero(m.geom_bodyid==body):
        mesh=int(m.geom_dataid[own]);start,count=m.mesh_vertadr[mesh],m.mesh_vertnum[mesh]
        world=m.mesh_vert[start:start+count].astype(float)@d.geom_xmat[own].reshape(3,3).T+d.geom_xpos[own]
        local.extend((world-old_position)@old_rotation)
    rotated=np.asarray(local)@rotation.T+old_position
    clearance=float(np.min((rotated-point)@support_normal))
    joint.qpos[:3]=old_position+support_normal*(a.gap-clearance)
    quaternion=Rotation.from_matrix(rotation).as_quat()
    joint.qpos[3:]=np.r_[quaternion[3],quaternion[:3]]
    mujoco.mj_forward(m,d)
    bad=[dict(parts=[m.geom(int(g)).name for g in c.geom],distance_m=float(c.dist))
         for c in d.contact if body in m.geom_bodyid[c.geom] and c.dist<0]
    if bad:raise ValueError('Authored coupon initially intersects geometry: '+str(bad))
    qa=int(m.joint('optical_witness_white_free').qposadr[0])
    keep=np.ones(m.nq,dtype=bool);keep[qa:qa+7]=False
    assert np.array_equal(old[keep],d.qpos[keep])
    out.mkdir(parents=True,exist_ok=False)
    for name in ['world.xml','model_inputs.json']:shutil.copyfile(scene/name,out/name)
    snapshot=out/'source_snapshot';snapshot.mkdir()
    for path in [Path(__file__),loader]:shutil.copyfile(path,snapshot/path.name)
    state.update(qpos=d.qpos.tolist(),scope=__doc__)
    (out/'initial_state.json').write_text(json.dumps(state,indent=2)+'\n')
    binding.update(upstream_scene=str(scene),upstream_binding_sha256=sha(scene/'binding.json'),
        initial_state_sha256=sha(out/'initial_state.json'),
        source_snapshot_sha256={p.name:sha(p) for p in snapshot.iterdir()},
        coupon_initial_support_revision=dict(scope=__doc__,previous_gap_m=gap,selected_gap_m=a.gap,
            displacement_work_m=(d.qpos[qa:qa+3]-old[qa:qa+3]).tolist(),
            orientation_change_rad=angle,source_support_triangle=face,
            support_point_work_m=point.tolist(),support_normal_work=support_normal.tolist(),
            cause='Earlier authored 2 mm drop exceeded the unchanged 20 micrometre other-contact bound during pickup execution',
            source_reported_placement=False,physical_acceptance_unchanged=True,
            robot_tool_tray_and_other_object_states_exact=True),qualified_robot_handling=False)
    binding['specimen_initial_support']['initial_release_gap_m']=a.gap
    binding['specimen_initial_support']['point_work_m']=point.tolist()
    binding['specimen_initial_support']['support_normal_work']=support_normal.tolist()
    binding['specimen_initial_support']['optical_face_normal_work']=(rotation@np.array([0.,0.,-1.])).tolist()
    (out/'binding.json').write_text(json.dumps(binding,indent=2)+'\n')
    print(json.dumps(binding['coupon_initial_support_revision']),flush=True)


if __name__=='__main__':main()
