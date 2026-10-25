"""Inspect the real post-level page and reject changed source/model bindings."""
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
        page=b.new_page(viewport={'width':1500,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url,wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.levelLoaded === "true"',timeout=120000)
        check('uncalibrated_status_visible','未校准' in page.locator('#level-status').inner_text())
        check('source_links_visible',page.locator('a[href="https://www.johnsonlevel.com/Content/files/ProductImages/175-O.png"]').count()==1)
        for mode,count in {'all':28,'tool':27,'body':1,'vials':24,'left':8,'corner':8,'strap':1}.items():
            page.select_option('#level-select',mode);data=page.evaluate('scienceGymPostLevelInspection()');check('visible_parts_'+mode,data['selected']==mode and len(data['visible'])==count and not data['measurementQualified'])
            for view in ['oblique','back','top','side']:
                page.locator('[data-view="'+view+'"]').click();page.wait_for_timeout(150)
                path=HERE/'evidence'/('post_level_'+mode+'_'+view+'.png');page.locator('#lift-viewport').screenshot(path=str(path));captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
        check('no_browser_errors',not errors);page.set_viewport_size({'width':390,'height':844});check('mobile_page_fits',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        record=json.loads((ROOT/'assets/cooling_lab_v1/post_level_assets.json').read_text());record['geometry']['sha256']='0'*64;page.route('**/assets/cooling_lab_v1/post_level_assets.json',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps(record)))
        page.reload(wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.levelLoaded === "error"',timeout=120000);check('tampered_model_rejected',page.locator('#lift-viewport canvas').count()==0)
        version=b.version;b.close()
    paths=[Path(__file__),HERE/'post_level.html',HERE/'post_level.js',HERE/'style.css',HERE/'lift.css',ROOT/'assets/cooling_lab_v1/post_level_assets.json',ROOT/'assets/cooling_lab_v1/post_level_checks.json']
    report=dict(passed=True,checks=checks,captures=captures,browser=version,source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in paths],scope='Static ordinary post-level inspection. No calibration, gravity-sensitive readout, strap retention, robot operation or owner acceptance.')
    (HERE/'POST_LEVEL_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,checks=len(checks),captures=len(captures))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--browser',required=True);p.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/post_level.html');a=p.parse_args();run(a.browser,a.url)
