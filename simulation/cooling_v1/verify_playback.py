"""Check chapter bytes, media clocks and binding to independently checked states."""
import argparse
import json
from pathlib import Path
import subprocess
from trace_store import sha,load_trace


def verify(directory):
    directory=Path(directory);manifest=json.loads((directory/'playback_manifest.json').read_text());checks=[]
    def check(name,passed,**details):checks.append(dict(name=name,passed=bool(passed),**details))
    for name,digest in manifest['input_sha256'].items():
        if name=='physics_trace.npz':load_trace(directory,digest)
        else:check('input_'+name,sha(directory/name)==digest)
    record=json.loads((directory/'result.json').read_text());verification=json.loads((directory/'verification.json').read_text())
    check('verified_exact_episode',record['status']=='passed' and verification['passed'] and verification['result_sha256']==sha(directory/'result.json'))
    check('recorded_state_presentation',manifest['presentation_only'] and not manifest['payload_interpolation'] and not manifest['whole_paper_validated'])
    elapsed=0.;frames=0
    for row in manifest['chapters']:
        path=directory/row['path']
        if not path.resolve().is_relative_to(directory.resolve()):raise ValueError('Nonlocal playback path')
        check(row['path']+'_bytes',sha(path)==row['sha256'] and path.stat().st_size==row['bytes'])
        metadata=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]));stream=metadata['streams'][0]
        duration=float(stream['duration']);count=int(stream['nb_frames'])
        check(row['path']+'_clock',abs(row['start_s']-elapsed)<1e-6 and abs(duration-row['duration_s'])<.001 and count==row['frames'] and stream['width']==1120 and stream['height']==800,
              duration_s=duration,frames=count)
        elapsed=row['end_s'];frames+=count
    check('complete_episode_clock',frames==manifest['frames'] and abs(elapsed-manifest['trace_seconds'])<=1/manifest['fps']+.001 and abs(record['simulated_seconds']-manifest['trace_seconds'])<.01,
          video_seconds=elapsed,trace_seconds=manifest['trace_seconds'],chapters=len(manifest['chapters']))
    report=dict(passed=all(c['passed'] for c in checks),checks=checks,manifest_sha256=sha(directory/'playback_manifest.json'),verifier_sha256=sha(Path(__file__)),
                scope='Media integrity and clock coverage only; original physical verification remains separate',whole_paper_validated=False)
    (directory/'playback_verification.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory');args=parser.parse_args();report=verify(args.directory)
    print(json.dumps(dict(passed=report['passed'],checks=len(report['checks']),failed=[c for c in report['checks'] if not c['passed']]),indent=2));raise SystemExit(0 if report['passed'] else 1)
