"""Capture an independently reviewed Cary access episode as a clean MP4.

This exports only the named access episode. Its review and receipt do not
represent a complete paper film, contact dynamics or branch qualification.
"""
import argparse
import base64
import gzip
import hashlib
import json
import math
import os
import subprocess
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from export_audit import HERE,BROWSER


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--review',required=True)
    parser.add_argument('--output',required=True);parser.add_argument('--fps',type=int,default=24)
    args=parser.parse_args();folder=HERE/args.review;output=HERE/args.output
    if output.exists():raise FileExistsError(output)
    review=json.loads((folder/'sampled_interaction_review.json').read_text())
    export=json.loads((folder/'export.json').read_text())
    assert review['passed'] and review['covers_entire_episode']
    assert review['episode']==export['episode']=='cary_access'
    for name,sha in review['evidence_sha256'].items():assert digest(folder/name)==sha,name
    for name,sha in export['source_sha256'].items():assert digest(HERE/name)==sha,'Stale live episode: '+name
    root=HERE.parents[1]
    for name,sha in export['scene']['sourceHashes'].items():assert digest(root/name)==sha,name
    with gzip.open(folder/'frames.jsonl.gz','rt') as f:first_reviewed=json.loads(next(f))
    source_pins={**export['source_sha256'],'capture_reviewed_episode.py':digest(Path(__file__))}
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_name(output.stem+'.rendering.mp4');errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=BROWSER,args=['--no-sandbox','--disable-dev-shm-usage',
            '--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],
            env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
        page=browser.new_page(viewport={'width':1280,'height':720},device_scale_factor=1)
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?episode=cary_access&clean',timeout=120000)
        page.wait_for_function('document.documentElement.dataset.ready==="true"',timeout=120000)
        actual=page.evaluate('(t)=>auditFrame(t)',first_reviewed['time_s'])
        # Asset loading is asynchronous; node traversal order is not a pose
        # identity. Compare every named part in a stable identity order.
        for frame in [first_reviewed,actual]:
            frame['parts']=sorted(frame['parts'],key=lambda item:(item['asset'],item['name']))
        differences=[]
        def compare(a,b,path=''):
            if isinstance(a,dict) and isinstance(b,dict):
                if a.keys()!=b.keys():differences.append(dict(path=path,expected_keys=list(a),actual_keys=list(b)))
                for k in a.keys()&b.keys():compare(a[k],b[k],path+'/'+k)
            elif isinstance(a,list) and isinstance(b,list):
                if len(a)!=len(b):differences.append(dict(path=path,expected_length=len(a),actual_length=len(b)))
                for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+'/'+str(i))
            elif a!=b:
                row=dict(path=path,expected=a,actual=b)
                if isinstance(a,(float,int)) and isinstance(b,(float,int)):row['absolute_error']=abs(a-b)
                differences.append(row)
        compare(first_reviewed,actual)
        if differences:
            output.with_suffix('.initial_difference.json').write_text(json.dumps(differences,indent=2)+'\n')
            raise AssertionError('Initial render state differs from reviewed export: '+str(differences[:3]))
        info=page.evaluate('({duration:concept.duration,sourceHashes:concept.sourceHashes,assetCount:concept.assetCount,robotCount:concept.robotCount})')
        assert info['sourceHashes']==export['scene']['sourceHashes'] and info['robotCount']==1
        assert abs(info['duration']-review['duration_s'])<1e-9
        count=math.ceil(info['duration']*args.fps);start=time.monotonic()
        ff=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','image2pipe','-vcodec','mjpeg',
            '-framerate',str(args.fps),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','22',
            '-pix_fmt','yuv420p','-movflags','+faststart',str(temporary)],stdin=subprocess.PIPE)
        try:
            for i in range(count):
                t=info['duration'] if i==count-1 else i/args.fps
                ff.stdin.write(base64.b64decode(page.evaluate('(t)=>concept.frameJpeg(t)',t)))
                if i%(args.fps*10)==0:print('frame',i,'/',count,'video_s',round(t,2),'wall_s',round(time.monotonic()-start,1),flush=True)
        finally:ff.stdin.close()
        assert ff.wait()==0 and not errors,errors
        for name,sha in source_pins.items():assert digest(HERE/name)==sha,'Source changed during capture: '+name
        temporary.replace(output)
        receipt=dict(scope=__doc__,episode='cary_access',continuous_scene=True,robot_count=1,
            asset_count=info['assetCount'],scene_duration_s=info['duration'],video_duration_s=count/args.fps,
            frames=count,fps=args.fps,resolution=[1280,720],watermarks=False,text_overlays=False,
            review=str(folder.relative_to(HERE)),review_sha256=digest(folder/'sampled_interaction_review.json'),
            source_sha256=source_pins,asset_sources=info['sourceHashes'],video_sha256=digest(output),
            browser=browser.version,javascript_errors=errors,wall_seconds=time.monotonic()-start,
            whole_paper_complete=False,physics_validation_claimed=False)
        receipt['initial_state_comparison']='Exact values after sorting parts by (asset, name).'
        output.with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n')
        browser.close();print('captured',count,'frames',output.stat().st_size,'bytes',flush=True)


if __name__=='__main__':main()
