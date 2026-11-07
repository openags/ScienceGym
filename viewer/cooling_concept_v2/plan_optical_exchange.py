"""Connect tool pickup to white/black carrier grasp and the FTIR carrying pose.

This constructs manipulation segments for a later continuous local episode.
It does not claim upstream specimen delivery, scan execution or dynamics.
"""
import argparse,hashlib,json,time
import numpy as np
from scipy.spatial.transform import Rotation
from optical_choreography import HERE,Scene,Space,canonical,load_json,solve_palm
from plan_optical_tool_pickup import seed_targets
from plan_optical_approaches import plan


def joint_path(scene,base,start,goal,state):
    space=Space(scene,base,start,goal,state);path=plan(space)
    return dict(rows=[dict(q=space.q_at(v)) for v in path],collision_queries=space.calls,passed_planner_edges=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--kind',choices=['white','black'],default='white');args=parser.parse_args();began=time.monotonic();kind=args.kind
    scene=Scene();pickup=load_json('previews/optical_tool_pickup_path.json');port=load_json('previews/specimen_port_refined.json')['candidates'][0];base=np.array(pickup['root']);tool_start=pickup['contact'][-1]['q'];carry=canonical(port['rows'][-1]['q']);requests=[]
    for angle in [0,120,240]:
        holder=scene.specimen_rest[kind].copy();holder[:3,:3]=Rotation.from_euler('z',angle,degrees=True).as_matrix();target=holder@scene.holder_T_tool@scene.tool_T_palm;target[:3,3]+=[0,0,.02]
        for seed in [carry,tool_start]:
            q={**seed,**scene.hand_q(0.)};requests.append(dict(base=base.tolist(),target=target.tolist(),q=q,holder=holder.tolist(),angle=angle))
    requests=seed_targets(requests);candidates=[]
    for i,request in enumerate(requests):
        q,error,angular=solve_palm(base,np.array(request['target']),request['q'],waist=True);stored={kind:np.array(request['holder'])};failure=scene.check(base,q,tool_held=True,stored=stored)
        row=dict(angle=request['angle'],holder=request['holder'],q=q,error_m=error,rotation_error_rad=angular,failure=failure,passed=error<1e-7 and angular<1e-6 and not failure);candidates.append(row);print(kind,'endpoint',i,row['passed'],error,failure,flush=True)
    (HERE/'previews'/('optical_'+kind+'_exchange_endpoints.json')).write_text(json.dumps(candidates,indent=2)+'\n')
    for candidate in [c for c in candidates if c['passed']]:
        stored={kind:np.array(candidate['holder'])};holder=stored[kind];target=holder@scene.holder_T_tool@scene.tool_T_palm;q=dict(candidate['q']);contact=[];bad=False
        for u in np.linspace(0,1,41):
            desired=target.copy();desired[:3,3]+=[0,0,.02*(1-u)];q,error,angular=solve_palm(base,desired,q,waist=True);failure=scene.check(base,q,tool_held=True,stored=stored)
            contact.append(dict(stage='lower_open_tips',q=dict(q),closure=0.,held_specimen=None,error_m=error,rotation_error_rad=angular,failure=failure))
            if error>1e-7 or angular>1e-6 or failure:bad=True;break
        if bad:print(kind,'rejected approach',contact[-1]['failure'],contact[-1]['error_m'],flush=True);continue
        held_body=dict(q);amount=scene.fit['carrier_grip_closure']
        for u in np.linspace(0,1,41):
            q={**held_body,**scene.hand_q(amount*u)};failure=scene.check(base,q,tool_held=True,closure=amount*u,stored=stored)
            contact.append(dict(stage='close_tweezers',q=dict(q),closure=amount*u,held_specimen=None,failure=failure))
            if failure:bad=True;break
        if bad:print(kind,'rejected closure',contact[-1]['failure'],flush=True);continue
        for u in np.linspace(0,1,41):
            desired=target.copy();desired[:3,3]+=[0,0,.03*u];q,error,angular=solve_palm(base,desired,q,waist=True);failure=scene.check(base,q,tool_held=True,closure=amount,held_specimen=kind,stored=stored)
            contact.append(dict(stage='lift_witness',q=dict(q),closure=amount,held_specimen=kind,error_m=error,rotation_error_rad=angular,failure=failure))
            if error>1e-7 or angular>1e-6 or failure:bad=True;break
        if bad:print(kind,'rejected lift',contact[-1]['failure'],contact[-1]['error_m'],flush=True);continue
        print(kind,'planning tool-to-pregrasp',flush=True);approach=joint_path(scene,base,tool_start,candidate['q'],dict(tool_held=True,stored=stored))
        print(kind,'planning held carrier to walking pose',flush=True);transfer=joint_path(scene,base,q,carry,dict(tool_held=True,closure=amount,held_specimen=kind,stored=stored))
        empty_carry={**carry,**scene.hand_q(0.)};at_port={kind:scene.specimen_port}
        print(kind,'planning empty-tool return after mounting',flush=True);tool_return=joint_path(scene,base,empty_carry,tool_start,dict(tool_held=True,stored=at_port))
        result=dict(scope=__doc__,kind=kind,root=base.tolist(),initial_holder=holder.tolist(),approach=approach,contact=contact,transfer=transfer,empty_tool_return=tool_return,passed_local_geometry=True,whole_scene_validation_pending=True,wall_seconds=time.monotonic()-began,source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['plan_optical_exchange.py','optical_choreography.py','previews/optical_tool_pickup_path.json','previews/specimen_port_refined.json','previews/specimen_tool_fit.json']})
        (HERE/'previews'/('optical_'+kind+'_exchange.json')).write_text(json.dumps(result,indent=2)+'\n');print(kind,'exchange planned',result['wall_seconds'],flush=True);return
    raise RuntimeError('No complete carrier pickup path survived for '+kind)


if __name__=='__main__':main()
