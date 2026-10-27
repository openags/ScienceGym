"""Pose-gated tray handling with explicit hand closure and tilt recovery.

The 8/10-degree operating/recovery limits and grip offsets are development
choices. They are not source measurements or qualified reliability bounds.
"""
import numpy as np
from policy import FeedbackPolicy


class PoseTransportPolicy(FeedbackPolicy):
    def __init__(self,begin,hand_callback,carried_mass=0.):
        super().__init__(begin,return_to_source=True,grip_force=15)
        self.hand_callback=hand_callback;self.curl=1.05;self.rotation=0.;self.unsafe=0;self.abort_reason=None
        self.start_curl=0.;self.goal_curl=0.;self.start_rotation=0.;self.goal_rotation=0.
        self.carried_mass=float(carried_mass);self.supported_mass=0.;self.target_mass=0.;self.previous_update=None

    def stage(self,name,now,goals=None,duration=0.,force=None,curl=None,rotation=None,evidence=None):
        self.enter(name,now,goals,duration,force,evidence)
        self.start_curl=self.curl;self.goal_curl=self.curl if curl is None else curl
        self.start_rotation=self.rotation;self.goal_rotation=self.rotation if rotation is None else rotation

    def start_route(self,now):
        self.x=self.target[0]+.035;self.y=self.target[1];self.grip_z=self.target[2]+.07;self.carry_z=self.grip_z+.12
        self.dx,self.dy=(-.025,.06) if self.phase==0 else (self.source[0]-self.target[0],self.source[1]-self.target[1])
        self.stage('prepare_fingers',now,duration=2.,force=0.,curl=1.05)

    def update(self,now,observation,fresh_depth):
        active={'lift','confirm_lift','transfer','confirm_transfer','place','confirm_place'}
        if fresh_depth:
            if observation:
                self.last_seen=now;self.recent.append(observation);self.recent=self.recent[-20:]
                if self.state=='locate' and observation['tilt_deg']<3:self.observations.append(observation)
                if self.source is not None and self.state in active|{'recover_lower'}:
                    self.target_mass=self.carried_mass if observation['low_m'][2]>self.source[2]+.005 else 0.
            if self.state in active and self.abort_reason is None:
                self.unsafe=self.unsafe+1 if observation and observation['tilt_deg']>10 else 0
                if self.unsafe>=2 or now-self.last_seen>1.5:
                    self.abort_reason='Excessive observed tray tilt' if self.unsafe>=2 else 'Tray pose observation lost'
                    goals={s:p.copy() for s,p in self.current.items()}
                    for p in goals.values():p[2]=self.grip_z
                    self.stage('recover_lower',now,goals,4.,evidence=observation)
            expected=np.array([self.target[0]+self.dx,self.target[1]+self.dy]) if self.target is not None else None
            ok=False
            if observation and self.target is not None:
                level=observation['tilt_deg']<8
                positioned=np.linalg.norm(np.array(observation['position_m'][:2])-expected)<.018
                supported=abs(observation['position_m'][2]-self.source[2])<.012
                if self.state=='confirm_lift':ok=level and observation['low_m'][2]>self.source[2]+.07
                elif self.state=='confirm_transfer':ok=level and positioned and observation['low_m'][2]>self.source[2]+.07
                elif self.state in {'confirm_place','verify_release','inspect'}:ok=level and positioned and supported
            self.streak=self.streak+1 if ok else 0
        if self.state not in active|{'recover_lower'}:self.target_mass=0.
        dt=.01 if self.previous_update is None else now-self.previous_update;self.previous_update=now
        self.supported_mass+=float(np.clip(self.target_mass-self.supported_mass,-self.carried_mass*dt/.25,self.carried_mass*dt/.25))
        if self.state=='locate':
            if now>=2:
                if len(self.observations)<8:raise RuntimeError('No reliable level-tray pose before approach')
                self.target=np.median([o['position_m'] for o in self.observations],axis=0);self.source=self.target.copy();self.start_route(now)
            self.hand_callback(self.curl,self.rotation);return None,None
        if self.state=='complete':return self.current,{s:[0,0,0] for s in self.begin}
        elapsed=now-self.started;a=float(np.clip(elapsed/max(self.duration,.001),0,1));a=a*a*(3-2*a)
        self.current={s:self.start_goals[s]+a*(self.goal[s]-self.start_goals[s]) for s in self.begin}
        self.current_force=self.start_force+a*(self.force_goal-self.start_force)
        self.curl=self.start_curl+a*(self.goal_curl-self.start_curl);self.rotation=self.start_rotation+a*(self.goal_rotation-self.start_rotation)
        self.hand_callback(self.curl,self.rotation)
        if elapsed>=self.duration:
            if self.state=='prepare_fingers':self.stage('withdraw_closed_hands',now,{s:np.array([.30,self.y+(1 if s=='left' else -1)*.27,self.current[s][2]]) for s in self.begin},2.,rotation=1. if self.phase else 0.)
            elif self.state=='withdraw_closed_hands':self.stage('raise',now,self.pose(.30,self.y,1.06,.27),3.,rotation=1.)
            elif self.state=='raise':self.stage('orient_above_worktop',now,self.pose(.40,self.y,1.06,.24),2.,rotation=2.)
            elif self.state=='orient_above_worktop':self.stage('open_above_worktop',now,duration=2.,curl=0.)
            elif self.state=='open_above_worktop':self.stage('approach',now,self.pose(self.x,self.y,1.06,.21),3.)
            elif self.state=='approach':self.stage('lower_to_grip',now,self.pose(self.x,self.y,self.grip_z,.21),3.)
            elif self.state=='lower_to_grip':self.stage('close',now,self.pose(self.x,self.y,self.grip_z,.148),3.,force=15.,curl=.45)
            elif self.state=='close':self.stage('settle_grip',now,duration=2.)
            elif self.state=='settle_grip':self.stage('lift',now,self.pose(self.x,self.y,self.carry_z,.148),4.)
            elif self.state=='lift':self.stage('confirm_lift',now,duration=.5)
            elif self.state=='confirm_lift' and self.streak>=4:self.stage('transfer',now,self.pose(self.x+self.dx,self.y+self.dy,self.carry_z,.148),4.,evidence=observation or self.recent[-1])
            elif self.state=='transfer':self.stage('confirm_transfer',now,duration=.5)
            elif self.state=='confirm_transfer' and self.streak>=4:self.stage('place',now,self.pose(self.x+self.dx,self.y+self.dy,self.grip_z,.148),4.,evidence=observation or self.recent[-1])
            elif self.state=='place':self.stage('confirm_place',now,duration=.5)
            elif self.state=='confirm_place' and self.streak>=4:self.stage('release',now,self.pose(self.x+self.dx,self.y+self.dy,self.grip_z,.21),3.,force=0.,curl=0.,evidence=observation or self.recent[-1])
            elif self.state=='release':self.stage('verify_release',now,duration=.7)
            elif self.state=='verify_release' and self.streak>=6:self.stage('retract',now,{s:np.array([self.begin[s][0],self.y+self.dy+(1 if s=='left' else -1)*.21,1.06]) for s in self.begin},3.,evidence=observation or self.recent[-1])
            elif self.state=='retract':self.stage('inspect',now,duration=2.)
            elif self.state=='inspect' and self.streak>=10:
                centers=np.array([x['position_m'] for x in self.recent[-10:]])
                if np.max(np.ptp(centers,axis=0))<.012:
                    if self.phase==0:self.phase=1;self.target=np.median(centers,axis=0);self.start_route(now)
                    else:self.complete=True;self.stage('complete',now,evidence=self.recent[-1])
            elif self.state=='recover_lower':
                goals={s:p.copy() for s,p in self.current.items()}
                for s,p in goals.items():p[1]+= .07 if s=='left' else -.07
                self.stage('recover_open',now,goals,3.,force=0.,curl=0.)
            elif self.state=='recover_open':self.stage('recover_retract',now,{s:np.array([self.begin[s][0],self.y+(1 if s=='left' else -1)*.22,1.06]) for s in self.begin},3.)
            elif self.state=='recover_retract':raise RuntimeError(self.abort_reason+'; controlled release/retraction attempted')
            if self.state in {'confirm_lift','confirm_transfer','confirm_place','verify_release','inspect'} and elapsed>self.duration+5:
                raise RuntimeError('Pose outcome gate timed out in '+self.state)
        return self.current,{s:[0,(-1 if s=='left' else 1)*self.current_force,0] for s in self.begin}
