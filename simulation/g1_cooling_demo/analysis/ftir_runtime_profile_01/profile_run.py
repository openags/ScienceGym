"""Bounded runtime component timings at retained states; concurrent development load."""
import json
import time
from pathlib import Path
import mujoco
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
run=ROOT/'simulation/g1_cooling_demo/runs/ftir_cover_12'
model=mujoco.MjModel.from_xml_path(str(run/'world.xml'))
data=mujoco.MjData(model);trace=np.load(run/'trace.npz')
renderer=mujoco.Renderer(model,height=360,width=640,max_geom=model.ngeom+1000)
option=mujoco.MjvOption();option.geomgroup[3]=0;option.sitegroup[:]=0
rows=[]
for t in [0.,16.,19.]:
    i=np.argmin(abs(trace['time']-t));data.qpos[:]=trace['qpos'][i];data.qvel[:]=trace['qvel'][i]
    data.ctrl[:]=trace['ctrl'][i];mujoco.mj_forward(model,data)
    start=time.perf_counter()
    for _ in range(50):mujoco.mj_step(model,data)
    physics=(time.perf_counter()-start)/50
    start=time.perf_counter()
    for _ in range(5):renderer.update_scene(data,camera='head_rgb',scene_option=option)
    update=(time.perf_counter()-start)/5
    start=time.perf_counter()
    for _ in range(5):renderer.render()
    rgb=(time.perf_counter()-start)/5
    renderer.enable_depth_rendering()
    start=time.perf_counter()
    for _ in range(5):renderer.render()
    depth=(time.perf_counter()-start)/5
    renderer.disable_depth_rendering()
    row=dict(start_time_s=float(trace['time'][i]),physics_step_wall_s=physics,scene_update_wall_s=update,
             rgb_render_wall_s=rgb,depth_render_wall_s=depth,contacts=int(data.ncon))
    rows.append(row);print(json.dumps(row),flush=True)
from OpenGL.GL import glGetString,GL_RENDERER
report=dict(scope=__doc__,rows=rows,geometries=model.ngeom,renderer=glGetString(GL_RENDERER).decode(),
            physical_execution_qualified=False)
(HERE/'review.json').write_text(json.dumps(report,indent=2)+'\n')
renderer.close()
