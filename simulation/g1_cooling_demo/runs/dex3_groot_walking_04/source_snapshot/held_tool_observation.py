"""Observe a partially occluded held tool from depth and own-robot geometry.

The known grasp bounds a search; it is never returned as a measurement. Remove
surfaces explained by the sensed robot pose, then fit the remaining visible
depth points to unposed tool CAD. A candidate is a partial surface observation,
not a qualified full pose, fingertip separation, or stable-grasp measurement.
"""
import numpy as np
import trimesh

from tool_pose import ToolPose


class HeldToolObservation:
    def __init__(self, tool_mesh, robot_meshes):
        self.tool = tool_mesh
        self.localizer = ToolPose(tool_mesh.vertices, tool_mesh.faces)
        self.robot = robot_meshes

    def detect(self, depth, world_from_camera, fovy, expected, body_poses):
        depth = np.asarray(depth); h,w = depth.shape
        y,x = np.mgrid[:h,:w]; fy=h/(2*np.tan(np.deg2rad(fovy/2)))
        local=np.stack([(x+.5-w/2)*depth/fy, -(y+.5-h/2)*depth/fy, -depth],axis=-1)
        D=np.asarray(world_from_camera);world=local@D[:3,:3].T+D[:3,3]
        predicted=self.tool.vertices@expected[:3,:3].T+expected[:3,3]
        lo,hi=predicted.min(0)-.02,predicted.max(0)+.02
        mask=np.isfinite(depth)&(depth>.05)&(depth<2.)&np.all((world>=lo)&(world<=hi),axis=-1)
        pixels=np.argwhere(mask);points=world[mask]
        report=dict(scope=__doc__,candidate_found=False,search_points=len(points),
            source='Native depth, own-robot pose/visual meshes and unposed tool CAD',
            robot_surface_exclusion_m=.0015,nominal_shape_search_distance_m=.012,
            partial_surface_only=True,qualified_tool_pose=False,qualified_tip_pose=False,
            grasp_hypothesis_is_not_an_observation=True)
        keep=np.ones(len(points),dtype=bool)
        # Exact triangles, with local boxes only as a conservative cull.
        # No simulator segmentation or object poses enter this calculation.
        for name,mesh in self.robot.items():
            T=body_poses[name]
            local_points=(points-T[:3,3])@T[:3,:3]
            nearby=keep&np.all((local_points>=mesh.bounds[0]-.0015)&(local_points<=mesh.bounds[1]+.0015),axis=1)
            ids=np.flatnonzero(nearby)
            if len(ids):
                distance=trimesh.proximity.closest_point(mesh,local_points[ids])[1]
                keep[ids[distance<=.0015]]=False
        report['robot_explained_points']=int((~keep).sum())
        ids=np.flatnonzero(keep)
        if len(ids):
            distance=self.localizer.tree.query((points[ids]-expected[:3,3])@expected[:3,:3])[0]
            keep[ids[distance>.012]]=False
        points,pixels=points[keep],pixels[keep]
        report['visible_candidate_points']=len(points)
        if len(points)<100:
            report['reason']='insufficient_unexplained_surface'
            return report,points,pixels
        fit=self.localizer.refine(points,expected[:3,3],expected[:3,:3])
        if fit is None:
            report['reason']='surface_registration_failed'
            return report,points,pixels
        center=points.mean(0);_,axes=np.linalg.eigh(np.cov((points-center).T))
        span=np.ptp((points-center)@axes[:,::-1],axis=0)
        report.update(observed_spans_m=span.tolist(),surface_fit=fit,
            fitted_origin_change_from_prior_m=float(np.linalg.norm(np.asarray(fit['position_m'])-expected[:3,3])))
        checks=dict(visible_length=.025<span[0]<.16,visible_width=.002<span[1]<.03,
            visible_thickness=span[2]<.02,surface_residual=fit['median_surface_distance_m']<.0007,
            surface_inliers=fit['inlier_fraction']>=.90,
            bounded_search=report['fitted_origin_change_from_prior_m']<.02)
        report['checks']={k:bool(v) for k,v in checks.items()}
        report['candidate_found']=all(report['checks'].values())
        return report,points,pixels
