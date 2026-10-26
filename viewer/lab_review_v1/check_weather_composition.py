"""Inspect weather composition in the complete laboratory browser scene."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def run(browser,url):
    checks=[];captures=[];errors=[]
    record=json.loads((ROOT/'assets/cooling_lab_v1/weather_scene_binding.json').read_text())
    geometry=json.loads((ROOT/'assets/cooling_lab_v1/weather_scene_binding_checks.json').read_text())
    def check(name,passed,**details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        if not passed:raise AssertionError(name+' '+str(details))
    def capture(page,name):
        path=HERE/'evidence'/('weather_composition_'+name+'.png');page.locator('#viewport').screenshot(path=str(path));captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=b.new_page(viewport={'width':1600,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(url,wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.sceneLoaded==="true" || document.getElementById("error").textContent.length>0',timeout=180000)
        check('complete_base_scene_loaded',page.locator('html').get_attribute('data-scene-loaded')=='true',error=page.locator('#error').inner_text())
        s=page.evaluate('scienceGymWeatherComposition()')
        check('base_default_preserves_original_instances',not s['enabled'] and all(s['baseVisibility'].values()) and s['floorVisibility']==[True] and not any(m['visible'] for m in s['modules']))
        page.check('#weather-composed');page.locator('[data-view="outdoor"]').click();s=page.evaluate('scienceGymWeatherComposition()')
        check('installed_reference_visible_without_duplicate_instances',s['enabled'] and s['floorVisibility']==[False] and all(m['visible'] for m in s['modules']) and {n for n,v in s['baseVisibility'].items() if not v}=={'hobo_u30','utility_cart'})
        check('independent_ambient_and_solar_instruments_preserved',all(s['baseVisibility'][n] for n in record['preserved_independent_scene_asset_ids']))
        check('all_named_parts_loaded',sum(m['parts'] for m in s['modules'])==531 and s['entities']==32)
        expected={m['id']:m for m in record['modules']}
        for m in s['modules']:
            check('actual_world_transform_'+m['id'],np.allclose(np.asarray(m['worldMatrix']).reshape(4,4).T,expected[m['id']]['to_world'],atol=1e-10,rtol=0))
            check('actual_world_bounds_'+m['id'],np.allclose(np.asarray(m['bounds']).reshape(2,3),geometry['module_world_bounds_m'][m['id']],atol=1e-5,rtol=0))
            check('source_geometry_preserved_'+m['id'],m['batch']['sourceGeometryPreserved'] and set(m['sourceParts'])=={p['id'] for p in expected[m['id']]['geometry']['part_records']})
        check('identity_and_scope_visible',page.locator('#weather-identities tr').count()==32 and '切换不是机器人搬运或装配' in page.locator('#weather-composition-review').inner_text() and not s['robotUseQualified'] and s['ownerAcceptance'] is None)
        check('cutter_source_and_joint_inspector_link',page.locator('#weather-identities a[href="wire_rope_cutter.html"]').count()==1)
        check('wrench_source_and_actual_nut_inspector_link',page.locator('#weather-identities a[href="adjustable_wrench.html"]').count()==1)
        check('grease_container_and_material_inspector_link',page.locator('#weather-identities a[href="mast_grease.html"]').count()==1)
        check('tape_measure_source_and_scale_inspector_link',page.locator('#weather-identities a[href="tape_measure.html"]').count()==1)
        capture(page,'outdoor')
        for identity in ['station','storage','remainders','weather_nut_driver_sw7','weather_nut_driver_half','weather_nut_driver_7_16','weather_wire_rope_cutter','weather_adjustable_wrench','weather_tape_measure_bt5m','weather_mast_grease_21030']:
            page.select_option('#weather-focus',identity);capture(page,identity)
        page.uncheck('#weather-composed');s=page.evaluate('scienceGymWeatherComposition()')
        check('base_restores_exactly_one_logger_and_cart',s['baseVisibility']['hobo_u30'] and s['baseVisibility']['utility_cart'] and s['floorVisibility']==[True] and not any(m['visible'] for m in s['modules']))
        page.check('#weather-composed');page.select_option('#asset-select','hobo_u30');s=page.evaluate('scienceGymWeatherComposition()')
        check('base_logger_inspector_returns_to_base_state',not s['enabled'] and s['baseVisibility']['hobo_u30'])
        page.check('#weather-composed');page.locator('#workspace-targets button').first.click();s=page.evaluate('scienceGymWeatherComposition()')
        check('old_workspace_pose_does_not_claim_new_obstacle_check',not s['enabled'])
        page.set_viewport_size({'width':390,'height':844});check('mobile_has_no_page_overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        check('no_browser_errors',not errors,errors=errors)
        altered=json.loads(json.dumps(record));altered['modules'][0]['geometry']['sha256']='0'*64
        page.route('**/assets/cooling_lab_v1/weather_scene_binding.json',lambda route:route.fulfill(status=200,content_type='application/json',body=json.dumps(altered)))
        page.reload(wait_until='domcontentloaded');page.wait_for_function('document.getElementById("error").textContent.length>0',timeout=180000)
        check('stale_composition_refused_before_ready',page.locator('html').get_attribute('data-weather-composition-loaded') is None and '版本不一致' in page.locator('#error').inner_text())
        version=b.version;b.close()
    paths=[Path(__file__),HERE/'index.html',HERE/'main.js',HERE/'weather_composition.js',HERE/'render_batches.js',HERE/'style.css',ROOT/'assets/cooling_lab_v1/weather_scene_binding.json',ROOT/'assets/cooling_lab_v1/weather_scene_binding_checks.json']
    out=dict(schema_version=1,passed=True,checks=checks,captures=captures,browser=version,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in paths],
        scope='Complete-laboratory static composition and identity-preserving alternatives. No accepted initial state, robot transition or execution.')
    (HERE/'WEATHER_COMPOSITION_VERIFICATION.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(dict(passed=True,checks=len(checks),captures=len(captures))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--browser',required=True);parser.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/index.html');args=parser.parse_args();run(args.browser,args.url)
