"""Connect adjacent acquisition controls without lowering and raising the arm."""
import argparse
import hashlib
import json
import time
import numpy as np
from ftir_measurement_scene import FTIRMeasurementScene
from optical_choreography import HERE, Space
from plan_optical_approaches import plan


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--trial',default='01');args=parser.parse_args()
    out=HERE/'previews'/('ftir_button_transfers_'+args.trial);out.mkdir(exist_ok=False)
    names=['plan_ftir_button_transfers.py','ftir_measurement_scene.py','optical_delivery.py',
           'optical_choreography.py','plan_optical_approaches.py','previews/ftir_button_paths_01/plan.json']
    pins={}
    for name in names:
        data=(HERE/name).read_bytes();dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(data);pins[name]=hashlib.sha256(data).hexdigest()
    source=json.loads((HERE/names[-1]).read_text());assert source['passed']
    strokes={v['button']:v for v in source['candidates'][0]['strokes']}
    scene=FTIRMeasurementScene();routes=[];started=time.monotonic()
    for identity in ['scan_1','scan_0']:
        a,b=strokes[identity]['rows'][0],strokes['scan_2']['rows'][0]
        base=np.array(a['root']);assert np.max(abs(base-np.array(b['root'])))<1e-10
        space=Space(scene,base,a['q'],b['q'],{});failure=None
        try:
            path=plan(space)
            rows=[dict(q=space.q_at(v),root=base.tolist(),button_travel_m=0.) for v in path]
            endpoint=max(abs(rows[-1]['q'][n]-b['q'][n]) for n in b['q'])
            assert endpoint<1e-8
        except (RuntimeError,AssertionError) as error:
            failure=str(error);rows=[]
        routes.append(dict(start=identity,goal='scan_2',rows=rows,passed=failure is None,
                           failure=failure,collision_queries=space.calls))
        print(identity,'to scan_2','knots',len(rows),'failure',failure,flush=True)
    report=dict(scope=__doc__,passed=all(v['passed'] for v in routes),routes=routes,source_sha256=pins,
                seconds=time.monotonic()-started,limitations=['Planner omits ankle housings; full composed interpolation and physics remain unqualified.'])
    (out/'plan.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],seconds=report['seconds'])),flush=True)


if __name__=='__main__':main()
