"""Check real mask openings and mechanical inspection sweeps, not optics."""
import copy
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE, ROOT, sha, write_json
from optical_ray_audit import inspect_angle


def build():
    model=json.loads((HERE/'angular_accessories.json').read_text())
    checks=[];sweeps=[];optical_coverage=[]
    def check(name,value,**data):
        checks.append(dict(name=name,passed=bool(value),**data))
        if not value:raise AssertionError(name+': '+str(data))
    for ref in model['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    for entry in model['items']:
        identity=entry['id'];geo=entry['geometry'];details=entry['details']
        check(identity+'_geometry_identity',sha(ROOT/geo['path'])==geo['sha256'])
        scene=trimesh.load(ROOT/geo['path'],force='scene');meshes={}
        for name in scene.graph.nodes_geometry:
            matrix,key=scene.graph[name];mesh=scene.geometry[key].copy();mesh.apply_transform(matrix);meshes[name]=mesh
        check(identity+'_unique_part_binding',len(meshes)==geo['parts']==len(geo['part_records']))
        for name,mesh in meshes.items():
            label=name.endswith('identification') or name.startswith('scale_number_')
            welded=mesh.copy();welded.merge_vertices(merge_tex=True,merge_norm=True)
            check(identity+'_solid_'+name,np.isfinite(mesh.vertices).all() and (label or (welded.is_watertight and welded.volume>0)))
        check(identity+'_no_installed_or_optical_claim',not details['mounting_adapter_supplied'] and not details['optical_alignment_qualified'] and not entry['asset_accepted'] and not entry['manipulation_qualified'])
        expected_apertures=[.003,.006,.013] if identity=='harrick_hrs' else [.006,.013]
        actual_apertures=sorted(m.get('diameter_m',m.get('width_m')) for m in details['masks'])
        check(identity+'_catalogue_apertures',len(actual_apertures)==len(expected_apertures) and np.allclose(actual_apertures,expected_apertures,atol=1e-12,rtol=0))
        # Necessary envelope condition only, on an explicitly inferred bay.
        extents=scene.extents
        check(identity+'_nominal_bay_envelope_only',np.all(extents<np.array([.210,.260,.200])),envelope_m=extents.tolist(),qualification='not mount, insertion clearance or optical fit')
        for mask in details['masks']:
            mesh=meshes[mask['part']];center=np.array(mask['center_m'])
            radius=mask.get('diameter_m',mask.get('width_m'))/2
            points=[center,center+[radius-.0002,0,0],center+[radius+.0002,0,0]]
            rays=np.array(points)+[0,0,.02]
            hit=mesh.ray.intersects_any(rays,np.tile([0,0,-1],(3,1))).tolist()
            check(identity+'_'+mask['part']+'_actual_opening',hit==[False,False,True],ray_hits=hit)
            check(identity+'_'+mask['part']+'_rests_on_base',abs(mesh.bounds[0,2]-(.010 if identity=='harrick_hrs' else .008))<2e-8)
            if identity=='spectratech_500':
                hit=mesh.ray.intersects_any([center+[0,-.012,.020]],[[0,0,-1]])[0]
                check(mask['part']+'_slot_open_to_edge',not hit)
        if identity=='harrick_hrs':
            mesh=meshes['hrs_apertured_top']
            hit=mesh.ray.intersects_any([[0,-.009,.11],[.009,-.009,.11]],[[0,0,-1],[0,0,-1]]).tolist()
            check('hrs_stage_real_through_aperture',hit==[False,True])
            mirror=meshes['hrs_solid_inclined_mirror_face']
            normal=np.array([0,-1,-1])/np.sqrt(2)
            check('hrs_reflection_not_false_hole',mirror.ray.intersects_any([np.array([0,-.010,.059])+normal*.03],[-normal])[0])
            for side in ['left','right']:
                mirror=trimesh.collision.CollisionManager();mirror.add_object('face',meshes['rear_'+side+'_concave_face'])
                supports=trimesh.collision.CollisionManager()
                for suffix in ['post','saddle','adjuster_boss']:supports.add_object(suffix,meshes['rear_'+side+'_'+suffix])
                check('harrick_'+side+'_support_does_not_pierce_mirror',not mirror.in_collision_other(supports))
        else:
            expected=['m1_face','m2_face','m3_face','m5_face']
            actual=sorted(n for n in meshes if n.startswith('m') and n.endswith('_face'))
            check('spectratech_M4_is_sample_not_extra_mirror',actual==expected and 'alignment_mirror_7004_001' in meshes,
                  independent_mirror_parts=actual)
            rejected=json.loads((HERE/'angular_topology_rejected.json').read_text())
            check('rejected_six_surface_fixture_pinned',sha(ROOT/rejected['geometry']['path'])==rejected['geometry']['sha256'])
            old=trimesh.load(ROOT/rejected['geometry']['path'],force='scene')
            old_names=list(old.graph.nodes_geometry)
            check('rejected_six_surface_fixture_detected','m4_face' in old_names and len([n for n in old_names if n.startswith('m') and n.endswith('_face')])==5)
            check('M3_and_M4_share_selected_rotor',all(n in details['inspection']['parts'] for n in ['m3_face','m3_back','alignment_mirror_7004_001','sample_carrier_open_frame']))
            hit=meshes['source_side_open_housing'].ray.intersects_any([[.13,-.020,.067]], [[-1,0,0]])[0]
            check('spectratech_source_port_open',not hit)
            hit=meshes['source_side_open_housing'].ray.intersects_any([[.13,-.008,.067]], [[-1,0,0]])[0]
            check('spectratech_source_port_has_real_surrounding_wall',hit)
            def mesh_normal(mesh):
                return np.linalg.svd(mesh.vertices-mesh.vertices.mean(axis=0),full_matrices=False)[2][-1]
            fold=details['nominal_fold_geometry'];points=np.array(fold['points_m'])
            check('five_optical_surfaces_include_sample',len(points)==7 and len(fold['mirrors'])==4 and fold['sample_surface']['part']=='alignment_mirror_7004_001')
            for item in fold['mirrors']+[fold['sample_surface']]:
                normal=mesh_normal(meshes[item['part']]);incoming=np.array(item['incoming'])
                reflected=incoming-2*np.dot(incoming,normal)*normal
                check(item['part']+'_actual_face_reflects_nominal_fold',np.linalg.norm(reflected-item['outgoing'])<1e-5)
            m3_normal=mesh_normal(meshes['m3_face']);normal=mesh_normal(meshes['alignment_mirror_7004_001'])
            measured=float(np.degrees(np.arccos(np.clip(abs(np.dot(m3_normal,normal)),-1,1))))
            check('selected_near_retro_corner_actual_faces',abs(measured-75)<1e-4 and details['selected_corner_degrees']==105,
                  acute_normal_angle_degrees=measured,scope='Selected 105-degree corner, not a manufacturer dimension')
            incoming=points[3]-points[2];incoming/=np.linalg.norm(incoming)
            angles=[]
            for degrees in [0,65]:
                rot=trimesh.transformations.rotation_matrix(-np.radians(degrees),[0,1,0])[:3,:3]
                m=rot@m3_normal;n=rot@normal;after_m3=incoming-2*np.dot(incoming,m)*m
                angles.append(float(np.degrees(np.arccos(np.clip(abs(np.dot(after_m3,n)),-1,1)))))
            check('coupled_plane_normals_nominal_20_to_85',np.allclose(angles,[20,85],atol=1e-4),incidence_degrees=angles,
                  scope='Infinite-plane normals only. Actual finite-aperture ray hits are audited separately; these angles do not prove beam coverage.')
            rotated=trimesh.transformations.rotation_matrix(-np.radians(65),[0,1,0])[:3,:3]@normal
            wrong=np.array([0,1,0]);wrong_after=trimesh.transformations.rotation_matrix(-np.radians(65),[0,1,0])[:3,:3]@wrong
            check('negative_in_plane_picture_rotation_rejected',np.linalg.norm(wrong_after-wrong)<1e-10 and np.linalg.norm(rotated-normal)>.5)
            fit=details['mask_fit_hypothesis'];mask=meshes[fit['part']].copy();mask.apply_transform(fit['transform_m'])
            holder=trimesh.collision.CollisionManager();mask_manager=trimesh.collision.CollisionManager();mask_manager.add_object('mask',mask)
            names=[n for n in meshes if n.startswith(('sample_carrier_open_','sample_guide_','sample_leaf_','sample_lower_stop'))]
            for name in names:holder.add_object(name,meshes[name])
            _,contacts=mask_manager.in_collision_other(holder,return_data=True)
            local=np.linalg.inv(np.array(details['sample_frame_transform_m']))
            mask.apply_transform(local);frame=meshes['sample_carrier_open_frame'].copy();frame.apply_transform(local)
            support_overlap=float(frame.bounds[1,2]-mask.bounds[0,2])
            # FCL reports millimetre SAT depth on coplanar triangulated rim
            # edges even when the two solids are separated to float32 accuracy.
            # Bound the frame and two end-stop contacts in the independent
            # holder frame; guide/leaf collisions retain the ordinary predicate.
            intended_touch={frozenset(['mask','sample_carrier_open_frame']):abs(support_overlap)<3e-8}
            for name in names:
                if name.startswith('sample_lower_stop_'):
                    stop=meshes[name].copy();stop.apply_transform(local)
                    overlap=float(stop.bounds[1,1]-mask.bounds[0,1])
                    check(name+'_actual_end_contact',abs(overlap)<3e-8,end_overlap_m=overlap)
                    intended_touch[frozenset(['mask',name])]=abs(overlap)<3e-8
            unintended=[c for c in contacts if c.depth>.00005 and not intended_touch.get(frozenset(c.names),False)]
            check('alternative_slot_mask_seats_without_holder_penetration',not unintended and abs(support_overlap)<3e-8,
                  support_overlap_m=support_overlap,scope='Reference removed. Coplanar frame/edge-stop contacts are classified by independent normal bounds within 30 nm; no guide/retainer exemption')
            bad_mask=mask.copy();bad_mask.apply_translation([0,0,-.002])
            bad_manager=trimesh.collision.CollisionManager();bad_manager.add_object('mask',bad_mask)
            local_holder=trimesh.collision.CollisionManager();local_holder.add_object('frame',frame)
            _,bad_contacts=bad_manager.in_collision_other(local_holder,return_data=True)
            check('negative_overinserted_mask_rejected',frame.bounds[1,2]-bad_mask.bounds[0,2]>.0019 and any(c.depth>.00005 for c in bad_contacts))
            stop=meshes['sample_lower_stop_1'].copy();stop.apply_transform(local)
            slipped=mask.copy();slipped.apply_translation([0,-.002,0])
            check('negative_past_end_stop_not_coplanar',stop.bounds[1,1]-slipped.bounds[0,1]>.0019)
            for side in [-1,1]:
                guide=meshes['sample_guide_'+str(side*14.2)].copy();guide.apply_transform(local)
                gap=(guide.bounds[0,0]-mask.bounds[1,0]) if side>0 else (mask.bounds[0,0]-guide.bounds[1,0])
                check('slot_mask_side_clearance_'+str(side),abs(gap-.0002)<3e-8)
                leaf=meshes['sample_leaf_retainer_'+str(side*14.2)].copy();leaf.apply_transform(local)
                check('slot_mask_retainer_gap_'+str(side),abs(leaf.bounds[0,2]-mask.bounds[1,2]-.00025)<3e-8)
                hits,_,_=frame.ray.intersects_location([[side*.011,0,.02]],[[0,0,-1]])
                check('slot_mask_supported_edge_'+str(side),len(hits)>0 and abs(hits[:,2].max()-mask.bounds[0,2])<3e-8)
            reference=meshes['alignment_mirror_7004_001'].copy();reference.apply_transform(local)
            check('displayed_M4_reference_is_supported',abs(reference.bounds[0,2]-frame.bounds[1,2])<3e-8)
            check('displayed_M4_reference_front_matches_sample_datum',abs(reference.bounds[1,2])<3e-8)
            m3_parts=trimesh.collision.CollisionManager()
            for name in ['m3_face','m3_back']:m3_parts.add_object(name,meshes[name])
            specimen_parts=trimesh.collision.CollisionManager()
            for name in names+['alignment_mirror_7004_001']:specimen_parts.add_object(name,meshes[name])
            _,intersections=m3_parts.in_collision_other(specimen_parts,return_data=True)
            check('rigid_carrier_internal_M3_holder_separation',not any(c.depth>.00005 for c in intersections))
            long_guide=trimesh.creation.box([.004,.044,.004]);long_guide.apply_translation([.0142,0,.0008]);long_guide.apply_transform(details['sample_frame_transform_m'])
            bad_holder=trimesh.collision.CollisionManager();bad_holder.add_object('extended_guide',long_guide)
            _,intersections=m3_parts.in_collision_other(bad_holder,return_data=True)
            check('negative_extended_guide_hits_M3',any(c.depth>.00005 for c in intersections))
            for index,(start,end) in enumerate(zip(points[:-1],points[1:])):
                direction=end-start;length=np.linalg.norm(direction);direction/=length;obstructions=[]
                for name,mesh in meshes.items():
                    hits,_,_=mesh.ray.intersects_location([start+direction*.002],[direction])
                    if len(hits):
                        distances=(hits-start)@direction
                        if np.any((distances>.0021)&(distances<length-.0021)):obstructions.append(name)
                check('nominal_fold_segment_'+str(index)+'_clear',not obstructions,obstructions=obstructions,
                      scope='Initial center ray only, excluding 2.1 mm endpoint mirror contact; no beam width, focus or spectral simulation')
            probe=details['geometric_probe'];full=[];coverage=[]
            for angle in range(20,86):
                record=inspect_angle(meshes,details,angle,probe['y_offsets_m'],probe['z_offsets_m'])
                bad=[r for r in record['rays'] if not r['passed']]
                check('finite_five_surface_path_'+str(angle),not bad,failures=bad)
                check('exit_direction_'+str(angle),all(np.linalg.norm(np.array(r['exit_direction'])-[-1,0,0])<1e-5 for r in record['rays']))
                full.append(record)
                if angle in [20,35,50,65,85]:
                    center=next(r for r in record['rays'] if r['y_offset_m']==r['z_offset_m']==0)
                    coverage.append(dict(dial_degrees=angle,m3_hit='m3_face' in center['hit_parts'],
                        m4_reference_hit='alignment_mirror_7004_001' in center['hit_parts'],
                        exit_ray_valid=center['passed'],bundle_passed=record['passed'],center_ray=center))
            # Actual counterexamples exercise the same complete-path predicate.
            removed={n:m for n,m in meshes.items() if n!='alignment_mirror_7004_001'}
            check('negative_missing_M4_reference_rejected',not inspect_angle(removed,details,50)['passed'])
            blocked={**meshes};slab=trimesh.creation.box([.001,.020,.020]);slab.apply_translation([.10,-.020,.067]);blocked['injected_port_block']=slab
            bad=inspect_angle(blocked,details,50)
            check('negative_blocked_source_port_rejected',not bad['passed'] and bad['rays'][0].get('obstruction')=='injected_port_block')
            # Recreate the observed full-width stop defect with actual geometry.
            stop=trimesh.creation.box([.028,.004,.004]);stop.apply_translation([0,-.019,.0008]);stop.apply_transform(details['sample_frame_transform_m'])
            stopped={n:m for n,m in meshes.items() if not n.startswith('sample_lower_stop_')};stopped['sample_lower_stop']=stop
            stopped_details=copy.deepcopy(details);stopped_details['inspection']['parts'].append('sample_lower_stop')
            bad=inspect_angle(stopped,stopped_details,85)
            check('negative_full_width_stop_blocks_grazing_exit',not bad['passed'] and bad['rays'][0].get('obstruction')=='sample_lower_stop',failure=bad)
            old_record=json.loads((HERE/'angular_rotor_rejected.json').read_text())
            check('rejected_corner_geometry_pinned',sha(ROOT/old_record['geometry']['path'])==old_record['geometry']['sha256'])
            old_scene=trimesh.load(ROOT/old_record['geometry']['path'],force='scene');old_meshes={}
            for n in old_scene.graph.nodes_geometry:
                matrix,key=old_scene.graph[n];m=old_scene.geometry[key].copy();m.apply_transform(matrix);old_meshes[n]=m
            old_fail=inspect_angle(old_meshes,old_record['details'],85)
            check('negative_old_rotor_misses_full_path',not old_fail['passed'],failure=old_fail)
            optical_coverage.append(dict(asset=identity,samples=coverage,full_range_samples=full,
                all_sampled_rays_hit=all(s['passed'] for s in full),diagnostic_rays=sum(len(s['rays']) for s in full),
                probe=probe,optics_qualified=False,rejected_previous_rotor=old_fail,
                limitation='Triangle-level finite-path clearance for the selected parallel probe only. The inferred corner, manufacturer beam size, focusing, throughput, coatings and mounting are unqualified.'))
        state=details['inspection'];moving=trimesh.collision.CollisionManager();fixed=trimesh.collision.CollisionManager()
        # These bearing surfaces are the intended revolute interface, whose
        # fit tolerances and retention have not yet been specified.
        exempt={'rotary_spindle','rotary_bearing_housing'} if identity=='spectratech_500' else set()
        for name,mesh in meshes.items():
            if name in state['parts']:moving.add_object(name,mesh)
            elif name not in exempt:fixed.add_object(name,mesh)
        samples=[]
        for fraction in np.linspace(0,1,27):
            t=np.eye(4)
            if state['kind']=='slide':t[:3,3]=np.array(state['axis'])*state['maximum']*fraction
            else:t=trimesh.transformations.rotation_matrix(state['maximum']*fraction,state['axis'],state['pivot_m'])
            for name in state['parts']:moving.set_transform(name,t)
            collision,contacts=moving.in_collision_other(fixed,return_data=True)
            depths={}
            for c in contacts:
                if c.depth>.00005:
                    pair=tuple(sorted(c.names));depths[pair]=max(depths.get(pair,0),float(c.depth))
            bad=[dict(parts=list(pair),depth_m=depth) for pair,depth in sorted(depths.items())]
            check(identity+'_inspection_sweep_'+str(round(float(fraction),6)),not bad,penetrations=bad)
            samples.append(dict(fraction=float(fraction),penetrations_over_50um=bad))
        sweeps.append(dict(asset=identity,samples=samples,excluded_intended_bearing_parts=sorted(exempt),scope='Sampled rigid part separation; no forces, robot contact or optical calibration'))
    # Counterexample: a solid dark plate must fail the same opening predicate.
    closed=trimesh.creation.box([.024,.034,.0014])
    check('negative_solid_mask_rejected',closed.ray.intersects_any([[0,0,.02]],[[0,0,-1]])[0])
    result=dict(schema_version=1,passed=all(c['passed'] for c in checks),checks=checks,sweeps=sweeps,optical_coverage=optical_coverage,
        model_sha256=sha(HERE/'angular_accessories.json'),validator_sha256=sha(__file__),
        source_artifacts=[dict(path=str((HERE/'optical_ray_audit.py').relative_to(ROOT)),sha256=sha(HERE/'optical_ray_audit.py'))],
        owner_acceptance=None,installed_compatibility_qualified=False,optics_qualified=False,
        limitations=['Outer dimensions and local mechanisms are inferred, not manufacturer CAD',
            'Sample retention, mounting adapters, fasteners and optical alignment remain open',
            'Inspection movements are not robot operations or a coupled optical simulation'])
    write_json(HERE/'angular_accessory_checks.json',result)
    print(json.dumps(dict(checks=len(checks),passed=result['passed'],sweep_samples=sum(len(s['samples']) for s in sweeps))))


if __name__=='__main__':build()
