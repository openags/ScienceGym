import * as THREE from 'three';
import {mergeGeometries} from 'three/addons/utils/BufferGeometryUtils.js';

// Renderer-only batching. The source GLBs/part ledger remain unchanged, and
// independently movable inspection parts keep their original scene nodes.
export function batchStaticMeshes(group,protectedNames=new Set()){
 group.updateMatrixWorld(true);
 const before=new THREE.Box3().setFromObject(group),buckets=new Map();let beforeMeshes=0,triangles=0;
 group.traverse(node=>{
  if(!node.isMesh)return;beforeMeshes++;triangles+=(node.geometry.index?.count||node.geometry.attributes.position.count)/3;
  let ancestor=node,protectedPart=false;while(ancestor&&ancestor!==group){if(protectedNames.has(ancestor.name))protectedPart=true;ancestor=ancestor.parent}
  if(protectedPart||Array.isArray(node.material)||node.material.transparent||node.isSkinnedMesh)return;
  const key=[node.material.uuid,Boolean(node.userData.cutaway),node.castShadow,node.receiveShadow,Object.keys(node.geometry.attributes).sort().join(',')].join('|');
  if(!buckets.has(key))buckets.set(key,[]);buckets.get(key).push(node);
 });
 let batch=0;
 for(const nodes of buckets.values()){
  if(nodes.length<2)continue;
  const inverse=new THREE.Matrix4().copy(group.matrixWorld).invert();
  const geometries=nodes.map(node=>{
   const g=node.geometry.index?node.geometry.toNonIndexed():node.geometry.clone();
   g.applyMatrix4(new THREE.Matrix4().multiplyMatrices(inverse,node.matrixWorld));return g;
  });
  const geometry=mergeGeometries(geometries,false);
  if(!geometry)throw Error('静态部件合并失败');
  const first=nodes[0],merged=new THREE.Mesh(geometry,first.material);
  merged.name='render_batch_'+batch++;merged.castShadow=first.castShadow;merged.receiveShadow=first.receiveShadow;
  merged.userData={...first.userData,sourceParts:nodes.map(n=>n.name)};
  for(const node of nodes)node.removeFromParent();
  group.add(merged);for(const g of geometries)g.dispose();
 }
 group.updateMatrixWorld(true);
 const after=new THREE.Box3().setFromObject(group);let afterMeshes=0,afterTriangles=0;
 group.traverse(node=>{if(node.isMesh){afterMeshes++;afterTriangles+=(node.geometry.index?.count||node.geometry.attributes.position.count)/3}});
 const error=Math.max(before.min.distanceTo(after.min),before.max.distanceTo(after.max));
 if(error>1e-5||afterTriangles!==triangles)throw Error('静态绘制合并改变了模型几何');
 return {beforeMeshes,afterMeshes,triangles,boundsErrorM:error,sourceGeometryPreserved:true};
}
