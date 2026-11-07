"""Replay native observations to evaluate a revised isolated visual planner.

The candidate must reproduce the accepted sensor/control prefix. Only the final
failed planning packet may change. No motor commands are applied to a plant;
even a recovered plan grants no approach or manipulation qualification.
"""
import argparse
import json
from pathlib import Path
import pickle
import shutil
import subprocess
import sys
import time

import numpy as np

from verify_tool_grasp import difference, sha


def run(source, candidate, output):
    source,candidate,output=map(lambda p:Path(p).resolve(),[source,candidate,output])
    result=json.loads((source/'result.json').read_text())
    original=json.loads((source/'contract.json').read_text())
    contract=json.loads((candidate/'contract.json').read_text())
    isolation=json.loads((candidate/'actor_isolation.json').read_text())
    assert result['failure']=='No collision-screened path from observed geometry'
    assert result['contract_sha256']==sha(source/'contract.json')
    assert original['model_sha256']==contract['model_sha256']==sha(candidate/'world.xml')
    assert isolation['passed'] and contract['actor_module']=='visual_tool_actor'
    for name,h in isolation['source_modules'].items():assert sha(candidate/'actor_bundle/code'/name)==h
    for file,key in [('sensors.npz','sensors_sha256'),('responses.pkl','responses_sha256'),('camera_index.json','camera_index_sha256')]:
        assert sha(source/file)==result[key]
    sensors=dict(np.load(source/'sensors.npz'))
    responses=pickle.loads((source/'responses.pkl').read_bytes())
    frames=json.loads((source/'camera_index.json').read_text())
    assert len(responses)==len(sensors['time_s'])
    assert responses[-1]['failure']==result['failure'] and not any(x['failure'] or x['error'] for x in responses[:-1])
    output.mkdir(parents=True,exist_ok=False)
    for p in [Path(__file__),Path(__file__).with_name('verify_tool_grasp.py')]:shutil.copyfile(p,output/p.name)
    command=isolation['command_prefix']+[sys.executable,'/actor/visual_tool_actor.py','--model','/model/world.xml']
    report=dict(scope=__doc__,source_result_sha256=sha(source/'result.json'),actor_contract_sha256=sha(candidate/'contract.json'),
        actor_isolation_sha256=sha(candidate/'actor_isolation.json'),script_sha256=sha(__file__),
        physical_execution=False,qualified_approach=False,qualified_tool_actuation=False,qualified_paper_branch=False)
    started=time.monotonic();maximum_error=0.;failure=None;final=None
    with (output/'actor_stderr.log').open('wb') as log:
        child=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,env=isolation['environment'])
        try:
            for i,recorded in enumerate(responses):
                packet={k:v[i] for k,v in sensors.items()};frame=int(packet.pop('camera_frame_id'))
                packet.update(head_rgb=None,head_depth=None)
                if frame>=0:
                    info=frames[frame];path=source/info['file'];assert sha(path)==info['sha256']
                    with np.load(path) as data:packet.update({k:data[k] for k in data.files})
                pickle.dump(packet,child.stdin,protocol=5);child.stdin.flush();response=pickle.load(child.stdout)
                if i<len(responses)-1:
                    error=difference(recorded,{k:response[k] for k in recorded});maximum_error=max(maximum_error,error)
                    assert error<=1e-10, 'Changed prefix at packet '+str(i)
                else:
                    final=response
                    report.update(prefix_packets_replayed=i,maximum_prefix_response_error=maximum_error,
                        rejected_planning_time_s=float(packet['time_s']),candidate_phase=response.get('phase'),
                        candidate_failure=response.get('failure'),candidate_error=response.get('error'),
                        plan_recovered=response.get('phase')=='approach' and not response.get('failure') and not response.get('error'))
                    (output/'events.json').write_text(json.dumps(response.get('events',[]),indent=2)+'\n')
                    path=output/'candidate_final_response.pkl';path.write_bytes(pickle.dumps(response,protocol=5))
                    report['candidate_final_response_sha256']=sha(path)
                if i%1000==0:print('replayed',i,'of',len(responses),'wall_s',round(time.monotonic()-started,1),flush=True)
        except Exception as error:failure=type(error).__name__+': '+str(error)
        finally:
            child.stdin.close()
            try:child.wait(timeout=15)
            except subprocess.TimeoutExpired:child.kill();child.wait()
    report.update(failure=failure,wall_seconds=time.monotonic()-started)
    (output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)
    return not failure and report.get('plan_recovered',False)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('recording');p.add_argument('candidate');p.add_argument('output')
    a=p.parse_args()
    if not run(a.recording,a.candidate,a.output):raise SystemExit(1)
