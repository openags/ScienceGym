"""Inspect three tool states and six actual service placements in Chromium."""
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
    record=json.loads((ROOT/'assets/cooling_lab_v1/adjustable_wrench_assets.json').read_text())
    service=json.loads((ROOT/'assets/cooling_lab_v1/adjustable_wrench_service_checks.json').read_text())
    items={i['id']:i for i in record['items']}
    def check(name,passed):
        checks.append(dict(name=name,passed=bool(passed)))
        if not passed:raise AssertionError(name)
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=b.new_page(viewport={'width':1500,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url,wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.wrenchLoaded === "true"',timeout=120000)
        check('unaccepted_static_status','静态检查' in page.locator('#wrench-status').inner_text() and '未验收' in page.locator('#wrench-status').inner_text())
        modes={key:['oblique','top'] for key in items};modes.update(head=['top','bottom'],internal=['oblique','top'])
        for t in service['targets']:modes['service:'+t['selected_candidate_id']]=['oblique']
        for mode,views in modes.items():
            page.select_option('#wrench-select',mode);data=page.evaluate('scienceGymWrenchInspection()')
            check('visible_parts_'+mode,data['selected']==mode and len(data['visible'])==(4 if mode=='internal' else 7) and not data['torqueQualified'] and not data['robotUseQualified'])
            expected=items[data['active']]['part_transforms']
            check('actual_part_transforms_'+mode,all(np.allclose(np.array(m).reshape(4,4).T,expected[n],atol=2e-7) for n,m in data['transforms'].items()))
            candidate=next((c for c in service['candidates'] if 'service:'+c['id']==mode),None)
            check('actual_tool_context_'+mode,data['stationVisible']==bool(candidate) and np.allclose(np.array(data['toolToWorld']).reshape(4,4).T,candidate['to_world'] if candidate else np.eye(4),atol=1e-9))
            for view in views:
                page.locator('[data-view="'+view+'"]').click();page.wait_for_timeout(150)
                path=HERE/'evidence'/('adjustable_wrench_'+mode.replace(':','_')+'_'+view+'.png');page.locator('#lift-viewport').screenshot(path=str(path));captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
        check('no_browser_errors',not errors)
        page.set_viewport_size({'width':390,'height':844});check('mobile_page_fits',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        record['items'][0]['geometry']['sha256']='0'*64
        page.route('**/assets/cooling_lab_v1/adjustable_wrench_assets.json',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps(record)))
        page.reload(wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.wrenchLoaded === "error"',timeout=120000)
        check('tampered_model_refused',page.locator('#lift-viewport canvas').count()==0)
        version=b.version;b.close()
    paths=[Path(__file__),HERE/'adjustable_wrench.html',HERE/'adjustable_wrench.js',HERE/'style.css',HERE/'lift.css']+[ROOT/'assets/cooling_lab_v1'/n for n in ['adjustable_wrench_assets.json','adjustable_wrench_checks.json','adjustable_wrench_service_checks.json','weather_station_assets.json']]
    report=dict(passed=True,checks=checks,captures=captures,browser=version,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in paths],
        scope='Static tool and actual tripod poses. No insertion, rotation sweep, torque, grasp or robot action.')
    (HERE/'ADJUSTABLE_WRENCH_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,checks=len(checks),captures=len(captures))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--browser',required=True);p.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/adjustable_wrench.html');a=p.parse_args();run(a.browser,a.url)
