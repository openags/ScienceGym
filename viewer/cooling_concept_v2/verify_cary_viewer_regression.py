"""Smoke-check the existing FTIR delivery viewer after adding Cary mode.

Compare its exported first and last delivery-prefix states with their frozen
review inputs. This checks shared viewer startup/state behavior, not a new
whole-episode geometric review.
"""
import gzip,hashlib,json,os
from playwright.sync_api import sync_playwright
from export_audit import BROWSER,HERE


def difference(a,b):
    if isinstance(a,dict):
        assert a.keys()==b.keys();return max([0.]+[difference(a[k],b[k]) for k in a])
    if isinstance(a,list):
        assert len(a)==len(b);return max([0.]+[difference(x,y) for x,y in zip(a,b)])
    if isinstance(a,(int,float)) and not isinstance(a,bool):return abs(a-b)
    assert a==b,(a,b);return 0.


def main():
    path=HERE/'audits/optical_delivery_02/frames.jsonl.gz'
    with gzip.open(path,'rt') as stream:
        first=json.loads(next(stream));last=first
        for line in stream:last=json.loads(line)
    errors=[];checks=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=BROWSER,args=['--no-sandbox','--disable-dev-shm-usage','--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
        page=browser.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean&episode=ftir_delivery',timeout=120000);page.wait_for_function('document.documentElement.dataset.ready==="true"',timeout=120000)
        for expected in [first,last]:
            actual=json.loads(page.evaluate('t=>JSON.stringify(auditFrame(t))',expected['time_s']))
            # Asset batches load asynchronously. Compare every named part's
            # pose after canonical ordering, retaining all entries and values.
            for frame in [expected,actual]:frame['parts'].sort(key=lambda part:(part['asset'],part['name']))
            error=difference(expected,actual);checks.append(dict(time_s=expected['time_s'],maximum_state_difference=error));assert error<1e-10
        duration=page.evaluate('concept.duration');browser.close()
    assert not errors,errors
    report=dict(scope=__doc__,passed=True,duration_s=duration,checks=checks,errors=errors,source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['main.js','optical_episode.js','optical_delivery_episode.json','verify_cary_viewer_regression.py','audits/optical_delivery_02/frames.jsonl.gz']})
    (HERE/'previews/cary_viewer_regression.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,checks=checks)),flush=True)


if __name__=='__main__':main()
