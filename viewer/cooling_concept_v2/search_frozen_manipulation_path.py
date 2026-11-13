"""Resume one missing path from the recorded, pre-integration endpoint states."""
import argparse
import hashlib
import json
import time
from pathlib import Path
from plan_manipulation_approaches import HERE,Geometry,Space
from plan_optical_approaches import plan
from manipulation_inputs import load_inputs


def main():
    parser=argparse.ArgumentParser();parser.add_argument('name');parser.add_argument('--seed',type=int,default=20261027);args=parser.parse_args()
    packet=load_inputs()
    source=packet['frames'][args.name];space=Space(source,packet['extraGeometry'],Geometry());started=time.monotonic()
    print('planning',args.name,'obstacles',len(space.obstacles._objs),flush=True)
    try:
        route=plan(space,seed=args.seed)
        result=dict(passed=True,joints=space.names,knots=[v.tolist() for v in route],
                    generalized_finger_joint={'right_unused_finger_fold':['right_'+f+'_1_joint' for f in ['middle','ring','little']]} if space.kind=='lid' else {},
                    maximum_edge_step=.045,roi=space.roi.tolist(),obstacle_count=len(space.obstacles._objs),
                    path_length=sum(space.distance(a,b) for a,b in zip(route,route[1:])))
    except RuntimeError as error:result=dict(passed=False,error=str(error))
    result.update(name=args.name,scope=__doc__,seed=args.seed,source_sha256=packet['source_sha256'],
                  input_sha256=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest(),
                  planner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  geometry_checker_sha256=hashlib.sha256((HERE/'plan_manipulation_approaches.py').read_bytes()).hexdigest(),
                  rrt_sha256=hashlib.sha256((HERE/'plan_optical_approaches.py').read_bytes()).hexdigest(),
                  collision_queries=space.calls,seconds=time.monotonic()-started)
    file=HERE/'previews/manipulation_paths'/(args.name+'.json')
    if file.exists():
        old=file.with_name(file.stem+'.previous.'+hashlib.sha256(file.read_bytes()).hexdigest()[:12]+'.json')
        old.write_bytes(file.read_bytes())
    file.write_text(json.dumps(result,indent=2)+'\n')
    print(args.name,result['passed'],space.calls,result.get('error',''),flush=True)


if __name__=='__main__':main()
