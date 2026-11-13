"""Render the declared optical initial state and a separate open-cover inspection.

The inspection pose is authored for geometry review. Neither image is a frame
from robot execution, and no cover opening or placement is credited.
"""
import argparse
import json
import os
from pathlib import Path
import shutil

os.environ.setdefault('MUJOCO_GL','egl')
import mujoco
import numpy as np
from PIL import Image

from build_tool_station import sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);a=p.parse_args()
    folder=a.folder.resolve();out=folder/'inspection';out.mkdir(exist_ok=False)
    shutil.copyfile(__file__,out/Path(__file__).name)
    binding=json.loads((folder/'binding.json').read_text())
    assert sha(folder/'world.xml')==binding['world_sha256']
    assert sha(folder/'initial_state.json')==binding['initial_state_sha256']
    for file,digest in json.loads((folder/'model_inputs.json').read_text()).items():assert sha(file)==digest
    m=mujoco.MjModel.from_xml_path(str(folder/'world.xml'));d=mujoco.MjData(m)
    initial=json.loads((folder/'initial_state.json').read_text());d.qpos[:]=initial['qpos'];d.qvel[:]=initial['qvel']
    mujoco.mj_forward(m,d)
    m.mat_rgba[:,:3]=np.clip(m.mat_rgba[:,:3],0,1)**(1/2.2)
    for i in range(m.ntex):
        if not m.texture(i).name.startswith('lab_texture_'):continue
        start=m.tex_adr[i];h,w,c=m.tex_height[i],m.tex_width[i],m.tex_nchannel[i]
        pixels=m.tex_data[start:start+h*w*c].reshape(h,w,c);pixels[:]=pixels[::-1].copy()
    m.vis.headlight.ambient[:]=.5;m.vis.headlight.diffuse[:]=.5
    port=np.asarray(binding['ftir_sample_port_work_m']);pelvis=d.body('pelvis').xpos.copy()
    specimen=d.body('optical_witness_white').xpos.copy()
    views=dict(room=dict(lookat=((port+pelvis)/2).tolist(),distance=3.2,azimuth=135.,elevation=-18.),
        specimen=dict(lookat=specimen.tolist(),distance=.38,azimuth=135.,elevation=-55.),
        instrument=dict(lookat=port.tolist(),distance=.72,azimuth=135.,elevation=-35.))
    renderer=mujoco.Renderer(m,height=720,width=1280,max_geom=m.ngeom+1000)
    option=mujoco.MjvOption();option.geomgroup[3]=0;option.sitegroup[:]=0
    camera=mujoco.MjvCamera();outputs={}
    def frame(name,view):
        for k,v in view.items():
            if k=='lookat':camera.lookat[:]=v
            else:setattr(camera,k,v)
        renderer.update_scene(d,camera=camera,scene_option=option)
        path=out/(name+'.png');Image.fromarray(renderer.render().copy()).save(path)
        outputs[path.name]=sha(path)
    for name,view in views.items():frame('initial_'+name,view)
    j=m.joint('nicolet_cover_hinge');angle=float(j.range[np.argmax(abs(j.range))]*.9)
    d.joint(j.name).qpos[0]=angle;mujoco.mj_forward(m,d)
    frame('inspection_open_instrument',views['instrument']);renderer.close()
    report=dict(scope=__doc__,binding_sha256=sha(folder/'binding.json'),
        world_sha256=binding['world_sha256'],initial_state_sha256=binding['initial_state_sha256'],
        camera_views=views,inspection_cover_joint=j.name,inspection_cover_angle_rad=angle,
        presentation_adjustments=['Material gamma and texture origin correction','Headlight ambient/diffuse 0.5'],
        source_sha256=sha(__file__),outputs=outputs,physical_execution=False,qualified_paper_branch=False)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(outputs=list(outputs),inspection_cover_angle_rad=angle)),flush=True)


if __name__=='__main__':main()
