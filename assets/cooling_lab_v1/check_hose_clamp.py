"""Actual clamp solids, selected neutral length and original RS3/mast fit."""
import itertools
import json
from pathlib import Path
import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial
from scipy.spatial import cKDTree,ConvexHull
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from check_weather_assets import load_parts,overlap


def build():
    record=json.loads((HERE/'hose_clamp_assets.json').read_text());checks=[];models={}
    weather=json.loads((HERE/'weather_assets.json').read_text());rs3=next(i for i in weather['items'] if i['id']=='onset_rs3')
    source=load_parts(rs3['geometry']);context={}
    for name,m in source.items():
        if name in ['mast_band_candidate','band_worm_housing','band_screw'] or name.startswith(('loose_tie_','optional_wall_screw_')):continue
        m=m.copy();m.apply_translation(record['installed_context']['rs3_origin_m']);context['rs3_'+name]=m
    # A short local segment exposes the interface from above; the independent
    # round-obstacle test below still uses a 140 mm solid axial envelope.
    mast=trimesh.creation.annulus(.0193,.0205,.035,sections=160)
    # Linear colour bytes for a selected metallic display material. Source
    # glTF parts are already linear and receive no second gamma conversion.
    mast.visual=trimesh.visual.TextureVisuals(material=PBRMaterial(baseColorFactor=[100,110,118,255],metallicFactor=.75,roughnessFactor=.5))
    context['isolated_mast_segment']=mast
    def check(name,passed,**details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        if not passed:raise AssertionError(name+' '+str(details))
    for ref in record['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    check('original_rs3_body_part_count',len(context)==25)
    for item in record['items']:
        identity=item['id'];parts=load_parts(item['geometry']);models[identity]=parts
        check('three_physical_parts_'+identity,len(parts)==3)
        for n,m in parts.items():check('closed_connected_'+identity+'/'+n,m.is_volume and len(m.split())==1)
        hits=[]
        for (n,a),(q,b) in itertools.combinations(parts.items(),2):
            volume=overlap(a,b)
            if not np.isfinite(volume) or volume>.001:hits.append(dict(parts=[n,q],volume_mm3=volume))
        check('internal_clearances_'+identity,not hits,intersections=hits)
        hood=parts['asymmetric_housing'];screw=parts['slotted_hex_worm_screw'];vertices=np.vstack([hood.vertices,screw.vertices]);dimensions=np.ptp(vertices,axis=0)
        check('source_rigid_closure_envelope_'+identity,np.allclose(dimensions,[.026,.011,.013],atol=3e-5,rtol=0),actual_xyz_m=dimensions.tolist())
        route=item['band_route'];translation=np.array(route['housing_translation_m']);band=parts['continuous_stamped_band']
        p=np.array(route['neutral_line_m']);length=float(np.linalg.norm(np.diff(p,axis=0),axis=1).sum())
        check('selected_neutral_length_'+identity,abs(length-.164)<1e-8,actual_m=length)
        check('recorded_band_volume_'+identity,abs(band.volume-item['band_volume_m3'])/item['band_volume_m3']<1e-5)
        samples=np.linspace(0,len(p)-1,201).astype(int)[1:-1]
        check('recorded_neutral_line_inside_actual_band_'+identity,np.all(band.contains(np.column_stack([p[samples],np.zeros(len(samples))]))))
        arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
        pairs=cKDTree(p).query_pairs(.003,output_type='ndarray');pairs=pairs[np.abs(arc[pairs[:,0]]-arc[pairs[:,1]])>.004]
        minimum=float(np.min(np.linalg.norm(p[pairs[:,0]]-p[pairs[:,1]],axis=1)))
        step=float(np.max(np.linalg.norm(np.diff(p,axis=0),axis=1)))
        # Width is axial Z; distinct strip runs must remain apart in XY.
        check('nonlocal_strip_clearance_'+identity,minimum-step-.00065>0,minimum_sample_distance_m=minimum,max_step_m=step,conservative_gap_m=minimum-step-.00065)
        probe=trimesh.creation.cylinder(.025 if identity=='loose' else .0205,.14,sections=192)
        conflicts=[dict(part=n,volume_mm3=overlap(m,probe)) for n,m in parts.items()]
        check('nominal_round_obstacle_clear_'+identity,all(r['volume_mm3']<.001 for r in conflicts),intersections=conflicts)
        # The driver entry is an isolated blade envelope, not a qualified tool.
        blade=trimesh.creation.box([.001,.006,.0008]);blade.apply_translation(translation+[-.0146,-.0045,0])
        check('actual_slotted_head_recess_'+identity,overlap(blade,screw)<.001)
        wide=trimesh.creation.box([.001,.006,.0012]);wide.apply_translation(translation+[-.0146,-.0045,0])
        check('negative_oversize_blade_rejected_'+identity,overlap(wide,screw)>.01)
        front=screw.vertices[np.abs(screw.vertices[:,0]+.015)<1e-7,1:]-np.array([translation[1]-.0045,0])
        hull=ConvexHull(front);flats=-hull.equations[:,2]
        check('source_SW7_head_'+identity,np.allclose(flats,.0035,atol=3e-6,rtol=0),half_across_flats_m=flats.tolist())
    installed=models['installed'];hits=[]
    for n,m in installed.items():
        for q,b in context.items():
            volume=overlap(m,b)
            if not np.isfinite(volume) or volume>.001:hits.append(dict(parts=[n,q],volume_mm3=volume))
    check('actual_exported_RS3_and_mast_fit',not hits,intersections=hits)
    previous=source['mast_band_candidate'].copy();previous.apply_translation([-.110,.030,-.004]);bad=overlap(previous,context['rs3_inclined_mounting_bracket'])
    check('negative_existing_round_kit_band_rejected',bad>.01,observed_intersection_mm3=bad,
        scope='Actual retained generic kit band placed at the selected mast axis; it cannot wrap the additional bracket thickness.')
    volume=[models[s]['continuous_stamped_band'].volume for s in ['loose','installed']];relative=abs(volume[1]-volume[0])/volume[0]
    check('static_state_band_volume_discrepancy_recorded',relative<.001,relative_volume_difference=relative,
        scope='Small geometric discrepancy is retained, not an incompressibility or material-law qualification.')
    check('no_unearned_qualification',not any(record[k] for k in ['staged_in_lab','initial_stock_credit','installation_qualified','worm_drive_qualified','robot_use_qualified','owner_acceptance']))
    # Export exactly the checked context. This is an alternative inspection
    # fixture, with the source RS3 shapes and without its old loose kit parts.
    g=Geometry()
    for n,m in {**installed,**context}.items():
        g.scene.add_geometry(m.copy(),node_name=n,geom_name=n);g.parts.append(dict(id=n,role='isolated_static_fit_reference',bounds_m=m.bounds.tolist()))
    # Imported glTF materials already contain linear colour factors. Preserve
    # them; the authored-asset sRGB exporter would convert them a second time.
    fixture=g.export('norma_torro_rs3_fit')
    refs=[Path(__file__),HERE/'hose_clamp_assets.json',HERE/'weather_assets.json',HERE/'check_weather_assets.py',HERE/'geometry_tools.py']
    report=dict(passed=True,checks=checks,fit_geometry=fixture,inspection_mast_segment_length_m=.035,source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        installation_qualified=False,worm_drive_qualified=False,robot_use_qualified=False,owner_acceptance=None,
        limits=['Only static selected shapes are tested. Screw profile, material deformation, factory retention, clamp loads and complete assembly paths remain unqualified.',
            'The actual pre-existing RS3 body is reused. Its two declared rod/nut thread-envelope intersections remain as recorded in weather_checks.json.',
            'The blade gauge is not a sourced complete screwdriver or a hand/tool accessibility result.'])
    write_json(HERE/'hose_clamp_checks.json',report);print(json.dumps(dict(passed=True,checks=len(checks),fixture_parts=fixture['parts'])))


if __name__=='__main__':build()
