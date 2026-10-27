"""Inspect the official alternate model without replacing the active robot.

This unloaded source-model timing excludes the laboratory and controllers.
It does not establish grasping, balance, source collision fidelity or safety.
"""
import hashlib,json,time
from pathlib import Path
import mujoco,numpy as np,trimesh

HERE=Path(__file__).resolve().parent
path=HERE/'g1_29dof_with_hand_rev_1_0.xml'
model=mujoco.MjModel.from_xml_path(str(path));data=mujoco.MjData(model)
mujoco.mj_forward(model,data)
initial=[]
for c in data.contact:
    if c.dist<0:
        initial.append(dict(bodies=[model.body(model.geom_bodyid[int(g)]).name for g in c.geom],distance_m=float(c.dist)))
rows=[]
for mesh in (HERE/'meshes').glob('right_hand*.STL'):
    source=trimesh.load(mesh,force='mesh');hull=source.convex_hull
    rows.append(dict(name=mesh.stem,vertices=len(source.vertices),faces=len(source.faces),
                     extent_m=source.extents.tolist(),source_is_volume=bool(source.is_volume),
                     convex_volume_ratio=float(hull.volume/source.volume) if source.is_volume else None))
started=time.perf_counter()
for _ in range(100):mujoco.mj_step(model,data)
seconds=(time.perf_counter()-started)/100
report=dict(scope=__doc__,source_xml_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            body_count=model.nbody,geometries=model.ngeom,joints=model.njnt,actuators=model.nu,
            independent_right_hand_joints=[model.joint(i).name for i in range(model.njnt) if model.joint(i).name.startswith('right_hand')],
            initial_penetrations=initial,source_hand_meshes=rows,unloaded_step_wall_s=seconds,
            numerical_warning_count=int(np.sum(data.warning.number)),selected_robot_changed=False,qualified=False)
(HERE/'inspection.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['geometries','joints','actuators','unloaded_step_wall_s','initial_penetrations']}),flush=True)
