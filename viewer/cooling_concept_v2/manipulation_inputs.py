"""Resolve frozen approach endpoints and explicit continuous-contact revisions."""
import hashlib,json
from pathlib import Path
import numpy as np
from source_geometry import fk
HERE=Path(__file__).resolve().parent


def load_inputs():
    packet=json.loads((HERE/'previews/manipulation_approach_inputs.json').read_text())
    file=HERE/'lid_contact_paths.json'
    if not file.exists():return packet
    contact=json.loads(file.read_text())
    if not contact.get('selected_continuous'):return packet
    revision=hashlib.sha256(file.read_bytes()).hexdigest()
    for name,values in contact['endpoint_updates'].items():
        source=packet['frames'][name];frame=source['target'];frame['joints'].update(values)
        base=np.array(frame['groups']['g1']).reshape(4,4).T
        frame['links']={n:(base@matrix).T.reshape(-1).tolist() for n,matrix in fk(frame['joints']).items()}
        source['target_revision']=dict(basis='Continuous cover-contact branch endpoint',path='lid_contact_paths.json',sha256=revision)
    return packet
