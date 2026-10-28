"""Reconstruct exported tweezer surfaces independently from pinned source GLB.

This supports only the declared, inferred cantilever geometry. It establishes
render/checker agreement, not elastic forces or frictional grasp stability.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
import trimesh
from source_geometry import ROOT


class DeformedGeometry:
    def __init__(self, folder, manifest):
        receipt=json.loads((Path(folder)/'export.json').read_text())
        self.definitions={};self.sources={};self.last={};self.maximum_vertex_error_m=0.
        assets={a['id']:a for a in manifest['assets']}
        for definition in receipt['scene'].get('deformableGeometry',[]):
            identity=definition['id'];asset=assets[identity]
            assert identity not in self.definitions
            assert definition['model']=='symmetric_fixed_heel_cantilever_v1'
            assert definition['length_m']==.130 and definition['tip_deflection_m']==.001775
            assert definition['source']==asset['geometry']
            assert definition['source_sha256']==asset['geometry_sha256']==hashlib.sha256((ROOT/asset['geometry']).read_bytes()).hexdigest()
            self.definitions[identity]=definition
            self.sources[identity]=trimesh.load(ROOT/asset['geometry'],force='scene',process=False)
            assert len(definition['samples'])>=3
            assert {0.,1.}.issubset({s['closure'] for s in definition['samples']})
            for sample in definition['samples']:
                parts=self.parts(identity,sample['closure'],normalized=False)
                assert set(parts)=={p['name'] for p in sample['parts']}
                for part in sample['parts']:
                    mesh=parts[part['name']];transform=self.sources[identity].graph[part['name']][0]
                    assert np.allclose(np.array(part['node_matrix']).reshape(4,4).T,transform,rtol=0,atol=1e-12)
                    vertices=np.array(part['vertices']).reshape(-1,3)
                    assert vertices.shape==mesh.vertices.shape
                    assert np.array_equal(np.array(part['indices']).reshape(-1,3),mesh.faces)
                    error=float(np.max(abs(vertices-mesh.vertices)))
                    self.maximum_vertex_error_m=max(error,self.maximum_vertex_error_m)
                    assert error<1e-9,(part['name'],error)

    def parts(self,identity,closure,normalized=True):
        assert np.isfinite(closure) and 0<=closure<=1
        source=self.sources[identity];result={}
        for name in source.graph.nodes_geometry:
            transform,key=source.graph[name];mesh=source.geometry[key].copy()
            if name.startswith('ptfe_spring_arm_'):
                sign=int(name.rsplit('_',1)[1]);x=mesh.vertices[:,0]
                # Fixed heel at x=130 mm; zero-displacement and zero-slope there.
                distance=np.clip(.130-x,0,.130)
                displacement=.001775*closure*(distance/.130)**2*(3-distance/.130)/2
                mesh.vertices[:,1]-=sign*displacement
            if normalized:mesh.apply_transform(transform)
            result[name]=mesh
        return result

    def apply(self,manager,frame):
        states=frame.get('deformable_states',{})
        assert set(states)==set(self.definitions),'Missing or unknown deformation state'
        for identity in self.definitions:
            if identity not in manager._objs:continue
            closure=states[identity];key=(id(manager),identity)
            if self.last.get(key)!=closure:
                mesh=trimesh.util.concatenate(list(self.parts(identity,closure).values()))
                # Replacing an existing key alone can leave a stale FCL object.
                manager.remove_object(identity);manager.add_object(identity,mesh)
                self.last[key]=closure
            manager.set_transform(identity,np.array(frame['groups'][identity]).reshape(4,4).T)
