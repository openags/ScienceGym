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
from film_contact import exact_cuboid_contacts
from film_geometry import FilmSolidAudit


def case(args):
    name,sectors,thickness,dt,missing,iterations=args
    out=HERE/'runs/membrane_debug/continuum_suite'/name;out.mkdir(parents=True,exist_ok=True)
    path=out/'workcell.xml';build(path,sectors=sectors,thickness=thickness,elastic=True)
    tree=ET.parse(path);root=tree.getroot();root.find('option').attrib.update(timestep=str(dt),integrator='discrete',solver='CG',iterations=str(iterations),impratio='10')
    cover=root.find("worldbody/body[@name='cover']")
    for e in root.findall('.//elasticity'):e.set('damping','.002')
    for e in root.findall('.//flexcomp/contact'):e.attrib.update(priority='1',solimp='.999 .999 .0001')
    if missing:cover.remove(cover.find("flexcomp[@name='lower']"))
    if missing==2:cover.remove(cover.find("flexcomp[@name='upper']"))
    for body,prefix in [(root.find("worldbody/body[@name='tube']"),'tube_wall'),(cover,'spacer')]:
        old=[body.find(f"geom[@name='{prefix}_{i}']") for i in range(48)]
        for geom in old:body.remove(geom)
        for i in range(24):
            geom=copy.deepcopy(old[2*i]);geom.set('name',prefix+'_'+str(i));size=np.fromstring(geom.get('size'),sep=' ');size[1]*=2;geom.set('size',vec(size));geom.set('mass',str(float(geom.get('mass'))*2));body.append(geom)
    exact_cuboid_contacts(root,'tube_wall_')
    tree.write(path);model=mujoco.MjModel.from_xml_path(str(path));data=mujoco.MjData(model);maximum=0.
    geometry=FilmSolidAudit(model,[f'tube_wall_{i}' for i in range(24)]) if model.nflex else None
    penetrating_samples=0;geometry_samples=0
    maximum_iterations=0;iteration_limit_steps=0
    for step in range(round(3/dt)):
        mujoco.mj_step(model,data)
        used=int(np.max(data.solver_niter));maximum_iterations=max(maximum_iterations,used);iteration_limit_steps+=used>=iterations
        if model.nflexedge:maximum=max(maximum,float(np.max(abs(data.flexedge_length/model.flexedge_length0-1))))
        if geometry and step%max(1,round(.005/dt))==0:
            geometry_samples+=1;penetrating_samples+=not geometry.observe(data)['passed']
        if any(w.number for w in data.warning):break
    observation=measure(model,data);warnings=[int(w.number) for w in data.warning];expected=missing==0
    passed=not any(warnings) and iteration_limit_steps==0 and observation['valid']==expected and (maximum<.01 and penetrating_samples==0 if expected else True)
    result=dict(case=name,passed=passed,sectors=sectors,timestep_s=dt,thickness_m=thickness,expected_supported=expected,
        max_edge_strain_throughout=maximum,observation=observation,warnings=warnings,physics_steps=step+1,
        geometry_samples=geometry_samples,penetrating_samples=penetrating_samples,geometry_tolerance_m=.0001,
        solver_iteration_limit=iterations,maximum_solver_iterations=maximum_iterations,iteration_limit_steps=iteration_limit_steps,
        workcell_sha256=sha(path))
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(name,passed,'peak strain',maximum,flush=True);return result


def main():
    cases=[('16um',16,.000016,.001,0,3200),('50um',16,.000050,.001,0,3200),('half_timestep',16,.000016,.0005,0,3200),
           ('mesh24',24,.000016,.001,0,3200),('solver_refinement',16,.000016,.001,0,6400),
           ('missing_lower',16,.000016,.001,1,6400),('missing_both',16,.000016,.001,2,3200)]
    with ProcessPoolExecutor(max_workers=4) as pool:rows=list(pool.map(case,cases))
    selected=rows[0]['observation'];comparisons=[]
    for index in [2,3,4]:
        other=rows[index]['observation'];delta=abs(selected['position_m'][2]-other['position_m'][2]);load=abs(selected['support_vertical_force_n']-other['support_vertical_force_n'])
        comparisons.append(dict(case=rows[index]['case'],passed=delta<.0003 and load<.02,vertical_difference_m=delta,support_load_difference_N=load))
    report=dict(passed=all(r['passed'] for r in rows+comparisons),cases=rows,refinement=comparisons,
        input_sha256={n:sha(HERE/n) for n in ['test_continuum_membrane.py','membrane.py','test_membrane.py','film_contact.py','film_geometry.py']},engine_version=mujoco.__version__,
        scope='Three-second static support and missing-sheet counterexamples; 16/50 um film, half-step, solver-cap and 16-to-24-sector refinement. Iteration caps are raised from exhausted 800/1600 trials; every case must finish without exhausting its cap. Geometric, strain and force tolerances are unchanged. Assumed material properties and ideal bonds; robot episode assessed separately.',whole_paper_validated=False)
    (HERE/'continuum_membrane_tests.json').write_text(json.dumps(report,indent=2)+'\n');return report['passed']


if __name__=='__main__':raise SystemExit(0 if main() else 1)
