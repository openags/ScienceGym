"""Inspect the inferred moving cover before any robot execution.

The swept poses below are geometry diagnostics, never execution evidence.
"""
import json,tempfile
from pathlib import Path
import numpy as np,mujoco
from optical_assets import load,DEVICES
from nicolet_world import build
from trace_store import sha


def main():
    here=Path(__file__).resolve().parent;checks=[]
    def check(name,passed,**values):checks.append(dict(name=name,passed=bool(passed),**values))
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/'workcell.xml';cfg=build(path);m=load(path);d=mujoco.MjData(m)
        hinge=m.joint('spectrometer_lid_hinge');slider=m.joint('sample_slider_travel')
        check('passive_cover_and_slider',hinge.id not in m.actuator_trnid[:,0] and slider.id not in m.actuator_trnid[:,0])
        check('robot_only_actuators',m.nu==8)
        check('no_moving_part_weld',not any(t==mujoco.mjtEq.mjEQ_WELD for t in m.eq_type))
        check('selected_hinge_friction',abs(float(m.dof_frictionloss[hinge.dofadr[0]])-cfg['selected_hinge_friction_Nm'])<1e-12)
        check('selected_cover_mass_is_positive',float(m.body('spectrometer_lid').mass[0])>0,
              cover_mass_kg=float(m.body('spectrometer_lid').mass[0]),slider_mass_kg=float(m.body('sample_slider').mass[0]))
        worst=0.;collisions=[]
        for angle in np.linspace(0,cfg['selected_open_angle_rad'],136):
            for travel in np.linspace(*m.jnt_range[slider.id],3):
                d.joint('spectrometer_lid_hinge').qpos[0]=angle;d.joint('sample_slider_travel').qpos[0]=travel
                mujoco.mj_forward(m,d)
                for contact in d.contact:
                    bodies=[m.body(int(m.geom_bodyid[g])).name for g in contact.geom]
                    if not set(bodies)&{'spectrometer_lid','sample_slider'}:continue
                    if 'nicolet' not in bodies:continue
                    worst=min(worst,float(contact.dist))
                    if contact.dist<-.00001 and len(collisions)<10:
                        collisions.append(dict(angle_rad=float(angle),slider_m=travel,bodies=bodies,
                                               geoms=[m.geom(g).name for g in contact.geom],overlap_m=float(contact.dist)))
        check('cover_and_slider_sweep_clear_case',not collisions,poses=408,maximum_overlap_m=-worst,collisions=collisions)
        card=json.loads((DEVICES['nicolet_6700']/'interfaces.json').read_text())
        handle=next(i for i in card['interfaces'] if i['id']=='sample_cover')
        d.qpos[:]=m.qpos0;mujoco.mj_forward(m,d)
        check('physical_handle_matches_asset',np.linalg.norm(d.site('spectrometer_lid_grasp').xpos-np.array(cfg['instrument_origin_m'])-handle['grasp_center_m'])<1e-9)
        check('source_geometry_checks_pass',json.loads((DEVICES['nicolet_6700']/'geometry_checks.json').read_text())['passed'])
    report=dict(passed=all(c['passed'] for c in checks),checks=checks,diagnostic_only=True,robot_execution_validated=False,
                input_sha256={n:sha(here/n) for n in ['check_nicolet_import.py','nicolet_world.py','optical_assets.py','geometry/nicolet_6700/catalog.json']},
                asset_interfaces_sha256=sha(DEVICES['nicolet_6700']/'interfaces.json'))
    (here/'nicolet_import_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],checks=len(checks),failed=[c for c in checks if not c['passed']]),indent=2))
    return report['passed']


if __name__=='__main__':raise SystemExit(0 if main() else 1)
