"""Verify actual wind-component views, shaft grouping and source rejection."""
import argparse
import hashlib
import json
import math
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
        path=HERE/'evidence'/('wind_'+name+'.png');page.locator('#lift-viewport').screenshot(path=str(path))
        captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
    def angle(page,control,value):
        page.locator('#wind-'+control+'-angle').evaluate('(el,value)=>{el.value=value;el.dispatchEvent(new Event("input",{bubbles:true}))}',str(value))
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=b.new_page(viewport={'width':1500,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(url,wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.windLoaded === "true"',timeout=120000)
        check('source_conflicts_and_limits_visible','尺寸歧义' in page.locator('body').inner_text() and '未放入库存' in page.locator('#wind-status').inner_text())
        expected={'all':39,'mechanical':22,'head':10,'cups':3,'vane':4,'base':11,'arm':1,'leads':14,'adapter':5,'plug':7,'route':12,'kit':3,'key':1,'fit':4,'comparison':2}
        for identity,count in expected.items():
            page.select_option('#wind-select',identity);data=page.evaluate('scienceGymWindInspection()')
            check('visible_parts_'+identity,data['selected']==identity and len(data['visible'])==count)
            for view in ['oblique','top','side']:
                page.locator('[data-view="'+view+'"]').click();page.wait_for_timeout(150);capture(page,identity+'_'+view)
        page.select_option('#wind-select','head');page.locator('[data-view="oblique"]').click()
        for degrees in [30,150,270]:
            angle(page,'cup',degrees/2);angle(page,'vane',degrees);data=page.evaluate('scienceGymWindInspection()')
            for group,value in [('cups',degrees/2),('vane',degrees)]:
                matrix=data['shaftMatrices'][group];radians=math.radians(value)
                check(group+'_shaft_follows_'+str(degrees),abs(matrix[0]-math.cos(radians))<1e-8 and abs(matrix[1]-math.sin(radians))<1e-8 and abs(matrix[12]-.3*(1-math.cos(radians)))<1e-8 and abs(matrix[13]+.3*math.sin(radians))<1e-8)
            page.wait_for_timeout(150);capture(page,'rotated_'+str(degrees))
        angle(page,'cup',0);angle(page,'vane',0)
        for identity in ['all','head']:
            page.select_option('#wind-select',identity);page.check('#wind-sweep');page.wait_for_timeout(150)
            check('full_turn_overlay_'+identity,page.evaluate('scienceGymWindInspection().sweep'));capture(page,identity+'_sweep');page.uncheck('#wind-sweep')
        for identity in ['base','head','adapter','plug']:
            page.select_option('#wind-select',identity);page.locator('[data-view="side"]').click();page.check('#wind-section');page.wait_for_timeout(150)
            check('section_'+identity,page.evaluate('scienceGymWindInspection().section'));capture(page,identity+'_section');page.uncheck('#wind-section')
        check('view_controls_reversible',not page.evaluate('scienceGymWindInspection().section || scienceGymWindInspection().sweep'))
        check('no_browser_errors',not errors)
        page.set_viewport_size({'width':390,'height':844});check('mobile_page_fits',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        record=json.loads((ROOT/'assets/cooling_lab_v1/wind_sensor_assets.json').read_text());record['geometry']['sha256']='0'*64
        page.route('**/assets/cooling_lab_v1/wind_sensor_assets.json',lambda route:route.fulfill(status=200,content_type='application/json',body=json.dumps(record)))
        page.reload(wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.windLoaded === "error"',timeout=120000)
        check('tampered_geometry_rejected',page.locator('#lift-viewport canvas').count()==0 and '不一致' in page.locator('#lift-error').inner_text())
        page.unroute('**/assets/cooling_lab_v1/wind_sensor_assets.json')
        lead_record=json.loads((ROOT/'assets/cooling_lab_v1/wind_lead_assets.json').read_text());lead_record['geometry']['sha256']='0'*64
        page.route('**/assets/cooling_lab_v1/wind_lead_assets.json',lambda route:route.fulfill(status=200,content_type='application/json',body=json.dumps(lead_record)))
        page.reload(wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.windLoaded === "error"',timeout=120000)
        check('tampered_lead_geometry_rejected',page.locator('#lift-viewport canvas').count()==0 and '不一致' in page.locator('#lift-error').inner_text())
        version=b.version;b.close()
    files=[Path(__file__),HERE/'wind.html',HERE/'wind.js',HERE/'style.css',HERE/'lift.css',*[ROOT/'assets/cooling_lab_v1'/name for name in ['wind_sensor_assets.json','wind_sensor_checks.json','wind_lead_assets.json','wind_lead_checks.json','wind_kit_assets.json','wind_kit_checks.json']]]
    report=dict(passed=True,checks=checks,captures=captures,browser=version,
        source_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in files],
        scope='Actual rigid sensor, external leads, loose kit, isolated drive fit and conflicting-radius comparison. Geometry sliders and sweep overlays do not simulate bearings, flexible cables or robot operation.')
    (HERE/'WIND_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,checks=len(checks),captures=len(captures))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--browser',required=True);p.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/wind.html');a=p.parse_args();run(a.browser,a.url)
