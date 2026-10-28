"""Source-scale weather components, before installation or robot qualification.

The RS3 envelope and probe dimensions are manufacturer facts. Unpublished
lamella profiles, hardware, cable rest poses and adapter dimensions are author
selections. This generator never substitutes a display assembly for initial
stock or grants a weather-station installation.
"""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from scipy.optimize import brentq
from geometry_tools import Geometry, HERE, ROOT, sha, write_json
from build_supplies import export_review, solid, cad_mesh

WHITE=[230,232,229]; BLACK=[30,32,34]; STEEL=[180,188,195]


def revolved_profile(points):
    mesh=trimesh.creation.revolve(np.asarray(points)*.001,sections=128)
    mesh.merge_vertices(digits_vertex=8);mesh.fix_normals()
    assert mesh.is_watertight and mesh.volume>0
    return mesh


def ring_plate(radius,top,inner=14.,rise=8.,thickness=1.2):
    """A hollow vent lamella, with a real central opening and radial skirt."""
    return revolved_profile([(inner,top),(radius-8,top),(radius,top-rise),
        (radius-thickness,top-rise),(radius-8-thickness,top-thickness),
        (inner,top-thickness),(inner,top)])


def lid(radius,top,rise=12.,thickness=1.2):
    return revolved_profile([(0,top),(radius-8,top),(radius,top-rise),
        (radius-thickness,top-rise),(radius-8-thickness,top-thickness),
        (0,top-thickness),(0,top)])


def pierced(mesh,holes):
    cutters=[]
    for x,y,r in holes:
        c=trimesh.creation.cylinder(r*.001,.3,sections=64)
        c.apply_translation([x*.001,y*.001,.03]);cutters.append(c)
    return trimesh.boolean.difference([mesh,*cutters],engine='manifold')


def radiation_shield():
    g=Geometry();levels=[12.,21.,33.,45.,57.,66.2,89.]
    rod_holes=[(-29,0,1.7),(29,0,1.7)]
    for i,top in enumerate(levels):
        if i>=5:
            m=lid(51,top)
            # The top lid terminates the rods at its underside; it has no
            # invented visible bolt holes through the manufacturer's cap.
            if i==5:m=pierced(m,rod_holes)
        else:m=pierced(ring_plate(51 if i==0 else 42,top,rise=12 if i==0 else 8),rod_holes)
        g.add('shield_lamella_'+str(i+1),m,WHITE,role='shield_lamella')
    for side,x in [('left',-.029),('right',.029)]:
        g.cylinder('tie_rod_'+side,.0015,.0968,[x,0,.0394],STEEL,role='selected_hardware',metal=.8)
        for i,(lower,upper) in enumerate(zip(levels[:-1],levels[1:])):
            height=(upper-1.2-lower)*.001
            g.ring('rod_spacer_'+side+'_'+str(i+1),.0017,.0036,height,
                [x,0,(lower+upper-1.2)*.0005],WHITE,role='inferred_lamella_spacer')
        g.ring('knurled_nut_'+side,.0014,.004,.006,[x,0,-.006],[184,153,78],role='selected_hardware',metal=.8)
    plate=cq.Workplane('XY').box(70,24,3).val().translate((0,0,-1.5))
    for x,y,r in [(-29,0,1.7),(29,0,1.7),(0,0,3)]:
        plate=plate.cut(cq.Solid.makeCylinder(r,8,cq.Vector(x,y,-6)))
    # The sloped arm and mast tab are one molded candidate, not a floating
    # plate. Its rear tip is 102 mm beyond the 51 mm shield radius.
    arm=(cq.Workplane('YZ').polyline([(-8,-3),(-8,0),(-45,0),(-153,-43),
        (-153,-70),(-150,-70),(-150,-45),(-44,-3)]).close().extrude(9,both=True).val())
    bracket=plate.fuse(arm)
    for z in [-39,-60]:bracket=bracket.cut(cq.Solid.makeCylinder(2.4,12,cq.Vector(0,-158,z),cq.Vector(0,1,0)))
    solid(g,'inclined_mounting_bracket',bracket,WHITE,role='inferred_mounting_bracket')
    # Loose kit hardware is displayed beside the shield, not on an absent mast.
    band=trimesh.creation.annulus(.0208,.0213,.007,sections=128)
    band.apply_translation([.11,-.03,.004]);g.add('mast_band_candidate',band,STEEL,role='selected_hardware',metal=.8)
    housing=cq.Workplane('XY').box(10,9,8).val().translate((110,-5.7,4))
    housing=housing.cut(cq.Solid.makeCylinder(1.7,14,cq.Vector(103,-5.7,4),cq.Vector(1,0,0)))
    band_clearance=cq.Solid.makeCylinder(21.4,7.2,cq.Vector(110,-30,.4)).cut(cq.Solid.makeCylinder(20.7,8,cq.Vector(110,-30,0)))
    solid(g,'band_worm_housing',housing.cut(band_clearance),STEEL,metal=.8,role='inferred_clamp_housing')
    screw=cq.Solid.makeCylinder(1.6,10,cq.Vector(105,-5.7,4),cq.Vector(1,0,0)).fuse(cq.Solid.makeCylinder(2.5,2,cq.Vector(115,-5.7,4),cq.Vector(1,0,0)))
    screw=screw.cut(cq.Solid.makeBox(.8,.6,6,cq.Vector(116.3,-6,1)))
    solid(g,'band_screw',screw,STEEL,metal=.8,role='selected_hardware')
    # Six ordinary loose ties and two optional screws complete the kit count.
    # Their local sizes are explicit selections because the RS3 list supplies
    # quantities but no tie length or screw thread standard.
    for i in range(6):
        y=.075+i*.009
        g.box('loose_tie_'+str(i+1)+'_strap',[.150,.0025,.0008],[.075,y,.0004],WHITE,role='inferred_kit_tie')
        head=cq.Solid.makeBox(5,4,3,cq.Vector(-5,y*1000-2,0)).cut(cq.Solid.makeBox(7,2.7,1,cq.Vector(-6,y*1000-1.35,.9)))
        solid(g,'loose_tie_'+str(i+1)+'_head',head,WHITE,role='inferred_kit_tie')
    for i in range(2):
        x=.075+i*.015
        screw=cq.Solid.makeCylinder(1.7,20,cq.Vector(x*1000,-80,2.5),cq.Vector(0,1,0)).fuse(cq.Solid.makeCylinder(3.2,2,cq.Vector(x*1000,-60,2.5),cq.Vector(0,1,0)))
        screw=screw.cut(cq.Solid.makeBox(7,.8,.7,cq.Vector(x*1000-3.5,-58.7,2.15)))
        solid(g,'optional_wall_screw_'+str(i+1),screw,STEEL,metal=.8,role='inferred_kit_wall_screw')
    geometry=export_review(g,'weather_onset_rs3')
    return dict(id='onset_rs3',identity='Onset RS3 solar radiation shield; selected ordinary accessory',
        geometry=geometry,resources=['equipment:WEATHER'],source_ids=['ONSET_RS3_MANUAL'],
        interfaces=dict(sensor_seat_z_m=0,lowest_closed_ceiling_z_m=.065,rod_centres_m=[[-.029,0,0],[.029,0,0]],selected_mast_diameter_m=.041),
        facts=dict(shield_height_m=.089,shield_diameter_m=.102,total_height_with_bracket_m=.159,bracket_protrusion_m=.102,ceiling_clearance_m=.065),
        inferences=['Seven lamella levels from the manual cross-section; 1.2 mm wall and exact skirt profiles are selected, not manufacturer CAD.',
            'M3 rods, spacers, nut shapes, 3 mm bracket section, holes and clamp dimensions are inferred; thread and clamp-drive contact are not modeled.',
            'Nominal sensor clearance and component geometry do not establish ventilation, radiation performance or retention.'],
        kit_counts=dict(shield=1,bracket=1,knurled_nuts=2,cable_ties=6,wall_mount_screws=2,hose_clamp=1),
        kit_dimension_inferences=['Loose ties: selected 150 x 2.5 x 0.8 mm straps; optional screws: selected 3.4 mm smooth thread envelopes and 20 mm length.',
            'Loose clamp has a real screw bore and band channel; worm teeth, thread preload and elastic band adjustment are not represented.'],
        missing_kit_parts=[],
        initial_stock_credit=False,assembly_qualified=False,owner_acceptance=None)


def cable_mesh(points,radius,endpoint_tangents=None):
    """One closed sweep with parallel-transport frames and no reference flip.

    Choosing a new reference axis at every ring twists polygonal sections when
    a lead turns through a near-vertical direction. Transport the previous
    normal by the shortest rotation between consecutive tangents instead.
    """
    points=np.asarray(points);tangent=np.gradient(points,axis=0);tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    if endpoint_tangents is not None:
        tangent[[0,-1]]=np.array(endpoint_tangents)/np.linalg.norm(endpoint_tangents,axis=1)[:,None]
    vertices=[];previous=None;previous_t=None
    for point,t in zip(points,tangent):
        if previous is None:
            ref=np.eye(3)[np.argmin(np.abs(t))]
            normal=np.cross(t,ref)
        else:
            axis=np.cross(previous_t,t);cosine=float(previous_t@t)
            if cosine < -1+1e-8:raise ValueError('Cable tangent reverses within one segment')
            # Rodrigues' shortest-arc rotation, including the parallel case.
            normal=previous+np.cross(axis,previous)+np.cross(axis,np.cross(axis,previous))/(1+cosine)
        normal-=t*(normal@t);normal/=np.linalg.norm(normal)
        previous=normal;previous_t=t;binormal=np.cross(t,normal)
        vertices.extend(point+radius*(np.cos(a)*normal+np.sin(a)*binormal) for a in np.linspace(0,2*np.pi,12,endpoint=False))
    faces=[];n=12
    for i in range(len(points)-1):
        for j in range(n):k=(j+1)%n;a=i*n+j;b=i*n+k;c=(i+1)*n+k;d=(i+1)*n+j;faces.extend([[a,b,c],[a,c,d]])
    for j in range(1,n-1):faces.extend([[0,j+1,j],[(len(points)-1)*n,(len(points)-1)*n+j,(len(points)-1)*n+j+1]])
    mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=True);mesh.fix_normals();assert mesh.is_watertight and mesh.volume>0
    return mesh


def rest_coil(length,centre,turns,start,end,start_direction,end_direction,angle0):
    """Solve one continuous lead, including its two smooth coil transitions."""
    start=np.array(start);end=np.array(end);angle=np.linspace(angle0,angle0+2*np.pi*turns,401)
    def bezier(a,b,c,d):
        t=np.linspace(0,1,61)[:,None]
        return (1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d
    def points(radius):
        helix=np.column_stack([centre[0]+radius*np.cos(angle),centre[1]+radius*np.sin(angle),np.linspace(start[2],start[2]+.0045*turns,len(angle))])
        tangents=[helix[1]-helix[0],helix[-1]-helix[-2]]
        tangents=[v/np.linalg.norm(v) for v in tangents]
        entry=bezier(start,start+.020*np.array(start_direction),helix[0]-.020*tangents[0],helix[0])
        # Turn out of the coil with an explicit 15 mm radius before routing
        # toward the adapter. A single short Bezier here produced a sub-mm
        # bend despite passing the nonlocal line-to-line separation check.
        tangent=tangents[1];normal=np.array([-tangent[1],tangent[0],0.]);normal/=np.linalg.norm(normal)
        if normal@(end-helix[-1])<0:normal=-normal
        theta=np.linspace(0,np.pi/2,41)[:,None]
        arc=helix[-1]+.015*(np.sin(theta)*tangent+(1-np.cos(theta))*normal)
        exit=bezier(arc[-1],arc[-1]+.035*normal,end-.035*np.array(end_direction),end)
        return np.vstack([entry[:-1],helix,arc[1:],exit[1:]])
    radius=brentq(lambda r:np.linalg.norm(np.diff(points(r),axis=0),axis=1).sum()-length,.008,.15)
    return points(radius)


def modular_plug(g,origin):
    """Original envelope reconstruction of a selected round-cable 6P6C plug.

    This is not an assertion that Onset used a Cinch part. Published dimensions
    constrain the interface; the cavities, latch profile and contact channels
    are authored. No electrical pin assignment is supplied by this geometry.
    """
    origin=np.array(origin)*1000;shift=origin-np.array([0,0,3.3])
    body=cq.Workplane('XY').box(12.32,9.65,6.60).edges('|X').fillet(.3).val().translate((6.16,0,3.3))
    body=body.cut(cq.Solid.makeBox(8.5,7.21,3.39,cq.Vector(-.1,-3.605,1.3)))
    for i in range(6):
        y=(i-2.5)*1.02
        body=body.cut(cq.Solid.makeBox(5.7,.6,1.6,cq.Vector(6.9,y-.3,5.1)))
        contact=cq.Solid.makeBox(6.34,.4,.4,cq.Vector(7,y-.2,5.2)).fuse(cq.Solid.makeBox(1.02,.4,6.47,cq.Vector(12.32,y-.2,1)))
        solid(g,'plug_contact_'+str(i+1),contact.translate(tuple(shift)),[208,165,66],metal=.8,role='inferred_modular_contact')
    latch=(cq.Workplane('XZ').polyline([(11.7,0),(10.7,0),(10.7,-.6),(-1.2,-3.7),(-1.2,-4.5),(11.7,-1.15)]).close().extrude(1.625,both=True).val())
    body=body.fuse(latch)
    mesh=cad_mesh(body.translate(tuple(shift)))
    g.add('modular_plug_body_and_latch',mesh,[210,222,223],alpha=155,role='inferred_modular_body')
    return dict(selected_reference='Cinch 32-5996UL round-cable RJ12 (6P6C)',
        historical_onset_vendor_unknown=True,cable_entry_m=(origin*.001).tolist(),
        dimensions_m=dict(reference_contact_to_body_length=.01334,body_width=.00965,body_height=.0066,contact_pitch=.00102),
        source_id='CINCH_325996UL_DRAWING',electrical_pinout_known=False,insertion_qualified=False)


def temperature_sensor():
    g=Geometry()
    # The manufacturer's 10 x 35 mm dimension applies to the probe head,
    # excluding the lead and inline digital adapter.
    g.cylinder('probe_receptacle',.005,.010,[0,0,.020],BLACK,role='probe_head')
    cap=cq.Solid.makeCylinder(5,25,cq.Vector(0,0,25)).cut(cq.Solid.makeCylinder(3.8,23.8,cq.Vector(0,0,25)))
    solid(g,'rh_membrane_cap',cap,WHITE,role='probe_head')
    g.cylinder('sensor_board_envelope',.0024,.020,[0,0,.035],BLACK,role='inferred_sensor_interior')
    relief=revolved_profile([(0,4.5),(2.5,4.5),(3,7),(4.5,15),(0,15),(0,4.5)])
    g.add('probe_strain_relief_candidate',relief,BLACK,role='inferred_strain_relief')
    # Lay the complete head on its cylindrical side. The cable exits along +X
    # at the actual relief face; the probe is not balanced on its flexible lead.
    pose=trimesh.transformations.rotation_matrix(-np.pi/2,[0,1,0]);pose[:3,3]=[.015,0,.005]
    for part in g.parts:
        mesh=g.scene.geometry[part['id']];mesh.apply_transform(pose);part['bounds_m']=mesh.bounds.tolist()
    # These measured-length leads form continuous paths between the probe,
    # adapter and selected free connector location; no U30 connection is claimed.
    leads=[]
    for name,length,centre,turns,start,end,initial,final,angle0 in [
        ('probe_lead',2.,[.12,0],4,[.0105,0,.005],[-.0625,.15,.007],[1,0,0],[-1,0,0],np.pi),
        ('network_lead',.5,[-.245,.15],1,[-.1375,.15,.007],[-.10,.28,.0078],[-1,0,0],[1,0,0],0)]:
        pts=rest_coil(length,centre,turns,start,end,initial,final,angle0)
        g.add(name,cable_mesh(pts,.0015,[initial,final]),BLACK,role='authored_stored_cable')
        leads.append(dict(id=name,length_m=length,points_m=pts.tolist(),radius_m=.0015,endpoints_m=[start,end],endpoint_tangents=[initial,final],installed_in_logger=False))
    adapter=cq.Workplane('XY').box(75,18,14).edges('|X').fillet(2).val().translate((-100,150,7))
    for x in [-138,-65]:adapter=adapter.cut(cq.Solid.makeCylinder(1.6,4,cq.Vector(x,150,7),cq.Vector(1,0,0)))
    solid(g,'inline_adapter_candidate',adapter,BLACK,role='inferred_digital_adapter')
    plug=modular_plug(g,[-.10,.28,.0078])
    geometry=export_review(g,'weather_onset_sthb_m002')
    return dict(id='onset_sthb_m002',identity='Onset S-THB-M002 temperature/RH probe and selected lead reconstruction',
        geometry=geometry,resources=['equipment:WEATHER'],source_ids=['ONSET_STHB_MANUAL','ONSET_U30_RC_MANUAL','CINCH_325996UL_DRAWING'],
        facts=dict(probe_diameter_m=.010,probe_length_m=.035,total_cable_m=2.5,network_cable_m=.5),
        stored_leads=leads,modular_plug=plug,inferences=['Probe cap/receptacle split, membrane geometry, 3 mm cable diameter and 75 x 18 x 14 mm inline adapter are authored hypotheses.',
            'The U30 manual identifies RJ12 ports. Cinch 32-5996UL supplies a selected round-cable envelope, not the unknown Onset connector vendor or an electrical compatibility result.',
            'Connected stored cable centerlines preserve 2.0 + 0.5 m, including smooth transitions; rest poses are authored and have not been gravity settled.'],
        missing_parts=['Verified Onset adapter and terminal connector details; U30 port cavity and retention fit'],
        initial_stock_credit=False,assembly_qualified=False,owner_acceptance=None)


def build():
    items=[radiation_shield(),temperature_sensor()]
    files=[Path(__file__),HERE/'weather_sources.json',HERE/'geometry_tools.py',HERE/'build_supplies.py']
    record=dict(schema_version=1,status='incomplete_weather_component_geometry',items=items,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in files],
        staged_in_lab=False,weather_station_complete=False,owner_acceptance=None)
    write_json(HERE/'weather_assets.json',record)
    print(json.dumps(dict(component_models=len(items),staged_in_lab=False)))


if __name__=='__main__':build()
