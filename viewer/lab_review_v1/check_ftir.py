"""Check the real mounting page against independently transformed mesh bounds."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
import trimesh
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'assets/cooling_lab_v1'))
from geometry_tools import sha,write_json,imported_scene


def run(browser,url):
    folder=ROOT/'assets/cooling_lab_v1';model=json.loads((folder/'ftir_mounts.json').read_text())
    source=(HERE/'ftir.js').read_text();hook='\nwindow.mountProbe={THREE,scene,renderer,camera,get instrument(){return instrument},get assembly(){return assembly},get meshes(){return meshes}};'
    checks=[];captures=[]
    def check(name,condition,**data):
        checks.append(dict(name=name,passed=bool(condition),**data))
        if not condition:raise AssertionError(name+': '+str(data))
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=b.new_page(viewport={'width':1550,'height':1100});page.set_default_timeout(60000);errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.route('**/lab_review_v1/ftir.js',lambda route:route.fulfill(status=200,content_type='application/javascript',body=source+hook))
        page.goto(url,wait_until='domcontentloaded');page.wait_for_function('["true","error"].includes(document.documentElement.dataset.mountLoaded)')
        check('page_loaded_without_initialization_error',page.locator('html').get_attribute('data-mount-loaded')=='true',error=page.locator('#mount-error').inner_text())
        def capture(identity,state):
            page.wait_for_timeout(150);path=HERE/'evidence'/('ftir_mount_'+identity+'_'+state+'.png')
            page.locator('#mount-viewport').screenshot(path=str(path));captures.append(dict(asset=identity,state=state,path=str(path.relative_to(ROOT)),sha256=sha(path)))
        def bounds(name):
            return np.array(page.evaluate('name=>{const d=mountProbe;d.scene.updateMatrixWorld(true);const o=d.meshes.get(name)||d.instrument.getObjectByName(name);const b=new d.THREE.Box3().setFromObject(o,true);return [b.min.toArray(),b.max.toArray()]}',name))
        for cfg in model['configurations']:
            identity=cfg['id'];page.select_option('#mount-select',identity)
            page.wait_for_function('id=>document.documentElement.dataset.mountAsset===id && document.documentElement.dataset.mountLoaded === "true"',arg=identity)
            scene=imported_scene(cfg['accessory_geometry']['path'],z_up=True)
            name='optical_base_slotted_plate' if identity=='harrick_hrs' else 'chassis_base';mesh=scene.geometry[name].copy();mesh.apply_translation(cfg['accessory_translation_m'])
            check(identity+'_actual_mesh_installation_transform',np.allclose(bounds('accessory:'+name),mesh.bounds,atol=1e-7))
            count=page.evaluate('()=>mountProbe.meshes.size')
            check(identity+'_only_listed_loose_parts_removed',count==cfg['accessory_geometry']['parts']-len(cfg['excluded_loose_parts'])+cfg['hardware']['parts'],visible_assembly_meshes=count)
            check(identity+'_explicit_unaccepted_status','未验收' in page.locator('#mount-status').inner_text())
            if identity=='harrick_hrs':check('harrick_displays_ray_failure','60 mm' in page.locator('#mount-finding').inner_text())
            else:check('spectratech_displays_cover_failure','16 mm' in page.locator('#mount-finding').inner_text())
            for view in ['front','side','top']:
                page.click('#mount-views [data-view="'+view+'"]');capture(identity,view)
            page.click('#mount-views [data-view="front"]')
            for angle in [45,0]:
                page.locator('#mount-cover').fill(str(angle));page.locator('#mount-cover').dispatch_event('input')
                original=imported_scene(model['instrument']['path'],z_up=False).geometry['sample_bay_lid'].copy();cover=model['instrument_cover']
                original.apply_transform(trimesh.transformations.rotation_matrix(-np.radians(angle),cover['axis'],cover['pivot_m']))
                check(identity+'_cover_transform_'+str(angle),np.allclose(bounds('sample_bay_lid'),original.bounds,atol=1e-7))
            capture(identity,'closed')
            page.locator('#mount-cover').fill('90');page.locator('#mount-cover').dispatch_event('input')
            page.locator('#mount-lift').fill('180');page.locator('#mount-lift').dispatch_event('input')
            check(identity+'_lift_preserves_hardware_assembly',np.allclose(bounds('accessory:'+name),mesh.bounds+[0,0,.180],atol=1e-7))
            capture(identity,'lifted')
            page.locator('#mount-lift').fill('0');page.locator('#mount-lift').dispatch_event('input');page.locator('#mount-cutaway').uncheck()
            page.click('#mount-views [data-view="overview"]');capture(identity,'whole')
            hidden=page.evaluate('()=>mountProbe.instrument.children.filter(o=>!o.visible).length');check(identity+'_full_shell_restored',hidden==0)
            page.locator('#mount-cutaway').check()
        check('no_browser_errors',not errors,errors=errors)
        check('linked_primary_sources',page.locator('#mount-sources a').count()==3)
        # A stale result must not silently authorize or display a different mesh.
        corrupted=json.loads((folder/'ftir_mount_checks.json').read_text());corrupted['source_artifacts'][-1]['sha256']='0'*64
        page.route('**/ftir_mount_checks.json',lambda route:route.fulfill(status=200,content_type='application/json',body=json.dumps(corrupted)))
        page.reload();page.wait_for_function('document.documentElement.dataset.mountLoaded === "error"')
        check('stale_installation_report_rejected','版本不匹配' in page.locator('#mount-error').inner_text())
        b.close()
    files=[Path(__file__),HERE/'ftir.html',HERE/'ftir.js',HERE/'style.css',folder/'ftir_mounts.json',folder/'ftir_mount_checks.json',folder/'ftir_mount_sources.json']
    write_json(HERE/'FTIR_MOUNT_VERIFICATION.json',dict(passed=all(c['passed'] for c in checks),checks=checks,captures=captures,
        source_files=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in files],scope='Browser controls, exact mesh transforms and retained failure display only. No mounting, optics or manipulation qualification.'))
    print(json.dumps(dict(checks=len(checks),captures=len(captures),passed=True)))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--browser',required=True);parser.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/ftir.html');args=parser.parse_args();run(args.browser,args.url)
