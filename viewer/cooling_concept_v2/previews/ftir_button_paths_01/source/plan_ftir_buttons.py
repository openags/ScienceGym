"""Plan whole-body Nicolet acquisition-button approaches and modeled presses.

The instrument is closed. Its source key geometry moves through a declared
0.3 mm inferred switch travel while the fitted index fingertip follows it.
The plan checks full-room source geometry, not forces or acquisition data.
"""
import argparse
import hashlib
import json
import time
import numpy as np

from ftir_measurement_scene import FTIRMeasurementScene
from optical_choreography import HERE, canonical, make_base, solve_palm, Space
from plan_optical_approaches import plan


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trial', default='01')
    args = parser.parse_args()
    out = HERE / 'previews' / ('ftir_button_paths_' + args.trial)
    out.mkdir(exist_ok=False)
    names = ['plan_ftir_buttons.py', 'ftir_measurement_scene.py', 'optical_delivery.py',
             'optical_choreography.py', 'source_geometry.py', 'plan_optical_approaches.py',
             'previews/ftir_buttons_01/fit.json', 'motion_poses.json', 'optical_setup.json']
    pins = {}
    for name in names:
        data = (HERE / name).read_bytes()
        dest = out / 'source' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        pins[name] = hashlib.sha256(data).hexdigest()
    fits = json.loads((HERE / names[6]).read_text())
    assert fits['passed']
    scene = FTIRMeasurementScene()
    poses = json.loads((HERE / 'motion_poses.json').read_text())['poses']
    rest = canonical({**poses['rest'], **poses['stance']})
    successes, failures = [], []
    started = time.monotonic()
    for x, y, yaw in [(9.50, 7.95, 1.7), (9.50, 7.85, 1.7), (9.60, 7.95, 1.7), (9.40, 7.95, 1.7)]:
        base = make_base(x, y, yaw, rest)
        for number, fit in enumerate(fits['candidates']):
            q = {**rest, **fit['q']}
            strokes, failure = [], None
            print('candidate', [x,y,yaw], number, flush=True)
            for button in fit['buttons']:
                target = np.array(button['palm'])
                normal = np.array(button['outward_normal'])
                rows = []
                for displacement in [*np.linspace(.06, 0., 25), *np.linspace(0., -.0003, 7)[1:]]:
                    desired = target.copy()
                    desired[:3, 3] += normal * displacement
                    travel = max(0., -float(displacement))
                    scene.set_key(button['button'], travel)
                    q, pe, re = solve_palm(base, desired, q, waist=True)
                    bad = scene.check(base, q) if pe < 1e-5 and re < 1e-4 else dict(reach_error_m=pe, orientation_error_rad=re)
                    if bad:
                        failure = dict(button=button['button'], displacement_m=float(displacement), error=bad)
                        break
                    rows.append(dict(root=base.tolist(), q=dict(q), button=button['button'],
                                     button_travel_m=travel, palm=desired.tolist(),
                                     position_error_m=pe, orientation_error_rad=re))
                scene.set_key(button['button'], 0.)
                if failure:
                    break
                strokes.append(dict(button=button['button'], label=button['label'], rows=rows))
            if not failure:
                # Each control can be entered and left from the same empty-hand
                # rest posture, so no unexplained hand repositioning is needed.
                for stroke in strokes:
                    space = Space(scene, base, rest, stroke['rows'][0]['q'], {}, fit['q'])
                    try:
                        print('entry', stroke['button'], flush=True)
                        path = plan(space)
                        stroke['entry'] = [dict(root=base.tolist(), q=space.q_at(v)) for v in path]
                        stroke['entry_collision_queries'] = space.calls
                    except RuntimeError as error:
                        failure = dict(button=stroke['button'], entry_error=str(error))
                        break
            if failure:
                failures.append(dict(base=[x,y,yaw], fit=number, failure=failure))
                continue
            successes.append(dict(base=[x,y,yaw], fit=number, strokes=strokes))
            break
        if successes:
            break
    report = dict(scope=__doc__, passed=bool(successes), candidates=successes, failures=failures,
                  source_sha256=pins, seconds=time.monotonic()-started,
                  inferred_switch_travel_m=.0003,
                  limitations=['Ankle housings are omitted by the planning scene.',
                               'Dense retimed interpolation, button contact-force and sensor-control checks remain required.',
                               'The controller PC must be running OMNIC; acquisition configuration is a declared initial condition.',
                               'This plan does not generate measured spectra or qualify a complete experiment.'])
    (out / 'plan.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=report['passed'], candidates=len(successes), failures=len(failures),
                          seconds=report['seconds'])), flush=True)


if __name__ == '__main__':
    main()
