"""Exercise the actual laboratory video, return-stage seek and sensor sync."""
import hashlib
import json
from pathlib import Path
import re
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent


def run():
    checks, errors = [], []
    def check(name, value):
        checks.append(dict(name=name, passed=bool(value)))
        if not value:
            raise AssertionError(name)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell', args=['--no-sandbox','--disable-dev-shm-usage'])
        page = browser.new_page(viewport={'width':1440,'height':1100})
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://localhost:8769/viewer/cooling_lab_runtime_v1/index.html')
        page.wait_for_function('document.documentElement.dataset.ready==="true" && document.documentElement.dataset.mediaReady==="true"', timeout=90000)
        check('actual_evidence_reports_passed', '检查通过' in page.locator('#status').inner_text())
        check('recorded_duration', abs(page.locator('#episode').evaluate('v=>v.duration')-80.54)<.1)
        for a in page.locator('a').all():
            check('link_'+a.inner_text(), page.request.head(a.evaluate('a=>a.href')).ok)
        page.get_by_role('button', name=re.compile('返回 · 抬起')).click()
        page.wait_for_timeout(1200)
        main = page.locator('#episode').evaluate('v=>v.currentTime')
        depth = page.locator('#depth').evaluate('v=>v.currentTime')
        check('return_stage_seeks_and_plays', main>51)
        check('recorded_depth_synchronized', abs(main-depth)<.25)
        page.locator('#episode').evaluate('v=>v.pause()')
        check('sensor_video_pauses_with_main', page.locator('#depth').evaluate('v=>v.paused'))
        page.screenshot(path=str(HERE/'desktop.png'), full_page=True)
        page.set_viewport_size({'width':390,'height':844})
        check('mobile_no_overflow', page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        page.screenshot(path=str(HERE/'mobile.png'), full_page=True)
        check('javascript_errors_absent', not errors)
        version = browser.version
        browser.close()
    result = dict(passed=all(c['passed'] for c in checks), checks=checks, javascript_errors=errors,
                  browser=version, source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest()
                  for n in ['index.html','main.js','check_browser.py']})
    (HERE/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    run()
