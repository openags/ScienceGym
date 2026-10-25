"""Exercise source-CAD inspection, transforms and missing/stale-source failures."""
import argparse
import hashlib
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(url, browser):
    checks, captures, errors = [], [], []

    def check(name, passed):
        checks.append(dict(name=name, passed=bool(passed)))
        if not passed:
            raise AssertionError(name)

    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=browser, args=['--no-sandbox', '--disable-dev-shm-usage'])
        page = b.new_page(viewport={'width': 1440, 'height': 1100})
        page.set_default_timeout(60000)
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(url)
        page.wait_for_function('document.documentElement.dataset.liftLoaded === "true"')
        snapshot = lambda: page.evaluate('window.scienceGymLiftInspection()')

        def capture(name):
            page.wait_for_timeout(150)
            path = HERE / 'evidence' / ('lift_' + name + '.png')
            page.locator('#lift-viewport').screenshot(path=str(path))
            captures.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path)))

        check('all_source_solids_loaded', len(snapshot()['visible']) == 86)
        check('six_groups_and_whole_assembly', page.locator('#lift-group option').count() == 7)
        check('actual_plate_hole_markers', snapshot()['markerCount'] == 29)
        check('source_topology_repair_and_limits_visible', '4 个支承块' in page.locator('#lift-finding').inner_text() and '原始失败网格仍保留' in page.locator('#lift-finding').inner_text())
        check('nominal_mount_and_unknown_paper_identity_visible', '三个装置参考模型已换入原尺寸 L200/M' in page.locator('body').inner_text() and '论文没有给出升降台型号' in page.locator('body').inner_text())
        for view in ['oblique', 'side', 'drive', 'top', 'bottom']:
            page.locator(f'button[data-view="{view}"]').click()
            check('view_' + view, page.locator('html').get_attribute('data-lift-view') == view)
            capture(view)
        page.locator('#lift-group').select_option('pantograph_links')
        page.locator('#lift-isolate').check()
        check('only_16_original_links_isolated', len(snapshot()['visible']) == 16 and all(2 <= int(n.rsplit('_', 1)[1]) <= 17 for n in snapshot()['visible']))
        page.locator('button[data-view="oblique"]').click()
        capture('links')
        page.locator('#lift-group').select_option('upper_plate')
        page.locator('#lift-holes').check()
        check('upper_plate_only', snapshot()['visible'] == ['L200_M__solid_000'])
        page.locator('button[data-view="top"]').click()
        capture('plate_holes')
        page.locator('#lift-group').select_option('all')
        page.locator('#lift-isolate').uncheck()
        page.locator('#lift-holes').uncheck()
        page.locator('#lift-explode').fill('60')
        state = snapshot()['matrices']
        check('only_top_plate_moves_in_exploded_inspection', all(abs(row['matrix'][14] - (.06 if row['id'] == 'L200_M__solid_000' else 0)) < 1e-9 and row['matrix'][12:14] == [0, 0] for row in state))
        check('explosion_is_not_a_jack_motion_claim', '不是实际升降姿态' in page.locator('#lift-status').inner_text())
        page.locator('button[data-view="oblique"]').click()
        capture('upper_plate_removed')
        page.locator('#lift-explode').fill('0')
        check('reset_restores_all_source_transforms', all(row['matrix'] == [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1] for row in snapshot()['matrices']))
        page.locator('#lift-model').select_option('mount')
        state=snapshot()
        check('actual_mount_core_loaded',state['mode']=='mount' and len(state['visible'])==101 and sum('L200_M__solid_' in n for n in state['visible'])==86)
        check('twelve_fasteners_and_three_plates_visible',sum(any(tag in n for tag in ['base_screw_','base_washer_','platform_screw_']) for n in state['visible'])==12 and all('COOLER_WHITE__'+n in state['visible'] for n in ['acrylic_base','mylar_base','lift_plate']))
        check('source_only_controls_disabled_in_mount_mode',all(page.locator('#'+name).is_disabled() for name in ['lift-group','lift-isolate','lift-holes','lift-explode']) and not state['markersVisible'])
        check('mount_load_and_assembly_limits_visible','亚克力应力' in page.locator('body').inner_text() and '底面可达的受支撑装配姿态' in page.locator('body').inner_text() and '尚未验收' in page.locator('#lift-status').inner_text())
        for view in ['oblique','side','top','bottom']:
            page.locator(f'button[data-view="{view}"]').click();capture('mount_'+view)
        page.locator('#lift-model').select_option('source')
        check('source_mode_restores_unmodified_assembly',snapshot()['mode']=='source' and len(snapshot()['visible'])==86 and not page.locator('#lift-explode').is_disabled())
        page.set_viewport_size({'width': 390, 'height': 844})
        page.wait_for_timeout(150)
        check('mobile_has_no_horizontal_overflow', page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        page.set_viewport_size({'width': 1440, 'height': 1100})
        check('no_browser_errors', not errors)
        for name, path, status, body, expected in [
            ('missing_local_geometry', '**/assets/thorlabs_l200_v1/geometry/L200_M.glb', 404, '', '本机缺少厂家资源'),
            ('changed_source_cad', '**/assets/thorlabs_l200_v1/cache/L200_M.step', 200, 'different CAD revision', '版本与检查记录不一致'),
            ('changed_source_ledger', '**/assets/thorlabs_l200_v1/sources.json', 200, '{}', '版本与检查记录不一致'),
            ('missing_mount_cache','**/assets/cooling_lab_v1/geometry/apparatus_mount_inspection.glb',404,'','本机缺少厂家资源'),
            ('stale_mount_geometry','**/assets/cooling_lab_v1/geometry/apparatus_mount_inspection.glb',200,'old mount','版本与检查记录不一致'),
            ('stale_mount_stock','**/assets/cooling_lab_v1/lift_mount_stock.json',200,'{}','版本与检查记录不一致')]:
            def response(route, request):
                route.fulfill(status=status, body=body)
            page.route(path, response)
            page.reload()
            page.wait_for_function('document.documentElement.dataset.liftLoaded === "error"')
            check(name + '_rejected', expected in page.locator('#lift-error').inner_text())
            check(name + '_does_not_display_unverified_mesh', page.locator('#lift-viewport canvas').count() == 0)
            page.unroute(path)
        b.close()
    files = [HERE / n for n in ['lift.html', 'lift.js', 'lift.css', 'style.css', 'check_lift.py']]
    files += [ROOT / 'assets/thorlabs_l200_v1' / n for n in ['sources.json', 'model.json', 'checks.json']]
    files += [ROOT / 'assets/cooling_lab_v1' / n for n in ['apparatus_stock_reconciliation.json','apparatus_mount_checks.json','apparatus_mount_sources.json','lift_mount_stock.json']]
    result = dict(passed=all(c['passed'] for c in checks), checks=checks, captures=captures,
                  scope='Static geometry browser review; no physical jack actuation or robot task execution',
                  source_artifacts=[dict(path=str(path.relative_to(ROOT)), sha256=sha(path)) for path in files])
    (HERE / 'LIFT_VERIFICATION.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=result['passed'], checks=len(checks), captures=len(captures))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--browser', required=True)
    parser.add_argument('--url', default='http://127.0.0.1:8769/viewer/lab_review_v1/lift.html')
    args = parser.parse_args()
    run(args.url, args.browser)
