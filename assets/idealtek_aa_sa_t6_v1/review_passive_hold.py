"""Additional hold-quality diagnosis; its gates postdate the first fixtures.

Passing the initial closure/release checks is insufficient for manipulating a
specimen. This review checks chatter and a linear-elastic stress estimate.
These are development gates, not a preregistered qualification campaign.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import mujoco
import numpy as np


def review(source, folder):
    source,folder=Path(source).resolve(),Path(folder).resolve()
    output=folder/'hold_quality_review.json'
    if output.exists(): raise FileExistsError(output)
    base=json.loads((folder/'review.json').read_text())
    asset=json.loads((source/'model_review.json').read_text())
    spec=importlib.util.spec_from_file_location('frozen_tool_builder',source/'source_snapshot/build_passive.py')
    builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    trace=dict(np.load(folder/'trace.npz'))
    model=mujoco.MjModel.from_xml_path(str(folder/'fixture.xml'))
    stress=0.;worst=None
    for label in ['negative','positive']:
        for i,row in enumerate(asset['mode_discretization']):
            j=model.joint(f'{label}_bend_{i:02d}').id
            angle=trace['qpos'][:,model.jnt_qposadr[j]]
            moment=float(model.jnt_stiffness[j]*np.max(abs(angle)))
            width,thickness,_=builder.profile(row['hi_m'],asset['inferred_interior_thickness_scale'])
            value=6*moment/(width*thickness**2)
            if value>stress:
                stress=value;worst=dict(joint=model.joint(j).name,elastic_moment_nm=moment,
                                       section_width_m=width,section_thickness_m=thickness)
    held=[r for r in base['observations'] if 4.5<=r['time_s']<=5.5]
    excursion=float(np.ptp([r['gap_m'] for r in held])) if held else None
    supported=bool(held) and all(min(r['loads_n'].values())>.05 for r in held)
    checks=dict(initial_contact_review_passed=base['passed'],hold_has_continuous_two_sided_contact=supported,
                hold_gap_excursion_below_50_um=excursion is not None and excursion<.00005,
                estimated_stress_below_source_minimum_yield=stress<200e6)
    result=dict(passed=all(checks.values()),checks=checks,hold_interval_s=[4.5,5.5],
                hold_gap_excursion_m=excursion,maximum_linear_bending_stress_pa=stress,worst_section=worst,
                limitations=['Linear section-stress approximation; not a validated finite-element stress field',
                             'Additional hold gates were introduced after observing fixture05 chatter',
                             'No robot, gripping skill or specimen-retention credit'],qualified_manipulation=False,
                source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),folder/'trace.npz',folder/'review.json',source/'model_review.json']})
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('folder');a=p.parse_args()
    if not review(a.source,a.folder)['passed']:raise SystemExit(1)
