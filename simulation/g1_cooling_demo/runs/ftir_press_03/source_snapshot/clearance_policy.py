"""Withdraw behind the worktop before raising and rotating the hands."""
import numpy as np
from policy import FeedbackPolicy


class ClearanceTransportPolicy(FeedbackPolicy):
    def __init__(self,*args,rotation_callback=None,**kwargs):
        super().__init__(*args,**kwargs);self.rotation_callback=rotation_callback

    def start_route(self,now):
        self.x=self.target[0]-.02;self.y=self.target[1]
        self.dx,self.dy=(-.025,.06) if self.phase==0 else (self.source[0]-self.target[0],self.source[1]-self.target[1])
        goals={s:p.copy() for s,p in self.current.items()}
        for side in goals:goals[side][0]=min(self.begin[side][0]-.08,goals[side][0])
        self.safe_x={s:p[0] for s,p in goals.items()}
        self.enter('withdraw_to_clearance',now,goals,2.,force=0.)

    def update(self,now,observation,fresh_depth):
        response=super().update(now,observation,fresh_depth)
        if self.state=='withdraw_to_clearance' and now-self.started>=self.duration:
            goals={s:np.array([self.safe_x[s],self.y+(1 if s=='left' else -1)*.20,1.04]) for s in self.begin}
            self.enter('raise',now,goals,3.,force=0.)
        if self.rotation_callback:
            weight=1.
            if self.phase==0:
                if self.state in ['locate','withdraw_to_clearance']:weight=0.
                elif self.state=='raise':
                    u=float(np.clip((now-self.started)/self.duration,0.,1.));weight=u*u*(3-2*u)
            self.rotation_callback(weight)
        return response
