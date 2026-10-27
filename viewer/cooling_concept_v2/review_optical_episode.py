"""Assemble the bounded local-episode verdict from independent review records."""
import argparse
import hashlib
import json
from pathlib import Path


def review(folder):
    folder=Path(folder)
    names=['export.json','geometry_review.json','self_contact_review.json','motion_review.json','optical_exchange_review.json']
    reports={name:json.loads((folder/name).read_text()) for name in names}
    export,geometry,self_contact,motion,optical=[reports[name] for name in names]
    assert export['episode']=='ftir' and export['sample_step_s']<=.1
    for name,sha in export['source_sha256'].items():
        assert hashlib.sha256((folder/'source'/name).read_bytes()).hexdigest()==sha,name
    assert hashlib.sha256((folder/'frames.jsonl.gz').read_bytes()).hexdigest()==export['compressed_frames_sha256']
    assert geometry['frames_sha256']==optical['frames_sha256']==export['frames_sha256']
    assert geometry['frames']==motion['frames']==self_contact['samples']==optical['samples']==export['frame_count']
    assert geometry['deformed_geometry']['identities']==['tweezers_white']
    # The legacy geometry reviewer intentionally has passed=False pending
    # contact classification; a zero unexpected intersection count needs none.
    passed=geometry['frames_with_nonfloor_intersections']==0 and all(r['passed'] for r in [self_contact,motion,optical])
    result=dict(
        passed=passed,
        scope='Sampled source geometry for the separately initialized FTIR exchange episode: both identified witnesses, ordinary tool pickup, mounting, tool return, retrieval and restaging. Delivered materials, open access and capped reference are initial conditions. No upstream delivery, scan acquisition, balance, force, dynamics, sensor-driven control, full-film or paper-branch qualification.',
        duration_s=export['scene']['duration'],frames=export['frame_count'],sample_step_s=export['sample_step_s'],phases=export['selected_phases'],
        robot_environment_intersection_frames=geometry['frames_with_nonfloor_intersections'],
        self_intersection_frames=len(self_contact['intersection_frames']),
        tool_specimen_environment_intersection_frames=len(optical['intersection_frames']),
        kinematic_failures=len(optical['kinematic_failures']),
        joint_limit_failures=len(motion['joint_limit_failures']),
        joint_speed_failures=len(motion['joint_velocity_failures']),
        sole_penetration_failures=len(motion['sole_penetration_failures']),
        maximum_source_fk_matrix_error=optical['maximum_source_fk_matrix_error'],
        maximum_object_matrix_error=optical['maximum_object_matrix_error'],
        maximum_render_source_vertex_error_m=optical['maximum_render_source_vertex_error_m'],
        source_sha256=export['source_sha256'],
        evidence_sha256={name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in names+['frames.jsonl.gz']},
        verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (folder/'sampled_interaction_review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['passed','duration_s','frames','robot_environment_intersection_frames','self_intersection_frames','tool_specimen_environment_intersection_frames','kinematic_failures']}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder');args=parser.parse_args();review(args.folder)
