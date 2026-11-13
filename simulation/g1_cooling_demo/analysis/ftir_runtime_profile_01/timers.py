"""MuJoCo internal timers at a retained unloaded full-plant state."""
import json,time
from pathlib import Path
import mujoco,numpy as np
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
run=ROOT/'simulation/g1_cooling_demo/runs/ftir_cover_12'
m=mujoco.MjModel.from_xml_path(str(run/'world.xml'));d=mujoco.MjData(m);trace=np.load(run/'trace.npz')
d.qpos[:]=trace['qpos'][0];d.qvel[:]=trace['qvel'][0];d.ctrl[:]=trace['ctrl'][0]
mujoco.set_mjcb_time(time.perf_counter)
for _ in range(50):mujoco.mj_step(m,d)
rows={name:dict(calls=int(d.timer[index].number),total_wall_s=float(d.timer[index].duration))
      for name,index in mujoco.mjtTimer.__members__.items() if name!='mjNTIMER'}
mujoco.set_mjcb_time(None)
(HERE/'timers.json').write_text(json.dumps(dict(scope=__doc__,rows=rows,steps=50),indent=2)+'\n')
print(json.dumps(rows),flush=True)
