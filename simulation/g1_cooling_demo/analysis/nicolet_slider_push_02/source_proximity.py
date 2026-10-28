"""Exact source-mesh proximity after conservative transformed-box culling.

This avoids computing the global distance between every robot and instrument
mesh when the planner only needs a fixed clearance threshold. Unchanged rigid
assembly pairs are checked separately, not repeatedly for each arm sample.
"""
import itertools

import fcl
import mujoco
import numpy as np


def corners(mesh):
    lo,hi=mesh.bounds
    return np.array([[hi[i] if bit[i] else lo[i] for i in range(3)]
                     for bit in itertools.product([0,1],repeat=3)])


def transform(obj):
    T=np.eye(4);T[:3,:3]=obj.getRotation();T[:3,3]=obj.getTranslation();return T


class SourceClearance:
    def __init__(self,model,data,robot,body_meshes,env,env_meshes,active_joints,adjacent):
        self.model,self.data,self.robot,self.env=model,data,robot,env
        self.names=list(body_meshes);self.environment_names=list(env_meshes)
        self.bids=np.array([model.body(n).id for n in self.names])
        self.rcorners=np.stack([corners(body_meshes[n]) for n in self.names])
        self.ecorners=np.stack([corners(env_meshes[n]) for n in self.environment_names])
        self.r_objs=[robot._objs[n]['obj'] for n in self.names]
        self.e_objs=[env._objs[n]['obj'] for n in self.environment_names]
        active_bodies={int(model.jnt_bodyid[j]) for j in active_joints}
        groups=[]
        for bid in self.bids:
            current=int(bid)
            while current and current not in active_bodies:current=int(model.body_parentid[current])
            groups.append(current)
        self.groups=np.array(groups)
        self.eligible=np.triu(self.groups[:,None]!=self.groups[None,:],1)
        for i,a in enumerate(self.names):
            for j,b in enumerate(self.names):
                if tuple(sorted([a,b])) in adjacent:self.eligible[i,j]=False
        self.fixed=np.ones(model.nq,dtype=bool)
        self.fixed[model.jnt_qposadr[list(active_joints)]]=False
        self.fixed_state=data.qpos[self.fixed].copy()
        self.update_environment()
        self.queries=0;self.exact_self_queries=0;self.exact_environment_queries=0

    def update_environment(self):
        T=np.stack([transform(o) for o in self.e_objs])
        points=np.einsum('nij,nkj->nki',T[:,:3,:3],self.ecorners)+T[:,None,:3,3]
        self.elo,self.ehi=points.min(1),points.max(1)

    def check(self,margin=.002):
        if np.max(abs(self.data.qpos[self.fixed]-self.fixed_state),initial=0.)>1e-10:
            raise ValueError('An unplanned joint changed a supposedly fixed assembly')
        self.queries+=1
        rotations=self.data.xmat[self.bids].reshape(-1,3,3)
        positions=self.data.xpos[self.bids]
        points=np.einsum('nij,nkj->nki',rotations,self.rcorners)+positions[:,None,:]
        lo,hi=points.min(1),points.max(1)
        # Conservative AABBs: every true triangle intersection must overlap
        # these boxes, including at rounded edges and arbitrary orientations.
        overlap=np.all(hi[:,None,:]>=lo[None,:,:],axis=2)&np.all(hi[None,:,:]>=lo[:,None,:],axis=2)
        updated=set()
        def update(i):
            if i not in updated:
                T=np.eye(4);T[:3,:3]=rotations[i];T[:3,3]=positions[i]
                self.robot.set_transform(self.names[i],T);updated.add(i)
        for i,j in zip(*np.where(overlap&self.eligible)):
            update(i);update(j);self.exact_self_queries+=1
            result=fcl.CollisionResult()
            fcl.collide(self.r_objs[i],self.r_objs[j],fcl.CollisionRequest(),result)
            if result.is_collision:
                return dict(clear=False,kind='self_contact',parts=[self.names[i],self.names[j]])
        separation=np.maximum(np.maximum(self.elo[None,:,:]-hi[:,None,:],lo[:,None,:]-self.ehi[None,:,:]),0.)
        near=np.sum(separation*separation,axis=2)<=(margin+1e-10)**2
        for i,j in zip(*np.where(near)):
            update(i);self.exact_environment_queries+=1
            result=fcl.DistanceResult()
            distance=float(fcl.distance(self.r_objs[i],self.e_objs[j],fcl.DistanceRequest(),result))
            if distance<margin:
                return dict(clear=False,kind='instrument_clearance',parts=[self.names[i],self.environment_names[j]],distance_m=distance)
        return dict(clear=True)

    def metrics(self):
        return dict(queries=self.queries,exact_self_queries=self.exact_self_queries,
                    exact_environment_queries=self.exact_environment_queries)
