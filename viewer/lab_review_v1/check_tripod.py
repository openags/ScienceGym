"""Verify actual tripod views and reject stale geometry without task credit."""
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
    def capture(page,name):
        path=HERE/'evidence'/('tripod_'+name+'.png');page.locator('#lift-viewport').screenshot(path=str(path));captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=b.new_page(viewport={'width':1500,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url,wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.tripodLoaded === "true"',timeout=120000)
        check('limits_and_missing_parts_visible','地桩' in page.locator('body').inner_text() and '未放入库存' in page.locator('#tripod-status').inner_text())
        for mode,count in {'all':62,'base':53,'masts':3,'upper':10,'lower':10,'leg':11,'splice':6,'joint':8,'ground':7,'site':69}.items():
            page.select_option('#tripod-select',mode);data=page.evaluate('scienceGymTripodInspection()');check('visible_parts_'+mode,data['selected']==mode and len(data['visible'])==count)
            for view in ['oblique','top','side']:
                page.locator('[data-view="'+view+'"]').click();page.wait_for_timeout(150);capture(page,mode+'_'+view)
                if mode in ['ground','site']:check('complete_site_framed_'+mode+'_'+view,page.evaluate('scienceGymTripodInspection().visibleBoundsFit'))
        for mode in ['joint','upper','lower','ground']:
            page.select_option('#tripod-select',mode);page.locator('[data-view="'+('top' if mode=='joint' else 'side')+'"]').click();page.check('#tripod-section');page.wait_for_timeout(150);check('section_'+mode,page.evaluate('scienceGymTripodInspection().section'));capture(page,mode+'_section');page.uncheck('#tripod-section')
        page.select_option('#tripod-select','ground');page.check('#tripod-section');check('actual_capped_ground_parts',len(page.evaluate('scienceGymTripodInspection().visible'))==5);page.uncheck('#tripod-section')
        page.wait_for_function('document.getElementById("site-plan").complete && document.getElementById("site-plan").naturalWidth > 0');check('verified_site_diagram_visible',not page.evaluate('scienceGymTripodInspection().siteStaged'))
        check('no_browser_errors',not errors);page.set_viewport_size({'width':390,'height':844});check('mobile_page_fits',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        record=json.loads((ROOT/'assets/cooling_lab_v1/tripod_assets.json').read_text());record['geometry']['sha256']='0'*64;page.route('**/assets/cooling_lab_v1/tripod_assets.json',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps(record)))
        page.reload(wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.tripodLoaded === "error"',timeout=120000);check('tampered_model_rejected',page.locator('#lift-viewport canvas').count()==0)
        version=b.version;b.close()
    paths=[Path(__file__),HERE/'tripod.html',HERE/'tripod.js',HERE/'style.css',HERE/'lift.css',*[ROOT/'assets/cooling_lab_v1'/n for n in ['tripod_assets.json','tripod_checks.json','weather_site_review.json','outdoor_ground_assets.json','outdoor_ground_checks.json']]]
    record=dict(passed=True,checks=checks,captures=captures,browser=version,source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in paths],scope='Rigid-geometry and spatial-proposal inspector only; no installation, load, robot operation or owner acceptance.')
    (HERE/'TRIPOD_VERIFICATION.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(dict(passed=True,checks=len(checks),captures=len(captures))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--browser',required=True);p.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/tripod.html');a=p.parse_args();run(a.browser,a.url)
