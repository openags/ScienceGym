"""Compare every retained exchange state inside the extended delivery episode.

Reuse the earlier sampled geometric verdict only after checking all source
assets, deforming vertices, extra geometry and every recorded state against
the live combined viewer. This is numeric state equivalence, not new physical
execution or a continuous-time clearance proof.
"""
import argparse,hashlib,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
from export_audit import BROWSER,HERE

COMPARE=r'''async args=>{
 const sha=async b=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',b))].map(x=>x.toString(16).padStart(2,'0')).join('');
 const receiptBytes=await(await fetch(args.receipt)).arrayBuffer();
 if(await sha(receiptBytes)!==args.receiptSha)throw Error('Reference export changed');
 const receipt=JSON.parse(new TextDecoder().decode(receiptBytes));
 const compressed=await(await fetch(args.frames)).arrayBuffer();
 const compressedSha=await sha(compressed);if(compressedSha!==receipt.compressed_frames_sha256)throw Error('Reference frames changed');
 let maximum=0,numericCount=0,failures=0,frames=0;const details=[],phases=new Set();
 function compare(a,b,path,errors){
  if(typeof a!==typeof b){errors.push(path+': type');return;}
  if(typeof a==='number'){numericCount++;const delta=Math.abs(a-b);maximum=Math.max(maximum,delta);if(!Number.isFinite(delta)||delta>args.tolerance)errors.push(path+': '+delta);return;}
  if(a===null||typeof a!=='object'){if(a!==b)errors.push(path+': value');return;}
  if(Array.isArray(a)!==Array.isArray(b)){errors.push(path+': array');return;}
  const ak=Object.keys(a).sort(),bk=Object.keys(b).sort();
  if(JSON.stringify(ak)!==JSON.stringify(bk)){errors.push(path+': keys');return;}
  for(const key of ak)compare(a[key],b[key],path+'/'+key,errors);
 }
 const metadataErrors=[];
 for(const key of ['manifest','sourceHashes','extraGeometry','deformableGeometry'])compare(receipt.scene[key],concept[key],key,metadataErrors);
 const reader=new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip')).pipeThrough(new TextDecoderStream()).getReader();let pending='';
 function frame(line){
  const old=JSON.parse(line),actual=auditFrame(old.time_s+args.offset);old.time_s+=args.offset;
  for(const value of [old,actual])value.parts.sort((a,b)=>(a.asset+'::'+a.name).localeCompare(b.asset+'::'+b.name));
  const errors=[];compare(old,actual,'frame',errors);frames++;phases.add(actual.phase);
  if(errors.length){failures++;if(details.length<20)details.push({time_s:actual.time_s,phase:actual.phase,errors:errors.slice(0,20)});}
 }
 while(true){
  const {value,done}=await reader.read();if(done)break;pending+=value;let newline;
  while((newline=pending.indexOf('\n'))>=0){const line=pending.slice(0,newline);pending=pending.slice(newline+1);if(line)frame(line);if(frames%200===0){console.log('suffix_checked',frames);await new Promise(r=>setTimeout(r,0));}}
 }
 if(pending.trim())frame(pending);
 return {passed:!metadataErrors.length&&!failures&&frames===receipt.frame_count,frames,frame_failures:failures,metadata_errors:metadataErrors,details,maximum_numeric_difference:maximum,numeric_comparisons:numericCount,phases:[...phases],reference_compressed_sha256:compressedSha};
}'''


def verify(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);reference=HERE/'audits/optical_exchange_01'
    aggregate=json.loads((reference/'sampled_interaction_review.json').read_text());assert aggregate['passed']
    for name,sha in aggregate['evidence_sha256'].items():assert hashlib.sha256((reference/name).read_bytes()).hexdigest()==sha,name
    original=json.loads((reference/'source/optical_episode.json').read_text());combined=json.loads((HERE/'optical_delivery_episode.json').read_text());offset=combined['delivery_duration_s']
    assert combined['continuous_at_segment_boundaries']
    suffix=combined['segments'][-len(original['segments']):]
    for old,new in zip(original['segments'],suffix):
        assert abs(old['start']+offset-new['start'])<1e-10 and abs(old['end']+offset-new['end'])<1e-10
        assert {k:v for k,v in old.items() if k not in ['start','end']}=={k:v for k,v in new.items() if k not in ['start','end']}
    names=['main.js','optical_episode.js','optical_delivery_episode.json','hand_ik.js','runtime_scene.json','verify_delivery_suffix.py'];pins={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in names};errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=BROWSER,args=['--no-sandbox','--disable-dev-shm-usage','--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
        page=browser.new_page(viewport={'width':960,'height':540});page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:print(m.text,flush=True) if m.text.startswith('suffix_checked') else None)
        page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean&episode=ftir_delivery',timeout=120000);page.wait_for_function('document.documentElement.dataset.ready==="true"',timeout=120000)
        result=page.evaluate(COMPARE,dict(receipt='./audits/optical_exchange_01/export.json',receiptSha=aggregate['evidence_sha256']['export.json'],frames='./audits/optical_exchange_01/frames.jsonl.gz',offset=offset,tolerance=1e-10));browser.close()
    assert all(hashlib.sha256((HERE/n).read_bytes()).hexdigest()==sha for n,sha in pins.items())
    result.update(scope=__doc__,errors=errors,offset_s=offset,tolerance=1e-10,source_sha256=pins,reference_review='audits/optical_exchange_01/sampled_interaction_review.json',reference_review_sha256=hashlib.sha256((reference/'sampled_interaction_review.json').read_bytes()).hexdigest(),original_segment_count=len(original['segments']),combined_segment_count=len(combined['segments']))
    result['passed']=result['passed'] and not errors
    (out/'suffix_equivalence.json').write_text(json.dumps(result,indent=2)+'\n');(out/'verify_delivery_suffix.py').write_bytes(Path(__file__).read_bytes());print(json.dumps({k:result[k] for k in ['passed','frames','frame_failures','maximum_numeric_difference','numeric_comparisons','metadata_errors']}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('out');args=parser.parse_args();verify(args.out)
