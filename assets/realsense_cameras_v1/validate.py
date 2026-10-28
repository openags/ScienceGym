"""Independently check unit/shape preservation and unqualified installation state."""
import json
from pathlib import Path
import sys
import numpy as np
import trimesh
from scipy.spatial import cKDTree

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'assets/cooling_lab_v1'))
from geometry_tools import sha,write_json


def validate():
    model=json.loads((HERE/'model.json').read_text());sources=json.loads((HERE/'sources.json').read_text());checks=[]
    def check(name,value,**data):
        checks.append(dict(name=name,passed=bool(value),**data))
        if not value:raise AssertionError(name)
    check('builder_identity',model['builder_sha256']==sha(HERE/'build.py'))
    check('source_identity',model['source_ledger_sha256']==sha(HERE/'sources.json'))
    for f in sources['vendor_files']:check('vendor_identity_'+f['path'],sha(HERE/f['path'])==f['sha256'])
    check('license_retained','Apache License' in (HERE/'vendor/LICENSE').read_text())
    check('three_sensor_roles',len(model['selected_roles'])==3)
    for row in model['selected_roles']:
        check('selected_channels_'+row['resource_id'],row['channels']==(['RGB','depth'] if row['resource_id']=='robot:HEAD_RGBD' else ['RGB']))
    for item in model['items']:
        key=item['id'];source=trimesh.load(HERE/item['manufacturer_mesh']['path'],force='mesh')
        scene=trimesh.load(ROOT/item['geometry']['path'],force='scene');vendor=trimesh.Scene()
        names={p['id'] for p in item['geometry']['parts'] if p['provenance']=='manufacturer_mesh'}
        for node in scene.graph.nodes_geometry:
            matrix,name=scene.graph[node]
            if node in names:vendor.add_geometry(scene.geometry[name],transform=matrix)
        converted=vendor.to_mesh()
        # Source STL axes are X=width,Y=height,Z=outward front, in mm.
        expected=source.vertices[:,[0,2,1]]*np.array([.001,-.001,.001])
        error=max(cKDTree(expected).query(converted.vertices)[0].max(),cKDTree(converted.vertices).query(expected)[0].max())
        check('vertices_preserved_'+key,error<1e-7,max_error_m=float(error))
        check('triangles_preserved_'+key,len(source.faces)==len(converted.faces))
        check('appearance_layer_separate_'+key,all(p['id'].startswith('appearance_') for p in item['geometry']['parts'] if p['provenance']=='authored_appearance_overlay'))
        check('finite_vertices_'+key,np.isfinite(converted.vertices).all())
        check('model_identity_'+key,sha(ROOT/item['geometry']['path'])==item['geometry']['sha256'])
        target=[.124,.026,.029] if key=='d455' else [.042,.023,.042]
        check('datasheet_envelope_'+key,np.allclose(scene.extents,target,atol=.00015),actual_m=scene.extents.tolist())
        check('no_installation_claim_'+key,item['installation']['status']=='unmounted_review_candidate' and item['installation']['extrinsic_matrix'] is None)
        check('no_calibration_claim_'+key,not item['observations']['enabled'] and item['observations']['intrinsics'] is None)
        check('no_dynamics_claim_'+key,not item['dynamics_qualified'])
    report=dict(passed=True,checks=checks,model_sha256=sha(HERE/'model.json'),validator_sha256=sha(__file__),
        scope='Manufacturer input identity, surface/unit preservation and claim limits. No installation, collision, sensor or dynamics qualification.')
    write_json(HERE/'VERIFICATION.json',report)
    print(json.dumps({'passed':True,'checks':len(checks)}))


if __name__=='__main__':validate()
