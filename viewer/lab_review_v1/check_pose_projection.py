"""Compare displayed mesh transforms to independent MuJoCo body frames."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
import mujoco
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'assets/unitree_g1_inspire_v1'))
from kinematics import Robot
from audit import sha


def run(browser,url):
    robot=Robot();model=mujoco.MjModel.from_xml_path(str(ROOT/'assets/unitree_g1_inspire_v1/simulation/robot.xml'))
    workspace=json.loads((ROOT/'assets/cooling_lab_v1/workspace_checks.json').read_text())
    hook='\nwindow.poseProbe=()=>{scene.updateMatrixWorld(true);return robotRest.map(x=>({name:x.node.name,matrix:x.node.matrixWorld.toArray()}))};'
    results=[]
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=b.new_page();page.set_default_timeout(60000)
        page.route('**/lab_review_v1/main.js',lambda r:r.fulfill(status=200,content_type='application/javascript',body=(HERE/'main.js').read_text()+hook))
        page.goto(url,wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.sceneLoaded === "true"',timeout=120000)
        rest=page.evaluate('poseProbe()')
        for identity in ['cary_front','cary_extension_base','nicolet_auxiliary']:
            result=next(t['result'] for t in workspace['targets'] if t['id']==identity)
            data=mujoco.MjData(model);data.qpos[:3]=result['base_position_m'];yaw=result['base_yaw_rad'];data.qpos[3:7]=[np.cos(yaw/2),0,0,np.sin(yaw/2)]
            for name,value in robot.resolve(result['joint_coordinates']).items():
                if robot.by_name[name]['type']=='revolute':data.qpos[model.joint(name).qposadr[0]]=value
            mujoco.mj_kinematics(model,data)
            page.locator(f'button[data-target="{identity}"]').click()
            actual=page.evaluate('poseProbe()');errors=[]
            for mesh in actual:
                name=mesh['name'].rsplit('_visual_',1)[0];body=data.body(name)
                transform=np.eye(4);transform[:3,:3]=body.xmat.reshape(3,3);transform[:3,3]=body.xpos
                # build_lab.imported_scene bakes the source bind transform into
                # vertices. The displayed node therefore carries a bind delta,
                # not the absolute original visual-link frame.
                expected=transform@np.linalg.inv(robot.bind[name])
                errors.append(float(np.max(np.abs(np.array(mesh['matrix']).reshape(4,4).T-expected))))
            assert len(errors)==93 and max(errors)<1e-6,(identity,max(errors))
            results.append(dict(target=identity,meshes=len(errors),max_matrix_error=max(errors)))
        page.locator('#workspace-reset').click();restored=page.evaluate('poseProbe()')
        reset_error=max(np.max(np.abs(np.array(a['matrix'])-c['matrix'])) for a,c in zip(rest,restored))
        assert reset_error<1e-9
        b.close()
    files=[Path(__file__),HERE/'main.js',ROOT/'assets/cooling_lab_v1/workspace_checks.json',ROOT/'assets/cooling_lab_v1/scene.json',ROOT/'assets/unitree_g1_inspire_v1/simulation/robot.xml']
    report=dict(passed=True,poses=results,reset_matrix_error=float(reset_error),test_hook_sha256=__import__('hashlib').sha256(hook.encode()).hexdigest(),
      source_files=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in files],scope='Displayed mesh frames match independent MuJoCo kinematics, including the revised low mounting approach; no motion execution credit')
    (HERE/'POSE_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,poses=len(results),meshes_per_pose=93)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--browser',required=True);p.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/index.html');a=p.parse_args();run(a.browser,a.url)
