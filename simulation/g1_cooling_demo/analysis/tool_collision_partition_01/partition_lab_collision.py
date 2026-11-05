"""Partition static architecture bodies without changing any geometry.

The laboratory import groups thousands of geoms into one body. Smaller static
bodies allow broad-phase rejection before narrow collision tests against each
distal hand cell. Meshes, poses, materials, contact parameters and weld groups
must remain identical in a compiled correspondence check.
"""
from copy import deepcopy
import xml.etree.ElementTree as ET


def partition(xml):
    body = xml.find(".//body[@name='lab_architecture']")
    if body is None: raise ValueError('Original laboratory architecture body missing')
    geoms = list(body.findall('geom'))
    if not geoms: raise ValueError('Architecture has already been partitioned')
    rows = []
    for geom in geoms:
        name = geom.get('name')
        if not name: raise ValueError('Architecture geometry requires stable names')
        child = ET.SubElement(body, 'body', name='architecture_partition_'+name)
        body.remove(geom); child.append(deepcopy(geom))
        rows.append(dict(geom=name, original_body='lab_architecture', body=child.get('name')))
    return rows
