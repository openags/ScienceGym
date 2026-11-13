"""Stage existing tweezers with their heel on an ordinary tray rim.

The lower tip rests on the bench and the heel rests on the existing 50 mm
tray rim. The inclination gives the lower gripping finger room above the
bench. This is a proposed initial arrangement, not an executed placement or
a stability/cleanliness qualification.
"""
import hashlib,itertools,json
from pathlib import Path
import numpy as np,trimesh
from scipy.optimize import brentq
from scipy.spatial.transform import Rotation
from source_geometry import ROOT,ASSETS,hand_manager,set_hand,fk,robot_meshes
from tweezers_geometry import meshes

HERE=Path(__file__).resolve().parent


def main():
    data=json.loads((HERE/'previews/tweezers_closure.json').read_text());parts=meshes(0);vertices=np.concatenate([m.vertices for m in parts.values()]);heel=parts['joined_heel'].vertices
    def rot(angle):return Rotation.from_euler('y',-angle).as_matrix()@Rotation.from_euler('x',np.pi/2).as_matrix()
    def rise(angle):
        r=rot(angle);return float((heel@r[2]).min()-(vertices@r[2]).min())
    angle=brentq(lambda a:rise(a)-.050001,.2,.6);r=rot(angle);tool_pose=np.eye(4);tool_pose[:3,:3]=r;tool_pose[:3,3]=[9.90,8.25,.850001-(vertices@r[2]).min()]
    points=heel@r.T+tool_pose[:3,3];bottom=points[points[:,2]<points[:,2].min()+1e-8];tray_position=[float(bottom[:,0].mean()+.1494),float(points[:,1].mean()),.850001]
    source=trimesh.load(ROOT/ASSETS['tray_white']['geometry'],force='scene',process=False);tray=trimesh.collision.CollisionManager();tray_pose=np.eye(4);tray_pose[:3,3]=tray_position
    for name in source.graph.nodes_geometry:
        local,key=source.graph[name];tray.add_object(name,source.geometry[key],tray_pose@local)
    tool=trimesh.collision.CollisionManager()
    for name,mesh in parts.items():tool.add_object(name,mesh,tool_pose)
    # The source spring arms near the joined end extend slightly below the
    # nominal heel block. Find their real first supported orientation instead
    # of using the heel bounding box as a proxy for the complete tool.
    def place(value):
        rotation=rot(value);pose=np.eye(4);pose[:3,:3]=rotation;pose[:3,3]=[9.90,8.25,.850001-(vertices@rotation[2]).min()]
        for name in parts:tool.set_transform(name,pose)
        return pose
    low,high=angle,angle+.08
    place(high);assert not tool.in_collision_other(tray)
    for _ in range(35):
        mid=(low+high)/2;place(mid)
        if tool.in_collision_other(tray):low=mid
        else:high=mid
    angle=high+1e-5;tool_pose=place(angle);r=tool_pose[:3,:3]
    hit,pairs=tool.in_collision_other(tray,return_names=True)
    tool_tray_gap=tool.min_distance_other(tray)
    hand=hand_manager('right');hand_meshes=robot_meshes('right');palm=tool_pose@np.array(data['palm_matrix']);closed=data['rows'][0]['q'];candidates=[]
    for index,thumb in itertools.product([.30,.4,.5,.6],[.08,.12,.18,.24]):
        opened={**closed,'right_index_1_joint':index,'right_thumb_2_joint':thumb};checks=[]
        for u in np.linspace(0,1,41):
            q={n:opened[n]*(1-u)+closed[n]*u for n in closed};set_hand(hand,'right',q,palm)
            _,ht=hand.in_collision_other(tool,return_names=True);_,hp=hand.in_collision_other(tray,return_names=True)
            # The hand meshes are already in their local force-sensor frame.
            world=fk(q);base=palm@np.linalg.inv(world['right_palm_force_sensor'])
            bottom_z=min(float((mesh.vertices@(base@world[n])[2,:3]+(base@world[n])[2,3]).min()) for n,mesh in hand_meshes.items())
            checks.append(dict(u=float(u),hand_tool_intersections=sorted(ht),hand_tray_intersections=sorted(hp),minimum_hand_z_m=bottom_z))
        passed=all(not c['hand_tool_intersections'] and not c['hand_tray_intersections'] and c['minimum_hand_z_m']>.85001 for c in checks)
        candidates.append(dict(open_q=opened,checks=checks,passed=passed))
    result=dict(scope=__doc__,tool_world_matrix=tool_pose.tolist(),tray_position_m=tray_position,tool_inclination_rad=float(angle),tool_tray_intersections=sorted(pairs),joined_end_to_tray_gap_m=float(tool_tray_gap),tip_support_height_m=float((vertices@r[2]).min()+tool_pose[2,3]),candidate_count=len(candidates),candidates=candidates,passed_candidates=sum(c['passed'] for c in candidates),passed=not hit and any(c['passed'] for c in candidates) and tool_tray_gap<2e-6,source_tray_sha256=ASSETS['tray_white']['geometry_sha256'],fit_sha256=hashlib.sha256((HERE/'previews/tweezers_closure.json').read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (HERE/'previews/tweezers_staging.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['candidates','scope']}),flush=True)


if __name__=='__main__':main()
