"""Attach source-derived distal finger cells without changing the visible hand."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
ROBOT=ROOT/'assets/unitree_g1_inspire_v1'
MANIFEST=ROBOT/'collision_refinements/distal_v1/manifest.json'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def attach(xml,out):
    manifest=json.loads(MANIFEST.read_text())
    for row in manifest['items']:
        if sha(ROBOT/row['source_path'])!=row['source_sha256']:raise ValueError('Source distal finger mesh changed')
        body=xml.find(f".//body[@name='{row['link']}']")
        old=body.find(f"geom[@name='{row['link']}_collision_0']");attrs=dict(old.attrib);body.remove(old)
        for i,piece in enumerate(row['pieces']):
            if sha(ROBOT/piece['path'])!=piece['sha256']:raise ValueError('Distal finger cell changed')
            name=row['link']+'_collision_cell_'+str(i)
            # Thin conforming cells can fall below the compiler's volume
            # inertia threshold. Each robot body already has explicit source
            # inertia; shell mesh centering leaves that body inertia intact.
            ET.SubElement(xml.find('asset'),'mesh',name=name,file=piece['path'],inertia='shell')
            ET.SubElement(body,'geom',**{**attrs,'name':name,'mesh':name})
    (Path(out)/'distal_contact_profile.json').write_text(json.dumps(dict(manifest=str(MANIFEST.relative_to(ROOT)),manifest_sha256=sha(MANIFEST),
        source_visuals_changed=False,collision_filters_changed=False,mesh_inertia_mode='shell',
        body_inertia_source='Unchanged explicit source body inertials',scope=manifest['scope']),indent=2)+'\n')
