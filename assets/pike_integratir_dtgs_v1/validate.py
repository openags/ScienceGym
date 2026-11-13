"""Check the exported legacy IntegratIR's source facts and open interfaces."""
import json,hashlib
from pathlib import Path
import numpy as np,trimesh
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    scene=trimesh.load(HERE/'geometry/pike_integratir_dtgs.glb',force='scene');meshes={}
    for name in scene.graph.nodes_geometry:
        transform,key=scene.graph[name];m=scene.geometry[key].copy();m.apply_transform(transform)
        m.vertices=np.asarray(m.vertices)@np.array([[1,0,0],[0,0,1],[0,-1,0]])
        m.merge_vertices(merge_norm=True,merge_tex=True);meshes[name]=m
    card=json.loads((HERE/'interfaces.json').read_text());parts=json.loads((HERE/'parts.json').read_text());receipt=json.loads((HERE/'build_receipt.json').read_text());checks=[]
    def check(name,passed,**details):checks.append(dict(name=name,passed=bool(passed),**details))
    check('all_named_parts_exported',set(meshes)=={p['id'] for p in parts},parts=len(parts))
    relevant=['gold_sphere_shell','top_sample_panel','purge_collet','reference_protective_cap','detector_connector_shell']
    check('interface_meshes_closed_and_oriented',all(meshes[n].is_watertight and meshes[n].is_winding_consistent and meshes[n].volume>0 for n in relevant),
          meshes={n:dict(watertight=meshes[n].is_watertight,positive_volume=bool(meshes[n].volume>0)) for n in relevant})
    base=meshes['module_base'];check('selected_footprint_explicitly_inferred',np.max(abs(base.extents[:2]-card['selected_main_envelope_m'][:2]))<1e-6 and card['envelope_is_inferred'])
    sphere=meshes['gold_sphere_shell'];center=np.array([.040,-.010,.0619]);radii=np.linalg.norm(sphere.vertices-center,axis=1);inner=radii[radii<.03815]
    check('source_three_inch_sphere_cavity',len(inner)>100 and np.max(abs(inner-.0381))<3e-5,inner_diameter_m=float(np.median(inner)*2),source_diameter_m=.0762)
    directions=np.array([[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,-1]])
    check('sphere_is_hollow',not sphere.contains(center+directions*.035).any() and sphere.contains(center+directions*.0387).all())
    port=np.array([.040,-.010,.101]);angles=np.arange(96)*2*np.pi/96
    def circle(radius,z):return np.c_[port[0]+radius*np.cos(angles),port[1]+radius*np.sin(angles),np.full(96,z)]
    top=meshes['top_sample_panel']
    check('source_eighteen_mm_sample_port',not top.contains(circle(.0089,.101)).any() and top.contains(circle(.0091,.101)).all(),source_diameter_m=.018)
    check('sample_port_opens_into_sphere',not sphere.contains(circle(.0088,.098)).any() and not top.contains([port]).any())
    detector=meshes['detector_enclosure'];check('legacy_dtgs_enclosure_separate_from_sample_port',detector.bounds[0,2]>.1019 and not detector.contains([port+[0,0,.020]]).any())
    check('no_mct_dewar_or_later_variant_parts',not any('dewar' in n.lower() or 'specular_exclusion' in n for n in meshes))
    knob=meshes['sample_reference_knob'];check('selector_exposed_on_front',knob.bounds[1,1]<meshes['front_panel'].bounds[0,1])
    purge=meshes['purge_collet'];check('purge_bore_is_open',not purge.contains([[.030,-.106,.018],[.030,-.103,.018]]).any())
    check('reference_and_protective_cap_separate',set(card['reference_parts']).isdisjoint(card['cap_parts']) and len(card['reference_parts'])==3 and len(card['cap_parts'])==1)
    cap=meshes['reference_protective_cap'];check('cap_has_open_recess_and_closed_floor',not cap.contains([[.210,-.060,.020]]).any() and cap.contains([[.210,-.060,.005]]).all())
    check('optional_window_is_a_separate_part',set(card['optional_plate_parts']).isdisjoint(card['module_parts']) and len(card['optional_plate_parts'])==2)
    connector=next(i for i in card['interfaces'] if i['id']=='detector')
    check('unknown_connector_pinout_not_asserted',connector['contact_count'] is None and connector['pinout'] is None and not connector['mating_qualified'])
    check('geometry_inference_record_per_part',all(p.get('geometry_basis') for p in parts) and not card['manufacturer_CAD'] and not card['contact_qualified'])
    check('builder_and_sources_pinned',receipt['builder_sha256']==sha(HERE/'build.py') and receipt['sources_sha256']==sha(HERE/'sources.json'))
    check('exported_artifacts_pinned',all(sha(HERE/n)==digest for n,digest in receipt['artifacts_sha256'].items()))
    report=dict(passed=all(c['passed'] for c in checks),checks=checks,glb_sha256=sha(HERE/'geometry/pike_integratir_dtgs.glb'),validator_sha256=sha(Path(__file__)),
                manufacturer_CAD=False,contact_qualified=False,scope='Static legacy DTGS reconstruction: source sphere/port dimensions, distinct sample/reference/cover parts and open interfaces. No robot, optical, detector-pinout or electronic qualification.')
    (HERE/'geometry_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],checks=len(checks),failed=[c for c in checks if not c['passed']]),indent=2));return report['passed']


if __name__=='__main__':raise SystemExit(0 if main() else 1)
