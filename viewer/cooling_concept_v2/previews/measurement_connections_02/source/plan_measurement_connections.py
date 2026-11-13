"""Connect reusable FTIR actions by full-room checked source-leg motion."""
import argparse
import hashlib
import json
import time
import numpy as np
from ftir_procedure_scene import FTIRProcedureScene
from optical_choreography import HERE, canonical, JOINTS
from measurement_walks import grounded_route


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--trial',default='01')
    parser.add_argument('--actions',required=True)
    parser.add_argument('--buttons')
    args=parser.parse_args()
    out=HERE/'previews'/('measurement_connections_'+args.trial);out.mkdir(exist_ok=False)
    names=['plan_measurement_connections.py','measurement_walks.py','ftir_procedure_scene.py',
           'ftir_measurement_scene.py','optical_delivery.py','optical_choreography.py','source_geometry.py',
           args.actions,'optical_episode.json','optical_delivery_episode.json','reference_transfer.json']
    if args.buttons:names.append(args.buttons)
    pins={}
    for name in names:
        data=(HERE/name).read_bytes();dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(data);pins[name]=hashlib.sha256(data).hexdigest()
    actions=json.loads((HERE/args.actions).read_text())['actions']
    optical=json.loads((HERE/'optical_episode.json').read_text())
    delivery=json.loads((HERE/'optical_delivery_episode.json').read_text())
    start=optical['segments'][0]['rows'][0];close=actions['ftir_close']['first']
    cap=actions['reference_restore']['first'];port=actions['reference_restore']['last']
    initial=delivery['initial_specimens'];staging={**initial,'white':optical['initial_specimens']['white']}
    scene=FTIRProcedureScene();mounted={**staging,'white':scene.specimen_port.tolist()}
    def variant(name,cover,reference,stored):return dict(name=name,cover=cover,reference=reference,stored=stored)
    opened=-65*np.pi/180;protected=cap['reference_delta'];installed=port['reference_delta']
    routes=[
      dict(id='staging_to_reference_cap',start=start,goal=cap,
           variants=[variant('gold_protected_white_staged',opened,protected,staging)]),
      dict(id='reference_port_to_cover',start=port,goal=close,
           variants=[variant('gold_installed_white_staged',opened,installed,staging)]),
      dict(id='staging_to_cover',start=start,goal=close,variants=[
           variant('initial_closed_white_at_materials',0.,protected,initial),
           variant('initial_open_white_at_materials',opened,protected,initial),
           variant('sample_mounted',opened,protected,mounted),
           variant('final_white_stored',opened,protected,staging)])]
    if args.buttons:
        buttons=json.loads((HERE/args.buttons).read_text());assert buttons['passed']
        goal=buttons['candidates'][0]['strokes'][0]['entry'][0]
        routes.append(dict(id='cover_to_controls',start=actions['ftir_close']['last'],goal=goal,variants=[
            variant('background',0.,installed,staging),variant('sample',0.,protected,mounted)]))
    results=[];started=time.monotonic()
    for route in routes:
        print('route',route['id'],flush=True)
        a,b=route['start'],route['goal'];q=canonical(a['q']);goal_q=canonical(b['q'])
        difference=max(abs(q[n]-goal_q[n]) for n in q)
        assert difference<1e-6,(route['id'],'endpoints are not the same empty-hand stance',difference)
        trajectory=grounded_route(a['root'],b['root'],q)
        failures=[]
        for configuration in route['variants']:
            scene.set_cover(configuration['cover']);scene.set_reference(configuration['reference'])
            for i,row in enumerate(trajectory['rows']):
                failure=scene.check(np.array(row['root']),row['q'],stored=configuration['stored'])
                if failure:
                    failures.append(dict(variant=configuration['name'],row=i,time_s=row['time_s'],failure=failure))
                    break
            print('checked',configuration['name'],'failures',len(failures),flush=True)
        speeds={n:max(abs(b['q'][n]-a['q'][n])/(b['time_s']-a['time_s']) for a,b in zip(trajectory['rows'],trajectory['rows'][1:]))
                for n in q}
        bad_speeds={n:v for n,v in speeds.items() if v>JOINTS[n]['limits']['velocity']+1e-6}
        results.append(dict(id=route['id'],**trajectory,variants=route['variants'],failures=failures,
                            maximum_joint_speeds_rad_s=speeds,speed_failures=bad_speeds,
                            passed=not failures and not bad_speeds))
    report=dict(scope=__doc__,passed=all(r['passed'] for r in results),routes=results,
                source_sha256=pins,seconds=time.monotonic()-started,
                limitations=['Ankle housings are omitted from the planning collision manager; soles and leg FK are checked.',
                             'Reverse reuse must preserve the same environment and ownership states.',
                             'Independent composed interpolation and dynamics are not qualified by this report.'])
    (out/'plan.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],routes=[dict(id=r['id'],passed=r['passed'],states=len(r['rows'])) for r in results],seconds=report['seconds'])),flush=True)


if __name__=='__main__':main()
