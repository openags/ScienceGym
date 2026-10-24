"""Physical load and missing-sheet tests for the selected coarse membrane."""
import copy
import hashlib
import json
import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
import mujoco
import numpy as np
from membrane import build
from test_membrane import measure
from world import HERE,vec

def run():
    rows=[]
    with tempfile.TemporaryDirectory(prefix='sciencegym-selected-membrane-') as td:
        cases=[('16um',8,.000016,.0005,0),('50um',8,.000050,.0005,0),
               ('half_timestep',8,.000016,.00025,0),('mesh12_reference',12,.000016,.0005,0),
               ('missing_lower',8,.000016,.0005,1),('missing_both',8,.000016,.0005,2)]
        for name,sectors,thickness,dt,missing in cases:
            p=Path(td)/(name+'.xml');build(p,sectors=sectors,thickness=thickness)
            tree=ET.parse(p);root=tree.getroot();root.find('option').set('timestep',str(dt));cover=root.find("worldbody/body[@name='cover']")
            if missing:cover.remove(cover.find("flexcomp[@name='lower']"))
            if missing==2:cover.remove(cover.find("flexcomp[@name='upper']"))
            # Independent construction of the declared 24-piece rigid rings.
            for body,prefix in [(root.find("worldbody/body[@name='tube']"),'tube_wall'),(cover,'spacer')]:
                old=[body.find(f"geom[@name='{prefix}_{i}']") for i in range(48)]
                for g in old:body.remove(g)
                for i in range(24):
                    g=copy.deepcopy(old[i*2]);g.set('name',prefix+'_'+str(i));size=np.fromstring(g.get('size'),sep=' ');size[1]*=2;g.set('size',vec(size));g.set('mass',str(float(g.get('mass'))*2));body.append(g)
            tree.write(p);model=mujoco.MjModel.from_xml_path(str(p));data=mujoco.MjData(model)
            for step in range(round(1.5/dt)):
                mujoco.mj_step(model,data)
                if any(w.number for w in data.warning):break
            observation=measure(model,data);expected=missing==0
            row=dict(case=name,passed=observation['valid']==expected,expected_supported=expected,
                     observation=observation,physics_steps=step+1);rows.append(row);print(name,row['passed'],flush=True)
    a,b=[r['observation'] for r in rows if r['case'] in ['16um','mesh12_reference']]
    difference=abs(a['position_m'][2]-b['position_m'][2])
    result=dict(passed=all(r['passed'] for r in rows) and difference<.0003,outcomes=rows,
        mesh_refinement=dict(reference_sectors=12,selected_sectors=8,vertical_position_difference_m=difference,tolerance_m=.0003),
        input_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['test_selected_membrane.py','membrane.py','test_membrane.py']},
        engine_version=mujoco.__version__,scope='Static contact support, 16/50 um sheets, time-step and mesh sensitivity, missing-sheet counterexamples. Ideal permanent bonds and inextensible cloth; no adhesion or rupture calibration.',whole_paper_validated=False)
    (HERE/'selected_membrane_tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['mesh_refinement'],indent=2));return result['passed']
if __name__=='__main__':raise SystemExit(0 if run() else 1)
