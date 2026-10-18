"""Check actual collision apertures and remove the old emitter-carrier shortcut."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import mujoco
from load_model import load
from world import HERE


def inspect(path):
    model=load(path);data=mujoco.MjData(model);mujoco.mj_forward(model,data)
    rows=[]
    collision_groups=np.array([1,1,0,1,1,1],dtype=np.uint8)
    for body,radius in [('pe_tube',.0445),('shield',.073),('aperture',.05)]:
        position=data.body(body).xpos.copy()
        observations=[]
        for offset in [0,radius]:
            hit=np.array([-1],dtype=np.int32)
            distance=mujoco.mj_ray(model,data,position+[offset,0,.2],np.array([0.,0.,-1.]),collision_groups,True,-1,hit)
            geom=model.geom(int(hit[0])) if hit[0]>=0 else None
            hit_body=model.body(int(geom.bodyid[0])).name if geom else None
            observations.append(dict(offset_m=offset,hit_body=hit_body,hit_geom=geom.name if geom else None,distance_m=float(distance)))
        rows.append(dict(case=body+'_open_bore',passed=observations[0]['hit_body']!=body and observations[1]['hit_body']==body,observations=observations))
    emitter=model.body('emitter').id
    children=np.flatnonzero(model.body_parentid==emitter).tolist()
    geometry=[model.geom(i).name for i in range(model.ngeom) if model.geom_bodyid[i]==emitter]
    rows.append(dict(case='emitter_has_no_permanent_lift_carrier',passed=not children and not any('handle' in x or 'carrier' in x for x in geometry),geometries=geometry,child_bodies=children))
    for body,expected in [('foam_lower',.025),('foam_upper',.025),('emitter',.0005)]:
        geom=model.geom(body+'_solid')
        height=float(geom.size[1])*2
        rows.append(dict(case=body+'_source_thickness',passed=abs(height-expected)<1e-10,expected_m=expected,observed_m=height))
    return dict(passed=all(r['passed'] for r in rows),checks=rows,
                input_xml_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                scope='Collision topology and listed dimensions only; not complete apparatus or commercial-asset fidelity qualification',
                whole_paper_validated=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--scene',default='runs/continuous_debug/workcell.xml');args=parser.parse_args()
    result=inspect(HERE/args.scene)
    (HERE/'continuous_geometry_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['passed'] else 1)
