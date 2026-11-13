"""Fit a known unposed tool mesh to a retained sensor-only point component."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
import trimesh

from tool_pose import ToolPose


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run(observation, shape, output):
    observation,shape,output=map(lambda p:Path(p).resolve(),[observation,shape,output])
    result=json.loads((observation/'detector_output.json').read_text())
    if not result['candidate_found']:raise ValueError('No detected tool component')
    output.mkdir(parents=True,exist_ok=False)
    for n in [Path(__file__).name,'tool_pose.py']:
        shutil.copyfile(Path(__file__).parent/n,output/n)
    shutil.copyfile(observation/'component_points.npy',output/'component_points.npy')
    mesh=trimesh.load(shape,force='scene',process=False).to_geometry()
    pose=ToolPose(mesh.vertices,mesh.faces).estimate(np.load(output/'component_points.npy'))
    (output/'pose.json').write_text(json.dumps(pose,indent=2)+'\n')
    inputs=dict(scope=__doc__,shape_path=str(shape),shape_sha256=sha(shape),
        source_detector_inputs={p.name:sha(p) for p in (observation/'detector_inputs').iterdir()},
        detector_output_sha256=sha(observation/'detector_output.json'),component_sha256=sha(output/'component_points.npy'),
        appearance_threshold_uint8=result['appearance_threshold_uint8'],
        pose_estimator_sha256=sha(output/'tool_pose.py'),producer_sha256=sha(__file__),qualified_perception=False)
    (output/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
    print(json.dumps({k:v for k,v in pose.items() if k!='hypotheses'}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('observation');p.add_argument('shape');p.add_argument('output')
    a=p.parse_args();run(a.observation,a.shape,a.output)
