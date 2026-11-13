"""Partition static architecture bodies without changing any geometry.

The laboratory import groups thousands of geoms into one body. Smaller static
bodies allow broad-phase rejection before narrow collision tests against each
distal hand cell. Meshes, poses, materials, contact parameters and weld groups
must remain identical in a compiled correspondence check.
"""
from copy import deepcopy
import xml.etree.ElementTree as ET


def partition(xml, body_names=('lab_architecture',), geometry_groups=None):
    rows = []
    excluded = {node.get(key) for node in xml.findall('contact/exclude') for key in ['body1', 'body2']}
    for body_name in body_names:
        if body_name in excluded: raise ValueError('Explicit body exclusion requires separate preservation: '+body_name)
        body = xml.find(f".//body[@name='{body_name}']")
        if body is None: raise ValueError('Original static body missing: '+body_name)
        geoms = list(body.findall('geom'))
        if not geoms: raise ValueError('Static body has already been partitioned')
        children = {}
        for geom in geoms:
            name = geom.get('name')
            if not name: raise ValueError('Static geometry requires stable names')
            key = name if geometry_groups is None else geometry_groups[name]
            if key not in children:
                children[key] = ET.SubElement(body, 'body', name='static_partition_'+body_name+'_'+str(key))
            child = children[key]
            body.remove(geom); child.append(deepcopy(geom))
            rows.append(dict(geom=name, original_body=body_name, body=child.get('name')))
    return rows
