"""Check real mask openings and mechanical inspection sweeps, not optics."""
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE, ROOT, sha, write_json


def build():
    model=json.loads((HERE/'angular_accessories.json').read_text())
    checks=[];sweeps=[]
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
            check('spectratech_five_separate_mirrors',all('m'+str(i)+'_face' in meshes for i in range(1,6)))
            hit=meshes['source_side_open_housing'].ray.intersects_any([[.13,-.025,.067]], [[-1,0,0]])[0]
            check('spectratech_source_port_open',not hit)
            hit=meshes['source_side_open_housing'].ray.intersects_any([[.13,-.013,.067]], [[-1,0,0]])[0]
            check('spectratech_source_port_has_real_surrounding_wall',hit)
            def mesh_normal(mesh):
                return np.linalg.svd(mesh.vertices-mesh.vertices.mean(axis=0),full_matrices=False)[2][-1]
            fold=details['nominal_fold_geometry'];points=np.array(fold['points_m'])
            for item in fold['mirrors']:
                normal=mesh_normal(meshes[item['part']]);incoming=np.array(item['incoming'])
                reflected=incoming-2*np.dot(incoming,normal)*normal
                check(item['part']+'_actual_face_reflects_nominal_fold',np.linalg.norm(reflected-item['outgoing'])<1e-5)
            normal=mesh_normal(meshes['sample_carrier_open_frame'])
            if normal[2]<0:normal=-normal
            incoming=points[4]-points[3];incoming/=np.linalg.norm(incoming)
            incidence=np.degrees(np.arccos(-np.dot(incoming,normal)))
            rotated=trimesh.transformations.rotation_matrix(-np.radians(65),[0,1,0])[:3,:3]@normal
            last=np.degrees(np.arccos(-np.dot(incoming,rotated)))
            check('sample_surface_normal_changes_incidence',abs(incidence-20)<1e-4 and abs(last-85)<1e-4,
                  initial_degrees=float(incidence),final_degrees=float(last))
            # A front-facing flat picture turning in its own plane fails this
            # constraint even when its angle label and endpoint motion look right.
            wrong=np.array([0,1,0]);wrong_after=trimesh.transformations.rotation_matrix(-np.radians(65),[0,1,0])[:3,:3]@wrong
            check('negative_in_plane_picture_rotation_rejected',np.linalg.norm(wrong_after-wrong)<1e-10 and np.linalg.norm(rotated-normal)>.5)
            fit=details['mask_fit_hypothesis'];mask=meshes[fit['part']].copy();mask.apply_translation(fit['translation_m'])
            holder=trimesh.collision.CollisionManager();mask_manager=trimesh.collision.CollisionManager();mask_manager.add_object('mask',mask)
            for name,mesh in meshes.items():
                if name.startswith(('sample_carrier_','sample_guide_','sample_leaf_','sample_lower_stop')):holder.add_object(name,mesh)
            _,contacts=mask_manager.in_collision_other(holder,return_data=True)
            check('slot_mask_seats_without_holder_penetration',not any(c.depth>.00005 for c in contacts))
            for side in [-1,1]:
                guide=meshes['sample_guide_'+str(side*14.2)]
                gap=(guide.bounds[0,0]-mask.bounds[1,0]) if side>0 else (mask.bounds[0,0]-guide.bounds[1,0])
                check('slot_mask_side_clearance_'+str(side),abs(gap-.0002)<2e-8)
                leaf=meshes['sample_leaf_retainer_'+str(side*14.2)]
                check('slot_mask_retainer_gap_'+str(side),abs(leaf.bounds[0,2]-mask.bounds[1,2]-.00025)<2e-8)
                hits,_,_=meshes['sample_carrier_open_frame'].ray.intersects_location([[side*.011,-.026,.1]],[[0,0,-1]])
                check('slot_mask_supported_edge_'+str(side),len(hits)>0 and abs(hits[:,2].max()-mask.bounds[0,2])<2e-8)
            for index,(start,end) in enumerate(zip(points[:-1],points[1:])):
                direction=end-start;length=np.linalg.norm(direction);direction/=length;obstructions=[]
                for name,mesh in meshes.items():
                    hits,_,_=mesh.ray.intersects_location([start+direction*.002],[direction])
                    if len(hits):
                        distances=(hits-start)@direction
                        if np.any((distances>.0021)&(distances<length-.0021)):obstructions.append(name)
                check('nominal_fold_segment_'+str(index)+'_clear',not obstructions,obstructions=obstructions,
                      scope='Center ray only, excluding 2.1 mm endpoint mirror contact; no beam width, focus or spectral simulation')
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
    result=dict(schema_version=1,passed=all(c['passed'] for c in checks),checks=checks,sweeps=sweeps,
        model_sha256=sha(HERE/'angular_accessories.json'),validator_sha256=sha(__file__),
        owner_acceptance=None,installed_compatibility_qualified=False,optics_qualified=False,
        limitations=['Outer dimensions and local mechanisms are inferred, not manufacturer CAD',
            'Sample retention, mounting adapters, fasteners and optical alignment remain open',
            'Inspection movements are not robot operations or a coupled optical simulation'])
    write_json(HERE/'angular_accessory_checks.json',result)
    print(json.dumps(dict(checks=len(checks),passed=result['passed'],sweep_samples=sum(len(s['samples']) for s in sweeps))))


if __name__=='__main__':build()
