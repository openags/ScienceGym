"""Counterfactual sensor replay: omit only unused moving-walk camera frames.

Preserve the initial frame and resume full-rate capture as soon as the prior
actor response reports parked walking. Registration and manipulation retain
all native frames. This checks an optimization before changing any runner;
it is not a new physical run or a successful experimental procedure.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pickle
import shutil
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np
from isolation import namespace_prefix
from verify_ftir_approach import frames, plain, event_differences
from verify_slider_outcome import difference, json_finite


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run(folder, output):
    folder,output=Path(folder).resolve(),Path(output).resolve()
    if output.exists():raise FileExistsError(output)
    output.mkdir(parents=True);shutil.copyfile(__file__,output/Path(__file__).name)
    receipt=json.loads((folder/'actor_isolation.json').read_text())
    staging=json.loads((folder/'staging.json').read_text())
    result=json.loads((folder/'result.json').read_text())
    code=folder/'actor_bundle/code';model=folder/'actor_bundle/model'
    if sha(model/'world.xml')!=receipt['bundled_model_sha256'] or any(sha(code/n)!=h for n,h in receipt['source_modules'].items()):
        raise ValueError('Frozen actor changed')
    sensors=dict(np.load(folder/'sensor_observations.npz'));trace=dict(np.load(folder/'trace.npz'))
    responses={round(r['time_s'],8):r for r in json.loads((folder/'actor_responses.json').read_text())}
    colors=iter(frames(folder,'head_rgb_index.json','chunks'));depths=iter(frames(folder,'head_depth_index.json','parts',depth=True))
    color=next(colors,None);depth=next(depths,None)
    command=namespace_prefix(code,model)+[sys.executable,'/actor/ftir_approach_actor.py','--model','/model/world.xml',
        '--initial-xy',*map(str,staging['robot_map_xy_prior_m']),'--station-xy',*map(str,staging['station_map_xy_goal_m']),
        '--walking-controller',staging['walking_controller']]
    if staging['walking_controller']!='quasistatic':raise ValueError('This camera schedule is only for the declared slow walker')
    previous={};max_torque=max_response=0.;compared=0;omitted=[];retained=[];failure=None
    with open(output/'actor_stderr.log','x') as stderr:
        actor=subprocess.Popen(command,env=receipt['environment'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr,close_fds=True)
        try:
            for i,t in enumerate(sensors['time_s']):
                packet={k:v[i] for k,v in sensors.items()};packet.update(rgb=None,depth=None)
                if color is not None and abs(color[0]-t)<1e-8:
                    if depth is None or abs(depth[0]-t)>1e-8:raise ValueError('Unpaired camera frame')
                    unused=(previous.get('mission_stage')=='approach' and previous.get('walking_phase') not in {None,'parked'})
                    if unused:
                        omitted.append(float(t))
                    else:
                        packet.update(rgb=color[1],depth=depth[1]);retained.append(float(t))
                    color,depth=next(colors,None),next(depths,None)
                pickle.dump(packet,actor.stdin,protocol=5);actor.stdin.flush();answer=pickle.load(actor.stdout)
                if answer.get('error'):raise RuntimeError(answer['error'])
                max_torque=max(max_torque,float(np.max(abs(answer['torque']-trace['ctrl'][i]))))
                key=round(float(t),8)
                if key in responses:
                    comparable=dict(time_s=float(t),**{k:plain(v) for k,v in answer.items() if k not in {'torque','events'}})
                    max_response=max(max_response,difference(comparable,responses[key]));compared+=1
                previous=answer
                if i%5000==0:print('camera_omission_replay',i,len(sensors['time_s']),'torque_error',max_torque,'response_error',max_response,flush=True)
        except Exception as error:
            failure=str(error)
        finally:
            actor.stdin.close()
            try:actor.wait(timeout=15)
            except subprocess.TimeoutExpired:actor.kill();actor.wait()
    actual=plain(previous.get('events',[]));expected=result.get('actor_last_output',{}).get('events',[])
    event_error=difference(actual,expected)
    checks=dict(actor_completed=failure is None and actor.returncode==0,
                original_initial_frame_kept=bool(retained) and retained[0]==0.,
                unused_frames_were_omitted=len(omitted)>0,
                all_native_camera_inputs_accounted=color is None and depth is None,
                every_motor_unchanged=max_torque<1e-8,
                every_retained_response_unchanged=compared==len(responses) and max_response<1e-9,
                every_event_unchanged=event_error<1e-9)
    report=json_finite(dict(passed=all(checks.values()),checks=checks,failure=failure,
        maximum_torque_difference_nm=max_torque,maximum_response_difference=max_response,maximum_event_difference=event_error,
        event_difference_examples=event_differences(actual,expected),omitted_camera_times_s=omitted,retained_camera_times_s=retained,
        native_sensor_packets=len(sensors['time_s']),compared_responses=compared,original_attempt_status=result['status'],
        qualified_physical_execution=False,qualified_paper_branch=False,scope=__doc__,
        source_hashes={str(p):sha(p) for p in [Path(__file__),folder/'result.json',folder/'actor_isolation.json',folder/'sensor_observations.npz',folder/'trace.npz']}))
    (output/'replayed_events.json').write_text(json.dumps(json_finite(actual),indent=2,allow_nan=False)+'\n')
    (output/'review.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(passed=report['passed'],checks=checks,omitted=len(omitted),retained=len(retained))),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder');p.add_argument('output');a=p.parse_args()
    if not run(a.folder,a.output)['passed']:raise SystemExit(1)
