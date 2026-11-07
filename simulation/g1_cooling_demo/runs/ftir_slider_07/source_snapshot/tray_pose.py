"""Rigid CAD registration from depth foreground points, without plant state.

The geometry is a declared object-shape prior. Translation and orientation are
estimated from observed points; no object placement or segmentation is input.
"""
import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation


class TrayPose:
    def __init__(self, vertices, faces):
        self.vertices=np.asarray(vertices,dtype=float)
        triangle=self.vertices[np.asarray(faces,dtype=int)]
        cross=np.cross(triangle[:,1]-triangle[:,0],triangle[:,2]-triangle[:,0])
        area=np.linalg.norm(cross,axis=1)
        normals=cross/np.maximum(area[:,None],1e-12)
        rng=np.random.default_rng(131)
        ids=rng.choice(len(triangle),size=40000,p=area/area.sum())
        uv=rng.random((len(ids),2));uv[uv.sum(axis=1)>1]=1-uv[uv.sum(axis=1)>1]
        self.points=triangle[ids,0]+uv[:,:1]*(triangle[ids,1]-triangle[ids,0])+uv[:,1:]*(triangle[ids,2]-triangle[ids,0])
        self.normals=normals[ids];self.tree=cKDTree(self.points)
        self.previous=None

    def refine(self, cloud, translation, rotation, iterations=45):
        translation=np.array(translation,dtype=float);rotation=np.array(rotation,dtype=float)
        for iteration in range(iterations):
            local=(cloud-translation)@rotation
            distance,index=self.tree.query(local)
            valid=distance<.045
            if valid.sum()<40:return None
            predicted=self.points[index[valid]]@rotation.T
            normal=self.normals[index[valid]]@rotation.T
            residual=np.einsum('ij,ij->i',normal,cloud[valid]-translation-predicted)
            weight=np.minimum(1.,.004/np.maximum(abs(residual),1e-12))
            jac=np.c_[normal,np.cross(predicted,normal)]
            lhs=(jac*weight[:,None]).T@jac
            rhs=(jac*weight[:,None]).T@residual
            step=np.linalg.solve(lhs+np.diag([1e-3]*3+[1e-4]*3),rhs)
            scale=min(1.,.025/max(np.linalg.norm(step[:3]),1e-12),.15/max(np.linalg.norm(step[3:]),1e-12))
            translation+=scale*step[:3]
            rotation=Rotation.from_rotvec(scale*step[3:]).as_matrix()@rotation
            if np.linalg.norm(step[:3])<.00003 and np.linalg.norm(step[3:])<.0003:break
        distance,_=self.tree.query((cloud-translation)@rotation)
        # Capped Euclidean distance also penalizes points outside a finite wall.
        score=float(np.mean(np.minimum(distance,.025)**2))
        return dict(position=translation,rotation=rotation,score=score,
                    inlier_fraction=float(np.mean(distance<.008)),
                    median_distance=float(np.median(distance)),iterations=iteration+1)

    def estimate(self, cloud):
        cloud=np.asarray(cloud,dtype=float)
        if len(cloud)<200:return dict(accepted=False,reason='insufficient_foreground',points=len(cloud))
        # Deterministic spatial sampling limits optimization cost.
        _,index=np.unique(np.floor(cloud/.003).astype(int),axis=0,return_index=True)
        cloud=cloud[np.sort(index)]
        if len(cloud)<200:return dict(accepted=False,reason='insufficient_spatial_coverage',points=len(cloud))
        if len(cloud)>2000:cloud=cloud[np.linspace(0,len(cloud)-1,2000,dtype=int)]
        low,high=np.quantile(cloud,[.02,.98],axis=0)
        center=(low+high)/2
        nominal=Rotation.from_euler('z',90,degrees=True).as_matrix()
        seeds=[];fits=[]
        if self.previous is not None:
            tracked=self.refine(cloud,*self.previous)
            if tracked is not None:fits.append(tracked)
        # A visible point cloud can cover only a front wall. Try offsets within
        # the declared 200 mm tray depth, and both signs of tray pitch.
        if not fits or fits[0]['inlier_fraction']<.97 or fits[0]['median_distance']>.002:
            for pitch in [-65,-35,0,35,65]:
                rotation=Rotation.from_euler('y',pitch,degrees=True).as_matrix()@nominal
                bounds=self.vertices@rotation.T
                offset=(bounds.min(axis=0)+bounds.max(axis=0))/2
                for dx in [0.,.045,-.045]:seeds.append((center-offset+[dx,0,0],rotation))
            fits.extend(fit for translation,rotation in seeds if (fit:=self.refine(cloud,translation,rotation)) is not None)
        if not fits:return dict(accepted=False,reason='no_registration',points=len(cloud))
        best=min(fits,key=lambda r:r['score']);position,rotation=best['position'],best['rotation']
        transformed=self.vertices@rotation.T+position
        tilt=float(np.degrees(np.arccos(np.clip(rotation[2,2],-1,1))))
        accepted=best['inlier_fraction']>.90 and best['median_distance']<.004
        if accepted:self.previous=(position.copy(),rotation.copy())
        return dict(accepted=bool(accepted),position_m=position.tolist(),rotation_matrix=rotation.tolist(),
                    center_m=((transformed.min(axis=0)+transformed.max(axis=0))/2).tolist(),
                    low_m=transformed.min(axis=0).tolist(),high_m=transformed.max(axis=0).tolist(),
                    tilt_deg=tilt,inlier_fraction=best['inlier_fraction'],median_distance_m=best['median_distance'],
                    score_m2=best['score'],points=len(cloud),hypotheses=len(fits),
                    source='depth_foreground_to_declared_cad_rigid_registration')
