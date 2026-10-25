"""Exercise the real anchoring inspector and refuse a corrupted model pin."""
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
        path=HERE/'evidence'/('anchoring_'+name+'.png');page.locator('#lift-viewport').screenshot(path=str(path));captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=b.new_page(viewport={'width':1500,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url,wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.anchoringLoaded === "true"',timeout=120000)
        check('stock_and_qualification_limits_visible','整卷' in page.locator('body').inner_text() and '未放入库存' in page.locator('#anchoring-status').inner_text())
        modes={'all':49,'collar':10,'turnbuckle':3,'hook':1,'clamp':2,'stakes':6,'guy_stake':1,'foot_stake':1,'ground':7,'rod':1,'ground_clamp':2,'ground_mast':4,'wires':2}
        for mode,count in modes.items():
            page.select_option('#anchoring-select',mode);data=page.evaluate('scienceGymAnchoringInspection()');check('visible_parts_'+mode,data['selected']==mode and len(data['visible'])==count and not data['staged'])
            for view in ['oblique','top','side']:
                page.locator('[data-view="'+view+'"]').click();page.wait_for_timeout(150);capture(page,mode+'_'+view)
            if mode in ['clamp','ground_clamp']:
                page.locator('[data-view="end"]').click();page.wait_for_timeout(150);capture(page,mode+'_end')
        check('no_browser_errors',not errors);page.set_viewport_size({'width':390,'height':844});check('mobile_page_fits',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        record=json.loads((ROOT/'assets/cooling_lab_v1/weather_anchoring_assets.json').read_text());record['geometry']['sha256']='0'*64;page.route('**/assets/cooling_lab_v1/weather_anchoring_assets.json',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps(record)))
        page.reload(wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.anchoringLoaded === "error"',timeout=120000);check('tampered_model_rejected',page.locator('#lift-viewport canvas').count()==0)
        version=b.version;b.close()
    paths=[Path(__file__),HERE/'anchoring.html',HERE/'anchoring.js',HERE/'style.css',HERE/'lift.css',*[ROOT/'assets/cooling_lab_v1'/n for n in ['weather_anchoring_assets.json','weather_anchoring_checks.json']]]
    record=dict(passed=True,checks=checks,captures=captures,browser=version,source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in paths],scope='Loose anchoring-kit geometry inspector; no initial inventory, installation, tension, grounding, robot operation or owner acceptance.')
    (HERE/'ANCHORING_VERIFICATION.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(dict(passed=True,checks=len(checks),captures=len(captures))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--browser',required=True);p.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/anchoring.html');a=p.parse_args();run(a.browser,a.url)
