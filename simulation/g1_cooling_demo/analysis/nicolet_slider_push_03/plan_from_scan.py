"""Exercise the runtime planner using retained preparation sensor inputs."""
import hashlib
import json
from pathlib import Path
import sys
import time

import mujoco
import numpy as np

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
ROOT=BASE.parents[1]
sys.path.insert(0,str(BASE))
from ftir_slider_posture import initialize_slider
from observations import StateEstimate
from ftir_slider_planning import SliderPlanner


def main():
    out=HERE/'sensor_plan.json'
    if out.exists():raise FileExistsError(out)
    started=time.monotonic();run=BASE/'runs/ftir_slider_scan_02'
    m=mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'))
    d=initialize_slider(m,[5.95,-5.20]);estimate=StateEstimate(m,d)
    sensors=np.load(run/'sensor_observations.npz');i=int(np.argmin(abs(sensors['time_s']-6.15)))
    packet={k:sensors[k][i] for k in sensors.files};packet['depth']=None;estimate.update(packet)
    result=json.loads((run/'result.json').read_text())
    observations=next(e['observations'] for e in result['actor_last_output']['events'] if e['state']=='observed_key_row')
    prior=ROOT/'assets/nicolet_6700_mechanism_v1/slider_push_prior.json'
    shape=ROOT/'assets/nicolet_6700_mechanism_v1/revisions/passive_dynamics/geometry/nicolet_passive_dynamics.glb'
    planner=SliderPlanner(m,d,observations,prior,shape)
    print('registered',planner.translation.tolist(),'root',d.qpos[:3].tolist(),flush=True)
    try:
        plan=planner.build()
        report=dict(passed=True,plan=plan)
    except Exception as error:
        report=dict(passed=False,error=str(error))
    deps=[Path(__file__),BASE/'ftir_slider_planning.py',BASE/'joint_rrt.py',BASE/'source_proximity.py',BASE/'robot_source_meshes.py',BASE/'ftir_slider_posture.py',run/'controller_model/world.xml',run/'sensor_observations.npz',run/'result.json',prior,shape]
    report.update(sensor_time_s=float(sensors['time_s'][i]),estimated_initial_qpos=d.qpos.tolist(),
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in deps},
        seconds=time.monotonic()-started,physical_push_executed=False,namespace_tested=False,
        scope='Runtime planning code exercised on actual prior preparation sensors, public robot/map model and unposed device CAD. No previous arm trajectory is loaded; this is still an offline diagnostic.')
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['plan','source_hashes','estimated_initial_qpos']}),flush=True)


if __name__=='__main__':main()
