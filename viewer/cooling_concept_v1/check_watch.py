"""Check the final video page and actual chapter playback."""
import hashlib,json
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE=Path(__file__).resolve().parent

def check():
 errors=[];checks=[]
 def record(name,value):
  checks.append(dict(name=name,passed=bool(value)))
  if not value:raise AssertionError(name)
 workflow=json.loads((HERE/'workflow.json').read_text());expected=next(p['start_s'] for p in workflow['sequence'] if p['id']=='open_white')
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell',args=['--no-sandbox','--disable-dev-shm-usage']);page=b.new_page(viewport={'width':1440,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://localhost:8769/viewer/cooling_concept_v1/watch.html');page.wait_for_function('document.documentElement.dataset.ready==="true" && document.documentElement.dataset.mediaReady==="true"',timeout=90000)
  record('fourteen_chapter_links',page.locator('#chapters button').count()==14);record('video_duration_matches',abs(page.locator('video').evaluate('(v)=>v.duration')-workflow['duration_s'])<.1)
  for link in page.locator('a').all():
   url=link.evaluate('(a)=>a.href');record('link_'+link.inner_text(),page.request.head(url).ok)
  page.locator('#chapters button').nth(9).click();page.wait_for_timeout(800);record('chapter_seek_and_playback',page.locator('video').evaluate('(v)=>v.currentTime')>expected+.15);page.locator('video').evaluate('(v)=>v.pause()');page.screenshot(path=str(HERE/'watch_desktop.png'),full_page=True)
  page.set_viewport_size({'width':390,'height':844});record('mobile_no_overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.screenshot(path=str(HERE/'watch_mobile.png'),full_page=True);record('javascript_errors_absent',not errors);version=b.version;b.close()
 result=dict(passed=True,checks=checks,javascript_errors=errors,browser=version,source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['watch.html','watch.js','check_watch.py','workflow.json']});(HERE/'watch_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':check()
