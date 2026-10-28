"""Observation-gated carrier transport and return-to-source policy.

This is an authored transport subtask, not the evaluator's paper reference plan.
Transitions that assert object outcomes require fresh depth observations.
"""
import numpy as np

class FeedbackPolicy:
    def __init__(self,begin,return_to_source=False,grip_force=15,grip_height=.93):
        self.begin={s:p.copy() for s,p in begin.items()};self.return_to_source=return_to_source;self.grip_force=grip_force
        self.grip_height=float(grip_height)
        self.state='locate';self.started=0.;self.phase=0;self.events=[];self.observations=[];self.recent=[];self.target=None;self.source=None
        self.current={s:p.copy() for s,p in begin.items()};self.current_force=0.;self.start_goals=None;self.goal=None;self.start_force=0.;self.force_goal=0.;self.duration=0.;self.streak=0;self.failure=None;self.complete=False;self.last_seen=-1.
    def enter(self,state,now,goals=None,duration=0.,force=None,evidence=None):
        self.state=state;self.started=now;self.duration=duration;self.start_goals={s:p.copy() for s,p in self.current.items()};self.goal=self.start_goals if goals is None else goals
        self.start_force=self.current_force;self.force_goal=self.current_force if force is None else force;self.streak=0
        self.events.append(dict(state=state,time_s=float(now),phase=self.phase,evidence=evidence));return state
    def pose(self,x,y,z,half_width):return {s:np.array([x,y+(1 if s=='left' else -1)*half_width,z]) for s in self.begin}
    def start_route(self,now):
        self.x=self.target[0]-.02;self.y=self.target[1]
        self.dx,self.dy=(-.025,.06) if self.phase==0 else (self.source[0]-self.target[0],self.source[1]-self.target[1])
        self.enter('raise',now,{s:np.array([self.begin[s][0],self.y+(1 if s=='left' else -1)*.20,1.04]) for s in self.begin},3,force=0)
    def update(self,now,observation,fresh_depth):
        if fresh_depth:
            if observation:
                self.last_seen=now;self.recent.append(observation);self.recent=self.recent[-20:]
                if self.state=='locate':self.observations.append(observation)
            if self.state=='confirm_lift':
                ok=observation and observation['high_m'][2]>self.baseline_high+.06 and observation['low_m'][2]>.935
                self.streak=self.streak+1 if ok else 0
            elif self.state=='confirm_transfer':
                ok=observation and abs(observation['center_m'][1]-(self.y+self.dy))<.025 and observation['high_m'][2]>self.baseline_high+.05
                self.streak=self.streak+1 if ok else 0
            elif self.state in ['confirm_place','verify_release','inspect']:
                ok=observation and abs(observation['high_m'][2]-self.baseline_high)<.022 and abs(observation['center_m'][1]-(self.y+self.dy))<.025
                self.streak=self.streak+1 if ok else 0
        elapsed=now-self.started
        if self.state=='locate':
            if now>=2:
                if len(self.observations)<8:raise RuntimeError('No reliable depth localization before approach')
                self.target=np.median([x['center_m'] for x in self.observations],axis=0);self.source=self.target.copy();self.baseline_high=float(np.median([x['high_m'][2] for x in self.observations]));self.start_route(now)
            return None,None
        if self.state=='complete':return self.current,{s:[0,0,0] for s in self.begin}
        a=np.clip(elapsed/max(self.duration,.001),0,1);a=a*a*(3-2*a)
        self.current={s:self.start_goals[s]+a*(self.goal[s]-self.start_goals[s]) for s in self.begin};self.current_force=self.start_force+a*(self.force_goal-self.start_force)
        if elapsed>=self.duration:
            if self.state=='raise':self.enter('approach',now,self.pose(self.x,self.y,1.04,.20),3)
            elif self.state=='approach':self.enter('lower_to_grip',now,self.pose(self.x,self.y,self.grip_height,.20),3)
            elif self.state=='lower_to_grip':self.enter('close',now,self.pose(self.x,self.y,self.grip_height,.148),2,force=self.grip_force)
            elif self.state=='close':self.enter('settle_grip',now,duration=2)
            elif self.state=='settle_grip':self.enter('lift',now,self.pose(self.x,self.y,1.11,.148),4)
            elif self.state=='lift':self.enter('confirm_lift',now,duration=.5)
            elif self.state=='confirm_lift' and self.streak>=4:
                self.enter('transfer',now,self.pose(self.x+self.dx,self.y+self.dy,1.11,.148),4,evidence=observation or self.recent[-1])
            elif self.state=='transfer':self.enter('confirm_transfer',now,duration=.5)
            elif self.state=='confirm_transfer' and self.streak>=4:
                self.enter('place',now,self.pose(self.x+self.dx,self.y+self.dy,self.grip_height,.148),4,evidence=observation or self.recent[-1])
            elif self.state=='place':self.enter('confirm_place',now,duration=.5)
            elif self.state=='confirm_place' and self.streak>=4:
                self.enter('release',now,self.pose(self.x+self.dx,self.y+self.dy,self.grip_height,.203),3,force=0,evidence=observation or self.recent[-1])
            elif self.state=='release':self.enter('verify_release',now,duration=.7)
            elif self.state=='verify_release' and self.streak>=6:
                self.enter('retract',now,{s:np.array([self.begin[s][0]-.025,self.y+self.dy+(1 if s=='left' else -1)*.203,1.04]) for s in self.begin},3,evidence=observation or self.recent[-1])
            elif self.state=='retract':self.enter('inspect',now,duration=2)
            elif self.state=='inspect' and self.streak>=10:
                centers=np.array([x['center_m'] for x in self.recent[-10:]])
                if np.max(np.ptp(centers,axis=0))<.012:
                    if self.return_to_source and self.phase==0:
                        self.phase=1;self.target=np.median(centers,axis=0);self.start_route(now)
                    else:self.complete=True;self.enter('complete',now,evidence=self.recent[-1])
            if self.state in ['confirm_lift','confirm_transfer','confirm_place','verify_release','inspect'] and elapsed>self.duration+5:
                self.failure='Depth outcome gate timed out in '+self.state;raise RuntimeError(self.failure)
        forces={s:[0,(-1 if s=='left' else 1)*self.current_force,0] for s in self.begin}
        return self.current,forces
