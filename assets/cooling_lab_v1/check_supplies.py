"""Independent physical-dimension and usable-shape checks for staged supplies."""
import json
import struct
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE,ROOT,sha,write_json


def validate():
    report=json.loads((HERE/'supplies.json').read_text());sources=json.loads((HERE/'supply_sources.json').read_text());checks=[];scenes={}
    def check(name,passed,**data):
        checks.append(dict(name=name,passed=bool(passed),**data))
        if not passed:raise AssertionError(name+' '+str(data))
    for ref in report['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    for item in report['items']:
        g=item['geometry'];check('identity_'+item['id'],sha(ROOT/g['path'])==g['sha256'])
        raw=(ROOT/g['path']).read_bytes();length=struct.unpack('<I',raw[12:16])[0];tree=json.loads(raw[20:20+length])
        check('explicit_pbr_materials_'+item['id'],all('material' in p for m in tree['meshes'] for p in m['primitives']) and bool(tree.get('materials')))
        check('explicit_surface_normals_'+item['id'],all('NORMAL' in p['attributes'] for m in tree['meshes'] for p in m['primitives']))
        if item['id']=='rubbermaid_1997206':
            palette=np.array([45,48,51])/255;linear=((palette+.055)/1.055)**2.4
            factors=[m.get('pbrMetallicRoughness',{}).get('baseColorFactor',[1,1,1,1])[:3] for m in tree['materials']]
            check('cart_dark_plastic_linear_color',any(np.allclose(c,linear,atol=1e-7) for c in factors))
        scene=trimesh.load(ROOT/g['path'],force='scene');scenes[item['id']]=scene
        check('bounded_'+item['id'],np.isfinite(scene.bounds).all() and np.allclose(scene.bounds,g['bounds_m'],atol=1e-6))
        for node in scene.graph.nodes_geometry:
            t,k=scene.graph[node];m=scene.geometry[k]
            if 'text' not in node and 'lot_card' not in node and 'waste_role' not in node:
                welded=m.copy();welded.merge_vertices(digits_vertex=8)
                check('closed_'+item['id']+'_'+node,welded.is_watertight)
    def mesh(item,node):
        s=scenes[item];t,k=s.graph[node];m=s.geometry[k].copy();m.merge_vertices(digits_vertex=8);m.apply_transform(t);return m
    facts={s['id']:s.get('facts',{}) for s in sources['items']}
    check('stripper_catalog_envelope',np.allclose(scenes['jonard_st450'].extents,facts['jonard_st450']['dimensions_m'],atol=.00005),measured_m=scenes['jonard_st450'].extents.tolist())
    t=scenes['idealtek_aa_sa_t6'].extents
    check('tweezer_catalog_envelope',np.allclose(t,[.13,.0125,.0115],atol=1e-6),measured_m=t.tolist())
    check('driver_overall_length',abs(scenes['wiha_26015'].extents[0]-.120)<1e-6)
    probe=mesh('omega_ambient_rtd','vented_air_sheath')
    check('ambient_probe_source_dimensions',np.allclose(probe.extents,[.1524,.00635,.00635],atol=1e-6))
    # A solid stick mislabeled as an air probe must fail: source-inspired vents
    # actually connect outside to the hollow bore.
    check('ambient_probe_hollow_and_vented',not probe.contains([[.009,0,0],[.009,.00295,0]]).any())
    cable=next(i['cable'] for i in report['items'] if i['id']=='omega_ambient_rtd')
    measured=np.linalg.norm(np.diff(cable['rest_points_m'],axis=0),axis=1).sum()+cable['breakout_length_m']
    check('ambient_six_foot_lead',abs(measured-1.8288)<1e-6,measured_m=float(measured))
    cup=mesh('buerkle_7102_2000','open_pp_vessel')
    check('jug_height',abs(cup.extents[2]-.213)<1e-6)
    check('jug_mouth_is_open',not cup.contains([[0,0,.1],[0,0,.212]]).any())
    check('jug_bottom_exists',cup.contains([[0,0,.001]]).all())
    # Independent axial ray sees the base at 3 mm and no lid at the mouth.
    locations,_,_=cup.ray.intersects_location([[0,0,.25]],[[0,0,-1]])
    check('jug_open_ray',len(locations)==2 and np.max(locations[:,2])<.00301)
    kit=next(i for i in report['items'] if i['id']=='omega_smpw_cc_kit');contents=kit['contents']
    check('eight_independent_connector_pairs',len(contents)==16 and len({c['id'] for c in contents})==16 and sum(c['model'].endswith('-M') for c in contents)==8)
    # 1.2 mm tray wall; bottom inside is narrower than the top rim. All staged
    # hardware must lie inside the smaller bottom footprint, not merely the AABB.
    s=scenes['omega_smpw_cc_kit'];hardware=[]
    for node in s.graph.nodes_geometry:
        if node.startswith('ordinary_tray_'):continue
        m=mesh('omega_smpw_cc_kit',node);hardware.extend(m.vertices)
    p=np.array(hardware)
    check('connector_contents_inside_tray',p[:,0].min()>-.1378 and p[:,0].max()<.1378 and p[:,1].min()>-.0878 and p[:,1].max()<.0878 and p[:,2].min()>=.001199 and p[:,2].max()<.050,bounds_m=[p.min(axis=0).tolist(),p.max(axis=0).tolist()])
    for item,count,thickness in [('nano_pe_stock',4,.000016),('ldpe_stock',2,.00005),('mylar_stock',3,.000012)]:
        nodes=[n for n in scenes[item].graph.nodes_geometry if n.startswith('raw_film_')]
        check('film_quantity_'+item,len(nodes)==count)
        check('actual_film_thickness_'+item,all(abs(mesh(item,n).extents[2]-thickness)<1e-8 for n in nodes),thickness_m=thickness)
    block=mesh('calibration_copper_stock','unmachined_copper_block')
    check('raw_block_not_pre_drilled',block.contains([[0,0,.015],[.01,0,.015],[-.01,0,.015]]).all())
    check('block_selected_dimensions',np.allclose(block.extents,[.06,.05,.03],atol=1e-6))
    check('cart_catalog_envelope',np.allclose(scenes['rubbermaid_1997206'].extents,facts['rubbermaid_1997206']['overall_dimensions_m'],atol=.0001),measured_m=scenes['rubbermaid_1997206'].extents.tolist())
    cart=scenes['rubbermaid_1997206']
    wheel_nodes=[n for n in cart.graph.nodes_geometry if n.startswith('rubber_wheel_')]
    check('four_grounded_five_inch_wheels',len(wheel_nodes)==4 and all(abs(mesh('rubbermaid_1997206',n).bounds[0,2])<1e-7 and abs(mesh('rubbermaid_1997206',n).extents[2]-.127)<1e-7 for n in wheel_nodes))
    check('cart_shelves_open',not mesh('rubbermaid_1997206','lower_shelf').contains([[0,0,.22]]).any() and not mesh('rubbermaid_1997206','upper_shelf').contains([[0,0,.81]]).any())
    check('waste_body_not_solid',not mesh('justrite_09100','steel_body').contains([[0,0,.20]]).any())
    check('waste_height',abs(scenes['justrite_09100'].extents[2]-.403)<1e-6)
    out=dict(schema_version=1,checks_passed=all(c['passed'] for c in checks),checks=checks,supplies_sha256=sha(HERE/'supplies.json'),validator_sha256=sha(__file__),asset_acceptance=False,
        limitations=['Catalogue shape checks do not qualify handling, deformation or electrical functions','Staged quantity is a selected starting allocation, not full campaign coverage','Commercial models contain explicitly recorded local inferences; source CAD was not obtained'])
    write_json(HERE/'supply_checks.json',out);print(json.dumps(dict(checks=len(checks),passed=out['checks_passed'])))


if __name__=='__main__':validate()
