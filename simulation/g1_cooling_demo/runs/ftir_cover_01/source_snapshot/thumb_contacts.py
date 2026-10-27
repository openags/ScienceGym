"""Bind source-derived concave thumb collision pieces without changing visuals."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
ROBOT=ROOT/'assets/unitree_g1_inspire_v1'
MANIFEST=ROBOT/'collision_refinements/thumb_2_v1/manifest.json'


def attach(xml,out):
    manifest=json.loads(MANIFEST.read_text())
    for item in manifest['items']:
        source=ROBOT/item['source_path']
        if hashlib.sha256(source.read_bytes()).hexdigest()!=item['source_sha256']:
            raise ValueError('Source thumb mesh changed: '+item['link'])
        body=xml.find(f".//body[@name='{item['link']}']")
        old=body.find(f"geom[@name='{item['link']}_collision_0']")
        attrs=dict(old.attrib);body.remove(old)
        for i,piece in enumerate(item['pieces']):
            path=ROBOT/piece['path']
            if hashlib.sha256(path.read_bytes()).hexdigest()!=piece['sha256']:
                raise ValueError('Thumb collision piece changed: '+str(path))
            name=item['link']+'_collision_refined_'+str(i)
            ET.SubElement(xml.find('asset'),'mesh',name=name,file=str(path.relative_to(ROBOT)))
            ET.SubElement(body,'geom',**{**attrs,'name':name,'mesh':name})
    (Path(out)/'thumb_contact_profile.json').write_text(json.dumps(dict(
        manifest=str(MANIFEST.relative_to(ROOT)),manifest_sha256=hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        source_visuals_changed=False,collision_filters_changed=False,
        scope=manifest['scope']),indent=2)+'\n')
