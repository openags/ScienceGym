"""Reject intersecting payloads before the first dynamics step."""
import numpy as np
import mujoco
from world import HOME
from load_model import load
from control import ExecutionFailure


def inspect(path, payload_supports):
    model=load(path);data=mujoco.MjData(model)
    data.qpos[:7]=HOME;data.qpos[7:9]=.04
    mujoco.mj_forward(model,data)
    violations=[]
    for c in data.contact:
        if min(c.geom)<0:continue
        a,b=[model.body(int(model.geom_bodyid[g])).name for g in c.geom]
        if not ({a,b}&set(payload_supports)):continue
        intended=(a in payload_supports and payload_supports[a]==b) or (b in payload_supports and payload_supports[b]==a)
        # Tiny numerical contact margins are allowed; a payload may not start
        # intersecting the apparatus, another payload, or its own support.
        limit=-.00005 if intended else -.00001
        if c.dist<limit:
            violations.append(dict(bodies=[a,b],geoms=[model.geom(int(g)).name for g in c.geom],distance_m=float(c.dist)))
    report=dict(passed=not violations,violations=violations,
                expected_supports=payload_supports,maximum_intended_overlap_m=.00005)
    if violations:raise ExecutionFailure('Invalid initial payload intersections: '+str(violations[:8]))
    return report
