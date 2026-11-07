"""Source-constrained Dex5-S visual/kinematic reconstruction, NOT vendor CAD.

No dynamics, torques, tactile layout, or H2 wrist compatibility are invented.
Joint frames and inspection angles are explicit unqualified hypotheses.
The manufacturer's oblique image is a proportion reference, not metrology.
"""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import trimesh

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'assets/cooling_lab_v1'))
from geometry_tools import Geometry

SILVER=[181,188,196]; DARK=[47,51,57]; BLACK=[26,29,33]

class ReferenceGeometry(Geometry):
    def add(self,name,mesh,color,role='structure',metal=0,alpha=255):
        c=np.asarray(color[:3])/255
        linear=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
        result=super().add(name,mesh,np.round(linear*255).astype(int).tolist(),role,metal,alpha)
        result.visual.material.roughnessFactor=.32 if metal>.5 else .72
        return result

def phalanx_mesh(width,length,depth,tip=False):
    vertices=[]
    stations=[(0,.73),(.002,.92),(.006,1),(length*.65,1),(length-.004,.90),(length,.64 if tip else .78)]
    for z,scale in stations:
        for a in np.linspace(0,2*np.pi,48,endpoint=False):
            # Rounded section with a broad back face and generous side radii.
            x=np.sign(np.cos(a))*abs(np.cos(a))**.65*width/2*scale
            y=np.sign(np.sin(a))*abs(np.sin(a))**.65*depth/2*scale
            vertices.append([x,y,z])
    return trimesh.convex.convex_hull(vertices)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

def palm_mesh():
    # Tapered, rounded aluminum shell. Local silhouette is image-derived.
    outline=[(-.022,0),(.022,0),(.036,.017),(.039,.061),(.033,.085),
             (-.029,.088),(-.038,.069),(-.038,.023)]
    points=[]
    for y,shrink in [(-.011,.004),(-.008,0),(.008,0),(.011,.004)]:
        for x,z in outline: points.append([x-np.sign(x)*shrink,y,z-(.003 if z>.080 else 0)])
    return trimesh.convex.convex_hull(points)

def build_hand(side):
    g=ReferenceGeometry(); joints=[]; attachments={}; transforms={'palm':np.eye(4)}
    sign=1 if side=='left' else -1
    def add_part(name,mesh,color,link='palm',role='housing',metal=.78):
        mesh.apply_transform(transforms[link]);g.add(name,mesh,color,role,metal=metal);attachments[name]=link
    def panel(name,w,h,d,center,r,color,link='palm',role='housing'):
        temp=Geometry();m=temp.rounded_panel(name,w,h,d,center,r,color)
        add_part(name,m,color,link,role,.08 if role=='contact_pad' else .78)
    def cylinder(name,r,length,center,axis,link='palm'):
        m=trimesh.creation.cylinder(r,length,sections=32)
        m.apply_transform(trimesh.geometry.align_vectors([0,0,1],axis));m.apply_translation(center)
        add_part(name,m,SILVER,link,'joint_cover')
    def barrel(name,width,link):
        m=trimesh.creation.cylinder(.006,width,sections=48)
        m.apply_transform(trimesh.geometry.align_vectors([0,0,1],[1,0,0]));m.apply_translation([0,0,0])
        add_part(name,m,BLACK,link,'joint_barrel',.2)
    def joint(name,parent,xyz,axis,angle):
        bind=np.eye(4);bind[:3,3]=xyz;transforms[name]=transforms[parent]@bind
        joints.append(dict(id=name,parent=parent,origin_m=list(xyz),axis=list(axis),
                           inspection_angle_rad=angle,frame_basis='image-informed authored kinematic hypothesis',
                           measured_limits_rad=None,effort_limit_Nm=None,velocity_limit_rad_s=None))
        return name
    mesh=palm_mesh()
    if sign<0:mesh.apply_transform(np.diag([-1,1,1,1]))
    add_part('palm_shell',mesh,SILVER)
    panel('palm_contact_pad',.055,.053,.002,[0,-.0115,.047],.008,DARK,role='contact_pad')
    panel('palm_rear_panel',.048,.061,.002,[0,.012,.048],.007,[162,170,180])
    # Pad ridges are visual rubber texture; no unsupported tactile taxel claim.
    for i in range(10):
        panel('palm_pad_ridge_'+str(i),.043,.0014,.0007,[0,-.01265,.026+i*.004],.0005,[66,69,74],role='contact_pad')
    for x in [-.027,.027]:
        for z in [.018,.072]:cylinder('palm_screw_'+str(x)+'_'+str(z),.0017,.001,[x,.012,z],(0,1,0))
    fingers=[('index',-.027,.083,[.040,.027,.027]),('middle',-.007,.088,[.043,.029,.030]),
             ('ring',.014,.084,[.041,.027,.026]),('pinky',.032,.069,[.034,.023,.023])]
    for name,x,z,lengths in fingers:
        parent='palm'
        if name=='pinky':parent=joint(name+'_metacarpal_roll',parent,[sign*x,0,z],(0,0,sign*1),-.12);origin=[0,0,0]
        else:origin=[sign*x,0,z]
        parent=joint(name+'_spread',parent,origin,(0,1,sign*0),0)
        for i,length in enumerate(lengths):
            parent=joint(name+'_flex_'+str(i),parent,[0,0,0 if i==0 else lengths[i-1]],(1,0,0),[.45,.7,.45][i])
            width=.017 if name=='pinky' else .019
            add_part(name+'_shell_'+str(i),phalanx_mesh(width,length-.003,.020,i==2),SILVER,parent)
            panel(name+'_pad_'+str(i),width-.003,length-.007,.0025,[0,-.0105,(length-.003)/2],.004,DARK,parent,'contact_pad')
            barrel(name+'_joint_barrel_'+str(i),width-.003,parent)
            cylinder(name+'_hinge_'+str(i),.004,width+.001,[0,0,0],(1,0,0),parent)
            for k in range(3):
                panel(name+'_pad_ridge_'+str(i)+'_'+str(k),width-.005,.001,.0007,[0,-.012,.008+k*.004],.0004,[70,72,78],parent,'contact_pad')
    # Thumb lateral offset and rotations are assumptions, constrained by the
    # selected 102 mm open width; the wrist adapter shown in photos is excluded.
    panel('thumb_metacarpal_shell',.023,.040,.022,[-sign*.043,0,.030],.005,SILVER)
    parent=joint('thumb_opposition','palm',[-sign*.053,0,.027],(0,0,sign),.25)
    parent=joint('thumb_spread',parent,[0,0,0],(0,1,0),0)
    for i,length in enumerate([.024,.024,.026]):
        parent=joint('thumb_flex_'+str(i),parent,[0,0,0 if i==0 else [.024,.024][i-1]],(1,0,0),[.3,.5,.3][i])
        add_part('thumb_shell_'+str(i),phalanx_mesh(.016,length-.003,.021,i==2),SILVER,parent)
        panel('thumb_pad_'+str(i),.014,length-.006,.0025,[0,-.0115,(length-.003)/2],.004,DARK,parent,'contact_pad')
        barrel('thumb_joint_barrel_'+str(i),.014,parent)
        cylinder('thumb_hinge_'+str(i),.004,.016,[0,0,0],(1,0,0),parent)
    # Original open pose is kept in world coordinates for scene inspection.
    # No uniform rescaling: source dimensions are design constraints.
    path=HERE/'geometry'/f'dex5s_pro_{side}.glb';path.parent.mkdir(exist_ok=True)
    path.write_bytes(g.scene.export(file_type='glb'))
    kin=dict(side=side,joints=joints,part_links=attachments,bind_world={k:v.tolist() for k,v in transforms.items()},
             scope='Inspection-only kinematic hypothesis; not manufacturer joint frames or physical execution model')
    write(HERE/f'{side}_kinematics.json',kin)
    return dict(id=side,path=str(path.relative_to(ROOT)),sha256=sha(path),bounds_m=g.scene.bounds.tolist(),
                parts=g.parts,kinematics=str((HERE/f'{side}_kinematics.json').relative_to(ROOT)),
                kinematics_sha256=sha(HERE/f'{side}_kinematics.json'),active_joint_count=len(joints))

def main():
    hands=[build_hand(s) for s in ['left','right']]
    sources=json.loads((HERE/'sources.json').read_text())
    write(HERE/'model.json',dict(schema_version=1,status='source_based_visual_kinematic_draft_not_accepted',
      manufacturer='Unitree',model='Dex5-S Pro',official_cad=False,source_record_sha256=sha(HERE/'sources.json'),
      builder_sha256=sha(Path(__file__)),axes='+Z fingers; -Y palm; SI metres',hands=hands,
      manufacturer_dimensions_mm=[102,187,26],dimension_interpretation='102 width, 187 wrist-to-fingertip, 26 palm thickness; hand excluding pictured wrist adapter',
      mass_kg_per_hand=.620,mass_distribution=None,actuator_model=None,tactile_taxel_layout=None,
      h2_mount_transform=None,appearance_accepted=False,kinematics_qualified=False,dynamics_qualified=False,
      reconstruction_assumptions=sources['reconstruction_assumptions'],
      blockers=['Joint frames/ranges and torque/speed limits require evidence or qualified bounded reconstruction',
                'Link inertias and contact properties missing; total mass is not a mass distribution',
                'H2 EDU wrist installation and rigid-wrist mass ownership unresolved',
                'Pro tactile placement, calibration and noise unavailable',
                'Oblique photos constrain appearance but cannot prove contact-surface dimensions']))
    print(json.dumps({'hands':len(hands),'joints_per_hand':[h['active_joint_count'] for h in hands],'status':'draft_not_physics_model'}))

if __name__=='__main__':main()
