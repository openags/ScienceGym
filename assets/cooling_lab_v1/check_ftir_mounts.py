"""Independent geometric mounting audit, including expected failed candidates."""
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE, ROOT, sha, write_json, imported_scene


def meshes(path,z_up=True):
    scene=imported_scene(path,z_up=z_up)
    return {n:scene.geometry[k].copy() for n in scene.graph.nodes_geometry for _,k in [scene.graph[n]]}


def contacts(a,b,tolerance=.00005):
    ma=trimesh.collision.CollisionManager();mb=trimesh.collision.CollisionManager()
    for n,m in a.items():ma.add_object(n,m)
    for n,m in b.items():mb.add_object(n,m)
    _,records=ma.in_collision_other(mb,return_data=True)
    return sorted({tuple(sorted(c.names)) for c in records if c.depth>tolerance})


def build():
    model=json.loads((HERE/'ftir_mounts.json').read_text());checks=[];results=[]
    def check(name,condition,**data):
        checks.append(dict(name=name,passed=bool(condition),**data))
        if not condition:raise AssertionError(name+': '+str(data))
    for ref in model['source_artifacts']+[model['instrument'],model['factory_floor']]:
        check('pinned_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    instrument=meshes(model['instrument']['path'],False)
    floor=meshes(model['factory_floor']['path']);plate=floor['factory_floor_candidate']
    check('manufacturer_plate_plan_dimensions',np.allclose(plate.extents[:2],[.206,.252],atol=2e-8))
    datums=model['datums'];focus=np.array(datums['beam_focus_m']);lo,hi=plate.bounds
    check('focus_xy_uses_correct_front_and_right_edges',abs(focus[1]-lo[1]-.132)<3e-8 and abs(hi[0]-focus[0]-.095)<3e-8)
    check('plate_is_distinct_from_chassis_floor',abs(plate.bounds[1,2]-.060)<1e-8 and abs(plate.bounds[0,2]-.054)<1e-8)
    check('focus_height_above_plate',abs(focus[2]-plate.bounds[1,2]-.090)<1e-8)
    cover=model['instrument_cover'];cover_closed={n:instrument[n] for n in cover['parts']}
    check('nominal_cover_clearance',abs(cover_closed['sample_bay_lid'].bounds[0,2]-plate.bounds[1,2]-.190)<2e-8)
    # A filled slab would lose the source's focus hole and finger opening.
    ray_origins=[focus+[0,0,.020],[lo[0]+.063,lo[1]+.033,.2],[lo[0]+.02,lo[1]+.02,.2]]
    hits=plate.ray.intersects_any(ray_origins,[[0,0,-1]]*3).tolist()
    check('floor_has_actual_datum_and_finger_holes',hits==[False,False,True],ray_hits=hits)
    supports={n:m for n,m in instrument.items() if n.startswith('mount_socket_')}
    check('four_existing_supports_reach_plate_underside',len(supports)==4 and all(abs(m.bounds[1,2]-plate.bounds[0,2])<2e-8 for m in supports.values()))
    check('factory_floor_does_not_penetrate_instrument',not contacts(floor,instrument))
    open_transform=trimesh.transformations.rotation_matrix(cover['selected_open_angle_rad'],cover['axis'],cover['pivot_m'])
    opened={n:m.copy() for n,m in instrument.items()}
    for n in cover['parts']:opened[n].apply_transform(open_transform)
    rejected=json.loads((HERE/'ftir_mount_rejected_purge.json').read_text())
    check('rejected_purge_fixture_pinned',sha(ROOT/rejected['geometry']['path'])==rejected['geometry']['sha256'])
    old=meshes(rejected['geometry']['path'])
    for m in old.values():m.apply_translation([0,0,.04])
    old_contacts=contacts(old,{'sample_bay_purge_outlet':instrument['sample_bay_purge_outlet']})
    check('rejected_adapter_still_hits_purge_outlet',bool(old_contacts),penetration_pairs=old_contacts)
    for cfg in model['configurations']:
        identity=cfg['id'];hardware=meshes(cfg['hardware']['path'])
        for ref in [cfg['hardware'],cfg['accessory_geometry']]:check('pinned_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
        accessory={n:m for n,m in meshes(cfg['accessory_geometry']['path']).items() if n not in cfg['excluded_loose_parts']}
        for m in accessory.values():m.apply_translation(cfg['accessory_translation_m'])
        for n,m in hardware.items():
            welded=m.copy();welded.merge_vertices(merge_tex=True,merge_norm=True)
            check(identity+'_solid_'+n,welded.is_watertight and welded.volume>0 and np.isfinite(m.vertices).all())
        check(identity+'_adapter_resting_on_factory_plate',abs(hardware['ordinary_adapter_plate'].bounds[0,2]-plate.bounds[1,2])<2e-8)
        check(identity+'_retention_relief',not contacts({'registration':floor['inferred_rear_registration_block']},hardware))
        base=accessory['optical_base_slotted_plate' if identity=='harrick_hrs' else 'chassis_base']
        support_meshes=[hardware['ordinary_adapter_plate']] if identity=='harrick_hrs' else [m for n,m in hardware.items() if n.startswith('spacer_')]
        check(identity+'_accessory_has_support',all(abs(m.bounds[1,2]-base.bounds[0,2])<2e-8 for m in support_meshes))
        for bolt in cfg['fasteners']:
            check(identity+'_'+bolt['id']+'_selected_engagement',bolt['engagement_m']>0 and bolt['plate_bottom_clearance_m']>=0,
                engagement_m=bolt['engagement_m'],bottom_clearance_m=bolt['plate_bottom_clearance_m'],scope='Geometric overlap only; no strength or thread-contact credit')
        # Ordinary screwdriver-axis corridor, not a robot hand/path proof.
        driver_findings=[]
        for bolt in cfg['fasteners']:
            if not bolt['id'].startswith('accessory_'):continue
            head=hardware[bolt['id']];xy=bolt['center_xy_m'];z=head.bounds[1,2]
            shaft=trimesh.creation.cylinder(radius=.004,height=.080,sections=32)
            shaft.apply_translation([*xy,z+.041])
            clashes=contacts({'driver_axis_envelope':shaft},accessory)
            driver_findings.append(dict(fastener=bolt['id'],radius_m=.004,length_m=.080,penetration_pairs=clashes,clear=not clashes))
        assembly={**{'accessory:'+n:m for n,m in accessory.items()},**{'hardware:'+n:m for n,m in hardware.items()}}
        closed_hits=contacts(assembly,cover_closed)
        open_hits=contacts(assembly,opened)
        roof=cover_closed['sample_bay_lid'].bounds[0,2]
        height=max(m.bounds[1,2] for m in accessory.values())
        ray_offset=np.array(cfg['accessory_input_ray_yz_m'])-focus[1:]
        # Keep failed rays/cover states in the report. Passing the audit means
        # the validator identified them, not that the installation passed.
        result=dict(id=identity,closed_cover_penetration_pairs=closed_hits,open_instrument_penetration_pairs=open_hits,
            highest_accessory_z_m=float(height),closed_roof_z_m=float(roof),nominal_roof_margin_m=float(roof-height),
            nominal_input_ray_offset_yz_m=ray_offset.tolist(),driver_access=driver_findings,
            closed_cover_fit=bool(not closed_hits and height<=roof),open_geometry_fit=not open_hits,
            optical_compatibility_qualified=False,operating_configuration_qualified=False)
        if identity=='harrick_hrs':
            needed_y=-float(ray_offset[0]);shifted={n:m.copy() for n,m in accessory.items()}
            for m in shifted.values():m.apply_translation([0,needed_y,0])
            result['ray_alignment_counterexample']=dict(required_y_translation_m=needed_y,
                penetration_pairs=contacts(shifted,opened),scope='Diagnostic shift only; never applied as an accepted installation')
            check('reject_harrick_envelope_only_optical_fit',abs(ray_offset[0])>.05 and bool(result['ray_alignment_counterexample']['penetration_pairs']))
        else:
            check('reject_spectratech_bare_envelope_false_positive',height-roof>.015 and bool(closed_hits))
            check('spectratech_authored_entry_height_and_y_alignment',np.linalg.norm(ray_offset)<1e-8)
        # Nominal top-down insertion of the assembled accessory mount into an
        # already-open bay. No hand, carried-load balance or retention assumed.
        sweep=[]
        for dz in np.linspace(.32,0,25):
            lifted={n:m.copy() for n,m in assembly.items()}
            for m in lifted.values():m.apply_translation([0,0,dz])
            pairs=contacts(lifted,opened)
            sweep.append(dict(lift_m=float(dz),penetration_pairs=pairs))
        result['open_bay_vertical_insertion_samples']=sweep
        result['insertion_geometry_clear']=all(not s['penetration_pairs'] for s in sweep)
        check(identity+'_revised_adapter_avoids_purge_during_sampled_insertion',result['insertion_geometry_clear'])
        results.append(result)
    report=dict(schema_version=1,audit_passed=all(c['passed'] for c in checks),checks=checks,configurations=results,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [Path(__file__),HERE/'geometry_tools.py',HERE/'ftir_mounts.json']],
        scope='Rigid nominal geometry audit with intentionally retained fit failures; no installation, optics, force, manipulation or owner acceptance.',
        installed_compatibility_qualified=False,owner_acceptance=None)
    write_json(HERE/'ftir_mount_checks.json',report)
    print(json.dumps(dict(audit_passed=report['audit_passed'],checks=len(checks),configurations=[{k:c[k] for k in ['id','closed_cover_fit','open_geometry_fit','insertion_geometry_clear','nominal_roof_margin_m','nominal_input_ray_offset_yz_m']} for c in results])))


if __name__=='__main__':build()
