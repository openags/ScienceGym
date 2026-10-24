"""Check source-model loading and inspect both hands in the real browser."""
import argparse
import hashlib
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(browser, url):
    errors=[];shots=[]
    dest=HERE/'evidence';dest.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=b.new_page(viewport={'width':1440,'height':1050},device_scale_factor=1)
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(url)
        page.wait_for_function('document.documentElement.dataset.ready',timeout=90000)
        assert page.locator('html').get_attribute('data-ready')=='true',page.locator('#error').inner_text()
        assert '93 个网格' in page.locator('#robot-counts').inner_text()
        assert '已进入实验室场景' in page.locator('.notice').inner_text()
        for view in ['full','left','right','back']:
            page.locator(f'button[data-view="{view}"]').click()
            assert page.locator('html').get_attribute('data-view')==view
            path=dest/(view+'.png')
            page.locator('#robot-viewport').screenshot(path=path,timeout=60000)
            shots.append(dict(view=view,path=str(path.relative_to(ROOT)),sha256=sha(path)))
        assert len({s['sha256'] for s in shots})==4,'Views did not change'
        assert not errors,errors
        version=b.version;b.close()
    inputs=[HERE/'index.html',HERE/'main.js',Path(__file__),ROOT/'assets/unitree_g1_inspire_v1/VERIFICATION.json']
    result=dict(passed=True,scope='Static source geometry and browser views; not physics or task validation',browser=version,
                inputs=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in inputs],screenshots=shots,errors=errors)
    (HERE/'VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,views=len(shots),errors=errors)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--browser',required=True);p.add_argument('--url',default='http://127.0.0.1:8769/viewer/robot_resource_review_v1/index.html')
    args=p.parse_args();run(args.browser,args.url)
