"""Follow source-finger closure against the explicitly bent tweezer arms."""
import hashlib,json
from pathlib import Path
import fcl,numpy as np,trimesh
from scipy.optimize import least_squares
from source_geometry import hand_manager,set_hand
from tweezers_geometry import meshes,provenance

HERE=Path(__file__).resolve().parent


def main():
    source=HERE/'previews/tweezers_right_fit.json';search=json.loads(source.read_text())
    candidate=next(c for c in search['candidates'] if abs(c['index_contact'][2][0]-c['thumb_contact'][2][0])<.01)
    palm=np.array(candidate['palm_matrix']);hand=hand_manager('right');q=dict(candidate['q']);rows=[]
    names=['right_index_1_joint','right_thumb_2_joint'];values=np.array([q[n] for n in names]);contact_keys=[candidate['index_contact'],candidate['thumb_contact']]
    target=np.array([c[0] for c in contact_keys])
    for closure in np.linspace(0,1,51):
        tool=trimesh.collision.CollisionManager()
        for name,mesh in meshes(float(closure)).items():tool.add_object(name,mesh)
        def evaluate(v,details=False):
            q.update(dict(zip(names,v)));set_hand(hand,'right',q,palm);dist=[];points=[]
            for c in contact_keys:
                result=fcl.DistanceResult();fcl.distance(hand._objs[c[3]]['obj'],tool._objs[c[1]]['obj'],fcl.DistanceRequest(enable_nearest_points=True),result)
                dist.append(float(result.min_distance));points.append([np.asarray(x).tolist() for x in result.nearest_points])
            return (dist,points) if details else np.array(dist)-target
        solved=least_squares(evaluate,values,bounds=([.4,.15],[.9,.5]),diff_step=1e-4,ftol=1e-12,xtol=1e-12,gtol=1e-12,max_nfev=80);values=solved.x
        distances,points=evaluate(values,True);_,pairs=hand.in_collision_other(tool,return_names=True)
        _,self_pairs=hand.in_collision_internal(return_names=True)
        self_pairs=[p for p in self_pairs if ('thumb' in p[0] and any(f in p[1] for f in ['index','middle','ring','little'])) or ('thumb' in p[1] and any(f in p[0] for f in ['index','middle','ring','little']))]
        rows.append(dict(closure=float(closure),q=dict(q),distances_m=distances,nearest_points=points,hand_tool_intersections=sorted(pairs),finger_intersections=sorted(self_pairs),maximum_contact_gap_m=max(distances)))
    result=dict(scope=__doc__,source=provenance(),search_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),candidate=candidate,palm_matrix=palm.tolist(),rows=rows,passed=all(not r['hand_tool_intersections'] and not r['finger_intersections'] and r['maximum_contact_gap_m']<.0005 for r in rows),limits='Local hand/tool mesh fit only. No approach, fixture, specimen, robot/environment, force or dynamics qualification.')
    (HERE/'previews/tweezers_closure.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=result['passed'],first=rows[0],last=rows[-1])),flush=True)


if __name__=='__main__':main()
