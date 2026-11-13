"""Connect the tested lid and hood operations with actual alternating steps."""
import argparse,hashlib,json,time
from cary_access_scene import CaryAccessScene
from cary_grounded_steps import translation_steps
from optical_choreography import HERE,load_json


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--lid-plan',default='previews/cary_lid_operation_06.json');parser.add_argument('--output',default='previews/cary_lid_to_hood_steps.json');args=parser.parse_args()
    started=time.monotonic();names=['plan_cary_stances.py','cary_grounded_steps.py','cary_access_scene.py',args.lid_plan,'previews/cary_cover_release_01.json']
    sources={n:(HERE/n).read_bytes() for n in names}
    lid=load_json(names[-2]);hood=load_json(names[-1]);q=lid['exit'][-1]['q'];assert q==hood['entry'][0]['q']
    scene=CaryAccessScene(cover_candidate=True);scene.set_access(lid=lid['lid_travel_m'])
    rows=translation_steps(lid['root'],hood['root'],q)
    for row in rows:row['failure']=scene.check(row['root'],row['q'])
    passed=all(not row['failure'] for row in rows)
    result=dict(scope=__doc__,passed_planning_geometry=passed,independent_composed_review_pending=True,rows=rows,lid_m=lid['lid_travel_m'],seconds=time.monotonic()-started,source_sha256={n:hashlib.sha256(content).hexdigest() for n,content in sources.items()})
    (HERE/args.output).write_text(json.dumps(result,separators=(',',':'))+'\n');print(json.dumps(dict(passed=passed,states=len(rows),seconds=result['seconds'],failures=[r['failure'] for r in rows if r['failure']][:3])),flush=True)
    if not passed:raise RuntimeError('Stance transfer intersects the scene')


if __name__=='__main__':main()
