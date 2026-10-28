"""Exercise the real support inspector and refuse a corrupted model pin."""
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
        path=HERE/'evidence'/('support_'+name+'.png');page.locator('#lift-viewport').screenshot(path=str(path));captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=b.new_page(viewport={'width':1500,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url,wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.supportLoaded === "true"',timeout=120000)
        check('stock_and_qualification_limits_visible','裁切' in page.locator('body').inner_text() and '未放入库存' in page.locator('#support-status').inner_text())
        modes={'all':113,'site':113,'frame':72,'guys':30,'wires':3,'anchors':21,'upper':8,'anchor':8,'foot':5,'ground':8,'ground_top':9}
        for mode,count in modes.items():
            page.select_option('#support-select',mode);data=page.evaluate('scienceGymSupportInspection()');check('visible_parts_'+mode,data['selected']==mode and len(data['visible'])==count and not data['staged'])
            for view in ['oblique','top','side']:
                page.locator('[data-view="'+view+'"]').click();page.wait_for_timeout(150);capture(page,mode+'_'+view)
            if mode in ['upper','anchor','ground_top']:
                page.locator('[data-view="end"]').click();page.wait_for_timeout(150);capture(page,mode+'_end')
        check('no_browser_errors',not errors);page.set_viewport_size({'width':390,'height':844});check('mobile_page_fits',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        record=json.loads((ROOT/'assets/cooling_lab_v1/weather_support_assets.json').read_text());record['geometry']['sha256']='0'*64;page.route('**/assets/cooling_lab_v1/weather_support_assets.json',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps(record)))
        page.reload(wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.supportLoaded === "error"',timeout=120000);check('tampered_model_rejected',page.locator('#lift-viewport canvas').count()==0)
        version=b.version;b.close()
    paths=[Path(__file__),HERE/'support.html',HERE/'support.js',HERE/'style.css',HERE/'lift.css',*[ROOT/'assets/cooling_lab_v1'/n for n in ['weather_support_assets.json','weather_support_checks.json','outdoor_ground_assets.json','outdoor_ground_checks.json']]]
    record=dict(passed=True,checks=checks,captures=captures,browser=version,source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in paths],scope='Static support installation-reference inspector with real stock transforms and continuous cut wires; no initial inventory, loads, ground retention, robot operation or owner acceptance.')
    (HERE/'SUPPORT_VERIFICATION.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(dict(passed=True,checks=len(checks),captures=len(captures))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--browser',required=True);p.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/support.html');a=p.parse_args();run(a.browser,a.url)
