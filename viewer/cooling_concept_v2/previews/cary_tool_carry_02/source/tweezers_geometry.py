"""Source-mesh tweezers with an explicitly inferred elastic closing shape.

The Ideal-tek AA.SA.T.6 source fixes the external dimensions. This geometry
model bends the two arms about their joined heel; it is not a force model.
Closure 1 selects a 2.05 mm inner tip gap for a 2 mm annular holder edge.
"""
import hashlib
import numpy as np
import trimesh
from source_geometry import ROOT, ASSETS

TIP_DEFLECTION_M = .001775
LENGTH_M = .130
RAW_X_OFFSET_M = .06499999761581421


def meshes(closure=0., identity='tweezers_white'):
    assert 0 <= closure <= 1
    source=trimesh.load(ROOT/ASSETS[identity]['geometry'],force='scene',process=False)
    result={}
    for name in source.graph.nodes_geometry:
        transform,key=source.graph[name]
        mesh=source.geometry[key].copy();mesh.apply_transform(transform)
        if name.startswith('ptfe_spring_arm_'):
            sign=int(name.rsplit('_',1)[1])
            a=1-np.clip((mesh.vertices[:,0]+RAW_X_OFFSET_M)/LENGTH_M,0,1)
            mesh.vertices[:,1]-=sign*TIP_DEFLECTION_M*closure*a*a*(3-a)/2
        result[name]=mesh
    return result


def provenance():
    asset=ASSETS['tweezers_white']
    return dict(source=asset['geometry'],source_sha256=asset['geometry_sha256'],
                model_sha256=hashlib.sha256(__import__('pathlib').Path(__file__).read_bytes()).hexdigest(),
                length_m=LENGTH_M,tip_deflection_m=TIP_DEFLECTION_M,raw_x_offset_m=RAW_X_OFFSET_M,
                closed_inner_tip_gap_m=.00205,
                inference='Symmetric small-deflection cantilever shape, fixed heel; no force or grip qualification')
