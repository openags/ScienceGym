"""Evaluate sensor-only leg odometry against a completed, retained trace."""
import argparse
import hashlib
import json
from pathlib import Path
import mujoco
import numpy as np
from odometry import LegOdometry


def evaluate(folder,output):
    folder=Path(folder);sensor=dict(np.load(folder/'sensor_observations.npz'));truth=dict(np.load(folder/'trace.npz'))
    m=mujoco.MjModel.from_xml_path(str(folder/'controller_model/world.xml'));d=mujoco.MjData(m)
    # This prior is declared initial staging, supplied once before observations.
    prior=json.loads((folder/'staging.json').read_text())['initial_qpos'][:2]
    estimate=LegOdometry(m,d,prior);positions=[]
    for i in range(len(sensor['time_s'])):
        packet={k:sensor[k][i] for k in ['time_s','joint_position','joint_velocity','imu_quaternion','imu_gyro']};packet['depth']=None
        positions.append(estimate.update(packet))
    positions=np.asarray(positions)
    # Ground truth appears only here, after all estimates have been generated.
    indices=np.searchsorted(truth['time'],sensor['time_s'])
    error=positions-truth['qpos'][indices,:3]
    report=dict(source='Encoder/IMU lower-sole anchoring with a declared initial map pose',
                initial_map_xy_prior_m=prior,samples=len(positions),stance_switches=len(estimate.switches),
                maximum_xy_error_m=float(np.linalg.norm(error[:,:2],axis=1).max()),
                final_xyz_error_m=error[-1].tolist(),maximum_z_error_m=float(abs(error[:,2]).max()),
                odometry_sha256=hashlib.sha256(Path(__file__).with_name('odometry.py').read_bytes()).hexdigest(),
                evaluator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                navigation_qualified=False,limitations=['Known initial map placement and level floor','Lower sole is inferred support, without contact measurement or slip recovery'])
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    Path(output).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report));return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder');parser.add_argument('output');args=parser.parse_args();evaluate(args.folder,args.output)
