"""Inspect actual browser poses, unresolved states and stale-source refusal."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from playwright.sync_api import sync_playwright
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run(browser,url):
    checks=[];captures=[];errors=[]
    reports={k:json.loads((ROOT/'assets/cooling_lab_v1'/n).read_text()) for k,n in [('installed','weather_workspace_checks.json'),('preparation','weather_preparation_workspace_checks.json')]}
    def check(name,passed):
        checks.append(dict(name=name,passed=bool(passed)))
        if not passed:raise AssertionError(name)
    def capture(page,name):
        page.wait_for_timeout(200);path=HERE/'evidence'/('weather_workspace_'+name+'.png')
        page.locator('#lift-viewport').screenshot(path=str(path));captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=b.new_page(viewport={'width':1500,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url,wait_until='domcontentloaded')
        page.wait_for_function('document.documentElement.dataset.workspaceLoaded === "true"',timeout=120000)
        check('nominal_standing_and_execution_limits_visible','检查名义站立与多组静态屈膝配置' in page.locator('#workspace-limits').inner_text() and '没有机器人执行动画' in page.locator('main').inner_text())
        check('partial_state_and_two_person_source_visible','逐件记为范围外' in page.locator('#preparation-basis').inner_text() and '建议两人合拢桅杆' in page.locator('#preparation-basis').inner_text())
        for context,report in reports.items():
            page.select_option('#workspace-context',context)
            for target in report['targets']:
                page.select_option('#workspace-target',target['id']);s=page.evaluate('scienceGymWeatherWorkspace()');r=target['result'];valid=r['position_candidate']
                check(context+'_'+target['id']+'_actual_state',s['positionCandidate']==valid and s['robotVisible']==valid and s['robotParts']==93 and s['groundParts']==7 and s['rigGroups']==(6 if valid else 0) and s['contextParts']==(351 if context=='installed' else 161) and s['storageVisible']==(context=='installed') and s['toolsVisible']==int('tool_pose' in target) and not s['robotUseQualified'] and not s['fullWorkspaceQualified'])
                if valid:
                    check(context+'_'+target['id']+'_all_actual_mesh_transforms',set(s['robotTransforms'])==set(r['visual_transforms']) and all(np.allclose(np.array(s['robotTransforms'][n]).reshape(4,4),m,atol=1e-10,rtol=0) for n,m in r['visual_transforms'].items()) and all(np.allclose(np.array(s['rigTransforms'][n]).reshape(4,4),m,atol=1e-10,rtol=0) for n,m in r['rig_transforms'].items()))
                else:check(context+'_'+target['id']+'_failure_visible','未找到位置候选' in page.locator('#workspace-result').inner_text() and not s['robotTransforms'])
                if context=='preparation' or target['id'] in ['tool_mount_1_nut_left','tool_rs3_clamp','temperature_coil_upper','wind_mount']:
                    capture(page,context+'_'+target['id'])
            page.check('#workspace-whole');capture(page,context+'_whole');page.uncheck('#workspace-whole')
        for view in ['front','rear','top']:
            page.select_option('#workspace-target','wind_mount');page.locator('[data-view="'+view+'"]').click();capture(page,'preparation_wind_mount_'+view)
        for view in ['front','rear','top']:
            page.select_option('#workspace-target','free_plug_tray');page.locator('[data-view="'+view+'"]').click();capture(page,'preparation_free_plug_tray_'+view)
        page.set_viewport_size({'width':390,'height':844});check('mobile_fits',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        check('no_browser_errors',not errors)
        altered=json.loads((ROOT/'assets/cooling_lab_v1/weather_preparation_assets.json').read_text());altered['geometry']['sha256']='0'*64
        page.route('**/assets/cooling_lab_v1/weather_preparation_assets.json',lambda route:route.fulfill(status=200,content_type='application/json',body=json.dumps(altered)))
        page.reload(wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.workspaceLoaded === "error"',timeout=120000)
        check('changed_preparation_source_rejected',page.locator('#lift-viewport canvas').count()==0);version=b.version;b.close()
    paths=[Path(__file__),HERE/'weather_workspace.html',HERE/'weather_workspace.js',HERE/'style.css',HERE/'lift.css']+[ROOT/'assets/cooling_lab_v1'/n for n in ['weather_workspace_checks.json','weather_preparation_workspace_checks.json','weather_preparation_assets.json','weather_preparation_checks.json','weather_station_assets.json','weather_storage_assets.json','outdoor_ground_assets.json','outdoor_ground_checks.json']]
    report=dict(passed=True,checks=checks,captures=captures,browser=version,source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in paths],scope='Versioned static asset-space review with all actual robot/rig mesh poses checked. No execution or whole-body stability qualification.')
    (HERE/'WEATHER_WORKSPACE_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,checks=len(checks),captures=len(captures))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--browser',required=True);parser.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/weather_workspace.html');args=parser.parse_args();run(args.browser,args.url)
