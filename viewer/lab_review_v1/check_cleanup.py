"""Exercise identity-preserving cleanup inspection and invalid-source rejection."""
import argparse
import hashlib
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(browser,url):
    checks=[];captures=[];errors=[]
    record=json.loads((ROOT/'assets/cooling_lab_v1/weather_cleanup_assets.json').read_text())
    def check(name,passed):
        checks.append(dict(name=name,passed=bool(passed)))
        if not passed:raise AssertionError(name)
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=b.new_page(viewport={'width':1500,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(url,wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.cleanupLoaded === "true"',timeout=120000)
        check('unaccepted_status_visible','未验收' in page.locator('#cleanup-status').inner_text())
        for mode,views in {'mast':['top','oblique','side','bottom'],'silicone':['top'],'pack':['oblique','top','side'],'stack':['oblique'],'sheet':['top','oblique']}.items():
            page.select_option('#cleanup-select',mode);page.wait_for_function('scienceGymCleanupInspection().mode === '+json.dumps(mode));data=page.evaluate('scienceGymCleanupInspection()')
            expected={'mast':'weather_mast_applicator','silicone':'weather_silicone_applicator','pack':'weather_wipes_tx609','stack':'weather_wipes_tx609','sheet':'weather_wipes_tx609/wipe_001'}[mode]
            check('correct_physical_identity_'+mode,data['identity']==expected)
            check('same_stock_and_acceptance_'+mode,data['stockWipes']==300 and data['reservedWipes']==36 and not data['robotUseQualified'] and data['ownerAcceptance'] is None)
            check('parts_'+mode,len(data['visible'])=={'mast':1,'silicone':1,'pack':303,'stack':300,'sheet':1}[mode])
            for view in views:
                page.locator('[data-view="'+view+'"]').click();page.wait_for_timeout(150)
                path=HERE/'evidence'/('cleanup_'+mode+'_'+view+'.png');page.locator('#lift-viewport').screenshot(path=str(path));captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
        text=page.locator('main').inner_text()
        check('limitations_and_quantity_visible','余 264 张' in text and '滚动稳定性' in text and '收集位置仍待分配' in text and '不是逐张称量' in text)
        check('no_browser_errors',not errors)
        page.set_viewport_size({'width':390,'height':844});check('mobile_no_overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        page.route('**/'+record['wipe_pack']['geometry']['path'],lambda r:r.fulfill(status=200,content_type='model/gltf-binary',body=b'bad geometry'))
        page.reload(wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.cleanupLoaded === "true"',timeout=120000)
        page.select_option('#cleanup-select','pack');page.wait_for_function('document.documentElement.dataset.cleanupLoaded === "error"',timeout=120000)
        check('tampered_pack_refused',page.locator('#lift-viewport canvas').count()==0 and '版本不匹配' in page.locator('#lift-error').inner_text())
        version=b.version;b.close()
    paths=[Path(__file__),HERE/'cleanup.html',HERE/'cleanup.js',HERE/'style.css',HERE/'lift.css']+[ROOT/'assets/cooling_lab_v1'/n for n in ['weather_cleanup_assets.json','weather_cleanup_checks.json']]
    report=dict(passed=True,checks=checks,captures=captures,browser=version,source_artifacts=[dict(path=str(q.relative_to(ROOT)),sha256=sha(q)) for q in paths],scope='Ordinary tools, packaging and same-sheet stock inspection; no performed robot or cleaning operation.')
    (HERE/'CLEANUP_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,checks=len(checks),captures=len(captures))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--browser',required=True);p.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/cleanup.html');a=p.parse_args();run(a.browser,a.url)
