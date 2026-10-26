"""Inspect actual exported BT5M solids and conserved blade geometry."""
import itertools
import json
from pathlib import Path
import numpy as np
import trimesh
from shapely.geometry import MultiPoint,Point
from geometry_tools import HERE,ROOT,sha,write_json
from check_weather_assets import load_parts,overlap


def build():
    record=json.loads((HERE/'tape_measure_assets.json').read_text());checks=[];models={}
    def check(name,passed,**detail):checks.append(dict(name=name,passed=bool(passed),**detail))
    for ref in record['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    volumes=[]
    for item in record['items']:
        ident=item['id'];parts=load_parts(item['geometry']);models[ident]=parts
        solids={n:m for n,m in parts.items() if not n.endswith('_text')}
        check('part_manifest_'+ident,set(parts)=={p['id'] for p in item['geometry']['part_records']})
        for n,m in solids.items():check('connected_volume_'+ident+'/'+n,m.is_volume and len(m.split())==1,volume_m3=float(m.volume))
        hits=[];pairs=0
        for (a,x),(b,y) in itertools.combinations(solids.items(),2):
            if np.any(np.minimum(x.bounds[1],y.bounds[1])-np.maximum(x.bounds[0],y.bounds[0])<=1e-8):continue
            pairs+=1
            if not x.is_volume or not y.is_volume:hits.append(dict(parts=[a,b],reason='nonvolume'));continue
            v=overlap(x,y)
            if not np.isfinite(v) or abs(v)>.01:hits.append(dict(parts=[a,b],intersection_mm3=v))
        check('distinct_material_volumes_'+ident,not hits,narrow_phase_pairs=pairs,intersections=hits)
        p=np.array(item['blade']['neutral_line_points_m']);length=np.linalg.norm(np.diff(p,axis=0),axis=1).sum()
        check('one_conserved_strip_'+ident,abs(length-5.30)<1e-7 and np.allclose(p[-1],[item['exposed_neutral_length_m'],0,.014],atol=1e-9),actual_neutral_length_m=float(length))
        check('tail_remains_inside_at_full_capacity_'+ident,item['blade']['winding_angle_rad']>2*np.pi)
        blade=parts['continuous_steel_blade'];volumes.append(blade.volume)
        nominal=5.30*.019*.00012-3*np.pi*.00108**2*.00012
        check('blade_stock_volume_consistency_'+ident,abs(blade.volume/nominal-1)<.01,
            actual_m3=float(blade.volume),nominal_before_reconstruction_m3=nominal,tolerance_fraction=.01,
            scope='Approximate volume under inferred cross curvature, thickness and holes; not a measured mass.')
        # Conservative polygon sag margin between neighbouring winding turns.
        radius=item['blade']['outer_radius_m'];k=.00020/(2*np.pi)
        pitch_normal=.00020*.010/np.sqrt(.010**2+k**2);sag=radius*(1-np.cos(.10/2))
        check('winding_turn_thickness_clearance_'+ident,pitch_normal-2*sag-.00012>0,
            conservative_clearance_m=float(pitch_normal-2*sag-.00012),scope='Archimedean winding reference only; lead-in and shell are separately inspected.')
        e=item['exposed_neutral_length_m']
        check('three_rivets_inside_real_blade_holes_'+ident,not blade.contains([[e-d,0,.014] for d in [.006,.014,.022]]).any())
        label_names=[n for n in parts if n.startswith('blade_graduations_')]
        check('scale_visible_faces_'+ident,all(np.all(parts[n].face_normals[:,2]>.9) for n in label_names))
        label_centres=np.vstack([parts[n].triangles_center for n in label_names])
        locations,rays,_=blade.ray.intersects_location(label_centres+[0,0,.003],np.tile([0,0,-1],(len(label_centres),1)))
        surface=np.full(len(label_centres),-np.inf);np.maximum.at(surface,rays,locations[:,2])
        distances=label_centres[:,2]-surface
        check('graduations_above_actual_blade_facets_'+ident,np.isfinite(distances).all() and np.all((distances>1e-6)&(distances<1e-5)),
            minimum_gap_m=float(np.min(distances)),maximum_gap_m=float(np.max(distances)))
        check('negative_buried_graduation_surface_rejected_'+ident,np.any(distances-.000008<0))
        # Each tile is mapped on the exposed blade and extends no farther than
        # its hook datum. Original text is not permitted to obscure a wire or
        # invent scene markers elsewhere.
        check('graduations_follow_exposed_blade_'+ident,all(parts[n].bounds[0,0]>=-1e-7 and parts[n].bounds[1,0]<=e+1e-7 for n in label_names))
        scale_rows=[]
        for n in label_names:
            label=parts[n];xmin,xmax=label.bounds[:,0];span=xmax-xmin
            texture=np.asarray(label.visual.material.baseColorTexture.convert('RGBA'))
            ticks=np.flatnonzero(texture[35,:,3]>0)
            distances_mm=(e-(xmin+ticks/(texture.shape[1]-1)*span))*1000
            error=np.abs(distances_mm-np.round(distances_mm/10)*10)
            uv_error=np.max(np.abs(label.visual.uv[:,0]-(label.vertices[:,0]-xmin)/span))
            scale_rows.append(dict(part=n,major_tick_count=len(ticks),max_centimetre_alignment_error_mm=float(error.max()),uv_error=float(uv_error)))
        check('actual_texture_centimetre_spacing_'+ident,all(r['major_tick_count']>0 and r['max_centimetre_alignment_error_mm']<.15 and r['uv_error']<1e-6 for r in scale_rows),tiles=scale_rows)
    check('same_strip_mass_across_inspection_shapes',max(volumes)/min(volumes)<1.01,actual_volumes_m3=list(map(float,volumes)))
    parts=models['retracted'];case=trimesh.util.concatenate([m for n,m in parts.items() if n in ['front_abs_shell','rear_abs_shell','front_rubber_impact_domain','rear_rubber_impact_domain','thumb_brake']])
    check('source_body_envelope',np.allclose(case.extents,[.087,.030,.078],atol=.0001,rtol=0),actual_m=case.extents.tolist(),reconstruction_tolerance_m=.0001)
    check('clip_is_additional_protrusion',parts['belt_clip_and_release_tongue'].bounds[1,2]>.078 and parts['belt_clip_and_release_tongue'].bounds[1,1]>.015)
    # Actual bottom support contains the mass centre under explicit material
    # density assumptions. This screen is not settling or a spring-lock test.
    solids={n:m for n,m in parts.items() if not n.endswith('_text')}
    def density(n):return 7850. if 'steel' in n or 'screw' in n or 'axle' in n or 'rivet' in n else 1100.
    mass=np.array([m.volume*density(n) for n,m in solids.items()]);com=np.sum(mass[:,None]*np.array([m.center_mass for m in solids.values()]),axis=0)/mass.sum()
    whole=trimesh.util.concatenate(list(solids.values()));z=whole.bounds[0,2];contact=whole.vertices[whole.vertices[:,2]<z+2e-7]
    polygon=MultiPoint(contact[:,:2]).convex_hull
    supported=polygon.contains(Point(com[:2]));margin=polygon.boundary.distance(Point(com[:2]))
    check('actual_base_support',abs(z)<1e-7 and supported and margin>.001,inferred_com_m=com.tolist(),margin_m=float(margin))
    check('negative_distant_com_rejected',not polygon.contains(Point([.3,0])))
    check('no_unearned_qualification',record['owner_acceptance'] is None and not any(record[k] for k in ['initial_stock_credit','measurement_qualified','robot_use_qualified']))
    failed=[c['name'] for c in checks if not c['passed']]
    refs=[Path(__file__),HERE/'tape_measure_assets.json',HERE/'check_weather_assets.py']
    result=dict(schema_version=1,passed=not failed,failed=failed,checks=checks,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        resting_reference=dict(to_support_plane=np.eye(4).tolist(),estimated_mass_kg=float(mass.sum()),support_margin_m=float(margin),
            mass_scope='Represented geometry and inferred densities only; unmodeled internal spring/reel mass prevents using this as qualified whole-tool inertia.'),
        scope='Three static source-constrained shapes and finite strip stock. No retraction, spring, brake, lost-motion calibration, measurement or robot operation.',
        owner_acceptance=None,robot_use_qualified=False)
    write_json(HERE/'tape_measure_checks.json',result)
    print(json.dumps(dict(passed=not failed,checks=len(checks),failed=failed,intersections=[c for c in checks if c.get('intersections')]),ensure_ascii=False))
    if failed:raise AssertionError(failed)


if __name__=='__main__':build()
