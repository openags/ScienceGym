"""Exercise offline playback, event seeking and source-step filtering."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--browser',required=True);args=parser.parse_args()
    out=HERE/'qa';out.mkdir(exist_ok=True)
    errors=[];checks=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=args.browser,headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page(viewport={'width':1440,'height':1100})
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto((HERE/'index.html').as_uri())
        assert page.locator('#cases button').count()==4
        assert page.locator('#steps tr').count()==200
        checks.append('four run records and all 200 source definitions present')
        for i in range(4):
            page.locator('#cases button').nth(i).click()
            page.wait_for_function('document.getElementById("video").readyState >= 1',timeout=20000)
            duration=page.locator('#video').evaluate('(v)=>v.duration')
            assert duration>10
            page.locator('#events button').first.click()
            page.wait_for_function('document.getElementById("video").currentTime > 1')
            page.locator('#video').evaluate('(v)=>v.pause()')
            checks.append('video metadata and event seek: '+str(i))
        page.select_option('#branch',index=1)
        assert 0<page.locator('#steps tr').count()<200
        page.select_option('#branch','')
        page.fill('#search','CAL_MOUNT.06')
        assert page.locator('#steps tr').count()==1
        page.fill('#search','')
        checks.append('branch filter and exact source-step search')
        page.locator('#cases button').first.click()
        page.wait_for_function('document.getElementById("video").readyState >= 1')
        page.locator('#video').evaluate('(v)=>{v.currentTime=10;v.pause()}')
        page.wait_for_function('document.getElementById("video").readyState >= 2')
        page.evaluate('window.scrollTo(0,0)')
        page.screenshot(path=str(out/'viewer-desktop.png'))
        page.set_viewport_size({'width':390,'height':844})
        page.evaluate('window.scrollTo(0,0)')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
        page.screenshot(path=str(out/'viewer-mobile.png'))
        checks.append('mobile layout has no horizontal overflow')
        assert not errors,errors
        browser.close()
    (out/'browser.json').write_text(json.dumps(dict(passed=True,checks=checks,page_errors=errors),indent=2)+'\n')
    print('Browser checks passed:',len(checks))


if __name__=='__main__':main()
