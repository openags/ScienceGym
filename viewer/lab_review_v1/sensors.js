import * as THREE from 'three';

// Inspection images only. No actor input or hidden task/evaluator state is used.
export class SensorReview {
 constructor({renderer,scene,robot,normalization,rig,hiddenGroups,canvas,status}){
  Object.assign(this,{renderer,scene,robot,rig,hiddenGroups,canvas,status});
  this.normalization=new THREE.Matrix4().fromArray(normalization.flat()).transpose();
  this.nodes=[];this.world=new Map();this.group=new THREE.Group();this.group.name='unaccepted_camera_mount_candidate';this.group.visible=false;robot.add(this.group);
  const options={type:THREE.UnsignedByteType,format:THREE.RGBAFormat,depthBuffer:true};
  this.rgbTarget=new THREE.WebGLRenderTarget(1280,720,options);this.rgbTarget.texture.colorSpace=THREE.LinearSRGBColorSpace;
  this.hdrTarget=new THREE.WebGLRenderTarget(1280,720,{...options,type:THREE.HalfFloatType});this.hdrTarget.texture.colorSpace=THREE.LinearSRGBColorSpace;
  this.depthTarget=new THREE.WebGLRenderTarget(1280,720,options);this.depthTarget.texture.colorSpace=THREE.LinearSRGBColorSpace;
  this.depthMaterial=new THREE.ShaderMaterial({uniforms:{displayRange:{value:1}},vertexShader:'varying float axialDepth; void main(){vec4 p=modelViewMatrix*vec4(position,1.0); axialDepth=-p.z; gl_Position=projectionMatrix*p;}',fragmentShader:'varying float axialDepth; uniform float displayRange; void main(){float v=clamp(axialDepth/displayRange,0.0,1.0); gl_FragColor=vec4(vec3(v),1.0);}',side:THREE.DoubleSide});
  // Three's offscreen scene pass omits display tone mapping. Keep radiance in
  // HDR, then explicitly apply the same ACES display transform as the viewer.
  this.outputMaterial=new THREE.ShaderMaterial({toneMapped:false,depthTest:false,depthWrite:false,uniforms:{inputImage:{value:this.hdrTarget.texture},toneMappingExposure:{value:renderer.toneMappingExposure}},vertexShader:'varying vec2 screenUV; void main(){screenUV=uv;gl_Position=vec4(position.xy,0.0,1.0);}',fragmentShader:'#include <tonemapping_pars_fragment>\nuniform sampler2D inputImage; varying vec2 screenUV; void main(){vec3 c=texture2D(inputImage,screenUV).rgb;gl_FragColor=sRGBTransferOETF(vec4(ACESFilmicToneMapping(c),1.0));}'});
  this.outputScene=new THREE.Scene();this.outputScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2,2),this.outputMaterial));this.outputCamera=new THREE.Camera();
  this.camera=new THREE.PerspectiveCamera();this.selected=null;this.metadata=null;
 }
 async load(loadPinned,prepare){
  for(const attachment of this.rig.attachments){const loaded=await loadPinned(attachment.geometry_path,attachment.geometry_sha256);prepare(loaded);const node=loaded.scene;node.name=attachment.id;node.matrixAutoUpdate=false;this.group.add(node);this.nodes.push({attachment,node})}
 }
 update(world){
  this.world=new Map([...world].map(([k,v])=>[k,v.clone()]));
  for(const {attachment,node} of this.nodes)node.matrix.copy(this.normalization).multiply(world.get(attachment.parent_link)).multiply(new THREE.Matrix4().fromArray(attachment.parent_from_geometry.flat()).transpose());
  if(this.metadata){this.status.textContent='机器人姿态已改变，点击相机按钮重新生成图像。';this.canvas.dataset.stale='true'}
 }
 opticalWorld(id){const optic=this.rig.optics.find(o=>o.id===id);if(!optic)throw Error('Unknown camera '+id);this.robot.updateWorldMatrix(true,false);return this.robot.matrixWorld.clone().multiply(this.normalization).multiply(this.world.get(optic.parent_link)).multiply(new THREE.Matrix4().fromArray(optic.parent_from_optical.flat()).transpose())}
 capture(id){
  const optic=this.rig.optics.find(o=>o.id===id),p=optic.profile,depth=optic.channels[0]==='depth',world=this.opticalWorld(id),cam=this.camera;
  // OpenGL camera looks along -Z with +Y up. Optical camera uses +Z / +Y down.
  const view=world.clone().multiply(new THREE.Matrix4().makeRotationX(Math.PI));
  view.decompose(cam.position,cam.quaternion,cam.scale);cam.near=p.near_m;cam.far=p.far_m;
  cam.projectionMatrix.makePerspective(-p.cx_px*p.near_m/p.fx_px,(p.width-p.cx_px)*p.near_m/p.fx_px,p.cy_px*p.near_m/p.fy_px,-(p.height-p.cy_px)*p.near_m/p.fy_px,p.near_m,p.far_m);
  cam.projectionMatrixInverse.copy(cam.projectionMatrix).invert();cam.updateMatrixWorld(true);
  const saved=[];this.scene.traverse(o=>{saved.push([o,o.visible]);o.visible=true});
  for(const group of this.hiddenGroups)group.visible=false;
  this.group.visible=id.includes('wrist')||saved.find(([o])=>o===this.group)[1];
  const oldMaterial=this.scene.overrideMaterial,oldBackground=this.scene.background,oldTarget=this.renderer.getRenderTarget();
  const oldTone=this.renderer.toneMapping,oldColor=this.renderer.outputColorSpace;
  const pixels=new Uint8Array(p.width*p.height*4),target=depth?this.depthTarget:this.rgbTarget;
  try{
   target.setSize(p.width,p.height);this.hdrTarget.setSize(p.width,p.height);
   if(depth){this.scene.overrideMaterial=this.depthMaterial;this.scene.background=new THREE.Color(0);this.renderer.toneMapping=THREE.NoToneMapping;this.renderer.outputColorSpace=THREE.LinearSRGBColorSpace}
   this.renderer.shadowMap.needsUpdate=true;
   this.renderer.setRenderTarget(depth?target:this.hdrTarget);this.renderer.clear();this.renderer.render(this.scene,cam);
   if(!depth){this.outputMaterial.uniforms.toneMappingExposure.value=this.renderer.toneMappingExposure;this.renderer.setRenderTarget(target);this.renderer.render(this.outputScene,this.outputCamera)}
   this.renderer.readRenderTargetPixels(target,0,0,p.width,p.height,pixels);
  }finally{
   this.renderer.setRenderTarget(oldTarget);this.scene.overrideMaterial=oldMaterial;this.scene.background=oldBackground;this.renderer.toneMapping=oldTone;this.renderer.outputColorSpace=oldColor;for(const [o,visible] of saved)o.visible=visible;this.renderer.shadowMap.needsUpdate=true;
  }
  this.canvas.width=p.width;this.canvas.height=p.height;const ctx=this.canvas.getContext('2d'),frame=ctx.createImageData(p.width,p.height);
  for(let y=0;y<p.height;y++)frame.data.set(pixels.subarray((p.height-1-y)*p.width*4,(p.height-y)*p.width*4),y*p.width*4);
  ctx.putImageData(frame,0,0);this.canvas.hidden=false;this.canvas.dataset.stale='false';this.canvas.dataset.camera=id;
  const range=this.depthMaterial.uniforms.displayRange.value;
  this.selected=id;this.metadata={camera:id,world_from_optical:world.toArray(),matrix_storage:'column_major',profile:p,preview_only:true,calibrated:false,display_transform:depth?'linear axial depth':{tone_mapping:'ACESFilmic',exposure:this.renderer.toneMappingExposure,encoding:'sRGB'},depth_display:depth?{axial_depth_white_m:range,background:'black without a hit',surface_model:'opaque geometry; no stereo validity/noise model'}:null};
  this.status.textContent=optic.label+' · '+(id.includes('wrist')?'未通过装配检查的候选视角。':'原生相机名义视角。')+(depth?'黑色 0 m → 白色 ≥'+range+' m；无命中背景为黑色。':'')+'1280 × 720；保留场景遮挡，隐藏审查标记；未经标定，无噪声、透明材质光学或观察流时序模拟。';
  return this.metadata;
 }
}
