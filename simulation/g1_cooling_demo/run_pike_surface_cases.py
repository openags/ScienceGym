"""Run all six unchanged support cases for a geometry-reviewed panel plugin."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
import multiprocessing
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import numpy as np

from build_pike_reference_runtime import evaluate_support_case
from build_tool_station import sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_component', type=Path)
    parser.add_argument('plugin', type=Path)
    parser.add_argument('geometry_review', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    source, plugin_folder, geometry, out = [p.resolve() for p in [
        args.source_component, args.plugin, args.geometry_review, args.output]]
    receipt = json.loads((plugin_folder/'plugin.json').read_text())
    shape = json.loads(geometry.read_text())
    contract = json.loads((source/'contract.json').read_text())
    assert sha(source/'world.xml') == receipt['source_world_sha256'] == contract['world_sha256']
    assert sha(plugin_folder/'world.xml') == receipt['world_sha256'] == shape['world_sha256']
    assert sha(plugin_folder/'plugin.json') == shape['plugin_receipt_sha256']
    assert sha(receipt['library']) == receipt['library_sha256'] == shape['plugin_library_sha256']
    if not shape['passed_sampled_surface']:
        raise ValueError('Source-surface geometry comparison has not passed')
    out.mkdir(parents=True, exist_ok=False)
    snapshot = out/'source_snapshot'; snapshot.mkdir()
    for name in [Path(__file__).name, 'build_pike_reference_runtime.py', 'build_tool_station.py']:
        shutil.copyfile(Path(__file__).with_name(name), snapshot/name)
    shutil.copyfile(plugin_folder/'world.xml', out/'world.xml')
    shutil.copyfile(plugin_folder/'plugin.json', out/'plugin.json')
    shutil.copyfile(geometry, out/'surface_review.json')
    xml = ET.parse(out/'world.xml').getroot()
    inputs = {n.get('file'): sha(n.get('file')) for n in xml.find('asset') if n.get('file')}
    inputs[receipt['library']] = receipt['library_sha256']
    (out/'model_inputs.json').write_text(json.dumps(inputs, indent=2)+'\n')
    contract.update(scope=__doc__, panel_collision='sdf_exact_surface_plugin',
        source_component_contract_sha256=sha(source/'contract.json'),
        world_sha256=sha(out/'world.xml'), model_inputs_sha256=sha(out/'model_inputs.json'),
        collision_plugin=receipt, sampled_surface_review_sha256=sha(geometry),
        sdf_surface_accuracy_qualified=True,
        surface_accuracy_scope='3744 retained points, exhaustive source triangles and ray occupancy, 5 micrometre limit; no arbitrary trajectory qualification',
        source_snapshot_sha256={p.name: sha(p) for p in snapshot.iterdir()},
        numeric_limitations='Native interpolated panel SDF and convex partitions are not adopted. Exact-source plugin still requires complete-room and manipulation qualification.')
    (out/'contract.json').write_text(json.dumps(contract, indent=2)+'\n')
    cases = [('port_center', 'port', [0., 0.]), ('port_x', 'port', [.0005, 0.]),
             ('port_y', 'port', [0., -.0005]), ('cap_center', 'cap', [0., 0.]),
             ('cap_x', 'cap', [.0005, 0.]), ('cap_y', 'cap', [0., -.0005])]
    with ProcessPoolExecutor(max_workers=6, mp_context=multiprocessing.get_context('spawn')) as pool:
        futures = [pool.submit(evaluate_support_case, out/'world.xml', out, contract, case) for case in cases]
        trials = [f.result() for f in futures]
    traces = {t['case']: np.load(out/(t['case']+'_trace.npz'))['samples'] for t in trials}
    np.savez_compressed(out/'support_traces.npz', **traces)
    review = dict(scope=__doc__, contract_sha256=sha(out/'contract.json'),
        world_sha256=contract['world_sha256'], trace_sha256=sha(out/'support_traces.npz'),
        optical_face_accessible=contract['optical_face_accessible'],
        trials=trials, passed_component_support=all(t['passed'] for t in trials),
        sampled_panel_surface_passed=True, surface_review_sha256=sha(geometry),
        qualified_robot_handling=False, qualified_paper_branch=False)
    (out/'review.json').write_text(json.dumps(review, indent=2)+'\n')
    if not review['passed_component_support']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
