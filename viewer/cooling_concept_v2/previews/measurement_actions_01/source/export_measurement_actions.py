"""Freeze reusable endpoints from the established laboratory action solvers."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from export_audit import BROWSER, HERE

INSTALL = '''
const {createMeasurementSourceActions}=await import('./measurement_source_actions.js');
window.measurementSourceActions=createMeasurementSourceActions({phases,robotAt,
 constrainHands,jointPose,ftirCoverAngle,referenceAt,referenceTransfer,handIK});
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trial', default='01')
    args = parser.parse_args()
    out = HERE / 'previews' / ('measurement_actions_' + args.trial)
    out.mkdir(exist_ok=False)
    names = ['export_measurement_actions.py', 'measurement_source_actions.js', 'main.js', 'hand_ik.js',
             'reference_motion.js', 'reference_transfer.json', 'motion_poses.json', 'grasp_profile.json',
             'optical_setup.json', 'optical_approach_paths.json', 'manipulation_motion.js',
             'manipulation_approach_paths.json', 'lid_contact_paths.json', 'runtime_scene.json']
    pins = {}
    for name in names:
        data = (HERE / name).read_bytes()
        path = out / 'source' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        pins[name] = hashlib.sha256(data).hexdigest()
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=BROWSER, args=['--no-sandbox', '--disable-dev-shm-usage',
            '--enable-gpu', '--use-gl=angle', '--use-angle=vulkan', '--ignore-gpu-blocklist'],
            env={**os.environ, 'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
        page = browser.new_page(viewport={'width':1280, 'height':720})
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.route('**/cooling_concept_v2/main.js', lambda route: route.fulfill(status=200,
            content_type='application/javascript', body=(HERE / 'main.js').read_text()+INSTALL))
        page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean', timeout=120000)
        page.wait_for_function('window.measurementSourceActions?.descriptions', timeout=120000)
        actions = page.evaluate('measurementSourceActions.descriptions')
        assert not errors, errors
        browser.close()
    assert all(hashlib.sha256((HERE/n).read_bytes()).hexdigest()==sha for n,sha in pins.items())
    report = dict(scope=__doc__, actions=actions, source_sha256=pins,
                  limitations=['Endpoint export is not a composed trajectory or an independent geometry review.'])
    (out / 'actions.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({n:dict(duration_s=v['duration_s'],first_root=v['first']['root'],last_root=v['last']['root'])
                      for n,v in actions.items()}), flush=True)


if __name__ == '__main__':
    main()
