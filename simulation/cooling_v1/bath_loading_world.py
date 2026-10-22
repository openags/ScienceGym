"""Development bath-load fixture with a genuinely bored copper block.

The paper omits block dimensions. This candidate selects 50 x 50 x 80 mm
instead of the earlier fixed 80 mm block, so the movable block and cradle
fit the selected 3 kg robot payload. It is not yet a released task profile.
"""
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import Delaunay
from world import World,TOP,vec
from bath_world import build as build_bath

BLOCK_PARK=np.array([.58,-.16,TOP+.012])
CRADLE_PARK=np.array([.265,.25,TOP+.012])
CRADLE_TARGET=np.array([.52,.000,.695])


def bored_block(world,body):
    # A planar triangulation is extruded into convex triangular prisms.
    # Every hole remains an open physical corridor, never a convex hull.
    holes=[dict(id='reference_rtd',center_m=[0.,0.],radius_m=.0033,segments=48)]
    holes += [dict(id='type_k_'+str(i+1),center_m=[.022*np.cos(a),.022*np.sin(a)],radius_m=.0004,segments=16)
              for i,a in enumerate(np.arange(8)*np.pi/4)]
    # Keep the solid outer 2 mm border as four continuous faces. Exposing
    # dozens of coplanar prism faces to a finger overconstrains friction.
    # The decomposition changes; the drilled volume and exterior do not.
    points=[[-.023,-.023],[.023,-.023],[.023,.023],[-.023,.023]]
    for hole in holes:
        x,y=hole['center_m'];r=hole['radius_m'];n=hole['segments']
        points.extend([[x+r*np.cos(a),y+r*np.sin(a)] for a in np.arange(n)*2*np.pi/n])
    points=np.array(points);triangles=[];area=0.;density=8960.
    for ids in Delaunay(points).simplices:
        tri=points[ids];center=tri.mean(axis=0)
        if any(np.linalg.norm(center-h['center_m'])<h['radius_m']*.999 for h in holes):continue
        cell_area=abs(float(np.linalg.det(np.array([tri[1]-tri[0],tri[2]-tri[0]]))))/2
        triangles.append((tri,cell_area));area+=cell_area
    exact_area=.046**2-sum(h['segments']*h['radius_m']**2*np.sin(2*np.pi/h['segments'])/2 for h in holes)
    if abs(area-exact_area)>1e-12:raise ValueError('Hole-preserving triangulation area mismatch')
    world.box(body,'calblock_floor',[.025,.025,.001],[0,0,.001],[.66,.34,.15,1],mass=str(.05*.05*.002*density))
    for side in [-1,1]:
        world.box(body,'calblock_outer_x_'+str(side),[.001,.025,.039],[side*.024,0,.041],[.66,.34,.15,1],density=str(density),friction='1.4 .01 .006',condim='3',solref='.004 1',solimp='.99 .99 .0001')
        world.box(body,'calblock_outer_y_'+str(side),[.023,.001,.039],[0,side*.024,.041],[.66,.34,.15,1],density=str(density),friction='1.4 .01 .006',condim='3',solref='.004 1',solimp='.99 .99 .0001')
    for i,(tri,cell_area) in enumerate(triangles):
        name='calblock_cell_'+str(i);vertices=np.vstack([np.c_[tri,np.full(3,z)] for z in [.002,.080]])
        ET.SubElement(world.assets,'mesh',name=name,vertex=vec(vertices.ravel()))
        ET.SubElement(body,'geom',name=name,type='mesh',mesh=name,mass=str(cell_area*.078*density),rgba='.66 .34 .15 1',friction='1.4 .01 .006',condim='3',solref='.004 1',solimp='.99 .99 .0001')
    ET.SubElement(body,'site',name='calibration_block_grasp',pos='0 0 .045',size='.002')
    for hole in holes:ET.SubElement(body,'site',name='calblock_hole_'+hole['id'],pos=vec([*hole['center_m'],.080]),size='.0003')
    return dict(envelope_m=[.05,.05,.08],bore_depth_m=.078,holes=holes,selected_density_kg_m3=density,
                mass_kg=(.05*.05*.002+(area+.05**2-.046**2)*.078)*density,convex_cells=len(triangles)+4,cross_section_area_m2=area+.05**2-.046**2)


def build(path):
    configuration=build_bath(path);w=World();w.root=ET.parse(path).getroot();w.w=w.root.find('worldbody');w.assets=w.root.find('asset')
    w.root.find('option').attrib.update(timestep='.0002',noslip_iterations='0')
    # Load handling uses the stock gripper configuration. The long panel
    # pusher has no role here and obstructs the cradle's lifting handle.
    # Remove its complete physical/visual assembly at scene construction;
    # this is an explicit tooling precondition, not a runtime collision mask.
    hand=w.root.find(".//body[@name='hand']")
    hand.remove(hand.find("body[@name='button_probe']"));hand.remove(hand.find("site[@name='bath_pusher_tcp']"))
    # Finite face contacts use three-dimensional friction cones; their
    # separated contact points supply the patch moment without adding a
    # rolling/spinning wrench at every vertex.
    # Selected flat rubber overlays cover the source pads' interrupted
    # inner face. The original collision geometry stays behind them. Their
    # real thickness, mass and inertia are included; no collision is masked.
    for side in ['left_finger','right_finger']:
        finger=w.root.find(".//body[@name='"+side+"']")
        half=np.array([.0085,.00075,.009]);position=np.array([0,-.00075,.0445]);mass=float(np.prod(2*half)*1300.)
        inertial=finger.find('inertial');old_mass=float(inertial.get('mass'));old_pos=np.fromstring(inertial.get('pos'),sep=' ')
        old_tensor=np.diag(np.fromstring(inertial.get('diaginertia'),sep=' '));total=old_mass+mass;center=(old_mass*old_pos+mass*position)/total
        sizes=2*half;pad_tensor=mass/12*np.diag([sizes[1]**2+sizes[2]**2,sizes[0]**2+sizes[2]**2,sizes[0]**2+sizes[1]**2]);tensor=np.zeros((3,3))
        for weight,point,inertia in [(old_mass,old_pos,old_tensor),(mass,position,pad_tensor)]:
            delta=point-center;tensor+=inertia+weight*(np.dot(delta,delta)*np.eye(3)-np.outer(delta,delta))
        inertial.attrib.clear();inertial.attrib.update(mass=str(total),pos=vec(center),fullinertia=vec([tensor[0,0],tensor[1,1],tensor[2,2],tensor[0,1],tensor[0,2],tensor[1,2]]))
        w.box(finger,side+'_load_overlay',half,position,[.12,.16,.18,1],mass=str(mass),friction='1.4 .01 .006',condim='3',solref='.004 1',solimp='.99 .99 .0001')
    block=w.body('calibration_block',BLOCK_PARK);block_configuration=bored_block(w,block)
    block_stand=w.body('calibration_block_stand',[*BLOCK_PARK[:2],TOP],False)
    w.box(block_stand,'calblock_staging_support',[.024,.024,.006],[0,0,.006],[.12,.32,.40,1])
    cradle=w.body('block_cradle',CRADLE_PARK)
    w.box(cradle,'block_cradle_floor',[.031,.031,.002],[0,0,.002],[.20,.39,.46,1],density='2700')
    for side in [-1,1]:
        w.box(cradle,'block_cradle_x_guide_'+str(side),[.002,.028,.004],[side*.028,0,.008],[.20,.39,.46,1],density='2700')
        w.box(cradle,'block_cradle_y_guide_'+str(side),[.026,.002,.004],[0,side*.028,.008],[.20,.39,.46,1],density='2700')
        ET.SubElement(cradle,'geom',name='block_cradle_handle_post_'+str(side),type='capsule',fromto=vec([side*.050,0,.004,side*.050,0,.174]),size='.0035',density='2700',rgba='.20 .39 .46 1')
        w.box(cradle,'block_cradle_handle_foot_'+str(side),[.014,.006,.002],[side*.043,0,.002],[.20,.39,.46,1],density='2700')
    # A balanced overhead yoke carries the load above its centre of mass.
    # The block is inserted horizontally underneath it with a side grasp.
    # Cover the source pads' full 17 mm height with a 20 mm rectangular
    # lifting section. The earlier short section was grasped near the pad
    # tips and could settle past their lower edge under the 1.9 kg load.
    w.box(cradle,'block_cradle_grip_bar',[.055,.006,.010],[0,0,.180],
        [.20,.39,.46,1],density='2700',friction='1.4 .01 .006',condim='3',
        solref='.004 1',solimp='.99 .99 .0001')
    # A continuous upper flange bears on the top of the source finger pads.
    # This authored lifting profile provides geometric load retention after
    # at most the selected 1.5 mm settling gap; a friction-only handle did
    # not retain this load. It is solid collision geometry, not a grasp weld.
    w.box(cradle,'block_cradle_grip_flange',[.055,.010,.002],[0,0,.192],
        [.20,.39,.46,1],density='2700',friction='1.4 .01 .006',condim='3',
        solref='.004 1',solimp='.99 .99 .0001')
    contact=w.root.find('contact')
    if contact is None:contact=ET.SubElement(w.root,'contact')
    pair_count=0
    for side in ['left_finger','right_finger']:
        for index,g in enumerate(w.root.findall(".//body[@name='"+side+"']/geom")):
            if g.get('class')=='visual' or (g.get('contype')=='0' and g.get('conaffinity')=='0'):continue
            name=g.get('name') or side+'_load_contact_'+str(index);g.set('name',name)
            # Retention must come from the lifting flange even on a low
            # friction handle. High friction between both orthogonal faces
            # locked in lateral tracking error during initial load transfer.
            for handle in ['block_cradle_grip_bar','block_cradle_grip_flange']:
                ET.SubElement(contact,'pair',geom1=name,geom2=handle,condim='3',friction='.3 .3 0 0 0',solref='.004 1',solimp='.99 .99 .0001')
            pair_count+=1
            for block_face in ['calblock_outer_x_-1','calblock_outer_x_1']:
                ET.SubElement(contact,'pair',geom1=name,geom2=block_face,condim='3',friction='1.4 1.4 .01 .006 .006',solref='.004 1',solimp='.99 .99 .0001')
    ET.SubElement(cradle,'site',name='block_cradle_grasp',pos='0 0 .180',size='.002')
    cradle_stand=w.body('block_cradle_stand',[*CRADLE_PARK[:2],TOP],False)
    w.box(cradle_stand,'block_cradle_staging_support',[.031,.031,.006],[0,0,.006],[.12,.32,.40,1])
    for side in [-1,1]:
        w.box(cradle_stand,'block_cradle_staging_foot_support_'+str(side),[.014,.006,.006],[side*.043,0,.006],[.12,.32,.40,1])
    for side in [-1,1]:
        for along in [-.015,.015]:
            w.cylinder(cradle_stand,'cradle_stage_x_guide_'+str(side)+'_'+str(along),.002,.010,[side*.034,along,.022],[.12,.32,.40,1])
            w.cylinder(cradle_stand,'cradle_stage_y_guide_'+str(side)+'_'+str(along),.002,.010,[along,side*.034,.022],[.12,.32,.40,1])
    support=w.body('bath_load_support',[*CRADLE_TARGET[:2],.615],False)
    # Four posts and an open frame keep water access around the block.
    for x in [-.025,.025]:
        for y in [-.025,.025]:w.cylinder(support,'bath_load_post_'+str(x)+'_'+str(y),.003,.038,[x,y,.038],[.25,.36,.41,1])
    for x in [-.027,.027]:w.box(support,'bath_load_rail_'+str(x),[.004,.035,.002],[x,0,.078],[.25,.36,.41,1])
    w.save(path)
    configuration.update(block=block_configuration,block_park_m=BLOCK_PARK.tolist(),cradle_park_m=CRADLE_PARK.tolist(),
        cradle_bath_target_m=CRADLE_TARGET.tolist(),block_in_cradle_offset_m=[0,0,.004],block_grip_N=30.,cradle_grip_N=12.,
        candidate_profile_deviation='Movable 50 x 50 x 80 mm block replaces the earlier fixed 80 mm cube; not released as the task profile.',
        initial_tool_configuration='Source fingers with selected 1.5 mm flat rubber overlays; panel pusher absent. Physical tool exchange is not credited by this development episode.',
        selected_pad_overlay_dimensions_m=[.017,.0015,.018],selected_pad_overlay_density_kg_m3=1300.,selected_loading_timestep_s=.0002,selected_surface_contact_dimension=3,
        block_grasp_offset_m=[0,0,.045],block_entry_clearance_m=.030,block_release_opening_m=.054,block_jaw_contact_pairs=pair_count*2,block_jaw_solimp=[.99,.99,.0001],
        cradle_handle_offset_m=[0,0,.180],cradle_crossbar_section_m=[.012,.020],cradle_crossbar_shape='12 x 20 mm stem with 20 x 4 mm upper load-bearing flange',cradle_grip_flange_section_m=[.020,.004],selected_flange_settling_gap_m=.0015,cradle_grasp_width_m=.012,cradle_grip_contact_pairs=pair_count*2,cradle_grip_solimp=[.99,.99,.0001],selected_cradle_jaw_friction=.3,selected_noslip_iterations=0,block_transfer_clearance_m=.20,
        scope='Development: lid removal, block-to-cradle transfer and retained bath load handling. Fluid, probes, electrical path and calibration remain separate.',whole_paper_validated=False)
    return configuration
