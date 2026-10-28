"""Check inspection modes, real rendering, mobile fit and stale-file refusal."""
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
    modes={'closed':['oblique','front'],'open':['oblique','front'],'inside':['oblique','front'],
        'battery':['oblique','front'],'ports':['oblique','bottom'],'usb':['oblique','front','bottom'],
        'channel':['oblique','bottom'],'mount':['oblique','rear'],'fit':['oblique','rear'],'plug':['oblique','bottom']}
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=b.new_page(viewport={'width':1500,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url,wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.u30Loaded === "true"',timeout=120000)
        check('static_unaccepted_status_visible','静态检查候选' in page.locator('#u30-status').inner_text() and '未验收' in page.locator('#u30-status').inner_text())
        for mode,views in modes.items():
            page.select_option('#u30-select',mode);data=page.evaluate('scienceGymU30Inspection()')
            check('visible_parts_'+mode,data['selected']==mode and len(data['visible'])>0 and not data['robotUseQualified'])
            if mode=='closed':check('complete_enclosure_visible',len(data['visible'])==143 and 'hinged_door' in data['visible'])
            if mode=='inside':check('inside_hides_door_keeps_module',len(data['visible'])==140 and 'hinged_door' not in data['visible'] and 'logger_clear_cover' in data['visible'])
            if mode=='ports':check('five_complete_seven_part_jacks',len(data['visible'])==35)
            if mode=='plug':check('actual_plug_and_jack_visible',len(data['visible'])==14 and 'selected_plug_modular_plug_body_and_latch' in data['visible'])
            if mode=='fit':check('full_fit_context_visible',len(data['visible'])==151 and 'selected_mast_fixture' in data['visible'])
            for view in views:
                page.locator('[data-view="'+view+'"]').click();page.wait_for_timeout(150)
                path=HERE/'evidence'/('u30_'+mode+'_'+view+'.png');page.locator('#lift-viewport').screenshot(path=str(path));captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
        check('no_browser_errors',not errors);page.set_viewport_size({'width':390,'height':844});check('mobile_page_fits',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        record=json.loads((ROOT/'assets/cooling_lab_v1/u30_assets.json').read_text());record['geometry']['sha256']='0'*64;page.route('**/assets/cooling_lab_v1/u30_assets.json',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps(record)))
        page.reload(wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.u30Loaded === "error"',timeout=120000);check('tampered_model_rejected',page.locator('#lift-viewport canvas').count()==0)
        version=b.version;b.close()
    paths=[Path(__file__),HERE/'u30.html',HERE/'u30.js',HERE/'style.css',HERE/'lift.css',ROOT/'assets/cooling_lab_v1/u30_assets.json',ROOT/'assets/cooling_lab_v1/u30_checks.json']
    report=dict(passed=True,checks=checks,captures=captures,browser=version,source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in paths],scope='Static U30 geometry, isolated interfaces and source comparison; no robot, electrical, sealing or load qualification.')
    (HERE/'U30_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,checks=len(checks),captures=len(captures))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--browser',required=True);p.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/u30.html');a=p.parse_args();run(a.browser,a.url)
