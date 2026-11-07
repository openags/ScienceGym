"""Check rendered optical frames against MuJoCo and preserve inspection images."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import mujoco
from PIL import Image
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'assets/unitree_g1_inspire_v1'))
from kinematics import Robot
from audit import sha


def run(browser,url):
    robot=Robot();model=mujoco.MjModel.from_xml_path(str(ROOT/'assets/unitree_g1_inspire_v1/simulation/robot.xml'))
    rig=json.loads((ROOT/'assets/g1_sensor_rig_v1/rig.json').read_text());workspace=json.loads((ROOT/'assets/cooling_lab_v1/workspace_checks.json').read_text())
    hook='\nwindow.sensorProbe=()=>({metadata:sensors.metadata,rigVisible:sensors.group.visible,matrices:sensorRig.optics.map(o=>({id:o.id,matrix:sensors.opticalWorld(o.id).toArray()})),attachments:sensors.nodes.map(({attachment,node})=>{node.updateWorldMatrix(true,false);return {id:attachment.id,matrix:node.matrixWorld.toArray()}})});'
    hook += """
window.sensorDepthFixture=()=>{
 const sampleScene=new THREE.Scene(),sampleRobot=new THREE.Group(),canvas=document.createElement('canvas');sampleScene.add(sampleRobot);
 const profile=sensorRig.optics.find(o=>o.id==='head_depth').profile;
 const optical={id:'fixture_depth',parent_link:'fixture',parent_from_optical:[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],profile,channels:['depth'],label:'Fixture'};
 const sample=new SensorReview({renderer,scene:sampleScene,robot:sampleRobot,normalization:optical.parent_from_optical,rig:{attachments:[],optics:[optical]},hiddenGroups:[],canvas,status:document.createElement('p')});
 sample.update(new Map([['fixture',new THREE.Matrix4()]]));sample.depthMaterial.uniforms.displayRange.value=4;
 const plane=new THREE.Mesh(new THREE.PlaneGeometry(20,20),new THREE.MeshBasicMaterial());plane.position.z=1;sampleScene.add(plane);sample.capture('fixture_depth');
 const value=Array.from(canvas.getContext('2d').getImageData(640,360,1,1).data);
 plane.geometry.dispose();plane.material.dispose();sample.rgbTarget.dispose();sample.hdrTarget.dispose();sample.depthTarget.dispose();sample.depthMaterial.dispose();sample.outputMaterial.dispose();sample.outputScene.children[0].geometry.dispose();return value;
};
"""
    checks=[];captures=[];errors=[]
    def check(name,value,**data):
        checks.append(dict(name=name,passed=bool(value),**data))
        if not value:raise AssertionError(name)
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=b.new_page(viewport={'width':1440,'height':1000});page.set_default_timeout(60000)
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.route('**/lab_review_v1/main.js',lambda r:r.fulfill(status=200,content_type='application/javascript',body=(HERE/'main.js').read_text()+hook))
        page.goto(url,wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.sceneLoaded === "true"',timeout=120000)
        depth_pixel=page.evaluate('sensorDepthFixture()');check('one_metre_axial_depth_encodes_linearly',all(abs(v-64)<=1 for v in depth_pixel[:3]),pixel=depth_pixel)
        check('four_optical_views',page.locator('#sensor-buttons button').count()==4)
        check('unaccepted_rig_hidden_by_default',not page.locator('#show-sensor-rig').is_checked())
        page.select_option('#asset-select','g1')
        for identity in ['cary_front','cary_extension_base','bath_front']:
            result=next(t['result'] for t in workspace['targets'] if t['id']==identity)
            data=mujoco.MjData(model);data.qpos[:3]=result['base_position_m'];yaw=result['base_yaw_rad'];data.qpos[3:7]=[np.cos(yaw/2),0,0,np.sin(yaw/2)]
            for name,value in robot.resolve(result['joint_coordinates']).items():
                if robot.by_name[name]['type']=='revolute':data.qpos[model.joint(name).qposadr[0]]=value
            mujoco.mj_kinematics(model,data)
            page.locator(f'button[data-target="{identity}"]').click();probe=page.evaluate('sensorProbe()')
            for collection,actuals in [('optics',probe['matrices']),('attachments',probe['attachments'])]:
                for record in rig[collection]:
                    body=data.body(record['parent_link']);body_t=np.eye(4);body_t[:3,:3]=body.xmat.reshape(3,3);body_t[:3,3]=body.xpos
                    expected=body_t@record['parent_from_optical' if collection=='optics' else 'parent_from_geometry']
                    actual=np.array(next(r['matrix'] for r in actuals if r['id']==record['id'])).reshape(4,4).T
                    error=float(np.max(np.abs(actual-expected)));check(identity+'_'+record['id']+'_frame',error<1e-7,maximum_matrix_error=error)
            if identity=='cary_front':
                for optic in rig['optics']:
                    page.locator(f'button[data-sensor="{optic["id"]}"]').click()
                    check('fresh_'+optic['id'],page.locator('#sensor-canvas').get_attribute('data-stale')=='false')
                    path=HERE/'evidence'/('sensor_'+optic['id']+'.png');path.parent.mkdir(exist_ok=True)
                    import base64
                    path.write_bytes(base64.b64decode(page.locator('#sensor-canvas').evaluate("c=>c.toDataURL('image/png').split(',')[1]")))
                    pixels=np.asarray(Image.open(path).convert('RGB'));spread=float(pixels.std());check('nonempty_'+optic['id'],spread>3 and pixels.shape==(720,1280,3),pixel_standard_deviation=spread)
                    captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),metadata=page.evaluate('sensorProbe().metadata')))
                # Reviewer cutaway/isolation must not remove walls or instruments
                # from the optical image. Pose and candidate selection unchanged.
                page.locator('button[data-sensor="head_rgb"]').click();before=page.locator('#sensor-canvas').evaluate('c=>c.toDataURL()')
                page.locator('#show-walls').check();page.locator('#isolate').check()
                page.locator('button[data-sensor="head_rgb"]').click();after=page.locator('#sensor-canvas').evaluate('c=>c.toDataURL()')
                check('reviewer_visibility_does_not_erase_occluders',before==after)
                page.locator('#isolate').uncheck()
        check('changed_pose_marks_image_stale',page.locator('#sensor-canvas').get_attribute('data-stale')=='true')
        page.locator('#show-sensor-rig').check();check('candidate_overlay_toggle',page.evaluate('sensorProbe().rigVisible'))
        page.locator('#workspace-reset').click();check('reset_stales_image',page.locator('#sensor-canvas').get_attribute('data-stale')=='true')
        for side in ['left','right']:
            page.locator(f'button[data-wrist="{side}"]').click();page.locator('#viewport').scroll_into_view_if_needed();page.wait_for_timeout(400)
            path=HERE/'evidence'/('sensor_mount_'+side+'.png');page.locator('#viewport').screenshot(path=str(path));check('mount_view_'+side,page.locator('html').get_attribute('data-mount-view')==side and page.evaluate('sensorProbe().rigVisible'))
            captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),kind='unaccepted_mount_candidate_closeup'))
        check('no_browser_errors',not errors,errors=errors);b.close()
    files=[Path(__file__),HERE/'main.js',HERE/'sensors.js',HERE/'index.html',ROOT/'assets/g1_sensor_rig_v1/rig.json',ROOT/'assets/g1_sensor_rig_v1/fit_checks.json',ROOT/'assets/cooling_lab_v1/workspace_checks.json',ROOT/'assets/cooling_lab_v1/scene.json',ROOT/'assets/unitree_g1_inspire_v1/simulation/robot.xml']
    out=dict(passed=True,checks=checks,captures=captures,source_files=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in files],test_hook_sha256=hashlib.sha256(hook.encode()).hexdigest(),scope='Independent frame matching, nonempty ideal geometric images and occluder preservation; candidate wrist mounting remains unqualified. No optical realism or controller success claim.')
    (HERE/'SENSOR_VERIFICATION.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(passed=True,checks=len(checks),captures=len(captures))))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--browser',required=True);p.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/index.html');a=p.parse_args();run(a.browser,a.url)
