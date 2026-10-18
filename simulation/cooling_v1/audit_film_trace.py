"""Audit film/box intersection at every saved state, without contact forces."""
import argparse
import json
from pathlib import Path
import numpy as np
import mujoco
from film_geometry import FilmSolidAudit
from load_model import load
from trace_store import load_trace, sha


def audit(directory, geom_prefix=None):
    directory = Path(directory)
    receipt = json.loads((directory/'result.json').read_text())
    expected = receipt.get('artifacts_sha256', {}).get('physics_trace.npz')
    trace = load_trace(directory, expected)
    model = load(directory/'workcell.xml')
    data = mujoco.MjData(model)
    prefixes = [geom_prefix] if geom_prefix else ['tube_wall_', 'pe_tube_wall_']
    names = [model.geom(g).name for g in range(model.ngeom)
             if any((model.geom(g).name or '').startswith(p) for p in prefixes)]
    geometry = FilmSolidAudit(model, names)
    failures = 0
    first = None
    worst = None
    worst_pairs = 0
    for i, at in enumerate(trace['time']):
        data.qpos[:] = trace['qpos'][i]
        mujoco.mj_kinematics(model, data)
        mujoco.mj_comPos(model, data)
        mujoco.mj_flex(model, data)
        check = geometry.observe(data)
        if not check['passed']:
            failures += 1
            record = dict(time_s=float(at), observation=check)
            if first is None:
                first = record
            if len(check['intersecting_pairs']) > worst_pairs:
                worst_pairs = len(check['intersecting_pairs'])
                worst = record
    result = dict(passed=failures == 0, samples=len(trace['time']),
        failed_samples=failures, first_failure=first, worst_pair_count=worst_pairs,
        worst=worst, tolerance_m=geometry.tolerance,
        source_trace_sha256=expected or sha(directory/'physics_trace.npz'),
        workcell_sha256=sha(directory/'workcell.xml'),
        verifier_sha256=sha(Path(__file__)), geometry_sha256=sha(Path(__file__).with_name('film_geometry.py')),
        engine_version=mujoco.__version__, whole_paper_validated=False,
        scope='Triangle/box separating-axis test at every saved state; no assertion about unsampled times or material failure')
    (directory/'film_geometry_verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['passed', 'samples', 'failed_samples', 'worst_pair_count']}), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory')
    parser.add_argument('--geom-prefix')
    args = parser.parse_args()
    raise SystemExit(0 if audit(args.directory, args.geom_prefix)['passed'] else 1)
