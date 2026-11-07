"""Apply the stricter observer guard to retained fit outputs and known labels.

The native depth fits are held fixed using a patched base observer. This tests
only the actual acceptance code, not new inference, calibration or execution.
All old acceptances and rejections remain in their original reports.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np
import trimesh

HERE=Path(__file__).resolve().parent;BASE=HERE.parents[1]
sys.path.insert(0,str(BASE))
from ftir_slider_outcome import SliderRangeObservation


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    out=HERE/'relief_guard_review.json'
    if out.exists():raise FileExistsError(out)
    shape=BASE/'runs/ftir_approach_08/object_shape_source/nicolet_passive_dynamics.glb'
    scene=trimesh.load(shape,force='scene',process=False)
    T,key=scene.graph['sample_access_slider_grip'];mesh=scene.geometry[key].copy();mesh.apply_transform(T)
    axial,height=.5*np.ptp(mesh.bounds[:,1]),.5*np.ptp(mesh.bounds[:,2])
    paths=[HERE/'view_fixtures.json',HERE/'candidate_views.json',
           BASE/'analysis/nicolet_slider_push_04/endpoint_views_02.json']
    rows=[]
    for path in paths:
        data=json.loads(path.read_text())
        for i,row in enumerate(data['rows']):
            old=row.get('observation',row.get('outcome'))
            inside=row.get('expected_in_physical_range',row.get('expected_inside_physical_window'))
            observer=SliderRangeObservation.__new__(SliderRangeObservation)
            observer.baseline=old['closed_observation_baseline_m']
            observer.minimum_axial_span=float(axial);observer.minimum_height_span=float(height)
            with patch('ftir_slider_outcome.SliderTargetObservation.observe',return_value=copy.deepcopy(old)):
                new=observer.observe(None,None)
            rows.append(dict(source=str(path),index=i,expected_inside=inside,
                             old_accepted=old['accepted'],new_accepted=new['accepted'],reason=new['reason'],
                             observed_relief_m=old.get('observed_span_m',[None,None,None])[2],
                             yaw_rad=row.get('evaluator_yaw_rad',row.get('evaluator_torso_yaw_rad')),
                             opening_m=row.get('evaluator_opening_m',row.get('evaluator_slider_position_m'))))
    selected=[r for r in rows if r['source']==str(HERE/'candidate_views.json') and -.6051<=r['yaw_rad']<=-.5949]
    target=[r for r in selected if .0699<=r['opening_m']<=.0722]
    checks=dict(no_new_acceptance=all(not r['new_accepted'] or r['old_accepted'] for r in rows),
                all_labeled_false_acceptances_rejected=not any(r['new_accepted'] and not r['expected_inside'] for r in rows),
                selected_view_nominal_targets_retained=bool(target) and all(r['new_accepted'] for r in target))
    report=dict(passed=all(checks.values()),checks=checks,rows=rows,
                minimum_observed_relief_m=float(height),public_grip_height_m=float(2*height),
                original_false_acceptances=sum(r['old_accepted'] and not r['expected_inside'] for r in rows),
                remaining_false_acceptances=sum(r['new_accepted'] and not r['expected_inside'] for r in rows),
                retained_true_acceptances=sum(r['new_accepted'] and r['expected_inside'] for r in rows),
                additional_true_rejections=sum(r['old_accepted'] and not r['new_accepted'] and r['expected_inside'] for r in rows),
                source_sha256={str(p):sha(p) for p in [Path(__file__),BASE/'ftir_slider_outcome.py',shape,*paths]},scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in {'rows','source_sha256'}}))
    if not report['passed']:raise SystemExit(1)


if __name__=='__main__':main()
