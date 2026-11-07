"""Source-kinematics IK for simultaneous left-reference/right-tool targets."""
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from optical_choreography import JOINTS, canonical
from source_geometry import KIN


PARENTS = {j['id']:j for j in KIN['joints']}
CHAINS = {}
for side in ['left', 'right']:
    chain = []
    link = side+'_palm_force_sensor'
    while link != KIN['root_link']:
        joint = PARENTS[link]
        chain.insert(0, joint)
        link = joint['parent']
    CHAINS[side] = chain


def palm_fk(q, side):
    pose = np.array(KIN['root_matrix'])
    for joint in CHAINS[side]:
        local = np.array(joint['origin_matrix'])
        value = q.get(joint['name'], 0.)
        if value:
            turn = np.eye(4)
            turn[:3, :3] = Rotation.from_rotvec(np.array(joint['axis'])*value).as_matrix()
            local = local @ turn
        pose = pose @ local
    return pose


def solve(base, targets, seed, max_nfev=180, cross_body=False):
    names = [n for n in JOINTS if any(n.startswith(side+'_') for side in targets)
             and any(k in n for k in ['shoulder', 'elbow', 'wrist'])]
    names += ['waist_pitch_joint', 'waist_yaw_joint']
    bounds = np.array([[JOINTS[n]['limits']['lower'], JOINTS[n]['limits']['upper']] for n in names])
    if 'left' in targets and not cross_body:
        bounds[names.index('left_shoulder_roll_joint'), 0] = .025
    if 'right' in targets and not cross_body:
        bounds[names.index('right_shoulder_roll_joint'), 1] = -.025
    bounds[-2] = [0, .4]
    bounds[-1] = [-.6, .6]
    q = canonical(seed)
    initial = np.clip([q[n] for n in names], bounds[:, 0]+1e-9, bounds[:, 1]-1e-9)
    def error(values):
        updated = {**q, **dict(zip(names, values))}
        rows = []
        for side, target in targets.items():
            actual = base @ palm_fk(updated, side)
            rows.extend((actual[:3, 3]-target[:3, 3])*10)
            rows.extend(Rotation.from_matrix(target[:3, :3].T @ actual[:3, :3]).as_rotvec())
        return np.array(rows)
    result = least_squares(lambda v:np.r_[error(v), (v-initial)*1e-7], initial,
        bounds=(bounds[:, 0], bounds[:, 1]), max_nfev=max_nfev,
        ftol=1e-12, xtol=1e-12, gtol=1e-12)
    q.update(dict(zip(names, map(float, result.x))))
    residual = error(result.x).reshape(-1, 6)
    return q, {side:dict(position_m=float(np.linalg.norm(row[:3])/10),
                        angle_rad=float(np.linalg.norm(row[3:])))
               for side, row in zip(targets, residual)}
