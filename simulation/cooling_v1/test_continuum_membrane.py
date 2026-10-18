"""Contact-load, refinement and missing-sheet checks for continuum film."""
import copy
import json
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import mujoco
from membrane import build
from test_membrane import measure
from trace_store import sha
from world import HERE,vec


def case(args):
    name,sectors,thickness,dt,missing=args
    out=HERE/'runs/membrane_debug/continuum_suite'/name;out.mkdir(parents=True,exist_ok=True)
    path=out/'workcell.xml';build(path,sectors=sectors,thickness=thickness,elastic=True)
    tree=ET.parse(path);root=tree.getroot();root.find('option').attrib.update(timestep=str(dt),integrator='discrete',solver='CG',iterations='800',impratio='10')
    cover=root.find("worldbody/body[@name='cover']")
    for e in root.findall('.//elasticity'):e.set('damping','.002')
    if missing:cover.remove(cover.find("flexcomp[@name='lower']"))
    if missing==2:cover.remove(cover.find("flexcomp[@name='upper']"))
    for body,prefix in [(root.find("worldbody/body[@name='tube']"),'tube_wall'),(cover,'spacer')]:
        old=[body.find(f"geom[@name='{prefix}_{i}']") for i in range(48)]
        for geom in old:body.remove(geom)
        for i in range(24):
            geom=copy.deepcopy(old[2*i]);geom.set('name',prefix+'_'+str(i));size=np.fromstring(geom.get('size'),sep=' ');size[1]*=2;geom.set('size',vec(size));geom.set('mass',str(float(geom.get('mass'))*2));body.append(geom)
    tree.write(path);model=mujoco.MjModel.from_xml_path(str(path));data=mujoco.MjData(model);maximum=0.
    for step in range(round(3/dt)):
        mujoco.mj_step(model,data)
        if model.nflexedge:maximum=max(maximum,float(np.max(abs(data.flexedge_length/model.flexedge_length0-1))))
        if any(w.number for w in data.warning):break
    observation=measure(model,data);warnings=[int(w.number) for w in data.warning];expected=missing==0
    passed=not any(warnings) and observation['valid']==expected and (maximum<.01 if expected else True)
    result=dict(case=name,passed=passed,sectors=sectors,timestep_s=dt,thickness_m=thickness,expected_supported=expected,
        max_edge_strain_throughout=maximum,observation=observation,warnings=warnings,physics_steps=step+1,
        workcell_sha256=sha(path))
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(name,passed,'peak strain',maximum,flush=True);return result


def main():
    cases=[('16um',8,.000016,.0005,0),('50um',8,.000050,.0005,0),('half_timestep',8,.000016,.00025,0),
           ('mesh16',16,.000016,.0005,0),('missing_lower',8,.000016,.0005,1),('missing_both',8,.000016,.0005,2)]
    with ProcessPoolExecutor(max_workers=4) as pool:rows=list(pool.map(case,cases))
    selected=rows[0]['observation'];comparisons=[]
    for index in [2,3]:
        other=rows[index]['observation'];delta=abs(selected['position_m'][2]-other['position_m'][2]);load=abs(selected['support_vertical_force_n']-other['support_vertical_force_n'])
        comparisons.append(dict(case=rows[index]['case'],passed=delta<.0003 and load<.02,vertical_difference_m=delta,support_load_difference_N=load))
    report=dict(passed=all(r['passed'] for r in rows+comparisons),cases=rows,refinement=comparisons,
        input_sha256={n:sha(HERE/n) for n in ['test_continuum_membrane.py','membrane.py','test_membrane.py']},engine_version=mujoco.__version__,
        scope='Three-second static support and missing-sheet counterexamples; 16/50 um film, half-step and 8-to-16-sector refinement. Assumed elastic properties and ideal bonds; full robot episode assessed separately.',whole_paper_validated=False)
    (HERE/'continuum_membrane_tests.json').write_text(json.dumps(report,indent=2)+'\n');return report['passed']


if __name__=='__main__':raise SystemExit(0 if main() else 1)
