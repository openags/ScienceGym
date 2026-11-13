"""Explore convex-cell growth contained inside the same source exterior.

Unlike disjoint-volume merging, cells may overlap where other source material
already exists. Every accepted expansion must have an empty Boolean difference
against the source solid. Original tetrahedra stay covered by construction.
This offline candidate never changes the active collision package.
"""
import argparse
from collections import defaultdict
import gzip
import hashlib
import heapq
import json
from pathlib import Path
import time

import manifold3d as md
import numpy as np
from scipy.spatial import ConvexHull
import trimesh

HERE=Path(__file__).resolve().parent
INPUT=HERE.parent/'ftir_distal_contact_03'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def convex(points,indices):
    indices=np.array(sorted(indices));vertices=points[indices]
    hull=ConvexHull(vertices);faces=hull.simplices.copy()
    tri=vertices[faces];normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    reverse=np.sum(normals*hull.equations[:,:3],axis=1)<0
    faces[reverse]=faces[reverse][:,[0,2,1]]
    compact=np.full(len(indices),-1);compact[hull.vertices]=np.arange(len(hull.vertices))
    return indices[hull.vertices],vertices[hull.vertices],compact[faces],float(hull.volume)

def grow(link,seconds):
    filename='thumb_external_tetrahedra.npz' if link=='right_thumb_4' else 'right_index_2_1e-06_tetrahedra.npz'
    input_path=INPUT/filename;source=np.load(input_path);points=source['points'];tet=source['elements']
    folder=HERE/link;folder.mkdir(exist_ok=False)
    volume=np.abs(np.linalg.det(points[tet[:,1:]]-points[tet[:,:1]]))/6
    cells={i:set(map(int,e)) for i,e in enumerate(tet)};volumes=dict(enumerate(volume))
    neighbors={i:set() for i in cells};boundary={}
    for i,element in enumerate(tet):
        for omit in range(4):
            face=tuple(sorted(np.delete(element,omit)))
            if face in boundary:
                j,_=boundary.pop(face);neighbors[i].add(j);neighbors[j].add(i)
            else:boundary[face]=(i,int(element[omit]))
    faces=[]
    for face,(_,inside) in boundary.items():
        face=list(face);tri=points[face]
        if np.dot(np.cross(tri[1]-tri[0],tri[2]-tri[0]),points[inside]-tri[0])>0:face=face[::-1]
        faces.append(face)
    shell=trimesh.Trimesh(points,np.array(faces),process=True)
    if not shell.is_volume or abs(shell.volume-volume.sum())>1e-14:raise ValueError('Invalid source tetrahedral exterior')
    solid=md.Manifold(md.Mesh64(vert_properties=np.asarray(shell.vertices)*1000,tri_verts=np.asarray(shell.faces,dtype=np.uint64)))
    if solid.status()!=md.Error.NoError:raise ValueError('Source Boolean solid rejected: '+str(solid.status()))
    versions={i:0 for i in cells};expanded={i:False for i in cells};queue=[]
    def push(i,j):
        i,j=sorted([i,j]);heapq.heappush(queue,(-(volumes[i]+volumes[j]),i,j,versions[i],versions[j]))
    for i in cells:
        for j in neighbors[i]:
            if i<j:push(i,j)
    started=time.monotonic();attempts=accepted=expansions=errors=0;proof=[]
    while queue and time.monotonic()-started<seconds:
        _,i,j,vi,vj=heapq.heappop(queue)
        if i not in cells or j not in cells or versions[i]!=vi or versions[j]!=vj or j not in neighbors[i]:continue
        attempts+=1;indices,vertices,faces,v=convex(points,cells[i]|cells[j])
        disjoint=not expanded[i] and not expanded[j] and abs(v-volumes[i]-volumes[j])<max(1e-15,(volumes[i]+volumes[j])*3e-7)
        if not disjoint:
            candidate=md.Manifold(md.Mesh64(vert_properties=vertices*1000,tri_verts=np.asarray(faces,dtype=np.uint64)))
            difference=candidate-solid
            if candidate.status()!=md.Error.NoError or difference.status()!=md.Error.NoError:
                errors+=1;continue
            if not difference.is_empty():continue
            expansions+=1
        proof.append(dict(into=i,removed=j,source_difference_empty=not disjoint,disjoint_volume_merge=disjoint))
        cells[i]=set(map(int,indices));volumes[i]=v;versions[i]+=1;expanded[i]=not disjoint
        adjacent=(neighbors[i]|neighbors[j])-{i,j}
        for k in adjacent:neighbors[k].discard(i);neighbors[k].discard(j);neighbors[k].add(i)
        neighbors[i]=adjacent;del cells[j],neighbors[j],volumes[j],expanded[j]
        for k in adjacent:push(i,k)
        accepted+=1
        if accepted%500==0:print(link,'cells',len(cells),'accepted',accepted,'expansions',expansions,'attempts',attempts,'seconds',round(time.monotonic()-started,1),flush=True)
    # Complete coverage is retained even when the bounded search stops early.
    vertices=[];faces=[];vo=[0];fo=[0]
    for indices in cells.values():
        _,v,f,_=convex(points,indices);vertices.append(v);faces.append(f);vo.append(vo[-1]+len(v));fo.append(fo[-1]+len(f))
    np.savez_compressed(folder/'cells.npz',vertices=np.vstack(vertices),faces=np.vstack(faces),vertex_offsets=vo,face_offsets=fo)
    with gzip.open(folder/'merge_proof.json.gz','wt') as f:json.dump(proof,f,separators=(',',':'))
    state=dict(cells={str(k):sorted(v) for k,v in cells.items()},neighbors={str(k):sorted(v) for k,v in neighbors.items()},
               volumes=volumes,expanded=expanded,versions=versions,queue=queue)
    with gzip.open(folder/'checkpoint.json.gz','wt') as f:json.dump(state,f,separators=(',',':'))
    report=dict(scope=__doc__,link=link,source_sha256=sha(input_path),builder_sha256=sha(Path(__file__)),
                source_cells=len(tet),cells=len(cells),attempts=attempts,accepted_merges=accepted,expansion_merges=expansions,
                boolean_errors=errors,search_exhausted=not queue,seconds=time.monotonic()-started,
                source_volume_m3=float(shell.volume),original_cells_covered_by_construction=True,
                candidate_only=True,physical_qualified=False)
    (folder/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--link',choices=['right_thumb_4','right_index_2'],required=True);p.add_argument('--seconds',type=float,default=180);a=p.parse_args();grow(a.link,a.seconds)
