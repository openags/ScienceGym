"""Export object-local hand affordances; no robot arm paths or world poses."""
import hashlib
import json
from pathlib import Path

import numpy as np
import trimesh

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]


def main():
    shape=ROOT/'assets/nicolet_6700_mechanism_v1/revisions/passive_dynamics/geometry/nicolet_passive_dynamics.glb'
    parent=ROOT/'assets/nicolet_6700_mechanism_v1/cover_grasp_prior.json'
    fits=HERE.parent/'nicolet_slider_push_02/review.json'
    scene=trimesh.load(shape,force='scene',process=False)
    def part(name):
        T,key=scene.graph[name];mesh=scene.geometry[key].copy();mesh.apply_transform(T);return mesh
    grip=part('sample_access_slider_grip')
    old=json.loads(parent.read_text());search=json.loads(fits.read_text())
    offset=grip.bounds.mean(0)-np.array(search['grip_bounds_port_frame_m']).mean(0)
    keys=[]
    for i,key in enumerate(old['keys']):
        keys.append(dict(key,center_m=part('scan_key_'+str(i)).bounds.mean(0).tolist()))
    shape_q=search['candidates'][237]['q']
    candidates=[]
    for i,c in enumerate(search['candidates']):
        if not c['passed_distal_path'] or c['q']!=shape_q:continue
        palm=np.array(c['palm_in_port_frame']);palm[:3,3]+=offset
        candidates.append(dict(id=i,hand_q=c['q'],palm_in_device=palm.tolist(),
            outward_surface_normal=c['outward_surface_normal'],source_pad=c['source_pad'],
            surface_m=(np.array(c['surface_in_port_frame'])+offset).tolist(),
            pad_gap_m=c['pad_gap_m']))
    candidates.sort(key=lambda c:abs(c['id']-237))
    result=dict(schema='sciencegym.object_local_slider_affordance.v1',
        scope='Inferred hand poses for the modeled sliding-window grip. No world registration, arm joint trajectory, device outcome or physical qualification.',
        source_shape_file=shape.name,source_shape_sha256=hashlib.sha256(shape.read_bytes()).hexdigest(),
        keys=keys,key_cap_thickness_m=old['key_cap_thickness_m'],
        grip_bounds_m=grip.bounds.tolist(),slider_parts=['sample_access_sliding_window','sample_access_slider_grip'],
        slider_axis=[0.,1.,0.],requested_travel_m=.070,maximum_modeled_travel_m=.104,
        required_observation='Closed window grip observed in native depth, after key-row registration',
        geometry_manufacturer_measured=False,manipulation_strategy_inferred=True,
        candidates=candidates)
    target=ROOT/'assets/nicolet_6700_mechanism_v1/slider_push_prior.json'
    if target.exists():raise FileExistsError(target)
    target.write_text(json.dumps(result,indent=2)+'\n')
    audit=dict(source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),shape,parent,fits,target]},
        old_key_to_raw_cad_offsets_m=[(np.array(a['center_m'])-b['center_m']).tolist() for a,b in zip(keys,old['keys'])],
        raw_grip_center_m=grip.bounds.mean(0).tolist(),exported_candidates=len(candidates),
        no_world_or_arm_path_exported=True,
        note='The raw GLB has a common +1.25 mm Y offset from the older key prior. The new keys and grasp poses both use the raw CAD frame. Do not combine the new shape with the old key translation without conversion.')
    (HERE/'public_prior_export.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit),flush=True)


if __name__=='__main__':main()
