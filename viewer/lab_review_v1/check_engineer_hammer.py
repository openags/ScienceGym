"""Inspect the original hammer, actual eye and inferred internal domains."""
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
    record=json.loads((ROOT/'assets/cooling_lab_v1/engineer_hammer_assets.json').read_text())
    geometry=json.loads((ROOT/'assets/cooling_lab_v1/engineer_hammer_checks.json').read_text())
    def check(name,passed):
        checks.append(dict(name=name,passed=bool(passed)))
        if not passed:raise AssertionError(name)
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=b.new_page(viewport={'width':1500,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(url,wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.hammerLoaded === "true"',timeout=120000)
        check('unaccepted_static_status','静态检查' in page.locator('#hammer-status').inner_text() and '未验收' in page.locator('#hammer-status').inner_text())
        modes={'assembled':['front','back','top'],'head':['front','top','eye'],'internal':['front','eye']}
        for mode,views in modes.items():
            page.select_option('#hammer-select',mode);data=page.evaluate('scienceGymHammerInspection()')
            expected=record['geometry']['parts'] if mode=='assembled' else 3 if mode=='head' else 2
            check('visible_parts_'+mode,data['selected']==mode and len(data['visible'])==expected)
            check('source_transform_'+mode,np.allclose(np.array(data['transform']).reshape(4,4).T,geometry['resting_reference']['to_support_plane'],atol=1e-9) and all(np.allclose(np.array(m).reshape(4,4).T,np.eye(4),atol=1e-9) for m in data['partTransforms'].values()))
            check('no_operation_credit_'+mode,not data['robotUseQualified'] and not data['impactQualified'] and data['ownerAcceptance'] is None)
            for view in views:
                page.locator('[data-view="'+view+'"]').click();page.wait_for_timeout(150)
                path=HERE/'evidence'/('engineer_hammer_'+mode+'_'+view+'.png');page.locator('#lift-viewport').screenshot(path=str(path));captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
        check('no_browser_errors',not errors)
        page.set_viewport_size({'width':390,'height':844});check('mobile_page_fits',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        record['geometry']['sha256']='0'*64
        page.route('**/assets/cooling_lab_v1/engineer_hammer_assets.json',lambda route:route.fulfill(status=200,content_type='application/json',body=json.dumps(record)))
        page.reload(wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.hammerLoaded === "error"',timeout=120000)
        check('tampered_geometry_refused',page.locator('#lift-viewport canvas').count()==0)
        version=b.version;b.close()
    paths=[Path(__file__),HERE/'engineer_hammer.html',HERE/'engineer_hammer.js',HERE/'style.css',HERE/'lift.css']+[ROOT/'assets/cooling_lab_v1'/n for n in ['engineer_hammer_assets.json','engineer_hammer_checks.json']]
    report=dict(passed=True,checks=checks,captures=captures,browser=version,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in paths],
        scope='Static hammer, actual eye, inferred internal construction and actual resting transform. No impact, retention strength or robot action.')
    (HERE/'ENGINEER_HAMMER_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,checks=len(checks),captures=len(captures))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--browser',required=True);p.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/engineer_hammer.html');a=p.parse_args();run(a.browser,a.url)
