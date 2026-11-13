"""Register an unposed tool-shape prior to an observed RGB-D component.

No simulator object pose, segmentation or reference trajectory is consumed.
The fitted rigid frame is a proposal; execution needs uncertainty and
ambiguity checks, plus contact feedback for the passive flexible tool.
"""
import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation


class ToolPose:
    def __init__(self, vertices, faces):
        vertices=np.asarray(vertices,dtype=float);tri=vertices[np.asarray(faces,dtype=int)]
        cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);area=np.linalg.norm(cross,axis=1)
        normals=cross/np.maximum(area[:,None],1e-15)
        rng=np.random.default_rng(61106);ids=rng.choice(len(tri),size=60000,p=area/area.sum())
        uv=rng.random((len(ids),2));uv[uv.sum(axis=1)>1]=1-uv[uv.sum(axis=1)>1]
        self.points=tri[ids,0]+uv[:,:1]*(tri[ids,1]-tri[ids,0])+uv[:,1:]*(tri[ids,2]-tri[ids,0])
        self.normals=normals[ids];self.tree=cKDTree(self.points)
        self.center=self.points.mean(axis=0)

    def refine(self, cloud, translation, rotation):
        t=np.asarray(translation,dtype=float).copy();R=np.asarray(rotation,dtype=float).copy()
        for iteration in range(70):
            dist,ix=self.tree.query((cloud-t)@R)
            keep=dist<.012
            if keep.sum()<100:return None
            pred=self.points[ix[keep]]@R.T;n=self.normals[ix[keep]]@R.T
            residual=np.einsum('ij,ij->i',n,cloud[keep]-t-pred)
            weights=np.minimum(1.,.001/np.maximum(abs(residual),1e-12))
            J=np.c_[n,np.cross(pred,n)]
            step=np.linalg.solve((J*weights[:,None]).T@J+np.diag([1e-4]*3+[1e-6]*3),
                (J*weights[:,None]).T@residual)
            scale=min(1.,.003/max(np.linalg.norm(step[:3]),1e-12),.12/max(np.linalg.norm(step[3:]),1e-12))
            t+=scale*step[:3];R=Rotation.from_rotvec(scale*step[3:]).as_matrix()@R
            if np.linalg.norm(step[:3])<1e-6 and np.linalg.norm(step[3:])<1e-5:break
        dist,_=self.tree.query((cloud-t)@R)
        return dict(position_m=t.tolist(),rotation_matrix=R.tolist(),median_surface_distance_m=float(np.median(dist)),
            inlier_fraction=float(np.mean(dist<.0015)),score_m2=float(np.mean(np.minimum(dist,.005)**2)),iterations=iteration+1)

    def estimate(self, cloud):
        cloud=np.asarray(cloud,dtype=float)
        if len(cloud)<100:return dict(candidate_found=False,reason='insufficient_component_points')
        center=np.median(cloud,axis=0)
        _,V=np.linalg.eigh(np.cov((cloud-center).T));axis=V[:,-1]
        rows=[]
        for sign in [-1,1]:
            x=sign*axis;y=np.cross([0.,0.,1.],x);y/=np.linalg.norm(y);z=np.cross(x,y)
            nominal=np.column_stack([x,y,z])
            for roll in [-60,-30,0,30,60,90,180]:
                R=nominal@Rotation.from_euler('x',roll,degrees=True).as_matrix()
                fit=self.refine(cloud,center-R@self.center,R)
                if fit is not None:rows.append(dict(**fit,seed_axis_sign=sign,seed_roll_deg=roll))
        rows.sort(key=lambda r:r['score_m2'])
        return dict(scope=__doc__,candidate_found=bool(rows),best=rows[0] if rows else None,hypotheses=rows,
            qualified_grasp_pose=False,uncertainty_evaluated=False)
