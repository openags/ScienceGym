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
        check('all_components_visible',page.locator('#allocation-components tr').count()==154)
        check('all_branches_available',page.locator('#allocation-branch option').count()==12)
        check('four_reference_models_excluded',page.locator('#allocation-references .risk-card').count()==4)
        summary=page.locator('#allocation-counts').inner_text()
        check('quantities_separated_from_nonstock_requirements','69 项已有选定数量' in summary and
              '77 项数量或规格待分配' in summary and '8 项状态／坐标／校准要求' in summary and '154 项均未完成验收' in summary)
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
        check('selected_quantities_filter',page.locator('#allocation-components tr').count()==69)
        page.locator('#allocation-search').fill('heater_white')
        check('search_matches_physical_identity',page.locator('#allocation-components tr').count()==1 and 'equipment:HEATER' in page.locator('#allocation-components').inner_text())
        page.locator('#allocation-search').fill('');page.locator('#allocation-filter').select_option('unallocated')
        check('unknown_quantities_not_zero',page.locator('#allocation-components tr').count()==77 and '待分配' in page.locator('#allocation-components').inner_text())
        page.locator('#allocation-filter').select_option('quantified');page.locator('#allocation-search').fill('robot:')
        check('robot_and_hands_are_component_bindings',page.locator('#allocation-components tr').count()==6 and
              all(page.locator('[data-component="'+r+':component_1"]').count()==1 for r in ['robot:G1_29DOF','robot:INSPIRE_FTP_LEFT','robot:INSPIRE_FTP_RIGHT']))
        check('unbound_native_camera_remains_explicit','缺少 1 台候选绑定' in page.locator('[data-component="robot:HEAD_RGBD:component_1"]').inner_text())
        page.locator('#allocation-components').scroll_into_view_if_needed();capture('robot_components')
        page.locator('#allocation-search').fill('');page.locator('#allocation-filter').select_option('nonstock')
        check('all_eight_nonstock_requirements_preserved',page.locator('#allocation-components tr').count()==8 and
              all('要求仍待完成' in t for t in page.locator('#allocation-components tr').all_inner_texts()))
        page.locator('#allocation-kind').select_option('acceptance_condition')
        check('three_calibrations_remain_visible',page.locator('#allocation-components tr').count()==3 and
              all('不计库存数量' in t for t in page.locator('#allocation-components tr').all_inner_texts()))
        page.locator('[data-component="robot:HEAD_RGBD:component_4"] summary').click()
        check('calibration_evidence_not_fictitious_stock','cannot be satisfied by counting inventory' in page.locator('[data-component="robot:HEAD_RGBD:component_4"] details').inner_text())
        page.locator('#allocation-components').scroll_into_view_if_needed();capture('calibration_requirements')
        page.locator('#allocation-kind').select_option('output_state')
        check('three_output_states_are_not_stock',page.locator('#allocation-components tr').count()==3 and
              '白色完成态' not in page.locator('#allocation-components').inner_text())
        page.locator('#allocation-components').scroll_into_view_if_needed();capture('output_states')
        page.locator('#allocation-kind').select_option('all');page.locator('#allocation-filter').select_option('quantified')
        page.locator('#allocation-search').fill('consumables:consumable_08')
        paste=page.locator('[data-component="consumables:consumable_08:component_1"]');paste.locator('summary').click()
        check('one_bottle_does_not_close_consumption_budget','1 瓶（选定）' in paste.inner_text() and 'Applied mass' in paste.inner_text() and '完整性未验收' in paste.inner_text())
        paste.scroll_into_view_if_needed();capture('consumable_quantity_basis')
        page.locator('#allocation-search').fill('');page.locator('#allocation-filter').select_option('all');page.locator('#allocation-kind').select_option('interface_requirement')
        check('interface_requirements_remain_open',page.locator('#allocation-components tr').count()==24)
        page.locator('#allocation-kind').select_option('all');page.locator('#allocation-filter').select_option('unallocated')
        check('unified_identities_include_temporary_stock',page.locator('#identity-rows tr').count()==118 and '2 根临时扎带' in page.locator('#identity-summary').inner_text())
        check('installation_needs_expose_missing_supplies',page.locator('#installation-needs tr').count()==16 and '1 项尚无候选物品' in page.locator('#installation-summary').inner_text())
        silicone=page.locator('[data-need="weather_need_silicone_grease"]').inner_text()
        check('silicone_is_one_independent_unaccepted_candidate','1 管' in silicone and 'weather_silicone_grease_93003' in silicone and '候选未验收' in silicone and '21030' not in silicone)
        check('pack_and_waste_reservation_displayed','1 包' in page.locator('[data-need="weather_need_wipes"]').inner_text() and '3 L' in page.locator('[data-need="weather_need_residue_collection"]').inner_text())
        check('clean_packaging_gap_is_visible','缺少候选物品' in page.locator('[data-need="weather_need_clean_packaging_collection"]').inner_text())
        page.locator('#installation-panel').scroll_into_view_if_needed();capture('installation_needs')
        page.locator('#identity-filter').select_option('reused')
        check('logger_and_cart_are_two_reused_identities',page.locator('#identity-rows tr').count()==2 and
              page.locator('[data-identity="hobo_u30"]').count()==1 and page.locator('[data-identity="utility_cart"]').count()==1)
        page.locator('#identity-panel').scroll_into_view_if_needed();capture('shared_identities')
        page.locator('#identity-filter').select_option('weather')
        check('weather_identities_include_two_temporary_ties',page.locator('#identity-rows tr').count()==39 and
              page.locator('[data-identity="weather_temporary_leg"]').count()==1 and page.locator('[data-identity="weather_temporary_brace"]').count()==1)
        page.locator('#identity-filter').select_option('unplaced')
        check('unpacked_layout_removes_missing_location_flags_without_qualification',page.locator('#identity-rows tr').count()==0 and
              page.locator('[data-identity="weather_tape_measure_bt5m"]').count()==0 and page.locator('[data-identity="weather_ground_design"]').count()==0)
        page.set_viewport_size({'width':390,'height':844})
        check('inventory_mobile_no_overflow',not page.evaluate('document.documentElement.scrollWidth > innerWidth'))
        page.set_viewport_size({'width':1440,'height':1000})
        check('no_browser_errors',not errors)
        # A real changed source must prevent a stale report from being rendered.
        page.route('**/assets/cooling_lab_v1/scene.json',lambda route:route.fulfill(status=200,content_type='application/json',body='{}'))
        page.reload();page.wait_for_function('document.documentElement.dataset.allocationLoaded === "error"')
        check('stale_scene_rejected','分配记录已过期' in page.locator('#allocation-error').inner_text())
        check('stale_rows_not_rendered',page.locator('#allocation-components tr').count()==0)
        page.unroute('**/assets/cooling_lab_v1/scene.json')
        page.route('**/assets/cooling_lab_v1/component_quantity_policy.json',lambda route:route.fulfill(status=200,content_type='application/json',body='{}'))
        page.reload();page.wait_for_function('document.documentElement.dataset.allocationLoaded === "error"')
        check('stale_quantity_policy_rejected','component_quantity_policy.json' in page.locator('#allocation-error').inner_text() and page.locator('#allocation-components tr').count()==0)
        page.unroute('**/assets/cooling_lab_v1/component_quantity_policy.json')
        page.route('**/assets/cooling_lab_v1/stock_cutplan.json',lambda route:route.fulfill(status=200,content_type='application/json',body='{}'))
        page.reload();page.wait_for_function('document.documentElement.dataset.allocationLoaded === "error"')
        check('stale_cutplan_rejected','stock_cutplan.json' in page.locator('#allocation-error').inner_text() and page.locator('#stock-plan polygon').count()==0)
        page.unroute('**/assets/cooling_lab_v1/stock_cutplan.json')
        page.route('**/assets/cooling_lab_v1/weather_scene_binding.json',lambda route:route.fulfill(status=200,content_type='application/json',body='{}'))
        page.reload();page.wait_for_function('document.documentElement.dataset.allocationLoaded === "error"')
        check('stale_composition_blocks_unified_inventory','weather_scene_binding.json' in page.locator('#allocation-error').inner_text() and page.locator('#identity-rows tr').count()==0 and page.locator('#installation-needs tr').count()==0)
        b.close()
    paths=[HERE/'allocation.html',HERE/'allocation.js',HERE/'allocation.css',HERE/'style.css',Path(__file__),ROOT/'assets/cooling_lab_v1/campaign_allocation.json',ROOT/'assets/cooling_lab_v1/stock_cutplan.json']
    paths += [ROOT/'assets/cooling_lab_v1/laboratory_inventory.json',ROOT/'assets/cooling_lab_v1/laboratory_inventory_checks.json']
    record=dict(passed=all(c['passed'] for c in checks),checks=checks,captures=captures,
                source_artifacts=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in paths])
    (HERE/'ALLOCATION_VERIFICATION.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(dict(passed=record['passed'],checks=len(checks),captures=len(captures))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--browser',required=True);parser.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/allocation.html')
    a=parser.parse_args();run(a.url,a.browser)
