import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

const folder='../../assets/unitree_g1_inspire_v1/';
const viewport=document.getElementById('robot-viewport');
try {
 const response=await fetch(folder+'VERIFICATION.json');
 if(!response.ok)throw Error('模型检查记录无法加载');
 const report=await response.json();
 const modelResponse=await fetch(folder+report.preview.path);
 if(!modelResponse.ok)throw Error('官方模型预览无法加载');
 const bytes=await modelResponse.arrayBuffer();
 const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
 if(hash!==report.preview.sha256)throw Error('模型文件与检查记录版本不一致');
 const gltf=await new Promise((resolve,reject)=>new GLTFLoader().parse(bytes,folder,resolve,reject));
 const scene=new THREE.Scene();scene.background=new THREE.Color('#edf1eb');
 const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));
 renderer.outputColorSpace=THREE.SRGBColorSpace;viewport.appendChild(renderer.domElement);
 const camera=new THREE.PerspectiveCamera(40,1,.005,100);camera.up.set(0,0,1);
 const controls=new OrbitControls(camera,renderer.domElement);controls.minDistance=.04;controls.maxDistance=8;
 scene.add(new THREE.HemisphereLight(0xffffff,0x686e6d,2));
 for(const [position,intensity] of [[[3,-3,5],2.3],[[-2,3,3],1.2]]){const light=new THREE.DirectionalLight(0xffffff,intensity);light.position.set(...position);scene.add(light)}
 scene.add(gltf.scene);
 const grid=new THREE.GridHelper(4,40,0x9aa79e,0xcbd4ca);grid.rotation.x=Math.PI/2;grid.position.z=-.002;scene.add(grid);
 const full=new THREE.Box3().setFromObject(gltf.scene);
 const hands={left:new THREE.Box3(),right:new THREE.Box3()};
 gltf.scene.traverse(node=>{if(!node.isMesh)return;for(const side of ['left','right'])if(new RegExp('^'+side+'_(base|thumb|index|middle|ring|little)_').test(node.name))hands[side].union(new THREE.Box3().setFromObject(node))});
 if(hands.left.isEmpty()||hands.right.isEmpty())throw Error('手部模型分组不完整');
 function render(){renderer.render(scene,camera)}
 function fit(view){const box=hands[view]||full;const target=box.getCenter(new THREE.Vector3());const size=box.getSize(new THREE.Vector3());
  const distance=Math.max(...size.toArray())/(2*Math.tan(THREE.MathUtils.degToRad(camera.fov/2)))*1.35/Math.min(camera.aspect,1);
  const direction=new THREE.Vector3(...(view==='back'?[-1,.7,.3]:view==='left'?[1,1,.4]:[1,-1,.4])).normalize();
  controls.target.copy(target);camera.position.copy(target).addScaledVector(direction,distance);controls.update();render();document.documentElement.dataset.view=view;
 }
 controls.addEventListener('change',render);
 new ResizeObserver(()=>{const {width,height}=viewport.getBoundingClientRect();renderer.setSize(width,height);camera.aspect=width/height;camera.updateProjectionMatrix();fit(document.documentElement.dataset.view||'full')}).observe(viewport);
 document.getElementById('robot-views').onclick=event=>{const view=event.target.closest('button')?.dataset.view;if(view)fit(view)};
 document.getElementById('robot-counts').textContent=`已核对 ${report.checked_source_files} 个来源文件、${report.mesh_files} 个网格；完整模型 ${report.links} 个链接，${report.movable_joints} 个活动关节，${report.mimic_joints} 个联动关节。`;
 const size=full.getSize(new THREE.Vector3());document.getElementById('robot-size').textContent='源模型零姿态范围：'+size.toArray().map(v=>v.toFixed(3)).join(' × ')+' m（X / Y / Z）。';
 fit('full');document.documentElement.dataset.ready='true';
} catch(error){document.getElementById('error').textContent=String(error);document.documentElement.dataset.ready='error'}
