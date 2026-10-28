"""Ensure the added measurement mode leaves reviewed older viewers unchanged."""
import gzip,hashlib,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
from export_audit import HERE,BROWSER


def compare(a,b,path='',worst=None):
    if worst is None:worst=[0.,'']
    if isinstance(a,dict):
        assert a.keys()==b.keys(),path+' keys'
        for k in a:compare(a[k],b[k],path+'/'+k,worst)
    elif isinstance(a,list):
        assert len(a)==len(b),path+' lengths'
        for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+'/'+str(i),worst)
    elif isinstance(a,(float,int)) and not isinstance(a,bool):
        error=abs(a-b)
        if error>worst[0]:worst[:]=[error,path]
    else:assert a==b,(path,a,b)
    return worst


def main():
    output=HERE/'previews/measurement_older_viewers_regression_01';output.mkdir(exist_ok=False)
    rows=[];errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=BROWSER,args=['--no-sandbox','--disable-dev-shm-usage','--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
        page=browser.new_page(viewport={'width':1280,'height':720});page.on('pageerror',lambda e:errors.append(str(e)))
        for episode,folder in [('cary_access','cary_access_05'),('ftir_delivery','optical_delivery_02')]:
            source=HERE/'audits'/folder;receipt=json.loads((source/'export.json').read_text());selected={0,receipt['frame_count']//3,2*receipt['frame_count']//3,receipt['frame_count']-1};frames=[]
            with gzip.open(source/'frames.jsonl.gz','rt') as stream:
                for i,line in enumerate(stream):
                    if i in selected:frames.append(json.loads(line))
            page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?episode='+episode+'&clean',timeout=120000)
            field='caryEpisode' if episode=='cary_access' else 'opticalEpisode'
            page.wait_for_function('document.documentElement.dataset.ready==="true" && window.concept?.'+field,timeout=120000)
            for expected in frames:
                actual=page.evaluate('t=>auditFrame(t)',expected['time_s'])
                for frame in [expected,actual]:frame['parts']=sorted(frame['parts'],key=lambda x:(x['asset'],x['name']))
                worst=compare(expected,actual);assert worst[0]<1e-9,worst
                rows.append(dict(episode=episode,time_s=expected['time_s'],maximum_error=worst[0],field=worst[1]))
            print('unchanged',episode,len(frames),'states',flush=True)
        browser.close()
    assert not errors,errors
    pins={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['main.js','hand_ik.js','measurement_episode.js','measurement_source_actions.js','verify_measurement_isolation.py']}
    (output/'review.json').write_text(json.dumps(dict(passed=True,scope=__doc__,source_sha256=pins,states=rows,javascript_errors=errors),indent=2)+'\n')

if __name__=='__main__':main()
