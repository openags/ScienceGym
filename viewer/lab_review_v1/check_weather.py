"""Exercise the weather inspector and retain directly rendered model views."""
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
        path=HERE/'evidence'/('weather_'+name+'.png')
        page.locator('#lift-viewport').screenshot(path=str(path))
        captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=b.new_page(viewport={'width':1500,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(url,wait_until='domcontentloaded')
        page.wait_for_function('document.documentElement.dataset.weatherLoaded === "true"',timeout=120000)
        check('source_scope_visible','尚未计入主场景库存' in page.locator('#weather-status').inner_text() and 'Onset 原配供应商及针脚定义未知' in page.locator('body').inner_text())
        check('measured_cable_lengths_visible',page.locator('#weather-cables tbody tr td:nth-child(2)').all_text_contents()==['2.000000 m','0.500000 m'])
        expected={'rs3':41,'shield':24,'sensor':14,'head':4,'plug':7,'clearance':28}
        check('six_inspection_modes',page.locator('#weather-select option').count()==len(expected))
        for identity,parts in expected.items():
            page.select_option('#weather-select',identity)
            probe=page.evaluate('scienceGymWeatherInspection()')
            check('correct_visible_parts_'+identity,probe['selected']==identity and probe['visible']==[{'id':identity,'parts':parts}])
            for view in ['oblique','top','side']:
                page.locator('[data-view="'+view+'"]').click();page.wait_for_timeout(150);capture(page,identity+'_'+view)
        for identity in ['shield','plug','clearance']:
            page.select_option('#weather-select',identity);page.locator('[data-view="side"]').click();page.check('#weather-section');page.wait_for_timeout(150)
            check('section_'+identity,page.evaluate('scienceGymWeatherInspection().section'));capture(page,identity+'_section')
            page.uncheck('#weather-section')
        check('section_reversible',not page.evaluate('scienceGymWeatherInspection().section'))
        check('no_browser_errors',not errors)
        page.set_viewport_size({'width':390,'height':844})
        check('mobile_page_fits',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        # Geometry evidence must fail closed after source tampering.
        record=json.loads((ROOT/'assets/cooling_lab_v1/weather_assets.json').read_text())
        record['items'][0]['geometry']['sha256']='0'*64
        page.route('**/assets/cooling_lab_v1/weather_assets.json',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps(record)))
        page.reload(wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.weatherLoaded === "error"',timeout=120000)
        check('tampered_asset_rejected',page.locator('#lift-viewport canvas').count()==0 and '不一致' in page.locator('#lift-error').inner_text())
        version=b.version;b.close()
    files=[Path(__file__),HERE/'weather.html',HERE/'weather.js',HERE/'style.css',HERE/'lift.css',ROOT/'assets/cooling_lab_v1/weather_assets.json',ROOT/'assets/cooling_lab_v1/weather_asset_checks.json']
    report=dict(passed=True,checks=checks,captures=captures,browser=version,
        source_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in files],
        scope='Actual component inspector and source binding. No owner acceptance, installation or robot operation credit.')
    (HERE/'WEATHER_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,checks=len(checks),captures=len(captures))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--browser',required=True);p.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/weather.html');a=p.parse_args();run(a.browser,a.url)
