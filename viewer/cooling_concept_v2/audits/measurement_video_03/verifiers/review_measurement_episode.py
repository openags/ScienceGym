"""Run and bind independent geometric reviews of the complete measurement.

The sampled review and the review of every encoded video frame are separate
receipts. Neither establishes force, balance, sensor control or paper results.
"""
import argparse
import concurrent.futures
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def run_reviews(folder,workers):
    frozen=folder/'verifiers';frozen.mkdir(exist_ok=False)
    names=['audit_geometry.py','audit_motion.py','audit_self_contact.py','audit_optical_exchange.py',
           'audit_measurement_reference.py','audit_ftir_mechanisms.py','source_geometry.py',
           'environment_poses.py','deformed_geometry.py','audit_payload_clearance.py','review_measurement_episode.py']
    pins={name:sha(HERE/name) for name in names}
    for name in names:shutil.copy2(HERE/name,frozen/name)
    python=__import__('sys').executable;env={**os.environ,'OPENBLAS_NUM_THREADS':'1'}
    def execute(script,target,log):
        with log.open('w') as out:
            result=subprocess.run([python,str(HERE/script),str(target)],stdout=out,stderr=subprocess.STDOUT,env=env)
        if result.returncode:raise RuntimeError(script+' failed: '+str(log))
        print('review_finished',script,str(target),flush=True)
    jobs=['audit_geometry.py','audit_motion.py','audit_optical_exchange.py','audit_measurement_reference.py','audit_ftir_mechanisms.py']
    # Each self-collision query is independent. Partition only that reviewer;
    # the motion reviewer retains the full ordered sequence for derivatives.
    export=json.loads((folder/'export.json').read_text());count=export['frame_count'];chunk=(count+workers-1)//workers
    temporary=Path(tempfile.mkdtemp(prefix='sciencegym-measurement-self-'))
    shard_records=[];streams=[]
    for i in range(workers):
        path=temporary/str(i);path.mkdir();streams.append(gzip.open(path/'frames.jsonl.gz','wt',compresslevel=1))
        shard_records.append(dict(first_frame=i*chunk,exclusive_last_frame=min((i+1)*chunk,count),path=path))
    try:
        with gzip.open(folder/'frames.jsonl.gz','rt') as stream:
            for i,line in enumerate(stream):streams[i//chunk].write(line)
        assert i+1==count
    finally:
        for stream in streams:stream.close()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(jobs)+workers) as pool:
        futures=[pool.submit(execute,n,folder,folder/(n[:-3]+'.log')) for n in jobs]
        futures += [pool.submit(execute,'audit_self_contact.py',r['path'],r['path']/'run.log') for r in shard_records]
        for future in futures:future.result()
    self_reports=[json.loads((r['path']/'self_contact_review.json').read_text()) for r in shard_records]
    merged=dict(self_reports[0]);merged['samples']=sum(r['samples'] for r in self_reports)
    merged['passed']=all(r['passed'] for r in self_reports)
    merged['intersection_frames']=sorted([f for r in self_reports for f in r['intersection_frames']],key=lambda f:f['time_s'])
    merged['contact_pairs']={}
    for r in self_reports:
        assert r['excluded_mechanical_neighbor_pairs']==merged['excluded_mechanical_neighbor_pairs']
        for pair,value in r['contact_pairs'].items():
            target=merged['contact_pairs'].setdefault(pair,dict(samples=0,phases=[]));target['samples']+=value['samples']
            target['phases']=sorted(set(target['phases'])|set(value['phases']))
    merged['ankle_housing_exception']=dict(merged['ankle_housing_exception'],
        maximum_observed_radius_m=max(r['ankle_housing_exception']['maximum_observed_radius_m'] for r in self_reports),
        pair_samples=sum(r['ankle_housing_exception']['pair_samples'] for r in self_reports))
    dest=folder/'self_review_partitions';dest.mkdir()
    partitions=[]
    for i,(r,report) in enumerate(zip(shard_records,self_reports)):
        assert report['samples']==r['exclusive_last_frame']-r['first_frame']
        shutil.copy2(r['path']/'self_contact_review.json',dest/(str(i)+'.json'))
        shutil.copy2(r['path']/'run.log',dest/(str(i)+'.log'))
        partitions.append(dict(first_frame=r['first_frame'],exclusive_last_frame=r['exclusive_last_frame'],
                               compressed_input_sha256=sha(r['path']/'frames.jsonl.gz'),report_sha256=sha(dest/(str(i)+'.json'))))
    merged['independent_frame_partitions']=partitions;merged['frames_sha256']=export['frames_sha256']
    merged['partitioner_sha256']=pins['review_measurement_episode.py']
    (folder/'self_contact_review.json').write_text(json.dumps(merged,indent=2)+'\n')
    assert all(sha(HERE/n)==v for n,v in pins.items()),'Reviewer changed during execution'
    (folder/'verifier_sources.json').write_text(json.dumps(pins,indent=2)+'\n')
    # Original ordered frames are retained; these are redundant temporary shards.
    shutil.rmtree(temporary)


def review(folder):
    names=['export.json','geometry_review.json','self_contact_review.json','motion_review.json',
           'optical_exchange_review.json','reference_clearance_review.json','ftir_mechanism_review.json']
    export,geometry,self_contact,motion,optical,reference,mechanism=[json.loads((folder/n).read_text()) for n in names]
    assert export['episode']=='ftir_measurement' and export['sample_step_s']<=.1
    config=json.loads((folder/'source/single_measurement_episode.json').read_text())
    for name,digest in export['source_sha256'].items():assert sha(folder/'source'/name)==digest,name
    assert sha(folder/'frames.jsonl.gz')==export['compressed_frames_sha256']
    assert geometry['frames_sha256']==optical['frames_sha256']==mechanism['frames_sha256']==export['frames_sha256']
    assert geometry['frames']==motion['frames']==self_contact['samples']==optical['samples']==reference['samples']==mechanism['samples']==export['frame_count']
    complete=set(export['selected_phases'])=={s['id'] for s in config['segments']} and not optical['missing_phases']
    # Match the exact robot/environment review's 10 micrometre sole-plane
    # tolerance for serialized source meshes; retain the actual signed value.
    sole_clear=motion['minimum_sole_z_m']>=-1e-5
    passed=complete and sole_clear and geometry['frames_with_nonfloor_intersections']==0 and all(r['passed'] for r in [self_contact,motion,optical,reference,mechanism])
    result=dict(passed=passed,scope=__doc__,episode='ftir_measurement',covers_entire_episode=complete,
        duration_s=export['scene']['duration'],frames=export['frame_count'],sample_step_s=export['sample_step_s'],
        every_video_frame='capture_frame_alignment' in export,phases=export['selected_phases'],
        initial_conditions=config['initial_conditions'],final_conditions=config['final_conditions'],
        robot_environment_intersection_frames=geometry['frames_with_nonfloor_intersections'],
        self_intersection_frames=len(self_contact['intersection_frames']),
        tool_specimen_intersection_frames=len(optical['intersection_frames']),
        reference_intersection_frames=len(reference['intersection_frames']),
        mechanism_intersection_frames=len(mechanism['intersection_frames']),
        contact_failures=len(mechanism['contact_failures']),acquisition_sequence_failures=len(mechanism['acquisition_sequence_failures']),
        acquisition_order=mechanism['acquisition_order'],maximum_grip_gaps_m=mechanism['maximum_grip_gaps_m'],
        minimum_sole_z_m=motion['minimum_sole_z_m'],sole_clear=sole_clear,
        source_sha256=export['source_sha256'],
        evidence_sha256={n:sha(folder/n) for n in names+['frames.jsonl.gz','verifier_sources.json']},
        verifier_sha256=sha(Path(__file__)),physics_qualified=False,full_paper_complete=False)
    (folder/'sampled_interaction_review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['passed','duration_s','frames','every_video_frame','robot_environment_intersection_frames','mechanism_intersection_frames','contact_failures','minimum_sole_z_m']}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder');parser.add_argument('--run',action='store_true');parser.add_argument('--self-workers',type=int,default=6)
    args=parser.parse_args();folder=Path(args.folder).resolve()
    if args.run:run_reviews(folder,args.self_workers)
    review(folder)
