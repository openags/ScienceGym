import json,sys,numpy as np,mujoco
from pathlib import Path
from PIL import Image
b=Path(sys.argv[1]);m=mujoco.MjModel.from_xml_path(str((b/'world.xml').resolve()));d=mujoco.MjData(m);trace=np.load(b/'trace.npz')
m.mat_rgba[:,:3]=np.clip(m.mat_rgba[:,:3],0,1)**(1/2.2)
for i in range(m.ntex):
 if not m.texture(i).name.startswith('lab_texture_'):continue
 a=m.tex_adr[i];h,w,c=m.tex_height[i],m.tex_width[i],m.tex_nchannel[i];pix=m.tex_data[a:a+h*w*c].reshape(h,w,c);pix[:]=pix[::-1].copy()
m.vis.headlight.ambient[:]=.5;m.vis.headlight.diffuse[:]=.5
r=mujoco.Renderer(m,height=720,width=1280,max_geom=m.ngeom+1000);opt=mujoco.MjvOption();opt.geomgroup[3]=0;opt.sitegroup[:]=0
out=b/'diagnostic_stills';out.mkdir(exist_ok=True);rows=[]
for t in [16.5,17.5,18.,18.5]:
 i=np.argmin(abs(trace['time']-t));d.qpos[:]=trace['qpos'][i];mujoco.mj_forward(m,d)
 for az in [45,135]:
  cam=mujoco.MjvCamera();cam.lookat[:]=[6.12,-5.52,1.10];cam.distance=.3;cam.azimuth=az;cam.elevation=-15
  r.update_scene(d,camera=cam,scene_option=opt);fn=f't{t:g}_az{az}.jpg';Image.fromarray(r.render()).save(out/fn)
  rows.append(dict(path=fn,time_s=float(trace['time'][i]),trace_index=int(i),scope='Diagnostic source-state rendering; failed run'))
r.close();(out/'frames.json').write_text(json.dumps(rows,indent=2)+'\n')
