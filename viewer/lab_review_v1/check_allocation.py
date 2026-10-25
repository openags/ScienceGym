"""Exercise branch filtering and stale-evidence rejection in the allocation UI."""
import argparse
import hashlib
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def run(url, browser):
    checks=[]; captures=[]; errors=[]
    def check(name, passed):
        checks.append(dict(name=name, passed=bool(passed)))
        if not passed: raise AssertionError(name)
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage'])
        page=b.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(url);page.wait_for_function('document.documentElement.dataset.allocationLoaded === "true"')
        check('all_components_visible',page.locator('#allocation-components tr').count()==150)
        check('all_branches_available',page.locator('#allocation-branch option').count()==12)
        check('four_reference_models_excluded',page.locator('#allocation-references .risk-card').count()==4)
        check('unallocated_quantities_exposed','117 项用量待分配' in page.locator('#allocation-counts').inner_text())
        def capture(name):
            path=HERE/'evidence'/('allocation_'+name+'.png');page.screenshot(path=str(path))
            captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
        capture('overview')
        check('stock_sheets_tubes_and_profiles_visible',page.locator('#stock-sheet option').count()==40 and page.locator('#stock-tubes p').count()==8 and page.locator('#stock-profiles p').count()==4 and page.locator('#stock-angles p').count()==6)
        for identity,count,label in [('acrylic_stock/raw_acrylic_sheet_1',1,'305 × 280'),('mylar_stock/raw_film_1',3,'底板贴膜'),('mylar_stock/raw_film_3',2,'支撑管包覆'),('aluminum_sheet_stock/raw_aluminum_1_5mm',4,'固定遮阳带'),('aluminum_sheet_stock/raw_aluminum_5mm',2,'180 × 180'),('nano_pe_stock/raw_film_5',1,'恢复用膜'),('ldpe_stock/raw_film_6',1,'红外光学试片预留'),('cover_adhesive_stock/raw_adhesive_09',1,'恢复跟踪构型'),('cover_adhesive_stock/raw_adhesive_12',1,'顶盖胶环')]:
            page.locator('#stock-sheet').select_option(identity)
            check('stock_profile_'+identity,page.locator('#stock-plan polygon').count()==count and label in page.locator('#stock-cuts').inner_text())
            if identity=='mylar_stock/raw_film_1':
                check('mylar_selected_dimensions','500 × 300 mm · 厚 0.012 mm' in page.locator('#stock-dimensions').inner_text())
                page.locator('#stock-panel').scroll_into_view_if_needed();capture('mylar_cutplan')
            if identity=='cover_adhesive_stock/raw_adhesive_12':
                check('adhesive_nominal_gauge_visible','厚 0.058 mm' in page.locator('#stock-dimensions').inner_text())
                page.locator('#stock-panel').scroll_into_view_if_needed();capture('aperture_adhesive')
        for identity,count,label in [('frame_machining_stock/frame_plate_3mm',10,'底板连接板'),('frame_machining_stock/frame_clamp_block_20mm',8,'立柱下夹块'),('frame_machining_stock/frame_carriage_plate_4mm',2,'需铣至 3.75 mm')]:
            page.locator('#stock-sheet').select_option(identity)
            check('frame_stock_profile_'+identity,page.locator('#stock-plan polygon').count()==count and label in page.locator('#stock-cuts').inner_text())
        page.locator('#stock-panel').scroll_into_view_if_needed();capture('frame_carriage_facing')
        page.locator('details').filter(has=page.locator('#stock-tubes')).locator('summary').click()
        check('stock_tube_details_visible',page.locator('#stock-tubes').is_visible())
        check('white_and_black_uprights_not_mislabelled',sum('白色装置 · 立柱铝管' in t for t in page.locator('#stock-tubes p').all_inner_texts())==2 and sum('黑色装置 · 立柱铝管' in t for t in page.locator('#stock-tubes p').all_inner_texts())==2)
        page.set_viewport_size({'width':390,'height':844})
        check('mobile_no_overflow',not page.evaluate('document.documentElement.scrollWidth > innerWidth'))
        page.set_viewport_size({'width':1440,'height':1000})
        page.locator('#allocation-branch').select_option('BUILD_PAIR')
        text=page.locator('#branch-allocation').inner_text()
        check('two_initial_jacks_allocated','白色装置升降台 → lab_jack_white' in text and '黑色装置升降台 → lab_jack_black' in text)
        page.locator('#allocation-branch').select_option('PID_POWER')
        text=page.locator('#branch-allocation').inner_text()
        check('paired_heater_allocation','白色发射体 → heater_white' in text and '黑色发射体 → heater' in text)
        check('paired_smu_allocation','白色加热通道 → smu_white' in text and '黑色加热通道 → smu_black' in text)
        page.locator('#branch-allocation').scroll_into_view_if_needed();capture('pid_pair')
        page.locator('#allocation-branch').select_option('MAP_CLEAR_NIGHT')
        text=page.locator('#branch-allocation').inner_text()
        check('same_white_apparatus_reused','apparatus_white' in text and 'apparatus_black' not in text)
        check('seven_map_probes_named','白色发射体 → tc_01' in text and '热分布点 6 → tc_07' in text and 'tc_08' not in text)
        page.locator('#allocation-branch').select_option('all');page.locator('#allocation-filter').select_option('quantified')
        check('selected_quantities_filter',page.locator('#allocation-components tr').count()==33)
        page.locator('#allocation-search').fill('heater_white')
        check('search_matches_physical_identity',page.locator('#allocation-components tr').count()==1 and 'equipment:HEATER' in page.locator('#allocation-components').inner_text())
        page.locator('#allocation-search').fill('');page.locator('#allocation-filter').select_option('unallocated')
        check('unknown_quantities_not_zero',page.locator('#allocation-components tr').count()==117 and '待分配' in page.locator('#allocation-components').inner_text())
        check('no_browser_errors',not errors)
        # A real changed source must prevent a stale report from being rendered.
        page.route('**/assets/cooling_lab_v1/scene.json',lambda route:route.fulfill(status=200,content_type='application/json',body='{}'))
        page.reload();page.wait_for_function('document.documentElement.dataset.allocationLoaded === "error"')
        check('stale_scene_rejected','分配记录已过期' in page.locator('#allocation-error').inner_text())
        check('stale_rows_not_rendered',page.locator('#allocation-components tr').count()==0)
        page.unroute('**/assets/cooling_lab_v1/scene.json')
        page.route('**/assets/cooling_lab_v1/stock_cutplan.json',lambda route:route.fulfill(status=200,content_type='application/json',body='{}'))
        page.reload();page.wait_for_function('document.documentElement.dataset.allocationLoaded === "error"')
        check('stale_cutplan_rejected','stock_cutplan.json' in page.locator('#allocation-error').inner_text() and page.locator('#stock-plan polygon').count()==0)
        b.close()
    paths=[HERE/'allocation.html',HERE/'allocation.js',HERE/'allocation.css',HERE/'style.css',Path(__file__),ROOT/'assets/cooling_lab_v1/campaign_allocation.json',ROOT/'assets/cooling_lab_v1/stock_cutplan.json']
    record=dict(passed=all(c['passed'] for c in checks),checks=checks,captures=captures,
                source_artifacts=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in paths])
    (HERE/'ALLOCATION_VERIFICATION.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(dict(passed=record['passed'],checks=len(checks),captures=len(captures))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--browser',required=True);parser.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/allocation.html')
    a=parser.parse_args();run(a.url,a.browser)
