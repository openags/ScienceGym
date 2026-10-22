"""Independent ray and mass checks for the selected movable calibration load."""
import json
from pathlib import Path
import tempfile
import numpy as np,mujoco
from bath_loading_world import build
from bath_assets import load
from world import HERE
from trace_store import sha


def main():
    checks=[]
    def check(name,passed,**values):checks.append(dict(name=name,passed=bool(passed),**values))
    with tempfile.TemporaryDirectory() as directory:
        path=Path(directory)/'workcell.xml';cfg=build(path);m=load(path);d=mujoco.MjData(m);mujoco.mj_forward(m,d)
        body=m.body('calibration_block').id;origin=d.body(body).xpos.copy();holes=cfg['block']['holes'];group=np.array([1,0,0,0,0,0],dtype=np.uint8)
        for hole in holes:
            radii=[0.,.003175] if hole['id']=='reference_rtd' else [0.,.00015]
            distances=[];wrong=[]
            for radius in radii:
                for angle in np.arange(16)*2*np.pi/16:
                    xy=np.array(hole['center_m'])+radius*np.array([np.cos(angle),np.sin(angle)]);point=origin+[xy[0],xy[1],.085];hit=np.array([-1],dtype=np.int32)
                    distance=mujoco.mj_ray(m,d,point,np.array([0.,0.,-1.]),group,True,-1,hit);distances.append(float(distance))
                    if hit[0]<0 or m.geom(hit[0]).name!='calblock_floor':wrong.append(int(hit[0]))
            check('open_corridor_'+hole['id'],not wrong and max(abs(np.array(distances)-.083))<1e-7,
                  rays=len(distances),minimum_free_distance_m=min(distances),maximum_free_distance_m=max(distances),unexpected_hits=wrong)
        block_mass=float(m.body_mass[body]);cradle_mass=float(m.body_mass[m.body('block_cradle').id]);total=block_mass+cradle_mass
        check('copper_mass_matches_bored_volume',abs(block_mass-cfg['block']['mass_kg'])<1e-9,mass_kg=block_mass)
        check('movable_load_within_selected_payload',total<3.,block_and_cradle_mass_kg=total,selected_robot_payload_kg=3.)
        check('separate_free_objects',m.jnt_type[m.joint('calibration_block_free').id]==mujoco.mjtJoint.mjJNT_FREE
              and m.jnt_type[m.joint('block_cradle_free').id]==mujoco.mjtJoint.mjJNT_FREE)
        check('no_attachment_weld',not any(v==mujoco.mjtEq.mjEQ_WELD for v in m.eq_type))
        overlap=[]
        for c in d.contact:
            names=[m.body(m.geom_bodyid[g]).name for g in c.geom]
            if set(names)&{'calibration_block','block_cradle'} and c.dist<-.00001:overlap.append(dict(bodies=names,depth_m=float(c.dist)))
        check('no_initial_load_interpenetration',not overlap,overlaps=overlap)
        check('bath_target_matches_support_plane',abs(cfg['cradle_bath_target_m'][2]-(.615+.078+.002))<1e-9)
    report=dict(passed=all(c['passed'] for c in checks),checks=checks,
        inputs_sha256={n:sha(HERE/n) for n in ['bath_loading_world.py','bath_world.py','check_bath_loading_geometry.py']},
        scope='Candidate 50 x 50 x 80 mm block and cradle geometry only. No robot execution or released task-profile qualification.',whole_paper_validated=False)
    (HERE/'bath_loading_geometry_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],checks=len(checks),failed=[c for c in checks if not c['passed']]),indent=2));return report['passed']


if __name__=='__main__':raise SystemExit(0 if main() else 1)
