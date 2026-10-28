import json
from pathlib import Path
from playwright.sync_api import sync_playwright
base=Path('/home/amax/data/media/xyl_ps/scigym/ScienceGym/viewer/cooling_concept_v2')
d=json.loads((base/'measurement_brief_delivery.json').read_text())
url='http://localhost:8769/viewer/cooling_concept_v2/measurement_demo.html'
results=[]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell',headless=True,args=['--no-sandbox'])
 for width,height,brief in [(1440,1000,True),(390,844,True),(1440,1000,False)]:
  page=browser.new_page(viewport={'width':width,'height':height});errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(url+('?cut=brief' if brief else ''),wait_until='networkidle')
  page.wait_for_function('document.querySelector("#film").readyState>=2 && !document.querySelector("#route-panel").hidden')
  assert page.locator('.chapter').count()==10
  assert page.locator('#length').inner_text()==('精简汇报版 · 5 分 33 秒' if brief else '完整时长版 · 9 分 1 秒')
  times=[]
  for n in [1,3,9]:
   page.locator('.chapter').nth(n).click()
   page.wait_for_function('!document.querySelector("#film").seeking')
   page.evaluate('document.querySelector("#film").pause()')
   row=page.evaluate('({video:document.querySelector("#film").currentTime,map:Number(document.querySelector("#route-robot").dataset.time),phase:document.querySelector("#route-robot").dataset.phase})')
   assert abs(row['video']-row['map'])<.3,row
   times.append(row)
  page.locator('[data-map-view="full"]').click()
  page.locator('.map-station').first.click()
  page.wait_for_function('!document.querySelector("#film").seeking')
  page.evaluate('document.querySelector("#film").pause()')
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), 'horizontal overflow'
  assert not errors,errors
  if brief and width==1440:
   page.locator('[data-map-view="detail"]').click()
   page.screenshot(path=str(base/'audits/measurement_brief_01/player_desktop.png'),full_page=True)
  if brief and width==390:
   page.screenshot(path=str(base/'audits/measurement_brief_01/player_mobile.png'),full_page=True)
  results.append(dict(width=width,brief=brief,chapters=10,seeks=times,page_errors=errors,overflow=False))
  page.close()
 browser.close()
(base/'audits/measurement_brief_01/browser_review.json').write_text(json.dumps(dict(passed=True,cases=results),indent=2)+'\n')
print(json.dumps(results),flush=True)
