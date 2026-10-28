"""Inspect the stock layout in the complete laboratory, including mode changes."""
import argparse
import json
from pathlib import Path
import hashlib
import numpy as np
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def run(browser,url):
    record=json.loads((ROOT/'assets/cooling_lab_v1/weather_initial_stock_assets.json').read_text())
    checks=[];captures=[];errors=[]
    def check(name,passed,**details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        if not passed:raise AssertionError(name+' '+str(details))
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=b.new_page(viewport={'width':1600,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(url,wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.sceneLoaded==="true" || document.getElementById("error").textContent.length>0',timeout=180000)
        check('complete_lab_ready',page.locator('html').get_attribute('data-scene-loaded')=='true',error=page.locator('#error').inner_text())
        initial=page.evaluate('scienceGymWeatherInitialStock()');weather=page.evaluate('scienceGymWeatherComposition()')
        check('direct_link_opens_initial_context',initial['enabled'] and initial['visible'] and not weather['enabled'])
        check('detailed_logger_replaces_exactly_one_base_identity',{k for k,v in weather['baseVisibility'].items() if not v}=={'hobo_u30'} and weather['baseVisibility']['utility_cart'])
        check('installed_mast_and_final_storage_are_hidden',all(not m['visible'] for m in weather['modules'] if m['id'] in ['station','ground','storage','remainders']) and weather['floorVisibility']==[True])
        check('all_source_stock_parts_and_identities_present',set(initial['parts'])=={x['id'] for x in record['geometry']['part_records']} and set(initial['identities'])==set(record['physical_identity_ids']))
        check('world_positions_and_batch_preserved',np.allclose(initial['worldBounds'],record['geometry']['bounds_m'],atol=1e-5) and initial['batch']['sourceGeometryPreserved'])
        check('no_qualification_credit',initial['ownerAcceptance'] is None and not initial['initialStockCredit'] and not initial['robotUseQualified'])
        for region in ['all','fabrication_fixture','fabrication_storage_shelf_3','raw_stock_shelf_3','specimens_shelf_1','specimens_shelf_2']:
            page.select_option('#weather-initial-focus',region)
            path=HERE/'evidence'/('weather_initial_'+region+'.png');page.locator('#viewport').screenshot(path=str(path));captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
        page.check('#weather-composed')
        check('installed_state_hides_initial_stock',not page.evaluate('scienceGymWeatherInitialStock().visible') and page.evaluate('scienceGymWeatherComposition().enabled'))
        page.check('#weather-initial')
        check('initial_state_hides_installed_state',not page.evaluate('scienceGymWeatherComposition().enabled') and page.evaluate('scienceGymWeatherInitialStock().visible'))
        page.select_option('#asset-select','hobo_u30')
        check('original_logger_inspection_restores_base',not page.evaluate('scienceGymWeatherInitialStock().enabled') and page.evaluate('scienceGymWeatherComposition().baseVisibility.hobo_u30'))
        page.check('#weather-initial');page.locator('#workspace-targets button').first.click()
        check('old_workspace_pose_exits_new_context',not page.evaluate('scienceGymWeatherInitialStock().enabled'))
        page.set_viewport_size({'width':390,'height':844});page.check('#weather-initial');page.select_option('#weather-initial-focus','fabrication_storage_shelf_3')
        check('mobile_no_horizontal_overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        path=HERE/'evidence/weather_initial_mobile.png';page.locator('#viewport').screenshot(path=str(path));captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
        check('browser_no_errors',not errors,errors=errors)
        version=b.version;b.close()
    refs=[Path(__file__),HERE/'index.html',HERE/'main.js',HERE/'weather_composition.js',HERE/'weather_initial_stock.js',
          HERE/'render_batches.js',ROOT/'assets/cooling_lab_v1/weather_initial_stock_assets.json',ROOT/'assets/cooling_lab_v1/weather_initial_stock_checks.json']
    report=dict(schema_version=1,passed=True,checks=checks,captures=captures,browser=version,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        scope='Unpacked stock placement and mutually exclusive review states; no robot execution or owner acceptance.')
    (HERE/'WEATHER_INITIAL_STOCK_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,captures=len(captures))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--browser',required=True);parser.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/index.html?weather=initial');args=parser.parse_args();run(args.browser,args.url)
