"""Fit ordinary tweezers across the annular carrier wall from above.

The two tips straddle the ring's inner and outer vertical faces. Neither tip
needs to enter underneath the bench-supported carrier or touch its coating.
This is a geometric handling candidate, not a force-qualified grasp.
"""
import hashlib,json
from pathlib import Path
import fcl,numpy as np,trimesh
from scipy.spatial.transform import Rotation
from source_geometry import ROOT,hand_manager,set_hand
from tweezers_geometry import meshes,provenance

HERE=Path(__file__).resolve().parent
CLOSURE=(.0056-.00495)/(.001775*2)


def transform(angle=300,withdrawal=0.):
    z=Rotation.from_euler('z',angle,degrees=True).as_matrix();matrix=np.eye(4)
    matrix[:3,:3]=z@np.array([[0,1,0],[0,0,1],[1,0,0]])
    matrix[:3,3]=z@np.array([.01505,-.00575,.0662+withdrawal])
    return matrix


def profile(closure,data):
    rows=data['rows'];i=min(int(closure*50),49);u=closure*50-i
    return {n:rows[i]['q'][n]*(1-u)+rows[i+1]['q'][n]*u for n in rows[i]['q']}


def main():
    source=HERE/'previews/tweezers_closure.json';data=json.loads(source.read_text());assert data['passed']
    witness=trimesh.collision.CollisionManager();path=ROOT/'assets/cooling_optical_specimens_v1/witness_white.glb';scene=trimesh.load(path,force='scene',process=False)
    for name in scene.graph.nodes_geometry:
        local,key=scene.graph[name];witness.add_object(name,scene.geometry[key],local)
    hand=hand_manager('right');rows=[];palm=np.array(data['palm_matrix']);tool=trimesh.collision.CollisionManager()
    phases=[('lower_open_tips',0.,.02*(1-u)) for u in np.linspace(0,1,41)]+[('close_on_carrier_wall',CLOSURE*u,0.) for u in np.linspace(0,1,41)]
    for stage,closure,withdrawal in phases:
        world=transform(300,withdrawal);tool=trimesh.collision.CollisionManager()
        for name,mesh in meshes(closure).items():tool.add_object(name,mesh,world)
        set_hand(hand,'right',profile(closure,data),world@palm)
        _,tp=tool.in_collision_other(witness,return_names=True);_,hp=hand.in_collision_other(witness,return_names=True)
        _,ht=hand.in_collision_other(tool,return_names=True)
        gaps=[]
        for name in ['ptfe_spring_arm_1','ptfe_spring_arm_-1']:
            d=fcl.DistanceResult();fcl.distance(tool._objs[name]['obj'],witness._objs['annular_carrier']['obj'],fcl.DistanceRequest(enable_nearest_points=True),d)
            gaps.append(dict(part=name,distance_m=float(d.min_distance),nearest_points=[np.asarray(x).tolist() for x in d.nearest_points]))
        bottom=min(float((mesh.vertices@world[2,:3]+world[2,3]).min()) for mesh in meshes(closure).values())
        rows.append(dict(stage=stage,closure=closure,withdrawal_m=withdrawal,tool_witness_intersections=sorted(tp),hand_witness_intersections=sorted(hp),hand_tool_intersections=sorted(ht),tip_to_carrier=gaps,minimum_tool_z_m=bottom))
    output=dict(scope=__doc__,passed=all(not any(r[n] for n in ['tool_witness_intersections','hand_witness_intersections','hand_tool_intersections']) and r['minimum_tool_z_m']>0 for r in rows),source=provenance(),closure_fit_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),witness_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),holder_T_tool=transform().tolist(),tool_T_palm=palm.tolist(),carrier_grip_closure=CLOSURE,carrier_grip_q=profile(CLOSURE,data),rows=rows)
    (HERE/'previews/specimen_tool_fit.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(dict(passed=output['passed'],rows=len(rows),final=rows[-1])),flush=True)


if __name__=='__main__':main()
