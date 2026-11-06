"""Render or check motor limits of a frozen plugin-equipped tool recording.

The wrapper only registers the plant's collision libraries. Recorded states,
geometry and existing checks are unchanged. It grants no execution credit.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path

os.environ.setdefault('MUJOCO_GL', 'egl')

from frozen_collision_plugins import load, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('job', choices=['render', 'limits'])
    p.add_argument('folder', type=Path)
    p.add_argument('--movie', action='store_true')
    p.add_argument('--sample-times', type=float, nargs='*', default=[])
    p.add_argument('--model-run', type=Path)
    a = p.parse_args()
    if a.job == 'limits' and (a.movie or a.sample_times or a.model_run is not None):
        p.error('Rendering options do not apply to motor-limit verification')
    folder = a.folder.resolve()
    model_folder = folder if a.model_run is None else a.model_run.resolve()
    contract = json.loads((model_folder/'contract.json').read_text())
    assert sha(model_folder/'world.xml') == contract['model_sha256']
    if (folder/'result.json').exists():
        result = json.loads((folder/'result.json').read_text())
        key = 'contract_sha256' if a.model_run is None else 'actor_contract_sha256'
        assert result[key] == sha(model_folder/'contract.json')
    pins = contract['source_snapshot_sha256']
    load(contract['collision_plugins'], pins['frozen_collision_plugins.py'])
    name = 'render_tool_grasp.py' if a.job == 'render' else 'verify_dex3_limits.py'
    helper_path = model_folder/'source_snapshot'/name
    assert sha(helper_path) == pins[name]
    assert sha(__file__) == pins['process_tool_grasp_plugins.py']
    spec = importlib.util.spec_from_file_location('frozen_tool_postprocessor', helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    if a.job == 'render':
        helper.render(folder, a.movie, a.sample_times, a.model_run)
        receipt_path = folder/'render_receipt.json'
    else:
        source = model_folder/'source_snapshot/g1_29dof_with_hand_rev_1_0.urdf'
        assert sha(source) == pins[source.name]
        helper.SOURCE = source
        helper.run(folder)
        receipt_path = folder/'source_limit_review.json'
    receipt = json.loads(receipt_path.read_text())
    receipt.update(plugin_wrapper_sha256=sha(__file__),
                   plugin_loader_sha256=pins['frozen_collision_plugins.py'],
                   collision_plugins=contract['collision_plugins'])
    receipt_path.write_text(json.dumps(receipt, indent=2)+'\n')
    if a.job == 'limits' and not receipt['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
