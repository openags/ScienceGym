"""Actual-stock dimensional checks, foil consistency and rejected old inputs."""
import copy
import json
from pathlib import Path
import numpy as np
import trimesh
from shapely.geometry import Polygon,box,MultiPoint
from shapely.affinity import translate
from build_stock_cutplan import load_parts
from geometry_tools import HERE,ROOT,sha,write_json,imported_scene


def sheet_errors(row,mesh):
    errors=[];size=mesh.extents;stock=box(0,0,*size[:2]);polygons=[]
    for cut in row['cuts']:
        p=Polygon(cut['outline_m']);buffered=p.buffer(row['edge_and_cut_clearance_m'])
        if not stock.buffer(1e-8).covers(buffered):errors.append(cut['id']+':outside_stock')
        if abs(size[2]-cut['required_thickness_m'])>1e-7:errors.append(cut['id']+':wrong_gauge')
        if not p.is_valid or p.area<=0:errors.append(cut['id']+':invalid_outline')
        for other,name in polygons:
            if buffered.intersection(other).area>1e-10:errors.append(cut['id']+':overlap:'+name)
        polygons.append((buffered,cut['id']))
    return errors


def build():
    plan=json.loads((HERE/'stock_cutplan.json').read_text());supplies=json.loads((HERE/'supplies.json').read_text())
    apparatus=json.loads((HERE/'apparatus_stock_reconciliation.json').read_text());checks=[];sheet_results=[]
    def check(name,value,**extra):
        checks.append(dict(name=name,passed=bool(value),**extra))
        if not value:raise AssertionError(name+' '+str(extra))
    for artifact in [plan,apparatus]:
        for s in artifact['source_artifacts']:check('source_'+s['path'],sha(ROOT/s['path'])==s['sha256'])
    by_asset={i['id']:i for i in supplies['items']};stock={a:load_parts(i['geometry']['path']) for a,i in by_asset.items()}
    outputs={i['id']:load_parts(i['geometry']['path']) for i in apparatus['items']}
    seen=set()
    for row in plan['sheets']:
        key=(row['asset_id'],row['part']);check('unique_stock_'+row['id'],key not in seen);seen.add(key)
        mesh=stock[key[0]][key[1]];errors=sheet_errors(row,mesh)
        check('cut_envelopes_'+row['id'],not errors,errors=errors)
        check('measured_stock_'+row['id'],np.allclose(mesh.extents,[*row['size_m'],row['thickness_m']],atol=1e-8))
        for cut in row['cuts']:
            if 'output_template' in cut:
                ref=cut['output_template'];m=outputs[ref['asset_id']][ref['part']]
                measured=MultiPoint(m.vertices[:,:2]).convex_hull;p=Polygon(cut['outline_m'])
                measured=translate(measured,p.bounds[0]-measured.bounds[0],p.bounds[1]-measured.bounds[1])
                check('output_shape_'+cut['id'],measured.hausdorff_distance(p)<1e-8 and abs(m.extents[2]-cut['required_thickness_m'])<1e-8)
            if 'wrapped_surface' in cut:
                f=cut['wrapped_surface'];bounds=Polygon(cut['outline_m']).bounds
                check('unrolled_surface_'+cut['id'],bounds[2]-bounds[0]>np.pi*f['diameter_m']+f['lap_m'] and bounds[3]-bounds[1]>=f['height_m'])
        # Goodfellow's listed -1% in-plane tolerance still fits this selected
        # cut reserve. This is not optical or tolerance acceptance of the film.
        if row['asset_id']=='mylar_stock':
            guaranteed=box(0,0,mesh.extents[0]*.99,mesh.extents[1]*.99)
            check('listed_length_lower_bound_'+row['id'],all(guaranteed.buffer(1e-8).covers(Polygon(c['outline_m']).buffer(.001)) for c in row['cuts']))
        sheet_results.append(dict(id=row['id'],cuts=len(row['cuts']),nominal_geometry_clear=True))
    for row in plan['tubes']:
        m=stock[row['asset_id']][row['part']];center=m.bounds.mean(axis=0)
        check('raw_length_'+row['id'],m.extents[2]>row['finished_length_m']+row['cut_allowance_m'])
        radial=np.linalg.norm(m.vertices[:,:2]-center[:2],axis=1)
        check('real_hollow_tube_'+row['id'],abs(radial.min()*2-row['inner_diameter_m'])<1e-7 and abs(radial.max()*2-row['outer_diameter_m'])<1e-7 and not m.contains([center]).any())
    for item in apparatus['items']:
        identity=item['id'];new=outputs[identity];prefix={'cooler_white':'COOLER_WHITE__','cooler_black':'COOLER_BLACK__','cooler_fixed':'COOLER_FIXED_BAND__'}[identity]
        original=imported_scene('assets/cooling_scene_assets_v2/geometry/cooling_pilot.glb',prefix=prefix)
        changed={c['part'] for c in item['changes']}
        # GLB stores POSITION as float32; compare the exact serialized values,
        # not the float64 transforms used by the importer (up to 15 nm apart).
        check('only_selected_foil_changed_'+identity,set(new)==set(original.geometry) and all(np.array_equal(new[n].vertices,original.geometry[n].vertices.astype(np.float32)) and np.array_equal(new[n].faces,original.geometry[n].faces) for n in new if n not in changed))
        base=new[prefix+'acrylic_base'];foil=new[prefix+'mylar_base']
        check('full_base_coverage_'+identity,np.allclose(foil.bounds[:,:2],base.bounds[:,:2],atol=1e-7) and abs(foil.bounds[0,2]-base.bounds[1,2])<1e-8)
        check('base_foil_matches_stock_'+identity,abs(foil.extents[2]-.000012)<1e-8)
        for c in item['changes']:
            if 'substrate' not in c:continue
            m=new[c['part']];under=new[c['substrate']];center=under.bounds.mean(axis=0);radial=np.linalg.norm(m.vertices[:,:2]-center[:2],axis=1)
            # The fixed configuration is 1.65 m from the legacy origin, so its
            # float32 positions quantize more coarsely than the paired devices.
            quantization=float(np.spacing(np.float32(np.abs(m.vertices).max())))*2
            base_radius=c['radius_m']+c['mesh_faceting_and_quantization_allowance_m']
            check('wrap_gauge_and_lap_'+c['part'],m.is_watertight and radial.min()>=base_radius-quantization and abs(radial.max()-base_radius-.000024)<quantization and abs(m.extents[2]-under.extents[2])<quantization,position_quantization_m=quantization)
            manager=trimesh.collision.CollisionManager();manager.add_object('substrate',under)
            check('foil_no_substrate_triangle_intersections_'+c['part'],not manager.in_collision_single(m))
        check('negative_legacy_thick_foil_'+identity,original.geometry[prefix+'mylar_base'].extents[2]>.0001)
    rejected=json.loads((HERE/'stock_rejected.json').read_text());check('rejected_geometry_pinned',sha(ROOT/rejected['geometry']['path'])==rejected['geometry']['sha256'])
    old=load_parts(rejected['geometry']['path']);base=outputs['cooler_white']['COOLER_WHITE__acrylic_base']
    acrylic=old['acrylic_acrylic_stock_sheet'];mylar=old['mylar_raw_film_1']
    check('negative_previous_acrylic_cannot_make_base',acrylic.extents[2]<base.extents[2] and np.prod(acrylic.extents[:2])<np.prod(base.extents[:2]))
    check('negative_previous_mylar_area_too_small',np.prod(mylar.extents[:2])<np.prod(base.extents[:2]))
    ldpe=[m for n,m in old.items() if n.startswith('ldpe_')]
    check('negative_previous_ldpe_cannot_supply_pair',len(ldpe)==2 and all(np.linalg.norm(m.extents[:2]-.127)<.127 for m in ldpe) and len(ldpe)<4)
    bad=copy.deepcopy(plan['sheets'][0]);bad['cuts'][1]['outline_m']=bad['cuts'][0]['outline_m']
    check('negative_overlapping_cut_reservations',any(':overlap:' in e for e in sheet_errors(bad,stock[bad['asset_id']][bad['part']])))
    foil_bad=json.loads((HERE/'foil_mesh_rejected.json').read_text());check('rejected_foil_geometry_pinned',sha(ROOT/foil_bad['geometry']['path'])==foil_bad['geometry']['sha256'])
    parts=load_parts(foil_bad['geometry']['path']);manager=trimesh.collision.CollisionManager();manager.add_object('substrate',parts[foil_bad['expected_substrate']])
    collision,contacts=manager.in_collision_single(parts[foil_bad['expected_foil']],return_data=True)
    check('negative_previous_foil_intersects_substrate',collision and max(c.depth for c in contacts)>.000001)
    out=dict(schema_version=1,passed=all(c['passed'] for c in checks),checks=checks,sheets=sheet_results,
        scope='Stock identities, nominal cut envelopes and selected foil geometry; not fabrication, optical, load or campaign qualification',
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [Path(__file__),HERE/'stock_cutplan.json',HERE/'supplies.json',HERE/'apparatus_stock_reconciliation.json',HERE/'stock_rejected.json',HERE/'foil_mesh_rejected.json']],
        owner_acceptance=None,manufacturing_qualified=False)
    write_json(HERE/'stock_cut_checks.json',out);print(json.dumps(dict(checks=len(checks),passed=out['passed'],sheets=len(sheet_results))))


if __name__=='__main__':build()
