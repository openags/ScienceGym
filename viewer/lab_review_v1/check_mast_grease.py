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
    record=json.loads((ROOT/'assets/cooling_lab_v1/mast_grease_assets.json').read_text())
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
                path=HERE/'evidence'/('mast_grease_'+mode+'_'+view+'.png');page.locator('#lift-viewport').screenshot(path=str(path));captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
        check('no_browser_errors',not errors)
        page.set_viewport_size({'width':390,'height':844});check('mobile_page_fits',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        record['geometry']['sha256']='0'*64
        page.route('**/assets/cooling_lab_v1/mast_grease_assets.json',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps(record)))
        page.reload(wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.greaseLoaded === "error"',timeout=120000)
        check('tampered_geometry_refused',page.locator('#lift-viewport canvas').count()==0)
        version=b.version;b.close()
    paths=[Path(__file__),HERE/'mast_grease.html',HERE/'mast_grease.js',HERE/'style.css',HERE/'lift.css']+[ROOT/'assets/cooling_lab_v1'/n for n in ['mast_grease_assets.json','mast_grease_checks.json']]
    report=dict(passed=True,checks=checks,captures=captures,browser=version,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in paths],
        scope='Static container and nominal stock inspection. No opening, dispensing, material compatibility or robot action.')
    (HERE/'MAST_GREASE_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,checks=len(checks),captures=len(captures))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--browser',required=True);p.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/mast_grease.html');a=p.parse_args();run(a.browser,a.url)
