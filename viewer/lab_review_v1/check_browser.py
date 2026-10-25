"""Exercise the real local review UI and retain exact-revision visual evidence."""
import argparse
import hashlib
import io
import json
from pathlib import Path
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run(url,browser):
    dest=HERE/'evidence';dest.mkdir(exist_ok=True);errors=[];checks=[];captures=[]
    def check(name,passed,**data):
        checks.append(dict(name=name,passed=bool(passed),**data))
        if not passed:raise AssertionError(name)
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=b.new_page(viewport={'width':1600,'height':1100},device_scale_factor=1)
        page.set_default_timeout(60000)
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(url,wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.sceneLoaded === "true"',timeout=120000)
        expected=json.loads((ROOT/'assets/cooling_lab_v1/scene.json').read_text())
        check('all_models_loaded',int(page.locator('html').get_attribute('data-asset-count'))==len(expected['assets']))
        actual_ids=page.locator('#asset-select option').evaluate_all('options=>options.map(o=>o.value).filter(Boolean)')
        check('all_asset_identities_loaded',set(actual_ids)=={a['id'] for a in expected['assets']})
        check('render_batch_geometry_preserved',page.locator('html').get_attribute('data-geometry-preserved')=='true')
        inventory_count=page.locator('#inventory tr').count()
        check('paper_facility_camera_and_selected_robot_requirements',inventory_count==66)
        check('current_inventory_excludes_historical_robot_requirements','60/63' in page.locator('#inventory-coverage').inner_text() and '历史选型 3 项' in page.locator('#inventory-coverage').inner_text())
        check('routes_rendered',page.locator('#route-table tr').count()==7)
        check('open_hand_selection_visible','Inspire FTP' in page.locator('#pilot-policy').inner_text() and '场景已使用 G1' in page.locator('#pilot-policy').inner_text())
        check('new_robot_resource_preview_link',page.locator('a[href="../robot_resource_review_v1/index.html"]').count()==1)
        check('sensor_only_policy_visible','传感器闭环' in page.locator('#pilot-policy').inner_text())
        check('branch_readiness_not_execution_credit',page.locator('#branch-progress tr').count()==11 and '通过 0 / 11' in page.locator('#pilot-counts').inner_text())
        def capture(name):
            data=page.locator('#viewport').screenshot();path=dest/(name+'.png');path.write_bytes(data)
            captures.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)));return data
        check('default_is_inside_complete_room',page.locator('html').get_attribute('data-camera-mode')=='room' and page.locator('#show-walls').is_checked() and page.locator('html').get_attribute('data-room-shell-visible')=='true')
        check('default_annotations_off',not page.locator('#show-space').is_checked() and not page.locator('#show-labels').is_checked())
        capture('overview')
        camera_before=page.locator('html').get_attribute('data-camera-position')
        page.locator('#walk-controls [data-move="forward"]').click()
        check('room_viewpoint_can_move',page.locator('html').get_attribute('data-camera-position')!=camera_before)
        canvas=page.locator('#viewport canvas');canvas.focus()
        for _ in range(60):page.keyboard.press('ArrowRight')
        check('room_viewpoint_stops_at_obstacle',page.locator('html').get_attribute('data-camera-blocked')=='true')
        check('room_viewpoint_height',page.locator('html').get_attribute('data-camera-position').endswith(',1.650'))
        for view in ['indoor','details','service','rear','outdoor','optics','wet','annex','coating','all','top']:
            page.locator('button[data-view="'+view+'"]').click();page.wait_for_timeout(250)
            check('view_'+view,page.locator('html').get_attribute('data-view')==view)
            capture(view)
            check('shell_mode_'+view,page.locator('#show-walls').is_checked()==(view not in ['all','top']))
        page.locator('button[data-view=indoor]').click();capture('full_walls');page.locator('#show-walls').uncheck()
        for identity in ['eko_ms56','eko_ms402','hobo_u30','cary','nicolet','bath','g1','caliper','driver','tray_white','waterjet','camera_head','camera_wrist_left','camera_wrist_right','tc_01',
            'wire_stripper','terminal_driver','tweezers_white','fill_jug','ambient_rtd','tc_transition_kit','nano_pe_stock','ldpe_stock','mylar_stock','masking_tape','calibration_block_stock','utility_cart','oily_waste_can',
            'fine_cutter','meter_leads_white','meter_leads_black','workholding_kit','deburring_tool','g1_spare_battery','g1_disconnected_charger','coating_white_stock','coating_black_stock','silver_paste_stock']:
            page.locator('#asset-select').select_option(identity);page.locator('#isolate').check();page.wait_for_timeout(200)
            check('inspect_'+identity,page.locator('html').get_attribute('data-selected-asset')==identity)
            closed=capture(identity+'_closed')
            if identity=='tc_01':
                check('probe_not_connected','尚未装接' in page.locator('#asset-detail').inner_text())
                page.locator('#asset-views [data-direction="top"]').click();capture('tc_01_top')
            if identity in ['fine_cutter','meter_leads_white','meter_leads_black','workholding_kit','deburring_tool','g1_spare_battery','g1_disconnected_charger','coating_white_stock','coating_black_stock','silver_paste_stock']:
                check('dimensions_basis_visible_'+identity,('推断尺寸（待核实）' if identity in ['coating_white_stock','coating_black_stock','silver_paste_stock'] else '厂家标注尺寸') in page.locator('#asset-detail').inner_text())
                for direction in ['front','back','side']:
                    page.locator('#asset-views [data-direction="'+direction+'"]').click();capture(identity+'_'+direction)
            if identity.startswith('camera_'):
                check('camera_installation_not_qualified_'+identity,'衬垫预紧' in page.locator('#asset-detail').inner_text())
                for direction in ['front','back','side']:
                    page.locator('#asset-views [data-direction="'+direction+'"]').click();capture(identity+'_'+direction)
            if identity in ['g1']:
                check('hand_hypothesis_visible_'+identity,'官方' in page.locator('#asset-detail').inner_text())
                for direction in ['front','back','side']:
                    page.locator('#asset-views [data-direction="'+direction+'"]').click()
                    check(identity+'_view_'+direction,page.locator('html').get_attribute('data-asset-view')==direction)
                    capture(identity+'_'+direction)
                page.locator('#asset-views [data-direction="front"]').click();closed=capture(identity+'_front_rest')
            if identity in ['wire_stripper','terminal_driver','tweezers_white','fill_jug','ambient_rtd','tc_transition_kit','nano_pe_stock','ldpe_stock','mylar_stock','masking_tape','calibration_block_stock',
                            'fine_cutter','meter_leads_white','meter_leads_black','workholding_kit','deburring_tool','g1_spare_battery','g1_disconnected_charger','coating_white_stock','coating_black_stock','silver_paste_stock']:
                check('supply_inferences_visible_'+identity,'推断' in page.locator('#asset-detail').inner_text())
                check('supply_units_bound_'+identity,'逐件候选' in page.locator('#asset-detail').inner_text())
                page.locator('#asset-views [data-direction="top"]').click();capture(identity+'_top')
            if identity in ['coating_white_stock','coating_black_stock','silver_paste_stock']:
                page.locator('#asset-views [data-direction="front"]').click();closed=capture(identity+'_front_rest')
            if identity in ['hobo_u30','cary','nicolet','bath','g1','caliper','waterjet','oily_waste_can','coating_white_stock','coating_black_stock','silver_paste_stock']:
                page.locator('#state-slider').fill('100');page.locator('#state-slider').dispatch_event('input');page.wait_for_timeout(200)
                opened=capture(identity+'_open')
                if identity in ['coating_white_stock','coating_black_stock','silver_paste_stock']:
                    check('separated_cap_stays_in_frame_'+identity,page.locator('html').get_attribute('data-inspection-in-frame')=='true')
                diff=ImageChops.difference(Image.open(io.BytesIO(closed)).convert('RGB'),Image.open(io.BytesIO(opened)).convert('RGB'))
                count=sum(1 for pixel in diff.getdata() if max(pixel)>20)
                check('visible_open_state_'+identity,count>100,changed_pixels=count)
                if identity=='g1':
                    page.locator('#state-slider').fill('0');page.locator('#state-slider').dispatch_event('input');page.wait_for_timeout(150)
                    restored=capture(identity+'_restored')
                    diff=ImageChops.difference(Image.open(io.BytesIO(closed)).convert('RGB'),Image.open(io.BytesIO(restored)).convert('RGB'))
                    check('hand_rest_pose_restored_'+identity,sum(max(p)>20 for p in diff.getdata())<100)
        page.locator('#isolate').uncheck();page.locator('button[data-view="top"]').click()
        page.locator('#measure').click();canvas=page.locator('#viewport canvas');canvas.scroll_into_view_if_needed();box=canvas.bounding_box()
        for x in [.50,.55]:page.mouse.click(box['x']+box['width']*x,box['y']+box['height']*.50)
        check('surface_measurement',page.locator('html').get_attribute('data-measurement-complete')=='true',value=page.locator('#measurement').inner_text())
        page.locator('#clear-measure').click();check('clear_measurement',not page.locator('#measurement').is_visible())
        page.locator('#search').fill('DEX5');check('historical_hands_not_current_requirements',page.locator('#inventory tr').count()==2 and '历史选型' in page.locator('#inventory').inner_text() and '不参与当前验收' in page.locator('#inventory').inner_text())
        page.locator('#search').fill('');page.locator('#filter').select_option('placed');placed=page.locator('#inventory tr').count()
        page.locator('#filter').select_option('missing');missing=page.locator('#inventory tr').count()
        page.locator('#filter').select_option('historical');historical=page.locator('#inventory tr').count()
        check('inventory_filter_partition',placed+missing+historical==inventory_count and historical==3 and missing==3,with_geometry=placed,without_geometry=missing,historical=historical)
        page.locator('#filter').select_option('all')
        expected_workspace=json.loads((ROOT/'assets/cooling_lab_v1/workspace_checks.json').read_text())
        check('workspace_targets_visible',page.locator('#workspace-targets tr').count()==len(expected_workspace['targets'])==71)
        page.locator('button[data-target="cary_front"]').click();check('static_workspace_pose_selected',page.locator('html').get_attribute('data-workspace-pose')=='cary_front');capture('g1_cary_access')
        page.locator('#workspace-reset').click();check('static_workspace_pose_reset',page.locator('html').get_attribute('data-workspace-pose') is None)
        page.locator('#review-notes').fill('QA temporary comment; not acceptance')
        with page.expect_download() as event:page.locator('#export-notes').click()
        download=event.value;record=json.loads(Path(download.path()).read_text())
        check('review_export_revision',record['kind']=='review_comments_not_acceptance' and record['scene_revision']==sha(ROOT/'assets/cooling_lab_v1/scene.json'))
        # Wait for the application's verified model load, not the browser load
        # event competing with large GLB decoding under software rendering.
        page.reload(wait_until='domcontentloaded');page.wait_for_function('document.documentElement.dataset.sceneLoaded === "true"',timeout=120000)
        check('notes_persist',page.locator('#review-notes').input_value()=='QA temporary comment; not acceptance')
        page.locator('#review-notes').fill('');page.evaluate('localStorage.clear()')
        page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(250)
        check('mobile_no_horizontal_overflow',not page.evaluate('document.documentElement.scrollWidth > innerWidth'))
        mobile=dest/'mobile.png';page.screenshot(path=str(mobile),full_page=True);captures.append(dict(path=str(mobile.relative_to(ROOT)),sha256=sha(mobile)))
        check('no_browser_errors',not errors and page.locator('#error').inner_text()=='',errors=errors)
        bad=b.new_page();original=(ROOT/'assets/cooling_lab_v1/scene.json').read_text()
        bad.route('**/assets/cooling_lab_v1/scene.json',lambda route:route.fulfill(status=200,content_type='application/json',body=original+' '))
        bad.goto(url);bad.wait_for_function('document.getElementById("error").textContent.includes("版本")',timeout=10000)
        check('stale_scene_rejected',bad.locator('html').get_attribute('data-scene-loaded') is None and bad.locator('#layout-status').inner_text()=='未通过版本核对')
        version=b.version;b.close()
    files=[HERE/'index.html',HERE/'main.js',HERE/'style.css',HERE/'check_browser.py',HERE/'render_batches.js']+[ROOT/'assets/cooling_lab_v1'/n for n in ['scene.json','inventory.json','layout_checks.json','risk_register.json','floorplan.svg','workspace_checks.json','pilot_contract.json','readiness.json']]
    report=dict(passed=True,checks=checks,captures=captures,source_files=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in files],browser=version,
        software_renderer='Chromium SwiftShader',scope='Interactive UI and visible geometry states only; images do not establish product fidelity or safety')
    (HERE/'VISUAL_VERIFICATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(passed=True,checks=len(checks),captures=len(captures)),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8769/viewer/lab_review_v1/index.html');p.add_argument('--browser',required=True)
    args=p.parse_args();run(args.url,args.browser)
