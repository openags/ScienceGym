"""Exercise the real tool inspector and retain matched model views."""
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
        path=HERE/'evidence'/('fastener_'+name+'.png');page.locator('#lift-viewport').screenshot(path=str(path))
        captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=b.new_page(viewport={'width':1500,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(url,wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.toolsLoaded === "true"',timeout=120000)
        check('four_tools_eight_samples',page.locator('#tool-select option').count()==12)
        check('boundaries_visible','未验收' in page.locator('#tool-status').inner_text() and 'AS-Drive' in page.locator('body').inner_text())
        check('installed_access_obstructions_visible','36' in page.locator('#tool-access-findings').inner_text() and '32' in page.locator('#tool-access-findings').inner_text() and '4 个' in page.locator('#tool-access-findings').inner_text())
        identities=page.locator('#tool-select option').evaluate_all('rows=>rows.map(r=>r.value)')
        for identity in identities:
            page.select_option('#tool-select',identity);probe=page.evaluate('scienceGymFastenerInspection()')
            check('only_selected_'+identity,len(probe['visible'])==1 and probe['selected']==identity and probe['visible'][0]['id']==identity)
            for view in (['oblique','top','side','end'] if identity.startswith(('wiha','stahlwille')) else ['oblique']):
                page.locator('[data-view="'+view+'"]').click();page.wait_for_timeout(150);capture(page,identity+'_'+view)
        page.select_option('#tool-select','platform_M3_countersunk');page.check('#tool-section');page.wait_for_timeout(150)
        check('inspection_section_enabled',page.evaluate('scienceGymFastenerInspection().section'));capture(page,'platform_socket_section')
        page.uncheck('#tool-section');check('inspection_section_reversible',not page.evaluate('scienceGymFastenerInspection().section'))
        check('no_browser_errors',not errors)
        page.set_viewport_size({'width':390,'height':844})
        check('mobile_page_fits',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        # A tampered tool source must be rejected before rendering its geometry.
        page.route('**/assets/cooling_lab_v1/fastener_tools.json',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps({**json.loads((ROOT/'assets/cooling_lab_v1/fastener_tools.json').read_text()),'source_artifacts':[{'path':'assets/cooling_lab_v1/fastener_tools_sources.json','sha256':'0'*64}]})))
        page.reload(wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.toolsLoaded === "error"')
        check('stale_source_rejected',page.locator('#lift-viewport canvas').count()==0 and '不一致' in page.locator('#lift-error').inner_text())
        version=b.version;b.close()
    files=[Path(__file__),HERE/'fasteners.html',HERE/'fasteners.js',HERE/'style.css',HERE/'lift.css',ROOT/'assets/cooling_lab_v1/fastener_tools.json',ROOT/'assets/cooling_lab_v1/fastener_tool_checks.json',ROOT/'assets/cooling_lab_v1/tool_access_inspection.json']
    report=dict(passed=True,checks=checks,captures=captures,source_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in files],browser=version,
        scope='Actual isolated asset inspector and fail-closed source binding; no appearance acceptance or robot operation credit')
    (HERE/'FASTENER_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,checks=len(checks),captures=len(captures))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--browser',required=True);p.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/fasteners.html');a=p.parse_args();run(a.browser,a.url)
