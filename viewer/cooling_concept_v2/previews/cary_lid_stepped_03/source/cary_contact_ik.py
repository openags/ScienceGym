"""Guide redundant Cary contact IK away from the closed extension envelope.

The point/envelope penalty only guides a search. Source-mesh checks still
decide whether each result is usable; these boxes are not collision evidence.
"""
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from optical_choreography import ARM,JOINTS,canonical,solve_palm
from source_geometry import fk


class ContactIK:
    def __init__(self,scene,include_cover=True,include_bay=False):
        self.scene=scene
        self.names=ARM+['waist_pitch_joint','waist_yaw_joint']
        self.limits=np.array([[JOINTS[n]['limits']['lower'],JOINTS[n]['limits']['upper']] for n in self.names])
        self.limits[self.names.index('right_shoulder_roll_joint'),1]=-.025
        self.limits[-2]=[0,.4];self.limits[-1]=[-.6,.6]
        vertices=[]
        for n in (scene.cover_names if include_cover else [])+scene.interfaces['extension_base_parts']:
            node,key=scene.cary_source.graph[n]
            if n in scene.access_rest:pose=scene.access_rest[n]
            else:
                from cary_access_scene import translation
                from source_geometry import ASSETS
                pose=translation(ASSETS['cary']['position_m'])@np.array(scene.setup['parts']['cary'][n]['matrix'])@node
            m=scene.cary_source.geometry[key];vertices.append(m.vertices@pose[:3,:3].T+pose[:3,3])
        v=np.vstack(vertices);lo=v.min(axis=0);hi=v.max(axis=0);self.center=(lo+hi)/2;self.half=(hi-lo)/2
        self.boxes=[(self.center,self.half)]
        if include_bay:
            from cary_access_scene import translation
            from source_geometry import ASSETS
            for n in scene.cary_source.graph.nodes_geometry:
                if not (n.startswith('sample_bay_side_') or n in ['left_optics_housing','right_optics_housing']):continue
                node,key=scene.cary_source.graph[n]
                pose=translation(ASSETS['cary']['position_m'])@np.array(scene.setup['parts']['cary'].get(n,{}).get('matrix',np.eye(4)))@node
                points=scene.cary_source.geometry[key].vertices@pose[:3,:3].T+pose[:3,3]
                lo=points.min(axis=0);hi=points.max(axis=0);self.boxes.append(((lo+hi)/2,(hi-lo)/2))
        selected=['torso_link','head_link','logo_link','right_shoulder_pitch_link','right_shoulder_roll_link','right_shoulder_yaw_link','right_elbow_link','right_wrist_roll_link']
        self.points={n:scene.meshes[n].vertices[np.linspace(0,len(scene.meshes[n].vertices)-1,min(96,len(scene.meshes[n].vertices))).astype(int)] for n in selected if n in scene.meshes}

    def solve(self,base,target,seed):
        # Preserve an already clear continuation before using a conservative
        # envelope to change posture. The source meshes decide acceptance.
        for waist in [False,True]:
            exact,position,angular=solve_palm(base,target,seed,waist=waist)
            if position<1e-7 and angular<1e-6 and not self.scene.check(base,exact):return exact,position,angular
        q=canonical(seed);initial=np.clip([q[n] for n in self.names],self.limits[:,0]+1e-9,self.limits[:,1]-1e-9)
        def residual(values,guide=True):
            world=fk({**q,**dict(zip(self.names,values))});palm=base@world['right_palm_force_sensor']
            error=np.r_[(palm[:3,3]-target[:3,3])*10,Rotation.from_matrix(target[:3,:3].T@palm[:3,:3]).as_rotvec()]
            if not guide:return error
            penalties=[]
            for n,points in self.points.items():
                pose=base@world[n];p=points@pose[:3,:3].T+pose[:3,3]
                for center,half in self.boxes:
                    d=abs(p-center)-half
                    signed=np.linalg.norm(np.maximum(d,0),axis=1)+np.minimum(np.max(d,axis=1),0)
                    penalties.extend(np.maximum(.008-signed,0)*20)
            return np.r_[error,penalties,(values-initial)*1e-6]
        result=least_squares(residual,initial,bounds=(self.limits[:,0],self.limits[:,1]),max_nfev=160,ftol=1e-12,xtol=1e-12,gtol=1e-12)
        q.update(dict(zip(self.names,map(float,result.x))));error=residual(result.x,False)
        if np.linalg.norm(error[:3])/10>1e-8 or np.linalg.norm(error[3:])>1e-7:
            # Project the envelope-guided posture back onto exact contact.
            # The source mesh check, not the conservative envelope margin,
            # decides whether this projection remains usable.
            for waist in [False,True]:
                exact,position,angular=solve_palm(base,target,q,waist=waist)
                if position<1e-7 and angular<1e-6 and not self.scene.check(base,exact):return exact,position,angular
        return q,float(np.linalg.norm(error[:3])/10),float(np.linalg.norm(error[3:]))
