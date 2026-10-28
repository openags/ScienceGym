"""Pixel-level regression for the missing-normal shadow failure.

Append a test-only hook to the exact local module through Playwright routing.
The production module, physical placements and lighting are not rewritten.
Compare the complete scene with receiver shadows enabled/disabled, then restore
the production setting. This checks rendering, not measured material fidelity.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(browser,url):
    source=(HERE/'main.js').read_text()
    hook='\nwindow.renderProbe={THREE,renderer,scene,camera,architecture,groups,requestRender};'
    records=[];checks=[]
    def check(name,passed,**data):
        checks.append(dict(name=name,passed=bool(passed),**data))
        if not passed:raise AssertionError(name)
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=b.new_page(viewport={'width':1600,'height':1100},device_scale_factor=1)
        page.set_default_timeout(60000)
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.route('**/lab_review_v1/main.js',lambda route:route.fulfill(status=200,content_type='application/javascript',body=source+hook))
        page.goto(url,wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.sceneLoaded === "true"',timeout=120000)
        batches=json.loads(page.locator('html').get_attribute('data-render-batches'))
        check('batch_geometry_preserved',all(b['sourceGeometryPreserved'] and b['boundsErrorM']<1e-5 for b in batches),before_meshes=sum(b['beforeMeshes'] for b in batches),after_meshes=sum(b['afterMeshes'] for b in batches))
        count=int(page.locator('html').get_attribute('data-normal-repairs'))
        check('absent_normals_recovered',count>0,mesh_count=count)
        data=page.evaluate('''()=>{const d=renderProbe;let missing=0,nonfinite=0,total=0;
          for(const group of [d.architecture,...d.groups.values()])group.traverse(o=>{if(!o.isMesh)return;total++;const normal=o.geometry.attributes.normal;if(!normal)missing++;else if(!normal.array.every(Number.isFinite))nonfinite++});return {total,missing,nonfinite}}''')
        check('all_scene_meshes_have_finite_normals',data['missing']==0 and data['nonfinite']==0,**data)
        def capture(name):
            page.wait_for_timeout(300)
            data=page.locator('#viewport').screenshot();path=HERE/'evidence'/(name+'.png');path.write_bytes(data)
            records.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
            return np.asarray(Image.open(io.BytesIO(data)).convert('RGB'),dtype=np.int16)
        with_shadows=capture('receiver_shadows_on')
        # Disable receiving only, leaving lights, cast depth maps and materials
        # untouched. A colour difference therefore measures shadow reception.
        page.evaluate('''()=>{const d=renderProbe;d.scene.traverse(o=>{if(o.isMesh){o.userData.probeReceiveShadow=o.receiveShadow;o.receiveShadow=false}});d.requestRender()}''')
        without_shadows=capture('receiver_shadows_off')
        changed=np.max(np.abs(with_shadows-without_shadows),axis=2)>12
        # The lower portion contains table legs, robot feet and floor. Isolate
        # it from ceiling/sign contrast to catch the original floating effect.
        lower=changed[int(changed.shape[0]*.52):,:]
        check('receiver_shadows_visible_on_floor_and_supports',lower.sum()>1000,changed_pixels=int(lower.sum()),threshold_per_channel=12)
        page.evaluate('''()=>{const d=renderProbe;d.scene.traverse(o=>{if(o.isMesh)o.receiveShadow=o.userData.probeReceiveShadow});d.requestRender()}''')
        restored=capture('receiver_shadows_restored')
        check('rendering_restored_after_probe',np.max(np.abs(restored-with_shadows))<=1)
        # MSAA previously corrupted the label even in otherwise unobstructed
        # oblique views. Its ordinary depth-tested rendering must agree with
        # the unobstructed reference, and still respect a foreground blocker.
        page.locator('#asset-select').select_option('coating_white_stock')
        page.locator('#isolate').check()
        page.evaluate('''()=>{const d=renderProbe;d.label=d.groups.get('coating_white_stock').getObjectByName('can_identification_text');}''')
        valid=capture('label_depth_valid')
        page.evaluate('()=>{const d=renderProbe;d.label.material.depthTest=false;d.label.renderOrder=100;d.requestRender()}')
        reference=capture('label_unobstructed_reference')
        check('label_depth_has_no_visible_interference',np.max(np.abs(valid-reference))<=1)
        page.evaluate('()=>{const d=renderProbe;d.label.material.depthTest=true;d.label.renderOrder=0;d.requestRender()}')
        page.evaluate('''()=>{const d=renderProbe,T=d.THREE;
          const center=new T.Box3().setFromObject(d.groups.get('coating_white_stock')).getCenter(new T.Vector3());
          const direction=d.camera.position.clone().sub(center).normalize();
          d.blocker=new T.Mesh(new T.PlaneGeometry(.16,.28),new T.MeshBasicMaterial({color:0xd02a90}));
          d.blocker.position.copy(center.addScaledVector(direction,.12));d.blocker.quaternion.copy(d.camera.quaternion);
          d.scene.add(d.blocker);d.requestRender()}''')
        blocked=capture('label_foreground_occlusion')
        page.evaluate('()=>{const d=renderProbe;d.label.visible=false;d.requestRender()}')
        hidden=capture('label_hidden_behind_foreground')
        check('foreground_blocks_label',np.max(np.abs(blocked-hidden))<=1)
        page.evaluate('()=>{const d=renderProbe;d.label.visible=true;d.label.material.depthTest=false;d.label.renderOrder=100;d.requestRender()}')
        invalid=capture('label_invalid_depth_disabled_fixture')
        check('disabled_depth_fixture_rejected',int((np.max(np.abs(invalid-blocked),axis=2)>12).sum())>100)
        page.evaluate('''()=>{const d=renderProbe;d.label.material.depthTest=true;d.label.renderOrder=0;
          d.blocker.removeFromParent();d.blocker.geometry.dispose();d.blocker.material.dispose();d.requestRender()}''')
        check('no_rendering_errors',not errors,errors=errors)
        render_config=page.evaluate('()=>({pixel_ratio:renderProbe.renderer.getPixelRatio(),context:renderProbe.renderer.getContext().getContextAttributes()})')
        version=b.version;b.close()
    files=[HERE/'main.js',HERE/'check_rendering.py',HERE/'render_batches.js',ROOT/'assets/cooling_lab_v1/scene.json',ROOT/'assets/cooling_lab_v1/room_details.py']
    report=dict(passed=True,checks=checks,captures=records,browser=version,renderer=render_config,
        source_files=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in files],
        test_hook_sha256=hashlib.sha256(hook.encode()).hexdigest(),
        scope='Receiver-shadow comparison, unobstructed label depth rendering and foreground occlusion with a rejected disabled-depth fixture; not photometric, product-fidelity or safety acceptance')
    (HERE/'RENDER_VERIFICATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(passed=True,checks=len(checks),changed_floor_pixels=int(lower.sum())),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--browser',required=True);p.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/index.html')
    args=p.parse_args();run(args.browser,args.url)
