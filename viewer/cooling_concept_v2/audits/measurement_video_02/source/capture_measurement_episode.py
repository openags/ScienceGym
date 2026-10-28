"""Render the continuous FTIR measurement and export every video-frame pose.

The output remains pending until independent source-geometry reviewers pass.
This is an authored demonstration, without force or controller qualification.
"""
import argparse
import base64
import gzip
import hashlib
import io
import json
import math
import os
import shutil
import subprocess
import time
from pathlib import Path
from PIL import Image, ImageStat
from playwright.sync_api import sync_playwright
from export_audit import HERE, BROWSER


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture(source, destination, fps):
    source=Path(source);destination=Path(destination)
    if destination.exists():raise FileExistsError(destination)
    receipt=json.loads((source/'export.json').read_text())
    assert receipt['episode']=='ftir_measurement'
    pins=dict(receipt['source_sha256'])
    for name,sha in pins.items():assert digest(HERE/name)==sha,'Stale live source: '+name
    for name,sha in receipt['scene']['sourceHashes'].items():assert digest(HERE.parents[1]/name)==sha,name
    with gzip.open(source/'frames.jsonl.gz','rt') as stream:first=json.loads(next(stream))
    destination.mkdir(parents=True)
    shutil.copytree(source/'source',destination/'source')
    script=Path(__file__);pins[script.name]=digest(script)
    shutil.copy2(script,destination/'source'/script.name)
    video=destination/'measurement.rendering.mp4';errors=[];frame_digest=hashlib.sha256()
    start=time.monotonic();stats_min=float('inf')
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=BROWSER,args=['--no-sandbox','--disable-dev-shm-usage',
            '--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],
            env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
        page=browser.new_page(viewport={'width':1280,'height':720},device_scale_factor=1)
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?episode=ftir_measurement&clean',timeout=120000)
        page.wait_for_function('document.documentElement.dataset.ready==="true" && window.concept?.measurementEpisode',timeout=120000)
        actual=page.evaluate('t=>auditFrame(t)',first['time_s'])
        for frame in [first,actual]:frame['parts']=sorted(frame['parts'],key=lambda x:(x['asset'],x['name']))
        assert actual==first,'Initial state differs from pinned source export'
        info=page.evaluate('({duration:concept.duration,sourceHashes:concept.sourceHashes,assetCount:concept.assetCount,robotCount:concept.robotCount})')
        assert info['sourceHashes']==receipt['scene']['sourceHashes'] and info['robotCount']==1
        assert info['duration']==receipt['scene']['duration']
        count=math.ceil(info['duration']*fps)
        ff=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','image2pipe','-vcodec','mjpeg',
            '-framerate',str(fps),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','22',
            '-pix_fmt','yuv420p','-movflags','+faststart',str(video)],stdin=subprocess.PIPE)
        try:
            with gzip.open(destination/'frames.jsonl.gz','wt',compresslevel=1) as stream:
                for i in range(count):
                    t=info['duration'] if i==count-1 else i/fps
                    result=page.evaluate('''t=>{const jpeg=concept.frameJpeg(t);const frame=JSON.stringify(auditFrame(t),
                        (k,v)=>{if(typeof v==='number'&&!Number.isFinite(v))throw Error('Nonfinite '+k);return v});return {jpeg,frame}}''',t)
                    data=base64.b64decode(result['jpeg'])
                    with Image.open(io.BytesIO(data)) as picture:
                        picture.load();assert picture.size==(1280,720)
                        deviation=max(ImageStat.Stat(picture.resize((32,18)).convert('RGB')).stddev)
                    if deviation<1.:raise RuntimeError('Uniform/empty frame '+str(i))
                    stats_min=min(stats_min,deviation)
                    line=result['frame']+'\n';stream.write(line);frame_digest.update(line.encode())
                    ff.stdin.write(data)
                    if i%(fps*10)==0:print('frame',i,'/',count,'video_s',round(t,2),'wall_s',round(time.monotonic()-start,1),flush=True)
        finally:ff.stdin.close()
        assert ff.wait()==0 and not errors,errors
        for name,sha in pins.items():assert digest(HERE/name)==sha,'Source changed during capture: '+name
        for name,sha in info['sourceHashes'].items():assert digest(HERE.parents[1]/name)==sha,name
        export={**receipt,'source_sha256':pins,'sample_step_s':1/fps,'frame_count':count,
                'frames_sha256':frame_digest.hexdigest(),'compressed_frames_sha256':digest(destination/'frames.jsonl.gz'),
                'capture_frame_alignment':'Every encoded video frame has the matching pose in frames.jsonl.gz, including the terminal state.',
                'parent_export_sha256':digest(source/'export.json')}
        (destination/'export.json').write_text(json.dumps(export,indent=2)+'\n')
        video.rename(destination/'measurement.pending.mp4');video=destination/'measurement.pending.mp4'
        record=dict(status='rendered_pending_independent_review',episode='ftir_measurement',continuous_scene=True,
            robot_count=1,asset_count=info['assetCount'],scene_duration_s=info['duration'],video_duration_s=count/fps,
            frames=count,fps=fps,resolution=[1280,720],watermarks=False,text_overlays=False,
            source_sha256=pins,asset_sources=info['sourceHashes'],video_sha256=digest(video),
            export_sha256=digest(destination/'export.json'),minimum_thumbnail_standard_deviation=stats_min,
            browser=browser.version,javascript_errors=errors,wall_seconds=time.monotonic()-start,
            whole_paper_complete=False,physics_validation_claimed=False)
        (destination/'capture.json').write_text(json.dumps(record,indent=2)+'\n')
        browser.close();print('captured_pending_review',count,'frames',video.stat().st_size,'bytes',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--destination',required=True)
    parser.add_argument('--fps',type=int,default=24);args=parser.parse_args();capture(args.source,args.destination,args.fps)
