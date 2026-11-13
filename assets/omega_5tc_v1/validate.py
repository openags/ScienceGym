"""Check source-sized conductors and storage geometry without claiming wiring."""
import json
from pathlib import Path
import sys
import numpy as np
import trimesh

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'assets/cooling_lab_v1'))
from geometry_tools import sha,write_json


def validate():
    record=json.loads((HERE/'model.json').read_text());checks=[]
    def check(name,value):
        checks.append(dict(name=name,passed=bool(value)))
        if not value:raise AssertionError(name)
    check('builder_identity',record['builder_sha256']==sha(HERE/'build.py'))
    check('source_identity',record['source_ledger_sha256']==sha(HERE/'sources.json'))
    check('geometry_identity',record['geometry']['sha256']==sha(ROOT/record['geometry']['path']))
    path=np.array(record['nominal_cable_centerline_m'])
    check('one_metre_catalogue_length',abs(np.linalg.norm(np.diff(path,axis=0),axis=1).sum()-1)<1e-9)
    check('conductor_diameter',record['conductor_diameter_m']==.00013)
    scene=trimesh.load(ROOT/record['geometry']['path'],force='scene')
    check('separate_ends_present',all(n in scene.graph.nodes_geometry for n in ['welded_junction','stripped_terminal_0','stripped_terminal_1']))
    for name,mesh in scene.geometry.items():
        check('finite_closed_'+name,np.isfinite(mesh.vertices).all() and mesh.is_watertight and mesh.volume>0)
    # Topology and scale check: bare terminal tubes must retain the selected
    # diameter; stored geometry may not be thickened to make it easier to see.
    for node in ['stripped_terminal_0','stripped_terminal_1']:
        matrix,name=scene.graph[node];mesh=scene.geometry[name].copy();mesh.apply_transform(matrix)
        check('bare_wire_metric_diameter_'+node,abs(mesh.extents[2]-.00013)<1e-7)
    check('no_wiring_or_sensor_receipt',not record['electrical_termination_qualified'] and not record['temperature_measurement_implemented'])
    check('no_flexible_physics_receipt',not record['dynamic_cable_qualified'])
    out=dict(passed=True,checks=checks,model_sha256=sha(HERE/'model.json'),validator_sha256=sha(__file__),
        scope='Static source-sized visual geometry only; excludes rest-shape mechanics, material parameters, connectors and electrical/thermal response.')
    write_json(HERE/'VERIFICATION.json',out);print(json.dumps({'passed':True,'checks':len(checks)}))


if __name__=='__main__':validate()
