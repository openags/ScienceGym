"""Connect Cary access, forceps pickup and exchange stances with grounded steps.

The existing full laboratory checks every generated source-leg IK state and
the carried forceps when present. This is kinematic composition, with no
balance, forces, closed-loop walking or independent interpolation credit.
"""
import argparse
import hashlib
import json
import time
import numpy as np
from cary_grounded_steps import translation_steps
from cary_tool_pickup_scene import CaryToolPickupScene
from optical_choreography import HERE


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--trial',default='01')
    parser.add_argument('--mode',choices=['to_pickup','to_exchange'],default='to_pickup')
    parser.add_argument('--pickup',default='previews/cary_tool_pickup_02/plan.json')
    parser.add_argument('--exchange',default='previews/cary_exchange_entry_01/plan.json')
    parser.add_argument('--carry',help='Validated withdrawal from the tool pickup into a walking posture.')
    args=parser.parse_args();out=HERE/'previews'/('cary_tool_transfer_'+args.mode+'_'+args.trial);out.mkdir(exist_ok=False)
    pickup=json.loads((HERE/args.pickup).read_text());assert pickup['passed'];p=pickup['candidates'][0]
    access=json.loads((HERE/'cary_access_episode.json').read_text())
    if args.mode=='to_pickup':initial=access['segments'][-1]['rows'][-1];goal=np.array(p['entry'][0]['root']);held=False
    else:
        exchange=json.loads((HERE/args.exchange).read_text());assert exchange['passed']
        if args.carry:
            carry=json.loads((HERE/args.carry).read_text());assert carry['passed']
            initial=carry['candidates'][0]['rows'][-1]
        else:initial=p['rows'][-1]
        goal=np.array(exchange['candidates'][0]['rows'][0]['root']);held=True
    names=['plan_cary_tool_transfer.py','cary_grounded_steps.py','cary_tool_pickup_scene.py','cary_tool_scene.py',
        'cary_clamp_scene.py','cary_clamp.py','cary_access_scene.py','optical_choreography.py',
        'optical_delivery.py','source_geometry.py','long_forceps.py','tweezers_geometry.py',
        'cary_access_episode.json','motion_poses.json',args.pickup,pickup['staging']]
    if held:names.append(args.exchange)
    if held and args.carry:names.append(args.carry)
    pins={}
    for name in names:
        data=(HERE/name).read_bytes();dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);pins[name]=hashlib.sha256(data).hexdigest()
    scene=CaryToolPickupScene(pickup['staging']);base=np.array(initial['root']);q=initial['q']
    assert np.max(abs(base[:3,:3]-goal[:3,:3]))<1e-10
    back=base.copy();back[1,3]=7.65;side=goal.copy();side[1,3]=7.65
    waypoints=[base,back,side,goal];rows=[];clock=0.;failure={};started=time.monotonic()
    for leg,(a,b) in enumerate(zip(waypoints,waypoints[1:])):
        planned=translation_steps(a,b,q)
        for row in planned:
            collision=scene.check(np.array(row['root']),row['q'],tool_held=held,closure=0.)
            if collision:failure=dict(leg=leg,time_s=clock+row['time_s'],collision=collision,row=row);break
            rows.append({**row,'time_s':clock+row['time_s'],'stage':args.mode,'tool_held':held,'closure':0.})
        if failure:break
        clock+=planned[-1]['time_s'];q=planned[-1]['q']
        print('leg clear',leg,'total states',len(rows),flush=True)
    report=dict(scope=__doc__,passed=not failure,mode=args.mode,rows=rows,failure=failure,
        waypoints=[m.tolist() for m in waypoints],source_sha256=pins,seconds=time.monotonic()-started,
        pickup=args.pickup,exchange=args.exchange if held else None,carry=args.carry if held else None,
        limitations=['Planning omits ankle housings; independent dense source geometry and speed retiming remain required.',
                     'Source-leg IK is not balance, force or sensor-controller qualification.'])
    (out/'plan.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],states=len(rows),failure=failure,seconds=report['seconds'])),flush=True)


if __name__=='__main__':main()
