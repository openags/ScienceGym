"""Inspect candidate/failed geometry, clipping pixels and stale-source rejection."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
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
        page.wait_for_function('document.documentElement.dataset.coverLoaded === "true"')
        snapshot=lambda:page.evaluate('window.scienceGymCoverInspection()')
        def capture(name):
            page.wait_for_timeout(150);data=page.locator('#lift-viewport').screenshot()
            path=HERE/'evidence'/('cover_'+name+'.png');path.write_bytes(data)
            captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
            return np.asarray(Image.open(io.BytesIO(data)).convert('RGB'),dtype=np.int16)
        for version,count in [('candidate',29),('legacy',14)]:
            page.locator('#cover-version').select_option(version);page.locator('#cover-group').select_option('all')
            check('exact_part_count_'+version,len(snapshot()['visible'])==count and all(m['version']==version for m in snapshot()['visible']))
            check('section_caps_match_display_'+version,len(snapshot()['sectionCaps'])==(17 if version=='candidate' else 0))
            for group in ['all','core','cover','lower','retention']:
                page.locator('#cover-group').select_option(group)
                check('selection_'+version+'_'+group,bool(snapshot()['visible']) and (group!='lower' or [m['name'] for m in snapshot()['visible']]==['cover_lower']))
                for view in ['oblique','front']:
                    page.locator('button[data-view="'+view+'"]').click();capture(version+'_'+group+'_'+view)
                if version=='candidate' and group=='retention':
                    page.locator('#cover-section').uncheck()
                    for view in ['top','bottom']:
                        page.locator('button[data-view="'+view+'"]').click();capture(version+'_'+group+'_'+view)
                    page.locator('#cover-section').check()
        page.locator('#cover-version').select_option('candidate');page.locator('#cover-group').select_option('all')
        page.locator('button[data-view="oblique"]').click();clipped=capture('candidate_section')
        page.locator('#cover-section').uncheck();full=capture('candidate_unclipped')
        check('clipping_changes_visible_geometry',np.sum(np.max(abs(clipped-full),axis=2)>12)>1000)
        check('clipping_does_not_remove_parts',len(snapshot()['visible'])==29 and all(not m['clipped'] for m in snapshot()['visible']))
        check('unclipped_has_no_diagnostic_caps',not snapshot()['sectionCaps'])
        page.locator('#cover-section').check();restored=capture('candidate_section_restored')
        check('clipping_restores_same_pixels',np.max(abs(restored-clipped))<=1)
        text=page.locator('body').inner_text()
        check('unaccepted_inference_scope_visible',all(t in text for t in ['已接入三种展示构型','工程推断','不代表力学平衡','0.1 μm','50 μm LDPE']))
        page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(150)
        check('mobile_no_overflow',page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        check('no_browser_errors',not errors)
        for name,path in [('candidate','**/geometry/apparatus_cover_candidate.glb'),('sections','**/geometry/apparatus_cover_sections.glb'),('legacy','**/geometry/cover_legacy_rejected.glb'),('source','**/apparatus_cover_sources.json'),('stock','**/cover_stock.json')]:
            page.route(path,lambda route:route.fulfill(status=200,body='stale content'));page.reload()
            page.wait_for_function('document.documentElement.dataset.coverLoaded === "error"')
            check('stale_'+name+'_fails_closed',page.locator('#lift-viewport canvas').count()==0 and bool(page.locator('#lift-error').inner_text()))
            page.unroute(path)
        b.close()
    paths=[HERE/n for n in ['cover.html','cover.js','check_cover.py','lift.css','style.css']]+[ROOT/'assets/cooling_lab_v1'/n for n in ['apparatus_cover_candidate.json','apparatus_cover_checks.json','apparatus_cover_sources.json','cover_legacy_rejected.json','apparatus_stock_reconciliation.json','cover_stock_checks.json']]
    report=dict(passed=True,checks=checks,captures=captures,
        source_artifacts=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in paths],
        scope='Static cover inspection with pinned three-configuration integration and stock evidence; clipping and failed-source handling only, not physical qualification')
    (HERE/'COVER_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,checks=len(checks),captures=len(captures))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--browser',required=True);parser.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/cover.html');a=parser.parse_args();run(a.url,a.browser)
