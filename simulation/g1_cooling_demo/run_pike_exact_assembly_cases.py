"""Test exact source surfaces with the unchanged six reference/cap support cases.

Removing internal convex-cell boundaries preserves each source exterior,
inertia and contact parameters. Surface audits and dynamic acceptance are
separate requirements. This does not qualify robot handling or optical use.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
import multiprocessing
from pathlib import Path
import shutil
import time
import xml.etree.ElementTree as ET

import numpy as np

from build_pike_reference_runtime import evaluate_support_case
from build_tool_station import sha


def evaluate(world, out, contract, case):
    start = time.monotonic()
    result = evaluate_support_case(world, out, contract, case)
    result['wall_seconds'] = time.monotonic()-start
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source_component', type=Path)
    p.add_argument('assembly_plugin', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--shoulder-surface', type=Path, required=True)
    p.add_argument('--shoulder-gradient', type=Path, required=True)
    p.add_argument('--cap-surface', type=Path)
    p.add_argument('--cap-gradient', type=Path)
    a = p.parse_args()
    source, plugin_folder, out = [v.resolve() for v in [a.source_component, a.assembly_plugin, a.output]]
    contract = json.loads((source/'contract.json').read_text())
    receipt = json.loads((plugin_folder/'plugin.json').read_text())
    plugins = receipt['parent_collision_plugins']+[receipt]
    exact_cap=receipt['part']=='reference_cap'
    if receipt['part'] not in ['reference_shoulder','reference_cap'] or len(plugins)!=(3 if exact_cap else 2):
        raise ValueError('Expected exact panel/shoulder, optionally followed by cap')
    if exact_cap != bool(a.cap_surface and a.cap_gradient):
        raise ValueError('Exact cap requires both independent surface reviews')
    shoulder = next(v for v in plugins if v.get('part')=='reference_shoulder')
    assert shoulder['source_world_sha256']==sha(source/'world.xml')==contract['world_sha256']
    if exact_cap:assert receipt['source_world_sha256']==shoulder['world_sha256']
    assert sha(plugin_folder/'world.xml')==receipt['world_sha256']
    panel = json.loads((source/'surface_review.json').read_text())
    assert sha(source/'surface_review.json')==contract['sampled_surface_review_sha256']
    assert panel['passed_sampled_surface']
    assert panel['plugin_library_sha256']==plugins[0]['library_sha256']
    reviews = {}
    surface_inputs=[('shoulder',shoulder,a.shoulder_surface,a.shoulder_gradient)]
    if exact_cap:surface_inputs.append(('cap',receipt,a.cap_surface,a.cap_gradient))
    for part, plugin, surface_path, gradient_path in surface_inputs:
        surface = json.loads(surface_path.read_text())
        gradient = json.loads(gradient_path.read_text())
        assert surface['passed_sampled_surface'] and gradient['passed']
        assert surface['world_sha256']==gradient['world_sha256']==plugin['world_sha256']
        assert gradient['source_review_sha256']==sha(surface_path)
        assert surface['plugin_library_sha256']==plugin['library_sha256']
        assert sha(surface_path.parent/'samples.npz')==surface['samples_sha256']
        assert sha(gradient_path.parent/'samples.npz')==gradient['samples_sha256']
        reviews[part]=dict(surface_path=str(surface_path.resolve()),surface_sha256=sha(surface_path),
            gradient_path=str(gradient_path.resolve()),gradient_sha256=sha(gradient_path))
    out.mkdir(parents=True,exist_ok=False)
    snapshot=out/'source_snapshot';snapshot.mkdir()
    for name in [Path(__file__).name,'build_pike_reference_runtime.py','build_tool_station.py','runtime_collision_plugins.py']:
        shutil.copyfile(Path(__file__).with_name(name),snapshot/name)
    shutil.copyfile(plugin_folder/'world.xml',out/'world.xml')
    xml=ET.parse(out/'world.xml').getroot()
    inputs={n.get('file'):sha(n.get('file')) for n in xml.find('asset') if n.get('file')}
    for plugin in plugins:
        assert sha(plugin['library'])==plugin['library_sha256']
        inputs[plugin['library']]=plugin['library_sha256']
    (out/'model_inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
    contract.update(scope=__doc__,world_sha256=sha(out/'world.xml'),
        model_inputs_sha256=sha(out/'model_inputs.json'),collision_plugins=plugins,
        shoulder_collision='sdf_exact_surface_plugin',
        cap_collision='sdf_exact_surface_plugin' if exact_cap else 'original_convex_cells',
        source_component_contract_sha256=sha(source/'contract.json'),new_surface_reviews=reviews,
        source_snapshot_sha256={v.name:sha(v) for v in snapshot.iterdir()},
        replacement_scope=('97 shoulder cells'+(' and 97 cap cells' if exact_cap else '')+
            ' replaced by their exact existing source surfaces; exterior vertices, inertia and contact settings preserved'),
        robot_handling_qualified=False)
    (out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    cases=[('port_center','port',[0.,0.]),('port_x','port',[.0005,0.]),('port_y','port',[0.,-.0005]),
           ('cap_center','cap',[0.,0.]),('cap_x','cap',[.0005,0.]),('cap_y','cap',[0.,-.0005])]
    with ProcessPoolExecutor(max_workers=6,mp_context=multiprocessing.get_context('spawn')) as pool:
        futures=[pool.submit(evaluate,out/'world.xml',out,contract,case) for case in cases]
        trials=[f.result() for f in futures]
    np.savez_compressed(out/'support_traces.npz',**{
        t['case']:np.load(out/(t['case']+'_trace.npz'))['samples'] for t in trials})
    result=dict(scope=__doc__,contract_sha256=sha(out/'contract.json'),world_sha256=contract['world_sha256'],
        trace_sha256=sha(out/'support_traces.npz'),trials=trials,
        passed_component_support=all(t['passed'] for t in trials),
        optical_face_accessible=contract['optical_face_accessible'],
        qualified_robot_handling=False,qualified_paper_branch=False)
    (out/'review.json').write_text(json.dumps(result,indent=2)+'\n')
    if not result['passed_component_support']:raise SystemExit(1)


if __name__=='__main__':
    main()
