"""Read a checked free-tool support state for offline grasp authoring.

Returns source-frame collision geometry for the actual retained support.
These evaluator/authoring records are never actor observations.
"""
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np
import trimesh
from scipy.spatial.transform import Rotation


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_support(path,project_root):
    path=Path(path).resolve();report=json.loads(path.read_text())
    assert report['passed']
    contract=json.loads((path.parent/'contract.json').read_text())
    assert sha(path.parent/'contract.json')==report['contract_sha256']
    for name,expected in contract['source_hashes'].items():
        assert sha(Path(project_root)/name)==expected,'Support source changed: '+name
    initial=np.asarray(report['tool_final_qpos'] if 'tool_final_qpos' in report else report['final_qpos'])
    world_from_source=np.eye(4)
    world_from_source[:3,:3]=Rotation.from_quat(np.r_[initial[4:7],initial[3]]).as_matrix()
    world_from_source[:3,3]=initial[:3]-world_from_source[:3,:3]@np.array([.13,0,.00575])
    obstacles=None;receipt=dict(review=str(path),review_sha256=sha(path),contract_sha256=report['contract_sha256'],
                                has_free_tray=False)
    if 'tray_final_qpos' in report:
        xml=path.parent/'support.xml';assert sha(xml)==contract['plant_sha256']
        model=mujoco.MjModel.from_xml_path(str(xml));data=mujoco.MjData(model)
        data.qpos[:]=report['full_final_qpos'];mujoco.mj_forward(model,data)
        tray=model.body('carrier_tray').id
        obstacles=trimesh.collision.CollisionManager()
        source_from_world=np.linalg.inv(world_from_source)
        mesh_receipts=[]
        for g in range(model.ngeom):
            if int(model.geom_bodyid[g])!=tray or not (model.geom_contype[g] or model.geom_conaffinity[g]):continue
            assert model.geom_type[g]==mujoco.mjtGeom.mjGEOM_MESH
            k=model.geom_dataid[g];v=model.mesh_vert[model.mesh_vertadr[k]:model.mesh_vertadr[k]+model.mesh_vertnum[k]].copy()
            f=model.mesh_face[model.mesh_faceadr[k]:model.mesh_faceadr[k]+model.mesh_facenum[k]].copy()
            mesh=trimesh.Trimesh(vertices=v,faces=f,process=False)
            tf=np.eye(4);tf[:3,:3]=data.geom_xmat[g].reshape(3,3);tf[:3,3]=data.geom_xpos[g]
            obstacles.add_object(model.geom(g).name,mesh,source_from_world@tf)
            mesh_receipts.append(dict(geom=model.geom(g).name,vertices_sha256=hashlib.sha256(v.tobytes()).hexdigest(),
                faces_sha256=hashlib.sha256(f.tobytes()).hexdigest(),world_transform=tf.tolist()))
        assert obstacles._objs
        receipt.update(has_free_tray=True,plant_sha256=sha(xml),compiled_support_meshes=mesh_receipts,
                       tray_contact_parameter_review_sha256=contract['tray_contact_parameter_review_sha256'])
    return initial,world_from_source,obstacles,receipt
