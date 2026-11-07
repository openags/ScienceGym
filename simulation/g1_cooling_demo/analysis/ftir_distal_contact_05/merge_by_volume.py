"""Try volume-prioritized conforming cell growth on the same tetrahedra.

The merge acceptance tolerances match convex_cells.decompose. No cells are
discarded and no collision approximation tolerance is relaxed.
"""
import heapq,json,time,numpy as np,trimesh
from pathlib import Path
from scipy.spatial import ConvexHull

HERE=Path(__file__).resolve().parent;prior=HERE.parent/'ftir_distal_contact_03'
for link,filename in [('right_thumb_4','thumb_external_tetrahedra.npz'),('right_index_2','right_index_2_1e-06_tetrahedra.npz')]:
 start=time.monotonic();data=np.load(prior/filename);points=data['points'];elements=data['elements']
 volumes=abs(np.linalg.det(points[elements[:,1:]]-points[elements[:,:1]]))/6
 cells={i:set(map(int,e)) for i,e in enumerate(elements)};volume=dict(enumerate(volumes));neighbors={i:set() for i in cells};faces={};versions={i:0 for i in cells}
 for i,e in enumerate(elements):
  for omit in range(4):
   face=tuple(sorted(np.delete(e,omit)))
   if face in faces:
    j=faces.pop(face);neighbors[i].add(j);neighbors[j].add(i)
   else:faces[face]=i
 queue=[]
 def push(i,j):
  i,j=sorted([i,j]);heapq.heappush(queue,(-(volume[i]+volume[j]),i,j,versions[i],versions[j]))
 for i in cells:
  for j in neighbors[i]:
   if i<j:push(i,j)
 attempts=0;merged=0
 while queue:
  _,i,j,vi,vj=heapq.heappop(queue)
  if i not in cells or j not in cells or versions[i]!=vi or versions[j]!=vj or j not in neighbors[i]:continue
  attempts+=1;indices=sorted(cells[i]|cells[j]);hull=ConvexHull(points[indices]);expected=volume[i]+volume[j]
  if abs(hull.volume-expected)>max(1e-15,expected*3e-7):continue
  cells[i]={indices[k] for k in hull.vertices};volume[i]=expected;versions[i]+=1;merged+=1
  adjacent=(neighbors[i]|neighbors[j])-{i,j}
  for k in adjacent:neighbors[k].discard(i);neighbors[k].discard(j);neighbors[k].add(i)
  neighbors[i]=adjacent;del cells[j],neighbors[j],volume[j]
  for k in adjacent:push(i,k)
  if merged%2000==0:print(link,'merged',merged,'cells',len(cells),'attempts',attempts,flush=True)
 parts=[trimesh.convex.convex_hull(points[sorted(v)]) for v in cells.values()]
 total=sum(p.volume for p in parts);expected=float(volumes.sum());error=abs(total-expected)/expected
 assert abs(total-expected)<=max(1e-14,expected*2e-6)
 # A single packed candidate supports later comparison without thousands of
 # temporary files. Faces remain local to each vertex interval.
 vo=np.cumsum([0]+[len(p.vertices) for p in parts]);fo=np.cumsum([0]+[len(p.faces) for p in parts])
 np.savez_compressed(HERE/(link+'_cells.npz'),vertices=np.vstack([p.vertices for p in parts]),faces=np.vstack([p.faces for p in parts]),vertex_offsets=vo,face_offsets=fo)
 report=dict(scope=__doc__,link=link,cells=len(parts),tetrahedra=len(elements),merge_attempts=attempts,
  source_tetrahedra_volume_m3=expected,cell_volume_sum_m3=float(total),relative_volume_error=float(error),seconds=time.monotonic()-start,qualified=False)
 (HERE/(link+'_review.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
