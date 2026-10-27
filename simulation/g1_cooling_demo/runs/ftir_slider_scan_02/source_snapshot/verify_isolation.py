"""Audit the actor bundle and actively reject a forbidden sensor-packet field."""
import argparse
import hashlib
import json
from pathlib import Path
import pickle
import subprocess
import sys

import mujoco
import numpy as np
from isolation import namespace_prefix


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(folder):
    folder = Path(folder).resolve()
    result = json.loads((folder/'result.json').read_text())
    receipt = json.loads((folder/'actor_isolation.json').read_text())
    checks = []
    def check(name, value, **details):
        checks.append(dict(name=name, passed=bool(value), **details))
    check('recorded_isolated_execution', result['actor_access_isolated'] and
          result['actor_isolation_sha256'] == sha(folder/'actor_isolation.json') and
          sha(folder/'source_snapshot/isolation.py') == receipt['isolation_source_sha256'])
    check('active_namespace_denial_probes', receipt['passed'] and
          all(receipt['forbidden_paths_blocked'].values()) and all(receipt['inputs_readonly'].values())
          and all(receipt['namespace_separation'].values()) and receipt['effective_capabilities']==0)
    code = folder/'actor_bundle/code'
    check('exact_actor_code_without_plant_or_evaluator',
          set(p.name for p in code.iterdir()) == set(receipt['source_modules']) and
          'world.py' not in receipt['source_modules'] and
          all(sha(code/name)==digest for name,digest in receipt['source_modules'].items()))
    check('bundled_model_matches_probe', sha(folder/'actor_bundle/model/world.xml') == receipt['bundled_model_sha256']
          and sha(folder/'controller_model/world.xml') == receipt['source_model_sha256'])
    check('bundled_meshes_and_textures_pinned', all(sha(folder/r['path'])==r['sha256'] for r in receipt['input_files']),
          files=len(receipt['input_files']))
    model = mujoco.MjModel.from_xml_path(str(folder/'actor_bundle/model/world.xml'))
    names = {model.body(i).name for i in range(model.nbody)}
    check('no_handled_object_in_actor_model', not names.intersection({'carrier_tray','buerkle_spatula','calibration_copper_stock'})
          and sum(model.jnt_type==mujoco.mjtJoint.mjJNT_FREE)==1)
    # This is a new, independent actor process. It never controls the recorded
    # plant and cannot modify the completed episode. Malformed packet content
    # is synthetic, not hidden ground truth from an experiment.
    prefix = namespace_prefix(code, folder/'actor_bundle/model')
    entry_point = result.get('actor_entry_point') or ('walking_actor.py' if 'walking_actor.py' in receipt['source_modules'] else 'actor_feedback.py')
    if entry_point not in receipt['source_modules']:
        raise ValueError('Recorded actor entry point is not in the pinned bundle')
    command = prefix + [sys.executable,'/actor/'+entry_point,'--model','/model/world.xml']
    ftir_actor=entry_point in {'ftir_actor.py','ftir_cover_actor.py','ftir_slider_scan_actor.py'}
    if ftir_actor:
        from depth_io import load as load_depth
        recorded=np.load(folder/'sensor_observations.npz')
        packet={k:recorded[k][0] for k in recorded.files}
        packet['depth']=next(load_depth(folder))[1]
        colors=json.loads((folder/'head_rgb_index.json').read_text())
        packet['rgb']=np.load(folder/colors['chunks'][0]['path'])['rgb'][0]
        baseline=subprocess.Popen(command,env=receipt['environment'],stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
        baseline_out,baseline_err=baseline.communicate(pickle.dumps(packet,protocol=5),timeout=60)
        baseline_response=pickle.loads(baseline_out)
        check('valid_recorded_rgbd_packet_accepted',baseline.returncode==0 and baseline_response.get('error') is None
              and np.shape(baseline_response.get('torque'))==(model.nu,) and np.isfinite(baseline_response['torque']).all(),
              stderr=baseline_err.decode(errors='replace'))
        check('no_instrument_state_in_actor_model',not any(n.startswith(('nicolet_','lab_nicolet')) for n in names))
        packet['simulator_object_pose']='deliberately_forbidden_synthetic_field'
    else:
        packet = dict(time_s=0., joint_position=np.zeros(53), joint_velocity=np.zeros(53),
                      imu_quaternion=np.array([1.,0.,0.,0.]), imu_gyro=np.zeros(3), depth=None,
                      simulator_object_pose='deliberately_forbidden_synthetic_field')
    process = subprocess.Popen(command, env=receipt['environment'], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    stdout, stderr = process.communicate(pickle.dumps(packet, protocol=5), timeout=60)
    try:
        response = pickle.loads(stdout)
    except Exception as error:
        response = dict(error='Invalid actor response: '+str(error))
    expected_error='Non-sensor field in FTIR actor input' if ftir_actor else 'Non-sensor field in actor input'
    rejection = bool(process.returncode==0 and response.get('error')==expected_error
                     and np.array_equal(response.get('torque'), np.zeros(model.nu)))
    check('forbidden_packet_rejected_before_control', rejection, error=response.get('error'),
          process_returncode=process.returncode, stderr=stderr.decode(errors='replace'))
    report = dict(passed=all(c['passed'] for c in checks), checks=checks,
                  verifier_sha256=sha(__file__), isolation_receipt_sha256=sha(folder/'actor_isolation.json'),
                  probe_command_prefix=prefix,
                  tested_actor_entry_point=entry_point,
                  scope='Observed access controls and packet rejection for this actor bundle; not a security audit of the kernel/GPU or sensor calibration')
    (folder/'isolation_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('folder'); args = parser.parse_args()
    if not verify(args.folder)['passed']:
        raise SystemExit(1)
