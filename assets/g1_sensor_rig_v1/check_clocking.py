"""Reproduce the finite source-mesh wrist mount clocking search."""
import json,sys,trimesh,numpy as np
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'assets/unitree_g1_inspire_v1'));from kinematics import Robot
from audit import sha
r=Robot();rig=json.loads((HERE/'failed_mount_fixture.json').read_text());robot_manager=trimesh.collision.CollisionManager()
for node in r.preview.graph.nodes_geometry:
 t,k=r.preview.graph[node];robot_manager.add_object(node,r.preview.geometry[k],t)
all_results={}
for side in ['left','right']:
 subset=[a for a in rig['attachments'] if a['id'].startswith(side)];manager=trimesh.collision.CollisionManager()
 for a in subset:manager.add_object(a['id'],trimesh.load(ROOT/a['geometry_path'],force='scene').to_geometry())
 results=[]
 for x in [.0325,.035,.0365,.0375,.04,.0425]:
  for deg in range(0,360,15):
   adjust=trimesh.transformations.rotation_matrix(np.radians(deg),[1,0,0]);adjust[0,3]=x-.0365
   for a in subset:manager.set_transform(a['id'],r.bind[a['parent_link']]@adjust@a['parent_from_geometry'])
   hit,pairs=manager.in_collision_other(robot_manager,return_names=True)
   conflicts=[list(pair) for pair in sorted(pairs) if side+'_wrist_yaw_link_visual_0' not in pair]
   results.append(dict(x=x,clock_deg=deg,non_clamp_conflicts=conflicts,all_intersections=[list(p) for p in sorted(pairs)]))
 good=[v for v in results if not v['non_clamp_conflicts']]
 print(side,'no other-link intersections',len(good),flush=True)
 all_results[side]=results

report=dict(schema_version=1,source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [Path(__file__),HERE/'failed_mount_fixture.json',ROOT/'assets/unitree_g1_inspire_v1/SOURCE.json']],grid_results=all_results,meaning='Finite zero-pose search; parent wrist contact retained, never accepted by exclusion. No full containment, arm sweep or mechanical preload qualification.')
(HERE/'clocking_checks.json').write_text(json.dumps(report,indent=2)+'\n')
