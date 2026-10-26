"""Check the actual delivery page, local evidence links and seeking controls."""
import argparse,json,hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE=Path(__file__).resolve().parent

def run(browser,url):
    errors=[];checks=[]
    def check(name,value):
        checks.append(dict(name=name,passed=bool(value)))
        if not value:raise AssertionError(name)
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage'])
        page=b.new_page(viewport={'width':1440,'height':1050});page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(url);page.wait_for_function('document.documentElement.dataset.ready==="true"')
        check('qualification_limit_visible','0 / 11' in page.inner_text('body'))
        check('checks_loaded',page.locator('#checks .check').count()>=14)
        check('metrics_loaded',float(page.inner_text('#duration'))==38 and float(page.inner_text('#lift'))>=7)
        for a in page.locator('a').all():
            href=a.get_attribute('href')
            if href and not href.startswith('https:'):
                check('local_link_'+href,page.request.get(page.evaluate('(href)=>new URL(href,location.href).href',href)).ok)
        # Headless Chromium builds can lack H.264. Validate source bytes even
        # when codec support is unavailable; only claim playback if it works.
        media=page.evaluate('document.querySelector("video").canPlayType(\'video/mp4; codecs="avc1.640028"\')')
        playback=False
        if media:
            page.wait_for_function('document.documentElement.dataset.mediaReady==="true"')
            page.wait_for_function('document.querySelector("video").readyState>=1')
            page.locator('#steps button').nth(6).click();page.wait_for_timeout(500)
            playback=page.evaluate('document.querySelector("video").currentTime>=22')
            check('timeline_video_seek',playback);page.evaluate('document.querySelector("video").pause()')
        page.screenshot(path=str(HERE/'desktop.png'),full_page=True)
        page.set_viewport_size({'width':390,'height':844});check('mobile_no_overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        page.screenshot(path=str(HERE/'mobile.png'),full_page=True)
        check('javascript_errors_absent',not errors);version=b.version;b.close()
    report=dict(passed=True,checks=checks,errors=errors,browser=version,h264_supported=bool(media),playback_verified=playback,
      source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['index.html','main.js','check_browser.py']})
    (HERE/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--browser',required=True);p.add_argument('--url',default='http://127.0.0.1:8769/viewer/cooling_demo_v1/index.html');a=p.parse_args();run(a.browser,a.url)
