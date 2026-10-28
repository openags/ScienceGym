"""Assemble the bounded Cary access verdict from independent export reviews."""
import argparse,hashlib,json
from pathlib import Path


def review(folder):
    folder=Path(folder);names=['export.json','geometry_review.json','self_contact_review.json','motion_review.json','cary_access_review.json'];reports={n:json.loads((folder/n).read_text()) for n in names}
    export,geometry,self_contact,motion,cary=[reports[n] for n in names]
    assert export['episode']=='cary_access' and export['sample_step_s']<=.1
    config=json.loads((folder/'source/cary_access_episode.json').read_text())
    for name,sha in export['source_sha256'].items():assert hashlib.sha256((folder/'source'/name).read_bytes()).hexdigest()==sha,name
    assert hashlib.sha256((folder/'frames.jsonl.gz').read_bytes()).hexdigest()==export['compressed_frames_sha256']
    assert geometry['frames_sha256']==cary['frames_sha256']==export['frames_sha256']
    assert geometry['frames']==motion['frames']==self_contact['samples']==cary['samples']==export['frame_count']
    complete=set(export['selected_phases'])=={s['id'] for s in config['segments']}
    passed=complete and geometry['frames_with_nonfloor_intersections']==0 and all(r['passed'] for r in [self_contact,motion,cary])
    result=dict(passed=passed,scope='Sampled source geometry for instrument access preparation only. '+config['scope']+' No retention-force, balance, dynamics, sensor-control, whole-film or paper-branch qualification.',initial_conditions=config['initial_conditions'],episode=export['episode'],covers_entire_episode=complete,duration_s=export['scene']['duration'],frames=export['frame_count'],sample_step_s=export['sample_step_s'],phases=export['selected_phases'],robot_environment_intersection_frames=geometry['frames_with_nonfloor_intersections'],self_intersection_frames=len(self_contact['intersection_frames']),mechanism_intersection_frames=len(cary['intersection_frames']),kinematic_failures=len(cary['kinematic_failures']),grip_clearance_failures=len(cary['grip_clearance_failures']),support_failures=len(cary['support_failures']),joint_limit_failures=len(motion['joint_limit_failures']),joint_speed_failures=len(motion['joint_velocity_failures']),sole_penetration_failures=len(motion['sole_penetration_failures']),maximum_source_fk_matrix_error=cary['maximum_source_fk_matrix_error'],maximum_object_matrix_error=cary['maximum_object_matrix_error'],maximum_grip_gaps_m=cary['maximum_grip_gaps_m'],bench_seating_gap_range_m=cary['bench_seating_gap_range_m'],source_sha256=export['source_sha256'],evidence_sha256={n:hashlib.sha256((folder/n).read_bytes()).hexdigest() for n in names+['frames.jsonl.gz']},verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (folder/'sampled_interaction_review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['passed','duration_s','frames','robot_environment_intersection_frames','mechanism_intersection_frames','kinematic_failures','grip_clearance_failures','support_failures']}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder');args=parser.parse_args();review(args.folder)
