"""Observe, plan, approach and attempt tool pickup using isolated sensor inputs.

Unposed CAD and hand geometry are priors. Tool placement and obstacles come
from native camera images; encoders and IMU close the robot motion loop.
"""
import argparse
import hashlib
import json
import pickle
from pathlib import Path
import sys

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation
import trimesh

from dex3_tool_actor import ToolActor as PickupActor
from tool_observation import detect
from tool_pose import ToolPose
from tool_approach_planning import ToolApproachPlanner, depth_surface


class ToolActor(PickupActor):
    fields=PickupActor.fields|{'head_rgb','head_depth'}

    def __init__(self,model,prior):
        super().__init__(model,prior)
        self.phase='observe';self.geometry=prior['grasp_geometry']
        shape=Path(prior.get('tool_shape_path','/model/known_objects/tool_shape.glb'))
        if hashlib.sha256(shape.read_bytes()).hexdigest()!=prior['tool_shape_sha256']:
            raise ValueError('Known unposed tool shape changed')
        self.mesh=trimesh.load(shape,force='scene',process=False).to_geometry()
        self.localizer=ToolPose(self.mesh.vertices,self.mesh.faces)
        self.threshold=float(prior['appearance_threshold_uint8'])
        self.poses=[];self.plan=None;self.path=None;self.path_times=None;self.path_clock=0.
        self.planner=None;self.tracking_clear_since=None
        self.next_clearance_check=0.;self.latest_clearance=None
        self.arm_posture_error=0.;self.wrist_path_error=0.;self.wrist_rotation_error=0.
        self.vision_reports=[];self.last_frame_time=None
        self.resolve_pose_ambiguity=bool(prior.get('resolve_tool_pose_ambiguity',False))
        self.hypothesis_history=[]
        self.arm_names=['right_'+n+'_joint' for n in ['shoulder_pitch','shoulder_roll','shoulder_yaw','elbow','wrist_roll','wrist_pitch','wrist_yaw']]
        self.arm_qa=np.array([model.joint(n).qposadr[0] for n in self.arm_names])
        self.arm_indices=np.array([self.names.index(n) for n in self.arm_names])
        self.reference_data=mujoco.MjData(model)
        g=model.geom('lab_part_1514').id
        if model.body(model.geom_bodyid[g]).name!='lab_architecture':raise ValueError('Bench is not part of public map')
        k=model.geom_dataid[g]
        vertices=model.mesh_vert[model.mesh_vertadr[k]:model.mesh_vertadr[k]+model.mesh_vertnum[k]]
        vertices=vertices@self.d.geom_xmat[g].reshape(3,3).T+self.d.geom_xpos[g]
        lo,hi=vertices.min(0),vertices.max(0);lo[2]=hi[2]+.002;hi[2]+=.18
        self.bounds=[lo,hi]
        self.observe_coupon=bool(prior.get('observe_optical_coupon',False))
        self.register_map=bool(prior.get('register_optical_static_map',False))
        if self.register_map and not self.observe_coupon:
            raise ValueError('Fine static-map registration requires the optical observation contract')
        self.map_localizer=None;self.map_registration=None
        self.coupon_poses=[];self.coupon_pose=None;self.coupon_report=None
        if self.observe_coupon:
            from optical_coupon_observation import detect as detect_coupon
            self.coupon_detector=detect_coupon

    def observe_optical_coupon(self,obs,D,C,df,cf):
        report=self.coupon_detector(obs['head_rgb'],obs['head_depth'],D,C,df,cf,self.bounds)
        self.coupon_report=report
        if not report['candidate_found']:
            self.coupon_poses=[];self.coupon_pose=None;return
        self.coupon_poses.append(report['candidate']);self.coupon_poses=self.coupon_poses[-4:]
        if len(self.coupon_poses)<4:return
        centers=np.asarray([p['center_m'] for p in self.coupon_poses])
        normals=np.asarray([p['normal_toward_camera'] for p in self.coupon_poses])
        center=np.median(centers,axis=0);normal=normals.mean(axis=0)
        normal/=max(np.linalg.norm(normal),1e-12)
        if np.max(np.linalg.norm(centers-center,axis=1))>.001 or np.min(normals@normal)<np.cos(.03):
            self.coupon_pose=None;return
        self.coupon_pose=dict(center_m=center.tolist(),normal_toward_camera=normal.tolist(),
            observed_frames=len(self.coupon_poses),yaw_observable=False,coating_side_observed=False,
            source='Native RGB-D circular copper rim; own-robot camera calibration and source radius')

    def camera(self,name):
        k=self.m.camera(name).id;T=np.eye(4)
        T[:3,:3]=self.d.cam_xmat[k].reshape(3,3);T[:3,3]=self.d.cam_xpos[k]
        return T,float(self.m.cam_fovy[k])

    def observe_tool(self,obs):
        t=float(obs['time_s'])
        if self.register_map:
            if self.map_localizer is None:
                from map_localization import MapLocalization
                h,w=np.asarray(obs['head_depth']).shape
                self.map_localizer=MapLocalization(self.m,self.d,width=w,height=h,pixel_center=.5)
            registration=self.map_localizer.register(obs['head_depth'],
                max_depth_difference_m=.004,huber_scale_m=.0002)
            self.map_registration=dict(time_s=t,**registration)
            if not registration['accepted']:
                self.poses=[];self.coupon_poses=[];self.coupon_pose=None
                return
            # Correct only the robot's estimated frame. The static map and
            # native depth do not contain handled-object pose observations.
            self.estimate.anchors+=np.asarray(registration['correction_m'])
            mujoco.mj_forward(self.m,self.d)
        D,df=self.camera('head_depth');C,cf=self.camera('head_rgb')
        if self.observe_coupon:self.observe_optical_coupon(obs,D,C,df,cf)
        proposal,component=detect(obs['head_rgb'],obs['head_depth'],D,C,df,cf,self.bounds,self.threshold)
        report=dict(time_s=t,component_found=proposal['candidate_found'])
        if not proposal['candidate_found']:
            self.hypothesis_history=[]
            self.poses=[];self.vision_reports.append(report);return
        fit=self.localizer.estimate(component)
        if not fit['candidate_found']:
            self.hypothesis_history=[]
            self.poses=[];self.vision_reports.append(report);return
        best=fit['best'];report.update(surface_median_m=best['median_surface_distance_m'],inlier_fraction=best['inlier_fraction'])
        if best['median_surface_distance_m']>.0007 or best['inlier_fraction']<.90:
            self.hypothesis_history=[]
            self.poses=[];self.vision_reports.append(report);return
        if self.resolve_pose_ambiguity:
            # Preserve genuinely observed alternatives. No pose is reflected
            # or replaced by a nominal grasp or simulator placement.
            admissible=[p for p in fit['hypotheses'] if p['median_surface_distance_m']<=.0007
                and p['inlier_fraction']>=.90 and p['score_m2']<=best['score_m2']+4e-8]
            self.hypothesis_history.append(admissible)
            self.hypothesis_history=self.hypothesis_history[-4:]
        self.poses.append(best);self.poses=self.poses[-4:];self.vision_reports.append(report)
        if len(self.poses)<4:return
        if self.observe_coupon and self.coupon_pose is None:return
        centers=np.array([p['position_m'] for p in self.poses]);rotations=Rotation.from_matrix(np.array([p['rotation_matrix'] for p in self.poses]))
        mean=rotations.mean()
        if np.max(np.linalg.norm(centers-np.median(centers,axis=0),axis=1))>.001 or np.max((rotations*mean.inv()).magnitude())>.015:
            return
        pose=dict(position_m=np.median(centers,axis=0).tolist(),rotation_matrix=mean.as_matrix().tolist())
        surface=depth_surface(obs['head_depth'],D,df)
        self.planner=ToolApproachPlanner(self.m,self.d.qpos.copy(),pose,self.geometry,self.mesh,surface,component)
        self.plan=self.planner.build()
        ambiguity_attempts=[]
        if self.resolve_pose_ambiguity and not self.plan['planned']:
            ambiguity_attempts.append(dict(pose=pose,plan=self.plan,primary=True))
            used=[pose]
            for alternative in self.stable_pose_alternatives():
                R=np.asarray(alternative['rotation_matrix']);t0=np.asarray(alternative['position_m'])
                if any(np.linalg.norm(t0-np.asarray(p['position_m']))<.001 and
                    Rotation.from_matrix(R@np.asarray(p['rotation_matrix']).T).magnitude()<.015 for p in used):continue
                used.append(alternative)
                planner=ToolApproachPlanner(self.m,self.d.qpos.copy(),alternative,self.geometry,self.mesh,surface,component)
                plan=planner.build()
                ambiguity_attempts.append(dict(pose=alternative,plan=plan,primary=False))
                if plan['planned']:
                    pose=alternative;self.planner=planner;self.plan=plan;break
            self.events.append(dict(time_s=t,kind='observed_tool_pose_ambiguity',
                source='Four native RGB-D fits; same original geometry and clearance checks',
                attempts=ambiguity_attempts,selected_observation_pose=pose,
                reference_tool_pose_used=False,qualified_tool_pose=False))
        self.events.append(dict(time_s=t,kind='observed_tool_plan',pose=pose,plan=self.plan,
            source='Four accepted native RGB-D frames and own-robot state'))
        if not self.plan['planned']:
            self.failure='No collision-screened path from observed geometry';self.change('finished',t);return
        self.reference_data.qpos[:]=self.planner.initial
        entry=np.asarray(self.plan['entry_path']);lower=np.asarray(self.plan['lowering_path'])
        # Slow joint-space movement with a stop at each free-space waypoint,
        # followed by a continuous five-second Cartesian lowering polyline.
        self.path=np.vstack([entry,lower[1:]])
        durations=[max(2.,1.5*np.max(abs(b-a))/.20) for a,b in zip(entry[:-1],entry[1:])]
        durations.extend([5./(len(lower)-1)]*(len(lower)-1))
        self.path_times=np.r_[0.,np.cumsum(durations)]
        self.path_clock=0.;self.change('approach',t)
        if self.map_localizer is not None:
            self.map_localizer.close();self.map_localizer=None

    def stable_pose_alternatives(self):
        """Return only separately fitted hypotheses consistent across four frames."""
        if len(self.hypothesis_history)!=4:return []
        output=[]
        for anchor in self.hypothesis_history[-1]:
            a=np.asarray(anchor['position_m']);R=np.asarray(anchor['rotation_matrix']);matched=[]
            for frame in self.hypothesis_history:
                group=[p for p in frame if np.linalg.norm(np.asarray(p['position_m'])-a)<=.001 and
                    Rotation.from_matrix(np.asarray(p['rotation_matrix'])@R.T).magnitude()<=.015]
                if not group:break
                matched.append(min(group,key=lambda p:p['score_m2']))
            if len(matched)!=4:continue
            centers=np.asarray([p['position_m'] for p in matched]);center=np.median(centers,axis=0)
            rotations=Rotation.from_matrix(np.asarray([p['rotation_matrix'] for p in matched]));mean=rotations.mean()
            if np.max(np.linalg.norm(centers-center,axis=1))>.001 or np.max((rotations*mean.inv()).magnitude())>.015:continue
            output.append(dict(position_m=center.tolist(),rotation_matrix=mean.as_matrix().tolist(),
                observed_frames=4,maximum_surface_score_m2=max(p['score_m2'] for p in matched),
                maximum_surface_median_m=max(p['median_surface_distance_m'] for p in matched),
                minimum_inlier_fraction=min(p['inlier_fraction'] for p in matched),
                source='Independent native RGB-D registration hypotheses consistent across four frames'))
        return sorted(output,key=lambda p:p['maximum_surface_score_m2'])

    def approach_target(self,t,dt):
        # Whole-body balance can change the redundant arm configuration while
        # reaching the same wrist pose. Gate on task-space tracking and check
        # actual encoder-derived arm geometry, not equality to every IK angle.
        w=self.d.site('right_wrist_reference')
        self.arm_posture_error=float(np.max(abs(self.d.qpos[self.arm_qa]-self.initial[self.arm_indices])))
        self.wrist_path_error=float(np.linalg.norm(w.xpos-self.wrist_position))
        self.wrist_rotation_error=float(np.linalg.norm(Rotation.from_matrix(w.xmat.reshape(3,3)@self.wrist_rotation.T).as_rotvec()))
        if t>=self.next_clearance_check:
            lowering=self.path_clock>=self.path_times[len(self.plan['entry_path'])-1]
            self.latest_clearance=self.planner.observed_arm_clearance(self.d.qpos,.00002 if lowering else .001)
            self.next_clearance_check=t+.05
            if not self.latest_clearance['clear']:
                self.failure='Observed arm violates approach clearance: '+json.dumps(self.latest_clearance)
                self.change('finished',t);return
        if self.wrist_path_error<.004 and self.wrist_rotation_error<.025:
            self.path_clock=min(float(self.path_times[-1]),self.path_clock+dt)
        i=min(len(self.path)-2,int(np.searchsorted(self.path_times,self.path_clock,side='right')-1))
        u=float(np.clip((self.path_clock-self.path_times[i])/(self.path_times[i+1]-self.path_times[i]),0,1))
        if i<len(self.plan['entry_path'])-1:u=u*u*(3-2*u)
        q=self.path[i]+u*(self.path[i+1]-self.path[i])
        self.initial[self.arm_indices]=q
        self.reference_data.qpos[self.arm_qa]=q
        mujoco.mj_kinematics(self.m,self.reference_data)
        wrist=self.reference_data.site('right_wrist_reference')
        self.wrist_position=wrist.xpos.copy();self.wrist_rotation=wrist.xmat.reshape(3,3).copy()
        self.balance.palm_rotations={'right':self.wrist_rotation}
        if self.path_clock>=self.path_times[-1]:
            w=self.d.site('right_wrist_reference')
            position_error=np.linalg.norm(w.xpos-self.wrist_position)
            rotation_error=np.linalg.norm(Rotation.from_matrix(w.xmat.reshape(3,3)@self.wrist_rotation.T).as_rotvec())
            if position_error<.001 and rotation_error<.01 and max(abs(self.d.qvel[self.va[self.arm_indices]]))<.015:
                if self.tracking_clear_since is None:self.tracking_clear_since=t
                if t-self.tracking_clear_since>=.3:
                    self.feature_reference=self.midpoint();self.change('settle',t)
            else:self.tracking_clear_since=None
        if t-self.phase_started>90.:
            self.failure='Observed approach did not settle before timeout';self.change('finished',t)

    def update(self,obs):
        if set(obs)!=self.fields:raise ValueError('Unexpected visual actor observation fields')
        if (obs['head_rgb'] is None)!=(obs['head_depth'] is None):raise ValueError('Unpaired camera frame')
        previous_time=self.last_time
        response=super().update({k:obs[k] for k in PickupActor.fields})
        t=float(obs['time_s']);dt=.001 if previous_time is None else t-previous_time
        if self.phase=='observe':
            if t>=2. and obs['head_rgb'] is not None:self.observe_tool(obs)
            if self.phase=='observe' and t>=12.:
                self.failure='No stable tool observation before timeout';self.change('finished',t)
        if self.phase=='approach':self.approach_target(t,dt)
        response.update(phase=self.phase,failure=self.failure,complete=self.phase=='finished',events=list(self.events),
            accepted_tool_frames=len(self.poses),approach_clock_s=self.path_clock,
            arm_posture_error_rad=self.arm_posture_error,wrist_path_error_m=self.wrist_path_error,
            wrist_rotation_error_rad=self.wrist_rotation_error,observed_arm_clearance=self.latest_clearance,
            latest_vision_report=self.vision_reports[-1] if self.vision_reports else None)
        if self.observe_coupon:
            response.update(observed_optical_coupon=self.coupon_pose,
                latest_optical_coupon_report=self.coupon_report)
        if self.register_map:response['static_map_registration']=self.map_registration
        return response


def main():
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--prior',default='/model/policy/tool_prior.json');a=p.parse_args()
    actor=ToolActor(mujoco.MjModel.from_xml_path(a.model),json.loads(Path(a.prior).read_text()))
    while True:
        try:obs=pickle.load(sys.stdin.buffer)
        except EOFError:break
        try:response=actor.update(obs)
        except Exception as error:response=dict(torque=np.zeros(actor.m.nu),error=str(error))
        pickle.dump(response,sys.stdout.buffer,protocol=5);sys.stdout.buffer.flush()
        if response['error']:break


if __name__=='__main__':main()
