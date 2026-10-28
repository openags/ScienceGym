"""Withdraw the lifted long forceps to a posture clear at both Cary stances.

The palm may change orientation while keeping the source grip. Check the
actual whole-body/tool meshes and the destination before planning the walk.
This supplies no dynamic carrying or balance qualification.
"""
import argparse
import hashlib
import json
import time
import numpy as np
from cary_tool_pickup_scene import CaryToolPickupScene
from optical_choreography import HERE,solve_position
from source_geometry import fk


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--trial',default='01')
    parser.add_argument('--pickup',default='previews/cary_tool_pickup_02/plan.json')
    parser.add_argument('--exchange',default='previews/cary_exchange_entry_01/plan.json')
    args=parser.parse_args();out=HERE/'previews'/('cary_tool_carry_'+args.trial);out.mkdir(exist_ok=False)
    pickup=json.loads((HERE/args.pickup).read_text());exchange=json.loads((HERE/args.exchange).read_text())
    assert pickup['passed'] and exchange['passed']
    names=['plan_cary_tool_carry.py','cary_tool_pickup_scene.py','cary_tool_scene.py','cary_clamp_scene.py',
        'cary_clamp.py','cary_access_scene.py','optical_choreography.py','optical_delivery.py',
        'source_geometry.py','long_forceps.py','tweezers_geometry.py','cary_access_episode.json',
        args.pickup,args.exchange,pickup['staging']]
    pins={}
    for name in names:
        data=(HERE/name).read_bytes();dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);pins[name]=hashlib.sha256(data).hexdigest()
    scene=CaryToolPickupScene(pickup['staging']);initial=pickup['candidates'][0]['rows'][-1]
    base=np.array(initial['root']);goal=np.array(exchange['candidates'][0]['rows'][0]['root'])
    assert np.max(abs(base[:3,:3]-goal[:3,:3]))<1e-10
    palm=base@fk(initial['q'])['right_palm_force_sensor'];failures=[];accepted=[];started=time.monotonic()
    for offset in [[0,-.12,.04],[0,-.10,.06],[.03,-.12,.04],[0,-.16,.06]]:
        q=dict(initial['q']);rows=[];failure={}
        for u in np.linspace(0.,1.,61):
            desired=palm[:3,3]+np.array(offset)*u;q,error=solve_position(base,desired,q)
            failure=scene.check(base,q,tool_held=True,closure=0.)
            if error>1e-5:failure['palm_position_error_m']=error
            if failure:break
            rows.append(dict(stage='withdraw_tool_to_carry',q=q,root=base.tolist(),tool_held=True,closure=0.,
                error_m=error,orientation_constraint='free; held tool follows source palm FK'))
        if not failure:failure=scene.check(goal,q,tool_held=True,closure=0.)
        if failure:failures.append(dict(offset_m=offset,fraction=float(u),failure=failure,completed_rows=rows))
        else:
            accepted.append(dict(offset_m=offset,rows=rows,destination_root=goal.tolist()));break
    report=dict(scope=__doc__,passed=bool(accepted),candidates=accepted,failures=failures,
        source_sha256=pins,pickup=args.pickup,exchange=args.exchange,seconds=time.monotonic()-started,
        limitations=['Planning omits ankle housings; independent interpolation and complete walk review remain required.',
                     'No physical grip, balance, dynamics or sensor-policy qualification.'])
    (out/'plan.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],failures=len(failures),seconds=report['seconds'])),flush=True)


if __name__=='__main__':main()
