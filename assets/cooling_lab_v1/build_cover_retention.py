"""Ordinary angle-stock retainers and an aperture bond for the cover candidate.

Selected machining and assembly geometry, not historical hardware identity or
thread/preload qualification. No robot-specific fixture is introduced.
"""
import numpy as np
import cadquery as cq
import trimesh
from build_apparatus_mounting import cad_mesh, display, washer, HOLES
from build_apparatus_frame import screw, pose


def apply_retention(parts):
    result={n:m.copy() for n,m in parts.items()};added=[];replaced=[]
    leg=12.7;thickness=1.5875;width=10.;base_radius=85.;angles=[30.,150.,270.]
    platform=cq.Solid.makeBox(180,180,5,cq.Vector(-90,-90,-5))
    for x,y in HOLES:
        platform=platform.cut(cq.Solid.makeCylinder(1.7,7,cq.Vector(x,y,-6)))
        platform=platform.cut(cq.Solid.makeCone(1.7,3.36,1.66,cq.Vector(x,y,-1.66)))
    shield=cq.Solid.makeCylinder(76,57).cut(cq.Solid.makeCylinder(70,57))
    bracket=cq.Solid.makeBox(leg,width,thickness,cq.Vector(76,-width/2,0)).fuse(
        cq.Solid.makeBox(thickness,width,leg,cq.Vector(76,-width/2,0))).clean()
    bracket=bracket.cut(cq.Solid.makeCylinder(1.7,thickness+2,cq.Vector(75,-0.,8),cq.Vector(1,0,0)))
    bracket=bracket.cut(cq.Solid.makeCylinder(1.7,thickness+2,cq.Vector(base_radius,0,-1)))
    connections=[]
    def add(name,mesh):
        result[name]=display(mesh);added.append(name)
    for i,angle in enumerate(angles,1):
        phi=np.radians(angle);direction=np.array([np.cos(phi),np.sin(phi),0.])
        base_xy=direction[:2]*base_radius
        platform=platform.cut(cq.Solid.makeCylinder(1.5,7,cq.Vector(*base_xy,-6)))
        # Major-diameter through-bore envelope only; no helical mating claim.
        shield=shield.cut(cq.Solid.makeCylinder(1.5,10,cq.Vector(*(direction*78+np.array([0,0,8]))),cq.Vector(*(-direction))))
        rotation=trimesh.transformations.rotation_matrix(phi,[0,0,1])
        angle_mesh=cad_mesh(bracket);angle_mesh.apply_transform(rotation)
        add('shield_angle_'+str(i),angle_mesh)
        side=pose(screw(3,6),[76+thickness,0,8],axis=(-1,0,0));side.apply_transform(rotation)
        add('shield_side_screw_'+str(i),side)
        bottom=pose(screw(3,6),[base_radius,0,thickness+.8],axis=(0,0,-1));bottom.apply_transform(rotation)
        add('shield_base_screw_'+str(i),bottom)
        ring=washer();ring.apply_translation([base_radius*.001,0,(thickness+.4)*.001]);ring.apply_transform(rotation)
        add('shield_base_washer_'+str(i),ring)
        connections.append(dict(index=i,angle_deg=angle,base_center_xy_m=(base_xy*.001).tolist(),
            side_screw_axis=(-direction).tolist(),side_screw_underhead_m=((direction*(76+thickness)+np.array([0,0,8]))*.001).tolist(),
            side_nominal_thread_insertion_m=(6-thickness)*.001,
            base_nominal_thread_insertion_m=(6-thickness-.8)*.001,
            side_bracket_contact='Flat stock tangent to the cylindrical wall; local bearing, deformation and preload unqualified'))
    for name,shape in [('lift_plate',platform),('radiation_shield',shield)]:
        m=display(cad_mesh(shape));m.visual=parts[name].visual.copy();result[name]=m;replaced.append(name)
    adhesive=trimesh.creation.annulus(.070,.076,.000058,sections=256)
    adhesive.apply_translation([0,0,.057+.000058/2])
    result['aperture_bond']=display(adhesive,(.73,.70,.59,.9),0);added.append('aperture_bond')
    result['aperture_plate'].apply_translation([0,0,.000058]);replaced.append('aperture_plate')
    return result,dict(added_parts=added,replaced_parts=replaced,connections=connections,
        platform_selected_size_m=[.180,.180,.005],angle_section_m=[.0127,.0127,.0015875],angle_cut_width_m=.010,
        base_screw='M3x6 cap, 9/3.2x0.8 mm large washer',side_screw='M3x6 cap',
        aperture_bond_gauge_m=.000058,physical_retention_qualified=False,
        assembly_scope='Three ordinary angle-stock retainers; source-dimensioned standard hardware envelopes. Drilling/tapping, stock, tools, tolerances, adhesion and preload remain unqualified.')
