"""Verify recorded fixture artifacts without granting whole-paper acceptance."""
import hashlib
import json
import subprocess
from pathlib import Path
import numpy as np
from recorded_source import recorded_source

HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    tests=json.loads((HERE/'physics_tests.json').read_text())
    assert tests['passed'] and tests['count']==18
    assert not tests['whole_paper_validated']
    for name,digest in tests['input_sha256'].items():assert sha(recorded_source(name,digest))==digest,name
    summaries=[]
    for scene in ['assembly','probe','lid','door']:
        root=HERE/'runs'/scene;result=json.loads((root/'result.json').read_text())
        assert result['scene']==scene and result['status']=='passed',scene
        assert result['evaluation']['passed']
        assert not result['whole_paper_validated']
        for name,digest in result['input_sha256'].items():
            assert sha(root/name if name=='workcell.xml' else recorded_source(name,digest))==digest,(scene,name)
        for name,digest in result['artifacts_sha256'].items():assert sha(root/name)==digest,(scene,name)
        assert 'execution.mp4' in result['artifacts_sha256']
        trace=np.load(root/'physics_trace.npz',allow_pickle=False)
        for name in trace.files:assert np.isfinite(trace[name]).all(),(scene,name)
        assert (np.diff(trace['time'])>0).all()
        assert abs(float(trace['time'][-1])-result['simulated_seconds'])<.022
        assert trace['ctrl'].shape[1]==8
        metadata=json.loads(subprocess.check_output(['ffprobe','-v','quiet','-show_format','-show_streams','-of','json',str(root/'execution.mp4')]))
        duration=float(metadata['format']['duration'])
        assert abs(duration-result['simulated_seconds'])<.2,(scene,duration,result['simulated_seconds'])
        assert metadata['streams'][0]['width']==1120
        summaries.append(dict(scene=scene,physics_steps=result['physics_steps'],duration_s=result['simulated_seconds'],trace_samples=len(trace['time'])))
    coverage=json.loads((HERE/'campaign_coverage.json').read_text())
    assert coverage['status']=='blocked' and not coverage['whole_paper_validated']
    assert coverage['required_manipulation_definitions']==200 and coverage['qualified_manipulation_definitions']==0
    report=dict(artifact_integrity_passed=True,fixture_regressions_passed=True,whole_paper_validated=False,scenes=summaries,
                verifier_sha256=sha(Path(__file__)),source_resolver_sha256=sha(HERE/'recorded_source.py'))
    (HERE/'EVIDENCE_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
