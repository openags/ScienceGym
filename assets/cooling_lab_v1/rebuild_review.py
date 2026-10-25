"""Rebuild the exact asset review in dependency order; never grant acceptance."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]

def run(script,*args):
    subprocess.run([sys.executable,script,*args],cwd=ROOT,env={**os.environ,'OPENBLAS_NUM_THREADS':'1'},check=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--browser');parser.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/index.html')
    a=parser.parse_args()
    for script in ['assets/unitree_g1_inspire_v1/audit.py',
      'assets/unitree_g1_inspire_v1/build_integration.py','assets/unitree_g1_inspire_v1/check_space.py',
      'assets/unitree_dex5s_reconstruction_v1/build.py',
      'assets/unitree_dex5s_reconstruction_v1/validate.py',
      'assets/realsense_cameras_v1/build.py','assets/realsense_cameras_v1/validate.py',
      'assets/g1_sensor_rig_v1/convert_mounts.py','assets/g1_sensor_rig_v1/build_adapters.py','assets/g1_sensor_rig_v1/build.py','assets/g1_sensor_rig_v1/check_clocking.py',
      'assets/omega_5tc_v1/build.py','assets/omega_5tc_v1/validate.py',
      'assets/cooling_lab_v1/check_hand_envelope.py',
      'assets/cooling_lab_v1/build_ordinary_tools.py','assets/cooling_lab_v1/build_supplies.py','assets/cooling_lab_v1/check_supplies.py','assets/cooling_lab_v1/build_waterjet.py',
      'assets/cooling_lab_v1/build_angular_accessories.py','assets/cooling_lab_v1/check_angular_accessories.py',
      'assets/cooling_lab_v1/build_ftir_mounts.py','assets/cooling_lab_v1/check_ftir_mounts.py','assets/cooling_lab_v1/build_lab.py',
      'assets/cooling_lab_v1/check_layout.py','assets/cooling_lab_v1/check_workspace.py','assets/g1_sensor_rig_v1/check_fit.py','assets/cooling_lab_v1/build_review.py',
      'assets/cooling_lab_v1/validate_review.py','assets/cooling_lab_v1/test_pilot_contract.py']:
        run(script)
    if a.browser:
        for script in ['viewer/lab_review_v1/check_browser.py','viewer/lab_review_v1/check_rendering.py','viewer/lab_review_v1/check_pose_projection.py','viewer/lab_review_v1/check_sensors.py']:
            run(script,'--browser',a.browser,'--url',a.url)
        run('assets/cooling_lab_v1/build_preparation_review.py')
        run('assets/cooling_lab_v1/build_angular_review.py')
        run('viewer/lab_review_v1/check_ftir.py','--browser',a.browser,'--url',a.url.rsplit('/',1)[0]+'/ftir.html')
    print('Asset-review candidate rebuilt. Owner acceptance and all humanoid execution gates remain open.')

if __name__=='__main__':main()
