"""Exercise full tool and fit views, mobile layout and corrupted-file refusal."""
import argparse
import hashlib
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(browser,url):
    checks=[];captures=[];errors=[]
    def check(name,passed):
        checks.append(dict(name=name,passed=bool(passed)))
        if not passed:raise AssertionError(name)
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=b.new_page(viewport={'width':1500,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url,wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.driverLoaded === "true"',timeout=120000)
        check('static_tool_and_unaccepted_status_visible','完整工具静态检查' in page.locator('#driver-status').inner_text() and '未验收' in page.locator('#driver-status').inner_text())
        for mode,count in {'tool':4,'socket':1,'grip':3,'fit':32,'interface':32}.items():
            page.select_option('#driver-select',mode);data=page.evaluate('scienceGymNutDriverInspection()');check('visible_parts_'+mode,data['selected']==mode and len(data['visible'])==count and not data['robotUseQualified'])
            for view in ['oblique','top','side','end']:
                page.locator('[data-view="'+view+'"]').click();page.wait_for_timeout(150)
                path=HERE/'evidence'/('nut_driver_'+mode+'_'+view+'.png');page.locator('#lift-viewport').screenshot(path=str(path));captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
        check('no_browser_errors',not errors);page.set_viewport_size({'width':390,'height':844});check('mobile_page_fits',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        record=json.loads((ROOT/'assets/cooling_lab_v1/nut_driver_assets.json').read_text());record['geometry']['sha256']='0'*64;page.route('**/assets/cooling_lab_v1/nut_driver_assets.json',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps(record)))
        page.reload(wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.driverLoaded === "error"',timeout=120000);check('tampered_model_rejected',page.locator('#lift-viewport canvas').count()==0)
        version=b.version;b.close()
    paths=[Path(__file__),HERE/'nut_driver.html',HERE/'nut_driver.js',HERE/'style.css',HERE/'lift.css',ROOT/'assets/cooling_lab_v1/nut_driver_assets.json',ROOT/'assets/cooling_lab_v1/nut_driver_checks.json']
    report=dict(passed=True,checks=checks,captures=captures,browser=version,source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in paths],scope='Static ordinary tool, actual drive fit and conservative rigid space bounds; no robot or torque qualification.')
    (HERE/'NUT_DRIVER_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,checks=len(checks),captures=len(captures))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--browser',required=True);p.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/nut_driver.html');a=p.parse_args();run(a.browser,a.url)
