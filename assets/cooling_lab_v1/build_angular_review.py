"""Pin author comparison findings to the actual tested accessory views."""
import json
from pathlib import Path
from geometry_tools import HERE,ROOT,sha,write_json


def build():
    files=[HERE/'angular_accessories.json',HERE/'angular_accessory_sources.json',HERE/'angular_accessory_checks.json',HERE/'scene.json',
        ROOT/'viewer/lab_review_v1/VISUAL_VERIFICATION.json',Path(__file__)]
    model,sources,checks,scene,visual=[json.loads(p.read_text()) for p in files[:-1]]
    assert checks['passed'] and checks['model_sha256']==sha(files[0]) and visual['passed']
    for ref in visual['source_files']:assert sha(ROOT/ref['path'])==ref['sha256'],ref['path']
    captures={Path(c['path']).stem:c for c in visual['captures']}
    findings={
      'harrick_hrs':dict(source_ids=['HARRICK_CURRENT_DATASHEET','HARRICK_HRS_PHOTO','HARRICK_LEGACY_CATALOGUE'],
        source_constrained_features=['Open horizontal HRS bracket with a real upper aperture and a solid inclined mirror',
            'Separate FTIR base, two rear circular and two front rectangular external mirrors',
            'Three interchangeable circular masks with documented 3/6/13 mm apertures'],
        author_observations=['Raised-stage view exposes the bracket, solid mirror, receiver and loose masks',
            'Rear support posts do not intersect the reflective surfaces; rigid separation sweep is checked'],
        unresolved_differences=['The combined HRS/base assembly has no matched manufacturer photograph; the base is reconstructed from a legacy diagram',
            'Envelope, mirror curvature and positions, sockets, fasteners and counterbore dimensions are inferred',
            'No installed specimen, mounting adapter, removal force or calibrated 12-degree optical path is accepted']),
      'spectratech_500':dict(source_ids=['SPECTRATECH_CATALOGUE','NICOLET_OPTICAL_LAYOUT'],
        source_constrained_features=['Black chassis, separate source-side housing and its real circular port',
            'Rotary specimen assembly and 20–85 degree dial; 6/13 mm U-slot masks and alignment-mirror candidate',
            'M1/M2/M3/M5 independent mirrors, with M4 occupied by the removable specimen/reference, and the documented right-to-left beam direction'],
        author_observations=['M3 and the M4 reference/sample holder share the selected rotor; both physical face normals change with rotation',
            'The initial M1/M2/M3/M4-reference/M5 ray is checked against actual meshes; an alternative mask fits with the reference removed',
            'Finite-aperture ray checks retain misses at other angles; the 20–85 degree label and infinite-plane normals cannot qualify optical coverage'],
        unresolved_differences=['Sample-frame shape, dial datum, mirror positions, support posts and housing depth remain authored hypotheses, not exact model-500 CAD',
            'The catalogue photograph has an unreported angle and perspective; these are comparison views, not a calibrated image registration',
            'The selected common-rotor mechanism and pivot remain hypotheses; no claim of manufacturer optical prescription, spring forces, historical paper SKU or Nicolet adapter compatibility'])}
    items=[]
    for a in model['items']:
        key=a['id'];instance=next(i for i in scene['assets'] if i['id']==key);note=findings[key]
        assert sha(ROOT/a['geometry']['path'])==a['geometry']['sha256']
        assert sha(ROOT/instance['geometry'])==instance['geometry_sha256']
        views=[]
        for direction in ['closed','front','back','side','top','front_rest','open']:
            capture=captures[key+'_'+direction];assert sha(ROOT/capture['path'])==capture['sha256']
            views.append(dict(view=direction,**capture))
        items.append(dict(asset_id=key,geometry=a['geometry'],scene_geometry=dict(path=instance['geometry'],sha256=instance['geometry_sha256']),
            sources=[s for s in sources['sources'] if s['id'] in note['source_ids']],findings=note,model_views=views,
            owner_acceptance=False,independent_fidelity_acceptance=False,manipulation_qualified=False))
    write_json(HERE/'angular_appearance_review.json',dict(schema_version=1,
        scope='Author comparison of source-constrained structure and actual browser views. Not independent fidelity, mounting or execution acceptance.',
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in files],items=items,reference_media_redistributed=False))
    print(json.dumps(dict(accessories=len(items),pinned_model_views=sum(len(i['model_views']) for i in items),owner_acceptance=False)))


if __name__=='__main__':build()
