"""Check configurable pad geometry against retained defaults and native FK."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import mujoco
import numpy as np

HERE=Path(__file__).resolve().parent;BASE=HERE.parents[1];ROOT=BASE.parents[1]
sys.path.insert(0,str(BASE))
from ftir_hand import PointingHand,POINTING,mimic


def main():
    output=HERE/'hand_pose_regression.json'
    if output.exists():raise FileExistsError(output)
    run=BASE/'runs/ftir_slider_04';model_path=run/'controller_model/world.xml'
    m=mujoco.MjModel.from_xml_path(str(model_path))
    old_path=run/'source_snapshot/ftir_hand.py'
    spec=importlib.util.spec_from_file_location('retained_hand',old_path)
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    before=old.PointingHand(m);after=PointingHand(m)
    defaults={name:bool(np.array_equal(getattr(before,name),getattr(after,name)))
              for name in ['pad_vertices','pad_origin','pad_rotation']}
    rows=[]
    for index in [0.,.2,.4]:
        pose=dict(POINTING,right_index_1_joint=index,right_thumb_1_joint=.2,right_thumb_2_joint=.1)
        hand=PointingHand(m,pose);d=mujoco.MjData(m)
        d.qpos[:3]=[6.,-5.2,.8];d.qpos[3:7]=[np.cos(.17),0.,0.,np.sin(.17)]
        for name,value in pose.items():d.joint(name).qpos[0]=value
        d.joint('right_shoulder_pitch_joint').qpos[0]=-.4
        d.joint('right_elbow_joint').qpos[0]=.8
        mimic(m,d);mujoco.mj_forward(m,d)
        geom=m.geom('right_index_force_sensor_3_collision_0').id;mesh=m.geom_dataid[geom]
        va,vn=m.mesh_vertadr[mesh],m.mesh_vertnum[mesh]
        world=m.mesh_vert[va:va+vn]@d.geom(geom).xmat.reshape(3,3).T+d.geom(geom).xpos
        wrist=d.site('right_wrist_reference')
        predicted=hand.pad_vertices@wrist.xmat.reshape(3,3).T+wrist.xpos
        vertex_error=float(np.max(np.linalg.norm(predicted-world,axis=1)))
        point=hand.pad_vertices.mean(0)
        actual=hand.observed_contact_point(d,point)
        expected=wrist.xpos+wrist.xmat.reshape(3,3)@point
        mapping_error=float(np.linalg.norm(actual-expected))
        wrong=before.observed_contact_point(d,point)
        rows.append(dict(index_joint_rad=index,maximum_native_vertex_error_m=vertex_error,
                         contact_point_mapping_error_m=mapping_error,
                         wrong_default_pose_mapping_error_m=float(np.linalg.norm(wrong-expected))))
    checks=dict(default_geometry_bit_identical=all(defaults.values()),
                configured_geometry_matches_native_fk=all(r['maximum_native_vertex_error_m']<1e-9 for r in rows),
                configured_contact_mapping_matches_native_fk=all(r['contact_point_mapping_error_m']<1e-9 for r in rows),
                wrong_default_pose_negative_control_detected=rows[-1]['wrong_default_pose_mapping_error_m']>.001)
    deps=[Path(__file__),BASE/'ftir_hand.py',BASE/'ftir_slider_actor.py',old_path,model_path]
    report=dict(passed=all(checks.values()),checks=checks,default_arrays=defaults,rows=rows,
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in deps},
        scope='Hand-frame geometry regression only. No new reach, contact stability or physical task result.')
    output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
    if not report['passed']:raise SystemExit(1)


if __name__=='__main__':main()
