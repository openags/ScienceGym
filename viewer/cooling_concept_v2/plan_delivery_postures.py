"""Connect instrument-clearance and lower aisle-carrying arm postures."""
import hashlib,json
import numpy as np
from optical_choreography import HERE,ARM,load_json
from optical_delivery import DeliveryScene
from plan_optical_exchange import joint_path


def main():
    scene=DeliveryScene();fit=load_json('previews/optical_delivery_carry.json');assert fit['selected']
    low=fit['selected']['q'];outbound=load_json('previews/optical_white_delivery_walk.json');high=outbound['rows'][0]['q'];names=ARM+['waist_pitch_joint','waist_yaw_joint'];amount=scene.fit['carrier_grip_closure'];paths={}
    for station,index in [('ftir',1),('cary',-2)]:
        root=np.array(outbound['waypoints'][index]);path=joint_path(scene,root,high,low,dict(tool_held=True,closure=amount,held_specimen='white'))
        paths[station]=dict(root=root.tolist(),lower=path);print('planned lower',station,len(path['rows']),flush=True)
    walks={}
    for direction,filename in [('out','previews/optical_white_delivery_walk.json'),('back','previews/optical_white_return_walk.json')]:
        data=load_json(filename);roots=[np.array(data['waypoints'][i]) for i in [1,-2]];indices=[]
        for target in roots:
            matches=[i for i,r in enumerate(data['rows']) if np.max(abs(np.array(r['root'])-target))<1e-9];assert matches;indices.append(matches[-1])
        failures=[];count=0
        for row in data['rows'][indices[0]:indices[1]+1]:
            q={**row['q'],**{n:low[n] for n in names}};root=np.array(row['root']);held=scene.check(root,q,tool_held=True,closure=amount,held_specimen='white');empty=scene.check(root,{**q,**scene.hand_q(0.)},tool_held=True) if not held else {};count+=1
            if held or empty:failures.append(dict(time_s=row['time_s'],held=held,empty=empty))
            if count%200==0:print(direction,'lower_walk_checked',count,'failures',len(failures),flush=True)
        walks[direction]=dict(source=filename,lower_after_index=indices[0],raise_after_index=indices[1],sampled_states=count,failures=failures,passed=not failures)
    result=dict(scope=__doc__,posture=fit['selected'],joint_names=names,paths=paths,walks=walks,passed=all(w['passed'] for w in walks.values()),source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['plan_delivery_postures.py','previews/optical_delivery_carry.json','previews/optical_white_delivery_walk.json','previews/optical_white_return_walk.json','optical_delivery.py']})
    (HERE/'previews/optical_delivery_postures.json').write_text(json.dumps(result,indent=2)+'\n');print('postures',result['passed'],flush=True)


if __name__=='__main__':main()
