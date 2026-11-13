"""Deformable two-sheet cover and its explicit ring-to-tube load path.

Dimensions come from SI Note 2; stiffness, density, attachment strength and
damping are selected simulation assumptions, not measured Targray properties.
The bond is ideal and permanent within this module. Attaching/removing it is a
separate manipulation obligation and is never credited by this load test.
"""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import mujoco
from world import vec,HERE


def sheet(parent,name,z,thickness=.000016,young=1e8,bonded=True,sectors=16,elastic=False):
    points=[[0.,0.,z]]
    # Include vertices inside the tube's 38--51 mm load-bearing annulus.
    # Vertices only on its two edges can slide off both edges during release,
    # letting the coarse mesh pass the narrow rim despite low edge strain.
    # The centre disk remains triangulated; resolution is spent at contact.
    # The bonded annulus is part of the rigid spacer. Giving it overlapping
    # rigid and two-sided flex collisions can trap a jaw between coincident
    # surfaces during opening. Only the unsupported disk needs flex contact.
    radii=[.038,.0445,.051,.0535] if bonded else [.038,.0445,.051,.0535,.0635]
    for r in radii:
        for theta in np.arange(sectors)*2*np.pi/sectors:
            points.append([r*np.cos(theta),r*np.sin(theta),z])
    points=np.asarray(points)
    # An explicitly rotationally symmetric triangulation avoids arbitrary
    # Delaunay diagonals on cocircular rings biasing a very light membrane.
    triangles=[]
    for i in range(sectors):triangles.append([0,1+i,1+(i+1)%sectors])
    for layer in range(len(radii)-1):
        inner=1+layer*sectors;outer=inner+sectors
        for i in range(sectors):
            j=(i+1)%sectors
            triangles.extend([[inner+i,outer+i,outer+j],[inner+i,outer+j,inner+j]])
    triangles=np.asarray(triangles)
    nominal_mass=920*thickness*np.pi*.0635**2
    mass=920*thickness*np.pi*radii[-1]**2
    bonded_annulus_mass=nominal_mass-mass
    flex=ET.SubElement(parent,'flexcomp',name=name,type='direct',dim='2',
        point=vec(points.ravel()),element=' '.join(str(x) for x in triangles.ravel()),
        mass=str(mass),radius='.00025',rgba='.80 .87 .91 .65',inertiabox='.001')
    if elastic:
        ET.SubElement(flex,'elasticity',young=str(young),poisson='.35',thickness=str(thickness),damping='.0002',elastic2d='both')
    else:
        # Inextensible triangulated cloth approximation. Free out-of-plane
        # vertices and actual contact carry the ring; no hidden support/weld.
        # This model cannot predict stretching, rupture or adhesive failure.
        ET.SubElement(flex,'edge',equality='true',solref='.001 1',solimp='.9999 .9999 .00001')
    ET.SubElement(flex,'contact',condim='3',friction='.4 .001 .0001',selfcollide='none',solref='.002 1',solimp='.95 .99 .0001')
    pins=np.flatnonzero(np.linalg.norm(points[:,:2],axis=1)>=.0535-1e-8)
    if bonded:ET.SubElement(flex,'pin',id=' '.join(map(str,pins)))
    if bonded:
        old=list(parent.findall('geom'))
        ring(parent,name+'_bonded_annulus',.0535,.0635,thickness,z,mass=0,color='.80 .87 .91 .65')
        for geom in parent.findall('geom'):
            if geom not in old:
                geom.set('contype','0');geom.set('conaffinity','0');geom.set('group','2')
    return dict(vertices=len(points),triangles=len(triangles),pinned_vertices=len(pins) if bonded else 0,
                thickness_m=thickness,collision_envelope_radius_m=.00025,
                model='Saint Venant-Kirchhoff' if elastic else 'constrained-edge cloth',
                young_Pa=young if elastic else None,poisson=.35 if elastic else None,damping_s=.0002 if elastic else None,
                nominal_mass_kg=nominal_mass,flex_patch_mass_kg=mass,
                bonded_annulus_collision='rigid spacer surface' if bonded else None,
                mass_on_parent_kg=mass*len(pins)/len(points)+bonded_annulus_mass if bonded else 0)


def ring(parent,name,inner,outer,height,z=0,mass=.1,color='.65 .69 .73 1'):
    for i in range(48):
        a=2*np.pi*i/48;r=(inner+outer)/2
        ET.SubElement(parent,'geom',name=name+'_'+str(i),type='box',
            size=vec([(outer-inner)/2,np.pi*r/48*1.03,height/2]),
            pos=vec([r*np.cos(a),r*np.sin(a),z]),euler=vec([0,0,a]),
            mass=str(mass/48),rgba=color)


def build(path,bonded=True,young=1e8,thickness=.000016,sectors=16,elastic=False,release_clearance=.0002):
    root=ET.Element('mujoco',model='Cooling cover membrane load path')
    ET.SubElement(root,'compiler',angle='radian')
    ET.SubElement(root,'option',timestep='.0001' if elastic else '.0005',integrator='discrete' if elastic else 'implicitfast',solver='CG' if elastic else 'Newton',iterations='300',tolerance='1e-8',gravity='0 0 -9.81')
    ET.SubElement(root,'size',memory='256M')
    ET.SubElement(ET.SubElement(root,'visual'),'global',offwidth='1120',offheight='720')
    default=ET.SubElement(root,'default')
    ET.SubElement(default,'geom',friction='.4 .001 .0001',solref='.002 1',solimp='.95 .99 .0001')
    world=ET.SubElement(root,'worldbody')
    ET.SubElement(world,'light',pos='0 -.5 1')
    ET.SubElement(world,'geom',name='table',type='plane',size='.3 .3 .01',rgba='.19 .25 .32 1')
    tube=ET.SubElement(world,'body',name='tube')
    ring(tube,'tube_wall',.038,.051,.057,.0285,color='.88 .88 .82 1')
    # Gentle placement is the operating condition; dropping the 64 g ring
    # several millimetres onto a 16 um membrane is a different impact test.
    body=ET.SubElement(world,'body',name='cover',pos=vec([0,0,.057+.0032+thickness/2+.00025+release_clearance]))
    ET.SubElement(body,'freejoint',name='cover_free')
    ring(body,'spacer',.0535,.0635,.0064,mass=np.pi*(.0635**2-.0535**2)*.0064*2700)
    properties=[]
    for name,z in [('lower',-.0032-thickness/2),('upper',.0032+thickness/2)]:
        properties.append(sheet(body,name,z,thickness,young,bonded,sectors,elastic))
    # Pinned vertex mass belongs to the rigid attachment body, explicitly.
    ET.SubElement(body,'geom',name='bonded_rim_mass',type='sphere',size='.0001',
                  mass=str(sum(x['mass_on_parent_kg'] for x in properties)),rgba='0 0 0 0',contype='0',conaffinity='0')
    ET.indent(root);ET.ElementTree(root).write(path,encoding='unicode')
    return properties


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--unbonded',action='store_true');parser.add_argument('--render',action='store_true');parser.add_argument('--young',type=float,default=1e8);parser.add_argument('--seconds',type=float,default=1);parser.add_argument('--sectors',type=int,default=16);parser.add_argument('--elastic',action='store_true')
    args=parser.parse_args();out=HERE/'runs/membrane_debug';out.mkdir(exist_ok=True)
    properties=build(out/'workcell.xml',not args.unbonded,args.young,sectors=args.sectors,elastic=args.elastic)
    model=mujoco.MjModel.from_xml_path(str(out/'workcell.xml'));data=mujoco.MjData(model)
    frames=[];trace=[];renderer=mujoco.Renderer(model,720,1120) if args.render else None
    for step in range(round(args.seconds/model.opt.timestep)):
        mujoco.mj_step(model,data)
        if step%10==0:
            trace.append((data.time,data.qpos.copy(),data.qvel.copy()))
        if renderer and step%round(.02/model.opt.timestep)==0:
            camera=mujoco.MjvCamera();camera.lookat[:]=[0,0,.045];camera.distance=.34;camera.azimuth=130;camera.elevation=-25
            renderer.update_scene(data,camera);frames.append(renderer.render().copy())
        if any(w.number for w in data.warning):raise RuntimeError('MuJoCo warning: '+str(data.warning))
    force=0;vertical_force=0
    for i,c in enumerate(data.contact):
        if c.flex[0]<0 and c.flex[1]<0:continue
        geom=int(c.geom1 if c.geom1>=0 else c.geom2)
        if geom>=0 and model.body(int(model.geom_bodyid[geom])).name=='tube':
            f=np.zeros(6);mujoco.mj_contactForce(model,data,i,f);force+=float(f[0])
            direction=1 if c.geom1>=0 else -1
            vertical_force+=float((c.frame.reshape(3,3).T@f[:3])[2])*direction
    report=dict(scope='membrane load path only; ideal bond, assumed material properties; no attachment action validated',
                properties=properties,cover_position=data.body('cover').xpos.tolist(),
                cover_speed=float(np.linalg.norm(data.body('cover').cvel)),tube_film_contact_force_n=force,
                tube_to_film_vertical_force_n=vertical_force,
                whole_paper_validated=False,physics_steps=step+1,warning_count=sum(w.number for w in data.warning),
                contacts=int(data.ncon),dofs=model.nv)
    print(json.dumps(report,indent=2),flush=True)
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    np.savez_compressed(out/'physics_trace.npz',time=[s[0] for s in trace],qpos=[s[1] for s in trace],qvel=[s[2] for s in trace])
    if renderer:
        import imageio.v2 as imageio
        imageio.mimwrite(out/'execution.mp4',frames,fps=50,codec='libx264',quality=8)
        imageio.imwrite(out/'final.png',frames[-1]);renderer.close()


if __name__=='__main__':main()
