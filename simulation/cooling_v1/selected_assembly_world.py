"""Declared contact discretization for the integrated manipulation sample.

Visual source meshes remain unchanged. Ring collisions approximate circular
surfaces with 24 pieces; the maximum outward envelope error is measured below.
The two membranes retain free vertices and contact-based load transfer.
"""
import copy
import json
import re
import xml.etree.ElementTree as ET
import numpy as np
from integrated_world import build as original
from membrane import sheet
from film_contact import exact_cuboid_contacts
from world import vec,HERE


def build(path):
    profile=json.loads((HERE.parents[1]/'tasks/directional_cooling_operations_v3/selected_reconstruction.json').read_text())['cards']
    geometry=profile['geometry_card']['selected_geometry_and_unresolved_conflict_record']['value']
    grasp=profile['manipulation_card']['contact_regions_and_approach_frames']['value']
    forces=profile['manipulation_card']['force_torque_clearance_limits']['value']
    if geometry['shield_shims_m']!=.0069 or geometry['PE_height_m']!=.057 or geometry['aperture_m']!=.001:
        raise ValueError('This bound workcell requires the declared 57 mm tube, 6.9 mm shims and 1 mm aperture')
    targets=original(path);tree=ET.parse(path);root=tree.getroot()
    root.find('option').attrib.update(timestep='.001',noslip_iterations='0',impratio='10',
                                    integrator='discrete',solver='CG',iterations='3200',tolerance='1e-8')
    root.find('option/flag').set('sleep','disable')
    # The original 6 mm-thick inner tip left only 0.5 mm beside the cover.
    # Select a 2 mm-thick stem and tip. The long aligned stem face provides
    # a stable moment arm on the 424 g cantilevered shield. Merely moving
    # a 3 mm pad to the top edge lost the payload during transport.
    for side in ['left_finger','right_finger']:
        tip=root.find(f".//geom[@name='{side}_edge_tip']")
        half=grasp['edge_jaw_thickness_m']/2
        tip.set('size',vec([.006,half,grasp['edge_tip_height_m']/2]));tip.set('pos',vec([0,half,.090]))
        stem=root.find(f".//geom[@name='{side}_edge_stem']")
        stem.set('size',vec([.006,half,.018]));stem.set('pos',vec([0,half,.070]))
        stem.set('friction','1.4 .01 .006');stem.set('condim','6')
    root.find(".//site[@name='shield_grasp']").set('pos',vec(grasp['shield_grip_local_m']))
    # The selected fixture, unlike the source-sized shield, is ours to design.
    # Its original 0.5 mm radial clearance was smaller than the polygonal
    # collision envelope plus observed placement error. The shield hung on
    # two pins instead of reaching the three height shims. Keep 2.5 mm of
    # nominal radial clearance; record the remaining discretized clearance.
    for geom in root.findall('.//geom'):
        if geom.get('name','').startswith('shield_alignment_pin_'):
            pos=np.fromstring(geom.get('pos'),sep=' ')
            pos[:2]*=geometry['shield_alignment_pin_radius_m']/np.linalg.norm(pos[:2]);geom.set('pos',vec(pos))
    cover=root.find(".//body[@name='cover']")
    for child in list(cover):
        if child.tag=='flexcomp' or '_bonded_annulus_' in child.get('name',''):cover.remove(child)
    props=[sheet(cover,'cover_lower',-.003208,sectors=16,elastic=True),sheet(cover,'cover_upper',.003208,sectors=16,elastic=True)]
    # Implicit continuum elasticity avoids the observed isolated 44% edge
    # excursion of the constrained-edge approximation. The damping is an
    # explicitly selected numerical/material parameter, not a vendor value.
    for flex in cover.findall('flexcomp'):
        flex.find('elasticity').set('damping','.002')
        flex.find('contact').attrib.update(priority='1',solimp='.999 .999 .0001')
    for prop in props:prop['damping_s']=.002
    cover.find("geom[@name='bonded_mass']").set('mass',str(sum(p['mass_on_parent_kg'] for p in props)))
    targets['cover']['film_properties']=props
    rings=[]
    for body in root.iter('body'):
        groups={}
        for geom in body.findall('geom'):
            if geom.get('type')!='box' or geom.get('contype')=='0':continue
            match=re.fullmatch(r'(.+)_(\d+)',geom.get('name',''))
            if match:groups.setdefault(match[1],[]).append((int(match[2]),geom))
        for name,pieces in groups.items():
            pieces.sort(key=lambda x:x[0])
            if [i for i,g in pieces]!=list(range(48)):continue
            p=np.array([np.fromstring(g.get('pos','0 0 0'),sep=' ') for i,g in pieces]);sizes=np.array([np.fromstring(g.get('size'),sep=' ') for i,g in pieces])
            radii=np.linalg.norm(p[:,:2],axis=1)
            if np.ptp(radii)>1e-8 or not np.allclose(sizes,sizes[0]) or np.ptp(p[:,2])>1e-8:continue
            total_mass=sum(float(g.get('mass',0)) for i,g in pieces)
            for i,g in pieces:body.remove(g)
            for i in range(24):
                g=copy.deepcopy(pieces[2*i][1]);g.set('name',name+'_'+str(i));size=sizes[0].copy();size[1]*=2;g.set('size',vec(size));g.set('mass',str(total_mass/24));body.append(g)
            analytic_outer=radii[0]+sizes[0,0]
            envelope=np.hypot(analytic_outer,2*sizes[0,1])-analytic_outer
            if envelope>.00075:raise ValueError('Ring collision envelope exceeds selected 0.75 mm tolerance: '+name)
            rings.append(dict(name=name,segments=24,total_mass_kg=total_mass,
                              minimum_bore_radius_m=float(radii[0]-sizes[0,0]),
                              maximum_outward_envelope_error_m=float(envelope)))
    cuboids=exact_cuboid_contacts(root)
    ET.indent(root);tree.write(path,encoding='unicode')
    return targets,dict(ring_collision_discretization=rings,membrane_sectors=16,
        membrane_model='Saint Venant-Kirchhoff',selected_young_Pa=1e8,selected_poisson=.35,selected_damping_s=.002,
        solver='CG',integrator='discrete',solver_iterations=3200,
        film_support_collision_method='exact cuboid mesh with convex-element narrow phase',
        film_support_cuboids=cuboids,film_contact_priority=1,film_contact_solimp=[.999,.999,.0001],
        source_visual_meshes_changed=False,noslip_iterations=0,impratio=10,sleep_enabled=False,
        selected_tip_thickness_m=grasp['edge_jaw_thickness_m'],selected_stem_thickness_m=grasp['edge_jaw_thickness_m'],shield_grasp_height_from_center_m=grasp['shield_grip_local_m'][2],shield_clamp_force_N=forces['shield_grip_N'],
        cover_clamp_force_N=forces['cover_grip_N'],
        shield_fixture_pin_radius_m=geometry['shield_alignment_pin_radius_m'],shield_fixture_nominal_radial_clearance_m=geometry['shield_alignment_radial_clearance_m'],
        reason='Implicit elastic membrane replaces a constrained-edge trial with a 44% transient strain. Exact cuboid meshes preserve tube geometry while using convex-element collision detection. Film/solid intersections beyond 0.1 mm are rejected independently.',
        timestep_s=.001,maximum_ring_envelope_error_m=max(r['maximum_outward_envelope_error_m'] for r in rings))
