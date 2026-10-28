"""Installed-pose support candidate using the actual reviewed stock solids.

This is a static reference configuration, not initial stock or robot execution.
It does not fix the tripod to the world or certify ground/load retention.
"""
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from check_weather_assets import load_parts
from build_weather_assets import cable_mesh


def pose(rotation=None,position=(0,0,0)):
    m=np.eye(4)
    if rotation is not None:m[:3,:3]=rotation
    m[:3,3]=position
    return m


def axis_rotation(angle,axis):return trimesh.transformations.rotation_matrix(angle,axis)[:3,:3]


def loop_leg(s,r,sign):
    u=np.linspace(s,.045,101);t=(u-s)/(.045-s);smooth=t**3*(10-15*t+6*t*t)
    return np.column_stack([u,sign*(r-(r-.002)*smooth)])


def attached_wire(top,bottom,down):
    """One open wire from upper free tail through both eyes to lower tail."""
    transverse=np.array([0.,1.,0.]);radius=.005
    upper_s=.0105+radius-.0025-.0015-.0001
    lower_s=.007+radius-.002-.0015-.0001
    def world(p,origin,axis):return origin+p[:,0,None]*axis+p[:,1,None]*transverse
    def arc(s):
        a=np.linspace(-np.pi/2,np.pi/2,129)
        return np.column_stack([s-radius*np.cos(a),radius*np.sin(a)])
    # Each tail extends 25 mm past the far end of its 14 mm clamp body.
    tail=.070+.007+.025
    top_tail=np.column_stack([np.linspace(tail,.045,61),np.full(61,-.002)])
    top_side=loop_leg(upper_s,radius,-1)[::-1]
    top_live=loop_leg(upper_s,radius,1)
    bottom_live=loop_leg(lower_s,radius,1)[::-1]
    bottom_side=loop_leg(lower_s,radius,-1)
    bottom_tail=np.column_stack([np.linspace(.045,tail,61),np.full(61,-.002)])
    a=world(top_live,top,down)[-1];b=world(bottom_live,bottom,-down)[0]
    pieces=[world(top_tail,top,down),world(top_side,top,down),world(arc(upper_s),top,down),world(top_live,top,down),
        np.linspace(a,b,1201),world(bottom_live,bottom,-down),world(arc(lower_s)[::-1],bottom,-down),
        world(bottom_side,bottom,-down),world(bottom_tail,bottom,-down)]
    points=np.vstack(pieces);keep=np.r_[True,np.linalg.norm(np.diff(points,axis=0),axis=1)>1e-10]
    return points[keep]


def ground_wire_points():
    start=np.array([0.,.0221,.281]);a=np.array([0.,.0221,.23]);r=.020
    theta=np.linspace(0,np.pi/2,81)
    arc=a+np.column_stack([r*(1-np.cos(theta)),np.zeros(len(theta)),-r*np.sin(theta)])
    b=arc[-1];end=np.array([.1118,0,.12]);c=b+[.04,0,0];d=end+[0,0,.04];t=np.linspace(0,1,201)[:,None]
    curve=(1-t)**3*b+3*(1-t)**2*t*c+3*(1-t)*t*t*d+t**3*end
    return np.vstack([np.linspace(start,a,61)[:-1],arc[:-1],curve[:-1],np.linspace(end,[.1118,0,.05],81)])


def build():
    tripod_record=json.loads((HERE/'tripod_assets.json').read_text());kit_record=json.loads((HERE/'weather_anchoring_assets.json').read_text())
    site=json.loads((HERE/'weather_site_review.json').read_text())
    tripod=load_parts(tripod_record['geometry']);kit=load_parts(kit_record['geometry']);g=Geometry();transforms=[];wires=[]
    centre=np.r_[site['mast_center_xy_m'],0.]
    def add(name,mesh,matrix,source,source_part):
        # Keep fine local geometry in mesh coordinates. Baking a 20 m world
        # offset into glTF float32 vertices collapses micron-scale CAD edges.
        m=mesh.copy();g.scene.add_geometry(m,node_name=name,geom_name=name,transform=matrix)
        world=m.copy();world.apply_transform(matrix)
        g.parts.append(dict(id=name,role='static_installed_pose_reference',bounds_m=world.bounds.tolist()))
        transforms.append(dict(part=name,source=source,source_part=source_part,pose=matrix.tolist()))
    for name,m in tripod.items():add(name,m,pose(position=centre),'tripod',name)
    for name,m in kit.items():
        if name.startswith('guy_collar_'):add(name,m,pose(position=centre+[0,0,1.889]),'anchoring_kit',name)
    angles=np.radians([90,210,330])
    for i,angle in enumerate(angles,1):
        rz=axis_rotation(angle,[0,0,1]);site_pose=pose(rz,centre)
        # Selected source-diameter J stake: shaft is vertical, curved head is
        # above earth. This pose is not a ground constraint or driving action.
        head_z=.075;shaft_z=.750-.0127-.00635;stake_offset=head_z-shaft_z
        stored=pose(axis_rotation(np.pi/2,[0,1,0]),[0,(-150-(i-1)*40)*.001,.00635])
        installed=site_pose@pose(position=[3.,0,stake_offset])@np.linalg.inv(stored)
        name='guy_stake_'+str(i);add(name,kit[name],installed,'anchoring_kit',name)
        anchor=np.array([3.-.0127,0,head_z]);top=np.array([.058,0,1.9]);up=top-anchor;up/=np.linalg.norm(up);down=-up
        side=np.array([0.,1.,0.]);radial=np.cross(side,up)
        hook_rotation=np.column_stack([side,-radial,up]);turn_rotation=np.column_stack([radial,side,up])
        # Orthogonal loop planes retain real holes. The 0.1 mm nominal gap
        # leaves geometric contact/preload unresolved and must be tested.
        hook_lower=anchor+up*(.0127+.010-.00635-.002-.0001)
        hook_centre=hook_lower+up*.010;hook_upper=hook_lower+up*.020
        buckle_lower=hook_upper+up*(.010+.007-.002-.002-.0001)
        buckle_centre=buckle_lower+up*.047;bottom=buckle_lower+up*.094
        stored_x=(140+(i-1)*65)*.001
        stored=pose(axis_rotation(np.pi/2,[1,0,0]),[stored_x,.095,.002])
        name='s_hook_'+str(i);add(name,kit[name],site_pose@pose(hook_rotation,hook_centre)@np.linalg.inv(stored),'anchoring_kit',name)
        stored=pose(axis_rotation(np.pi/2,[1,0,0]),[stored_x,0,.004])
        for suffix in ['body','eye_lower','eye_upper']:
            name='turnbuckle_'+str(i)+'_'+suffix
            add(name,kit[name],site_pose@pose(turn_rotation,buckle_centre)@np.linalg.inv(stored),'anchoring_kit',name)
        for endpoint,origin,axis,index in [('upper',top,down,2*i-1),('lower',bottom,up,2*i)]:
            rotation=np.column_stack([side,np.cross(axis,side),axis]);position=origin+.070*axis
            stored=pose(position=[(120+(index-1)*28)*.001,.155,.007])
            for suffix in ['body','screw']:
                source_name='wire_clamp_'+str(index)+'_'+suffix;name='guy_'+str(i)+'_'+endpoint+'_clamp_'+suffix
                add(name,kit[source_name],site_pose@pose(rotation,position)@np.linalg.inv(stored),'anchoring_kit',source_name)
        p=attached_wire(top,bottom,down);p=p@rz.T+centre
        wire=cable_mesh(p-centre,.0015);wire.visual=kit['uncut_guy_wire'].visual.copy();name='cut_guy_wire_'+str(i)
        g.scene.add_geometry(wire,node_name=name,geom_name=name,transform=pose(position=centre));g.parts.append(dict(id=name,role='static_routed_cut_wire',bounds_m=(wire.bounds+centre).tolist()))
        wires.append(dict(id=name,points_m=p.tolist(),radius_m=.0015,length_m=float(np.linalg.norm(np.diff(p,axis=0),axis=1).sum()),
            source_stock='uncut_guy_wire',upper_tail_m=.025,lower_tail_m=.025,loop_radius_m=.005,
            upper_eye_center_m=(rz@top+centre).tolist(),lower_eye_center_m=(rz@bottom+centre).tolist()))
        # One source-diameter foot stake passes through one actual plate hole.
        foot_offset=.0064-(.400-.009525-.003175)
        stored=pose(axis_rotation(np.pi/2,[0,1,0]),[0,(-280-(i-1)*40)*.001,.003175])
        name='foot_stake_'+str(i);add(name,kit[name],site_pose@pose(position=[.535,.015,foot_offset])@np.linalg.inv(stored),'anchoring_kit',name)
    # Use the same reviewed grounding parts, with a real rod/wire bore and
    # mast-side wire groove. No ideal electrical bond is created here.
    stored=pose(axis_rotation(np.pi/2,[0,1,0]),[0,.350,.00635])
    add('ground_rod',kit['ground_rod'],pose(position=centre+[.12,0,-1.1192])@np.linalg.inv(stored),'anchoring_kit','ground_rod')
    for suffix in ['body','bolt']:
        name='ground_rod_clamp_'+suffix
        add(name,kit[name],pose(position=centre+[.12,0,.075])@pose(position=[-.09,-.28,0]),'anchoring_kit',name)
    for name in ['ground_mast_u_bolt','ground_mast_saddle','ground_mast_nut_left','ground_mast_nut_right']:
        add(name,kit[name],pose(position=centre+[-.180,-.270,.245]),'anchoring_kit',name)
    p=ground_wire_points();wire=cable_mesh(p,.0015);wire.visual=kit['uncut_ground_wire'].visual.copy();name='cut_ground_wire'
    g.scene.add_geometry(wire,node_name=name,geom_name=name,transform=pose(position=centre));g.parts.append(dict(id=name,role='static_ground_wire_reference',bounds_m=(wire.bounds+centre).tolist()))
    ground_length=float(np.linalg.norm(np.diff(p,axis=0),axis=1).sum())
    wires.append(dict(id=name,points_m=(p+centre).tolist(),radius_m=.0015,length_m=ground_length,source_stock='uncut_ground_wire',
        upper_tail_m=.025,lower_tail_m=.025,tail_length_basis='Selected ground-wire tails, not dimensions supplied by the manufacturer',
        electrical_grounding_qualified=False))
    geometry=g.export('weather_support_installed_reference')
    guy_wires=[w for w in wires if w['source_stock']=='uncut_guy_wire'];used=sum(w['length_m'] for w in guy_wires);remaining=15.24-used
    assert remaining>0
    refs=[Path(__file__),HERE/'geometry_tools.py',HERE/'check_weather_assets.py',HERE/'build_weather_assets.py',HERE/'tripod_assets.json',HERE/'weather_anchoring_assets.json',HERE/'weather_site_review.json']
    record=dict(schema_version=1,status='unqualified_installed_pose_reference',geometry=geometry,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],rigid_part_transforms=transforms,installed_wires=wires,
        wire_stock_balance=dict(source_stock='uncut_guy_wire',source_length_m=15.24,cuts_m=[w['length_m'] for w in guy_wires],remaining_length_m=remaining,
            material_loss_m=0.,material_loss_status='Ideal length-only cut hypothesis; cutter kerf and deformation are not yet modeled',initial_inventory_credit=False),
        ground_wire_stock_balance=dict(source_stock='uncut_ground_wire',source_length_m=3.,cuts_m=[ground_length],remaining_length_m=3.-ground_length,material_loss_m=0.,
            material_loss_status='Ideal length-only cut hypothesis; selected stock length, no simulated cutting',initial_inventory_credit=False),
        missing=['Post level, attached weather sensors and logger, installed sensor/power/data routes','Ground-wire contact and electrical continuity','Contact, preload, tensile response, soil/anchor retention, loads and full robot access'],
        scope='Alternative static reference using the reviewed kit; uncut loose stock and this cut-wire state are not simultaneous initial inventory.',
        staged_in_lab=False,initial_stock_credit=False,installation_qualified=False,structural_load_qualified=False,ground_retention_qualified=False,electrical_grounding_qualified=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'weather_support_assets.json',record);print(json.dumps(dict(parts=geometry['parts'],used_guy_wire_m=used,remaining_guy_wire_m=remaining)))


if __name__=='__main__':build()
