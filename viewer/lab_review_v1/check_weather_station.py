"""Check station review controls, visible limitations and stale-model refusal."""
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
        page.wait_for_timeout(200);path=HERE/'evidence'/('weather_station_'+name+'.png')
        page.locator('#lift-viewport').screenshot(path=str(path));captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=b.new_page(viewport={'width':1500,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url,wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.stationLoaded === "true"',timeout=120000)
        check('unaccepted_candidate_visible','静态候选未验收' in page.locator('#station-status').inner_text())
        check('incomplete_delivery_remains_visible',page.locator('#station-missing li').count()==1 and '人形机器人空间' in page.locator('#station-missing').inner_text())
        check('ground_source_uncertainty_visible','原厂端子型号未知' in page.locator('#ground-reference').inner_text() and '400 mm' in page.locator('#ground-reference').inner_text())
        check('storage_is_final_candidate_not_initial_inventory','尚未绑定主场景库存' in page.locator('#storage-reference').inner_text())
        check('tool_space_is_distinct_from_robot_execution','人形机器人双手、握持、受力及动作仍待验证' in page.locator('#service-reference').inner_text())
        for mode in ['whole','instruments','coils','adapters','bracket','logger','stock','head','ground','flag','ring','cart','trays']:
            page.select_option('#station-select',mode);state=page.evaluate('scienceGymStationInspection()');stock=mode in ['stock','head'];ground=mode in ['ground','flag'];storage=mode in ['cart','trays']
            check('mode_'+mode,len(state['visible'])==(1 if stock else 7 if ground else 96 if storage else 447 if mode=='whole' else 351) and state['active']==('stock' if stock else 'ground' if ground else 'storage' if storage else 'station') and state['clipPlanes']==(0 if mode in ['whole','stock','ground','cart'] else 6) and not state['robotUseQualified'])
            page.locator('[data-view="oblique"]').click();capture(page,mode+'_oblique')
        for target in ['mount_1_nut_left','mount_1_nut_right','mount_2_nut_left','mount_2_nut_right','rs3_clamp']:
            mode='tool_'+target;page.select_option('#station-select',mode);state=page.evaluate('scienceGymStationInspection()')
            check('installed_tool_'+target,len(state['visible'])==355 and state['active']=='station' and state['clipPlanes']==6 and 'steel_shaft_and_blind_socket' in state['visible'])
            page.locator('[data-view="oblique"]').click();capture(page,mode+'_oblique')
        for mode,view in [('head','front'),('head','top'),('stock','top'),('coils','rear'),('adapters','rear'),('bracket','bottom'),('ground','front'),('flag','rear'),('ring','front'),('trays','top')]:
            page.select_option('#station-select',mode);page.locator('[data-view="'+view+'"]').click();capture(page,mode+'_'+view)
        page.select_option('#station-select','logger');page.check('#hide-door');state=page.evaluate('scienceGymStationInspection()');record=json.loads((ROOT/'assets/cooling_lab_v1/u30_assets.json').read_text())
        check('only_actual_door_parts_hidden',len(state['visible'])==351-len(record['door_parts']) and all('u30__'+n not in state['visible'] for n in record['door_parts']))
        page.locator('[data-view="front"]').click();capture(page,'logger_front_door_hidden')
        page.set_viewport_size({'width':390,'height':844});check('mobile_fits',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        check('no_browser_errors',not errors)
        record=json.loads((ROOT/'assets/cooling_lab_v1/weather_station_assets.json').read_text());record['geometry']['sha256']='0'*64
        page.route('**/assets/cooling_lab_v1/weather_station_assets.json',lambda route:route.fulfill(status=200,content_type='application/json',body=json.dumps(record)))
        page.reload(wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.stationLoaded === "error"',timeout=120000)
        check('modified_candidate_rejected',page.locator('#lift-viewport canvas').count()==0);version=b.version;b.close()
    paths=[Path(__file__),HERE/'weather_station.html',HERE/'weather_station.js',HERE/'style.css',HERE/'lift.css',ROOT/'assets/cooling_lab_v1/weather_station_assets.json',ROOT/'assets/cooling_lab_v1/weather_station_checks.json',ROOT/'assets/cooling_lab_v1/cable_tie_assets.json',ROOT/'assets/cooling_lab_v1/u30_ground_assets.json',ROOT/'assets/cooling_lab_v1/u30_ground_checks.json',ROOT/'assets/cooling_lab_v1/weather_storage_assets.json',ROOT/'assets/cooling_lab_v1/weather_storage_checks.json',ROOT/'assets/cooling_lab_v1/weather_service_checks.json']
    report=dict(passed=True,checks=checks,captures=captures,browser=version,source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in paths],scope='Static review and truthful incomplete status. No installation, electrical or robot qualification.')
    (HERE/'WEATHER_STATION_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,checks=len(checks),captures=len(captures))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--browser',required=True);parser.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/weather_station.html');args=parser.parse_args();run(args.browser,args.url)
