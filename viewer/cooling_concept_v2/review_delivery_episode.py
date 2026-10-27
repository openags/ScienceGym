"""Combine newly checked delivery states with verified unchanged exchange states.

The prefix requires its own full-scene checks. Prior suffix evidence is reused
only after source and every recorded renderer state match inside the extended
episode. This grants sampled geometric coverage, not a completed paper demo.
"""
import argparse,hashlib,json
from pathlib import Path


def review(prefix,suffix,out):
    prefix,suffix,out=map(Path,[prefix,suffix,out]);out.mkdir(parents=True,exist_ok=True)
    p=json.loads((prefix/'sampled_interaction_review.json').read_text());s=json.loads((suffix/'suffix_equivalence.json').read_text())
    export=json.loads((prefix/'export.json').read_text());config=json.loads((prefix/'source/optical_delivery_episode.json').read_text())
    assert p['passed'] and s['passed'] and config['continuous_at_segment_boundaries']
    for name,sha in p['evidence_sha256'].items():assert hashlib.sha256((prefix/name).read_bytes()).hexdigest()==sha,name
    for name,sha in s['source_sha256'].items():
        if name=='verify_delivery_suffix.py':assert hashlib.sha256((suffix/name).read_bytes()).hexdigest()==sha
        else:assert export['source_sha256'][name]==sha,name
    covered=set(p['phases'])|set(s['phases']);expected={segment['id'] for segment in config['segments']};assert covered==expected,(expected-covered,covered-expected)
    paths={'prefix_review':prefix/'sampled_interaction_review.json','suffix_equivalence':suffix/'suffix_equivalence.json'}
    result=dict(passed=True,scope=__doc__,duration_s=config['duration_s'],delivery_duration_s=config['delivery_duration_s'],segments=len(expected),newly_reviewed_prefix_states=p['frames'],reused_suffix_states=s['frames'],state_count_note='Counts describe two review sets, with overlap at the handoff; they are not summed as unique states.',prefix_sample_step_s=p['sample_step_s'],suffix_maximum_state_difference=s['maximum_numeric_difference'],initial_conditions=config['initial_conditions'],source_sha256=export['source_sha256'],evidence={name:dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for name,path in paths.items()},verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (out/'composed_review.json').write_text(json.dumps(result,indent=2)+'\n');(out/'review_delivery_episode.py').write_bytes(Path(__file__).read_bytes());print(json.dumps({k:result[k] for k in ['passed','duration_s','segments','newly_reviewed_prefix_states','reused_suffix_states']}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('prefix');parser.add_argument('suffix');parser.add_argument('out');args=parser.parse_args();review(args.prefix,args.suffix,args.out)
