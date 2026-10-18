"""Offline evidence viewer: recorded physics and explicit campaign coverage."""
import json
from pathlib import Path
from world import HERE


def main():
    cases=[]
    for scene,title in [('assembly','Layer assembly and button press'),('probe','Probe insertion and return'),('lid','Lid placement and removal'),('door','Supported door opening and closing')]:
        p=HERE/'runs'/scene/'result.json'
        if p.exists():
            r=json.loads(p.read_text());cases.append(dict(id=scene,title=title,result=r,video=f'runs/{scene}/execution.mp4',poster=f'runs/{scene}/final.png'))
    data=dict(cases=cases,coverage=json.loads((HERE/'campaign_coverage.json').read_text()),
              tests=json.loads((HERE/'physics_tests.json').read_text()),scope=json.loads((HERE/'PHYSICS_SCOPE.json').read_text()))
    template=(HERE/'viewer_template.html').read_text()
    encoded=json.dumps(data,ensure_ascii=False).replace('<','\\u003c')
    (HERE/'index.html').write_text(template.replace('__EVIDENCE_JSON__',encoded))
    print('Viewer cases:',len(cases),'whole-paper accepted:',data['coverage']['whole_paper_validated'])


if __name__=='__main__':main()
