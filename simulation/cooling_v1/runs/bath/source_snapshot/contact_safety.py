"""Reject loaded unintended arm contacts even with tiny soft-contact overlap."""
import numpy as np
import mujoco
from control import ExecutionFailure


def audit(robot,owner=None):
    m=robot.model;d=robot.data
    arm={'link1','link2','link3','link4','link5','link6','link7','hand'}
    if any(w.number for w in d.warning):raise ExecutionFailure('MuJoCo physics warning')
    def body(c,side):
        if owner:return owner(c,side)
        g=int(c.geom[side])
        return m.body(int(m.geom_bodyid[g])).name if g>=0 else 'deformable'
    for i,c in enumerate(d.contact):
        a,b=body(c,0),body(c,1)
        if a not in arm and b not in arm:continue
        if a in {'link0','left_finger','right_finger'} or b in {'link0','left_finger','right_finger'}:
            # Connected hand/finger and base/link1 geometry is intentional;
            # fingers touching another arm segment is not exempted.
            other=b if a in {'link0','left_finger','right_finger'} else a
            if other=='hand' or (other=='link1' and 'link0' in [a,b]):continue
        if a in arm and b in arm:
            ai,bi=m.body(a).id,m.body(b).id
            if m.body_parentid[ai]==bi or m.body_parentid[bi]==ai:continue
        f=np.zeros(6);mujoco.mj_contactForce(m,d,i,f)
        robot.peak_unintended_force=max(robot.peak_unintended_force,float(f[0]))
        if f[0]>2:
            raise ExecutionFailure(f'unintended arm contact {a}/{b}: {f[0]:.3f} N, overlap={c.dist:.7f} m')
