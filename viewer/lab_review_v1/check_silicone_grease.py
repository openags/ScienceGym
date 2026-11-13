"""Inspect container states and refuse mismatched geometry in Chromium."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from playwright.sync_api import sync_playwright
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(browser,url):
    checks=[];captures=[];errors=[]
    record=json.loads((ROOT/'assets/cooling_lab_v1/silicone_grease_assets.json').read_text())
    def check(name,passed):
        checks.append(dict(name=name,passed=bool(passed)))
        if not passed:raise AssertionError(name)
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=b.new_page(viewport={'width':1500,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(url,wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.greaseLoaded === "true"',timeout=120000)
        check('unaccepted_static_status','静态检查' in page.locator('#grease-status').inner_text() and '未验收' in page.locator('#grease-status').inner_text())
        for mode,views in {'closed':['oblique','front','back'],'open':['oblique','bottom'],'stock':['front'],'nozzle':['oblique','bottom']}.items():
            page.select_option('#grease-select',mode);data=page.evaluate('scienceGymGreaseInspection()')
            check('visible_parts_'+mode,data['selected']==mode and len(data['visible'])==({'stock':3,'nozzle':4}.get(mode,5)))
            expected={n:np.eye(4) for n in data['transforms']}
            if mode!='closed':
                for n in record['groups']['cap']:expected[n][:3,3]=record['inspection']['cap_translation_m']
            check('part_transforms_'+mode,all(np.allclose(np.array(m).reshape(4,4).T,expected[n],atol=1e-9) for n,m in data['transforms'].items()))
            check('no_operation_or_silicone_credit_'+mode,not data['robotUseQualified'] and not data['dispensingQualified'] and not data['siliconeRequirementSatisfied'])
            for view in views:
                page.locator('[data-view="'+view+'"]').click();page.wait_for_timeout(150)
                path=HERE/'evidence'/('silicone_grease_'+mode+'_'+view+'.png');page.locator('#lift-viewport').screenshot(path=str(path));captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
        page.select_option('#grease-select','stock');page.select_option('#density-select','sds_0_96')
        page.wait_for_function('scienceGymGreaseInspection().densityScenario === "sds_0_96"')
        data=page.evaluate('scienceGymGreaseInspection()')
        check('density_switch_keeps_one_85g_identity',data['nominalMassG']==85 and data['physicalIdentity']=='weather_silicone_grease_93003' and len(data['transforms'])==5)
        check('sds_larger_volume_visible','88.54 mL' in page.locator('#grease-note').inner_text() and len(data['visible'])==3)
        check('density_switch_preserves_open_cap_transform',all(np.allclose(np.array(data['transforms'][n]).reshape(4,4).T[:3,3],record['inspection']['cap_translation_m']) for n in record['groups']['cap']))
        page.locator('[data-view="front"]').click();page.wait_for_timeout(150)
        path=HERE/'evidence'/'silicone_grease_stock_sds_front.png';page.locator('#lift-viewport').screenshot(path=str(path));captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
        page.select_option('#density-select','tds_1_11');page.wait_for_function('scienceGymGreaseInspection().densityScenario === "tds_1_11"')
        check('tds_nominal_fill_restores','76.58 mL' in page.locator('#grease-note').inner_text())
        check('material_boundary_and_unknown_cable_compatibility_visible','硅橡胶门密封圈排除' in page.locator('main').inner_text() and '实际电缆护套' in page.locator('main').inner_text())
        check('no_browser_errors',not errors)
        page.set_viewport_size({'width':390,'height':844});check('mobile_page_fits',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        alternate=record['items'][1]['geometry']['path']
        page.route('**/'+alternate,lambda r:r.fulfill(status=200,content_type='model/gltf-binary',body=b'bad geometry'))
        page.reload(wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.greaseLoaded === "true"',timeout=120000)
        page.select_option('#density-select','sds_0_96');page.wait_for_function('document.documentElement.dataset.greaseLoaded === "error"',timeout=120000)
        check('tampered_alternate_fill_refused',page.locator('#lift-viewport canvas').count()==0 and '版本不匹配' in page.locator('#lift-error').inner_text())
        version=b.version;b.close()
    paths=[Path(__file__),HERE/'silicone_grease.html',HERE/'silicone_grease.js',HERE/'style.css',HERE/'lift.css']+[ROOT/'assets/cooling_lab_v1'/n for n in ['silicone_grease_assets.json','silicone_grease_checks.json']]
    report=dict(passed=True,checks=checks,captures=captures,browser=version,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in paths],
        scope='Static container and nominal stock inspection. No opening, dispensing, material compatibility or robot action.')
    (HERE/'SILICONE_GREASE_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,checks=len(checks),captures=len(captures))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--browser',required=True);p.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/silicone_grease.html');a=p.parse_args();run(a.browser,a.url)
