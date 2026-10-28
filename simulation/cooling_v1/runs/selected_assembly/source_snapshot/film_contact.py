"""Use exact cuboid meshes for triangle/solid contact, preserving geometry.

MuJoCo 3.16.0's boxTriangle narrow phase checks triangle vertices against box
faces and box corners against the triangle. Edge/face intersections can be
missed. An eight-corner mesh uses the general convex-element contact path.
Source: google-deepmind/mujoco, tag 3.16.0,
src/engine/engine_collision_flex.c (boxTriangle and mjc_GeomElem).
"""
from itertools import product
import xml.etree.ElementTree as ET
import numpy as np
from world import vec


def exact_cuboid_contacts(root, prefix='pe_tube_wall_'):
    asset=root.find('asset')
    if asset is None:asset=ET.SubElement(root,'asset')
    meshes={};converted=[]
    for geom in root.findall('.//geom'):
        name=geom.get('name','')
        if not name.startswith(prefix):continue
        if geom.get('type')!='box':raise ValueError('Expected source box: '+name)
        size=tuple(np.fromstring(geom.get('size'),sep=' '))
        if len(size)!=3:raise ValueError('Expected three box half-sizes')
        if size not in meshes:
            mesh='film_support_cuboid_'+str(len(meshes))+'_'+prefix.rstrip('_')
            vertices=np.array(list(product([-1,1],repeat=3)))*size
            ET.SubElement(asset,'mesh',name=mesh,vertex=vec(vertices.ravel()))
            meshes[size]=mesh
        geom.set('type','mesh');geom.set('mesh',meshes[size]);geom.attrib.pop('size')
        converted.append(dict(geom=name,half_size_m=list(size),mesh=meshes[size]))
    if not converted:raise ValueError('No support boxes found for '+prefix)
    return converted
