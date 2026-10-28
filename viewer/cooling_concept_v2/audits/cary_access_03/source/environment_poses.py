"""Apply final exported obstacle poses, skipping unchanged FCL transforms.

Explicit articulated poses take precedence over group-times-source defaults.
Verification reconstructs every expected matrix independently of the cache.
"""
import numpy as np


def matrix(values):return np.array(values).reshape(4,4).T


class EnvironmentPoses:
    def __init__(self,manager,instances,defaults):
        self.manager=manager;self.instances=instances;self.defaults=defaults;self.cache={};self.maximum_verification_error=0.;self.verification_count=0

    def expected(self,frame):
        for name in self.instances:yield name,'raw',frame['groups'][name],None
        explicit={p['asset']+'::'+p['name']:p['matrix'] for p in frame['parts']}
        for name,(identity,rest) in self.defaults.items():
            if name in explicit:yield name,'raw',explicit[name],None
            else:yield name,'group',frame['groups'][identity],rest
        for identity,pose in frame.get('extra_matrices',{}).items():
            name='extra::'+identity
            if name in self.manager._objs:yield name,'raw',pose,None

    def update(self,frame):
        for name,kind,values,rest in self.expected(frame):
            token=(kind,values)
            if self.cache.get(name)==token:continue
            pose=matrix(values)
            if rest is not None:pose=pose@rest
            self.manager.set_transform(name,pose);self.cache[name]=token

    def verify(self,frame):
        for name,kind,values,rest in self.expected(frame):
            expected=matrix(values)
            if rest is not None:expected=expected@rest
            obj=self.manager._objs[name]['obj'];actual=np.eye(4);actual[:3,:3]=obj.getRotation();actual[:3,3]=obj.getTranslation()
            error=float(np.max(abs(actual-expected)));self.maximum_verification_error=max(error,self.maximum_verification_error)
            assert error<1e-10,(name,error)
        self.verification_count+=1
