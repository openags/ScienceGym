"""Measure support load on designated surfaces, rather than sum all normals."""
import numpy as np
import mujoco


def support_load(model,data,body,support,allowed_prefixes=None):
    bid=model.body(body).id;sid=model.body(support).id
    vector=np.zeros(3);points=[];geoms=set()
    for i,c in enumerate(data.contact):
        if min(c.geom)<0:continue
        a,b=[int(model.geom_bodyid[g]) for g in c.geom]
        if {a,b}!={bid,sid}:continue
        support_geom=int(c.geom1 if a==sid else c.geom2)
        name=model.geom(support_geom).name
        if allowed_prefixes and not any(name.startswith(p) for p in allowed_prefixes):continue
        f=np.zeros(6);mujoco.mj_contactForce(model,data,i,f)
        on_body=(c.frame.reshape(3,3).T@f[:3])*(1 if b==bid else -1)
        vector+=on_body
        if on_body[2]>.0001:
            points.append(c.pos[:2].tolist());geoms.add(name)
    return dict(vertical_force_n=float(vector[2]),force_world_n=vector.tolist(),
                loaded_support_geoms=sorted(geoms),contact_points_xy_m=points,
                body_weight_n=float(model.body_subtreemass[bid])*9.81)


def designated_surfaces(body,support):
    if support!='assembly_base':return None
    if body=='shield':return ['shield_height_shim_']
    return ['assembly_base_plinth','physical_frame_COOLER_WHITE__lift_plate']
