"""Load-path regressions, including physical missing-layer counterexamples."""
import hashlib
import json
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET
import numpy as np
import mujoco
from membrane import build
from world import HERE


def measure(model,data):
    bid=model.body('cover').id
    vertical=0
    for i,c in enumerate(data.contact):
        if c.flex[0]<0 and c.flex[1]<0:continue
        geom=int(c.geom1 if c.geom1>=0 else c.geom2)
        if geom<0 or model.body(int(model.geom_bodyid[geom])).name!='tube':continue
        force=np.zeros(6);mujoco.mj_contactForce(model,data,i,force)
        vertical+=float((c.frame.reshape(3,3).T@force[:3])[2])*(1 if c.geom1>=0 else -1)
    weight=float(model.body_subtreemass[bid])*9.81
    strain=float(np.max(np.abs(data.flexedge_length/model.flexedge_length0-1))) if model.nflexedge else 0
    position=data.body('cover').xpos.copy()
    tilt=float(np.arccos(np.clip(data.body('cover').xmat.reshape(3,3)[2,2],-1,1)))
    speed=float(np.linalg.norm(data.body('cover').cvel))
    return dict(position_m=position.tolist(),tilt_rad=tilt,speed=speed,
                support_vertical_force_n=vertical,assembly_weight_n=weight,max_edge_strain=strain,
                valid=bool(abs(position[2]-.0602)<.001 and np.linalg.norm(position[:2])<.001
                           and tilt<.01 and speed<.03 and abs(vertical-weight)<weight*.1
                           and strain<.01 and model.nflex==2 and not any(w.number for w in data.warning)))


def main():
    names=['membrane.py','test_membrane.py']
    pins={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in names}
    outcomes=[]
    with tempfile.TemporaryDirectory(prefix='sciencegym-membrane-') as directory:
        for case in ['nanoporous_16um','ldpe_50um','half_timestep','missing_lower_sheet','missing_both_sheets']:
            path=Path(directory)/(case+'.xml')
            build(path,thickness=.000050 if case=='ldpe_50um' else .000016)
            tree=ET.parse(path);root=tree.getroot();body=root.find("worldbody/body[@name='cover']")
            if case=='half_timestep':root.find('option').set('timestep','.00025')
            if case.startswith('missing'):
                body.remove(body.find("flexcomp[@name='lower']"))
                if case=='missing_both_sheets':body.remove(body.find("flexcomp[@name='upper']"))
            tree.write(path)
            model=mujoco.MjModel.from_xml_path(str(path));data=mujoco.MjData(model)
            for _ in range(round(1.25/model.opt.timestep)):
                mujoco.mj_step(model,data)
                if any(w.number for w in data.warning):break
            observation=measure(model,data)
            expected=not case.startswith('missing')
            outcomes.append(dict(case=case,passed=observation['valid']==expected,expected_valid=expected,
                                 observations=observation,engine_version=mujoco.__version__))
            print(case,outcomes[-1]['passed'],observation,flush=True)
    unchanged=all(hashlib.sha256((HERE/n).read_bytes()).hexdigest()==pin for n,pin in pins.items())
    result=dict(passed=all(x['passed'] for x in outcomes) and unchanged,outcomes=outcomes,input_sha256=pins,
        scope='Assumed constrained cloth, permanent edge bonds and 0.25 mm collision envelope. Tests validate simulated load support only; no measured material, damage, adhesion or robot attachment qualification.',
        whole_paper_validated=False)
    (HERE/'membrane_tests.json').write_text(json.dumps(result,indent=2)+'\n')
    return result['passed']


if __name__=='__main__':raise SystemExit(0 if main() else 1)
