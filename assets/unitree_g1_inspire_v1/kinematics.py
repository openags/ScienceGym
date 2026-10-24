"""Source-frame kinematics for the pinned G1/Inspire FTP asset, in metres."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
from audit import origin,sha

HERE=Path(__file__).resolve().parent


class Robot:
    def __init__(self):
        self.source=json.loads((HERE/'SOURCE.json').read_text())
        for record in self.source['files']:
            if sha(HERE/record['path'])!=record['sha256']:raise ValueError('Changed source '+record['path'])
        self.path=HERE/self.source['model_path']
        self.xml=ET.parse(self.path).getroot()
        self.links={e.get('name'):e for e in self.xml.findall('link')}
        raw={e.find('child').get('link'):e for e in self.xml.findall('joint')}
        self.root=next(iter(set(self.links)-set(raw)))
        self.joints=[];done={self.root}
        while raw:
            ready=[name for name,e in raw.items() if e.find('parent').get('link') in done]
            if not ready:raise ValueError('Disconnected/cyclic URDF')
            for name in ready:
                e=raw.pop(name);limit=e.find('limit');mimic=e.find('mimic')
                self.joints.append(dict(name=e.get('name'),id=name,parent=e.find('parent').get('link'),type=e.get('type'),
                  origin_matrix=origin(e.find('origin')).tolist(),axis=[float(v) for v in e.find('axis').get('xyz').split()] if e.find('axis') is not None else [0,0,1],
                  limits={k:float(v) for k,v in limit.attrib.items()} if limit is not None else None,
                  mimic=dict(mimic.attrib) if mimic is not None else None))
                done.add(name)
        self.by_name={j['name']:j for j in self.joints}
        self.root_matrix=np.eye(4)
        self.root_matrix[:3,3]=json.loads((HERE/'VERIFICATION.json').read_text())['preview']['source_to_preview_translation_m']
        self.meshes={};self.corners={}
        self.preview=trimesh.load(HERE/'geometry/g1_inspire_ftp_zero.glb',force='scene')
        for name,link in self.links.items():
            corners=[]
            for visual in link.findall('visual'):
                m=visual.find('geometry/mesh');path=self.path.parent/m.get('filename')
                if path not in self.meshes:self.meshes[path]=trimesh.load(path,force='mesh',process=False)
                mesh=self.meshes[path];lo,hi=mesh.bounds
                cube=np.array([[x,y,z] for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]])
                cube*=np.array([float(v) for v in m.get('scale','1 1 1').split()])
                corners.extend(trimesh.transform_points(cube,origin(visual.find('origin'))))
            if corners:self.corners[name]=np.array(corners)
        self.bind=self.fk()

    def resolve(self,coordinates=None):
        q=dict(coordinates or {})
        def get(name):
            j=self.by_name[name]
            if j['mimic']:
                m=j['mimic'];q[name]=float(m.get('offset',0))+float(m.get('multiplier',1))*get(m['joint'])
            return q.get(name,0.)
        for j in self.joints:q[j['name']]=get(j['name'])
        return q

    def fk(self,coordinates=None):
        q=self.resolve(coordinates);world={self.root:self.root_matrix.copy()}
        for j in self.joints:
            t=np.asarray(j['origin_matrix'])
            if j['type']=='revolute':t=t@trimesh.transformations.rotation_matrix(q[j['name']],j['axis'])
            elif j['type']!='fixed':raise ValueError('Unsupported joint type '+j['type'])
            world[j['id']]=world[j['parent']]@t
        return world

    def link_bounds(self,coordinates=None):
        world=self.fk(coordinates)
        return {name:np.array([v.min(axis=0),v.max(axis=0)]) for name,c in self.corners.items()
                for v in [trimesh.transform_points(c,world[name])]} # Conservative transformed mesh-box corners.

    def scene(self,coordinates=None):
        world=self.fk(coordinates);scene=self.preview.copy()
        for node in scene.graph.nodes_geometry:
            name=node.rsplit('_visual_',1)[0];matrix,geometry=scene.graph[node]
            scene.graph.update(frame_to=node,matrix=world[name]@np.linalg.inv(self.bind[name])@matrix,geometry=geometry)
        return scene

    def inspection(self):
        q={}
        for j in self.joints:
            if j['type']=='revolute' and not j['mimic'] and any('_'+finger+'_' in j['name'] for finger in ['thumb','index','middle','ring','little']):
                q[j['name']]=.7*j['limits']['upper']
        return self.resolve(q)
