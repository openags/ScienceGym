"""Exercise real frame selection, source failures and visual review views."""
import argparse
import hashlib
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def run(url,browser):
    checks=[];captures=[];errors=[]
    def check(name,value):
        checks.append(dict(name=name,passed=bool(value)))
        if not value:raise AssertionError(name)
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage'])
        page=b.new_page(viewport={'width':1440,'height':1100});page.set_default_timeout(60000)
        page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url)
        page.wait_for_function('document.documentElement.dataset.frameLoaded === "true"')
        snapshot=lambda:page.evaluate('window.scienceGymFrameInspection()')
        def capture(name):
            page.wait_for_timeout(150);f=HERE/'evidence'/('frame_'+name+'.png')
            page.locator('#lift-viewport').screenshot(path=str(f));captures.append(dict(path=str(f.relative_to(ROOT)),sha256=sha(f)))
        data=json.loads((ROOT/'assets/cooling_lab_v1/apparatus_stock_reconciliation.json').read_text())
        white=data['items'][0]
        check('exact_exported_frame_parts',set(snapshot()['visible'])==set(white['frame']['review_parts']))
        for group in ['all','base','uprights','reflector','rail']:
            page.locator('#frame-group').select_option(group)
            check('selection_'+group,snapshot()['group']==group and bool(snapshot()['visible']))
            for view in (['oblique','front','top','bottom'] if group=='all' else ['end'] if group=='rail' else ['oblique','bottom']):
                page.locator(f'button[data-view="{view}"]').click();capture(group+'_'+view)
        check('only_one_actual_rail',snapshot()['visible']==['COOLER_WHITE__frame_rail_right'])
        page.locator('#frame-group').select_option('all');before=set(snapshot()['visible'])
        page.locator('#frame-hardware').uncheck();after=set(snapshot()['visible'])
        check('hardware_toggle_changes_actual_parts',after<before and all('screw' not in n and 'tnut' not in n for n in after))
        page.locator('button[data-view="oblique"]').click();capture('hardware_hidden')
        page.locator('#frame-hardware').check();check('all_parts_restored',set(snapshot()['visible'])==before)
        text=page.locator('body').inner_text()
        check('inferences_and_unqualified_mechanics_visible',all(t in text for t in ['不是已确认的论文原件','未验证预紧力','尚未验收','底面可达','150 mm','100 mm']))
        page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(150)
        check('mobile_no_horizontal_overflow',page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        check('no_browser_errors',not errors)
        for name,path,status,body in [
            ('missing_frame','**/geometry/apparatus_frame_inspection.glb',404,''),
            ('stale_frame','**/geometry/apparatus_frame_inspection.glb',200,'old mesh'),
            ('stale_source_ledger','**/apparatus_frame_sources.json',200,'{}'),
            ('stale_reconciliation','**/apparatus_stock_reconciliation.json',200,'{}')]:
            page.route(path,lambda route:route.fulfill(status=status,body=body));page.reload()
            page.wait_for_function('document.documentElement.dataset.frameLoaded === "error"')
            check(name+'_fails_closed',page.locator('#lift-viewport canvas').count()==0 and bool(page.locator('#lift-error').inner_text()))
            page.unroute(path)
        b.close()
    paths=[HERE/n for n in ['frame.html','frame.js','lift.css','style.css','check_frame.py']]+[ROOT/'assets/cooling_lab_v1'/n for n in ['apparatus_stock_reconciliation.json','apparatus_frame_checks.json','apparatus_frame_sources.json']]
    report=dict(passed=True,checks=checks,captures=captures,source_artifacts=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in paths],scope='Static frame browser review only; no manipulation, movement, load or installation qualification')
    (HERE/'FRAME_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,checks=len(checks),captures=len(captures))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--browser',required=True);parser.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/frame.html');a=parser.parse_args();run(a.url,a.browser)
