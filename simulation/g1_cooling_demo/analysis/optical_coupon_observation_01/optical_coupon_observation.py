"""Locate a circular coated copper witness using native RGB-D observations.

The exposed copper rim, source diameter and public work-surface bounds are
appearance/shape priors. No instance pose, segmentation ID or evaluator state
is accepted. The circular specimen's in-plane yaw is unobservable.
"""
import numpy as np
from scipy.ndimage import label


def detect(rgb, depth, world_from_depth_camera, world_from_rgb_camera,
           depth_fovy, rgb_fovy, bounds, radius_m=.0125):
    rgb = np.asarray(rgb)
    depth = np.asarray(depth, dtype=float)
    h, w = depth.shape
    rh, rw = rgb.shape[:2]
    D, C = np.asarray(world_from_depth_camera), np.asarray(world_from_rgb_camera)
    fy = h/(2*np.tan(np.deg2rad(depth_fovy/2)))
    y, x = np.mgrid[:h, :w]
    local = np.stack([(x+.5-w/2)*depth/fy, -(y+.5-h/2)*depth/fy, -depth], axis=-1)
    world = local@D[:3, :3].T+D[:3, 3]
    color_local = (world-C[:3, 3])@C[:3, :3]
    z = -color_local[:, :, 2]
    f = rh/(2*np.tan(np.deg2rad(rgb_fovy/2)))
    u = np.rint(rw/2-.5+f*color_local[:, :, 0]/np.maximum(z, 1e-9)).astype(int)
    v = np.rint(rh/2-.5-f*color_local[:, :, 1]/np.maximum(z, 1e-9)).astype(int)
    valid = np.isfinite(depth)&(depth>.05)&(depth<2)&(z>.05)&(u>=0)&(u<rw)&(v>=0)&(v<rh)
    lower, upper = np.asarray(bounds)
    valid &= np.all((world>=lower)&(world<=upper), axis=-1)
    color = np.zeros((h, w, 3), dtype=float)
    color[valid] = rgb[v[valid], u[valid], :3]
    red, green, blue = np.moveaxis(color, -1, 0)
    rim = valid&(red>12)&(red>1.35*green)&(green>1.20*blue)
    groups, count = label(rim, structure=np.ones((3, 3)))
    rows = []
    for component in range(1, count+1):
        points = world[groups == component]
        if len(points)<20:
            continue
        origin = np.mean(points, axis=0)
        _, _, axes = np.linalg.svd(points-origin, full_matrices=False)
        plane = (points-origin)@axes[:2].T
        # Algebraic circle fit in a plane inferred from observed rim points.
        # This estimates the center; the source radius is an independent gate.
        coefficients, _, rank, _ = np.linalg.lstsq(
            np.c_[2*plane, np.ones(len(points))], np.sum(plane**2, axis=1), rcond=None)
        center2 = coefficients[:2]
        squared_radius = coefficients[2]+center2@center2
        if rank<3 or squared_radius<=0:
            continue
        radius = float(np.sqrt(squared_radius))
        radial = np.linalg.norm(plane-center2, axis=1)
        normal = axes[2]
        if np.dot(normal, D[:3, 3]-origin)<0:
            normal = -normal
        angle = np.sort(np.arctan2(*(plane-center2).T[::-1]))
        coverage = float(2*np.pi-np.max(np.diff(np.r_[angle, angle[0]+2*np.pi])))
        plane_error = float(np.quantile(abs((points-origin)@normal), .95))
        radial_error = float(np.quantile(abs(radial-radius), .95))
        checks = dict(source_radius=abs(radius-radius_m)<.0015,
            rim_planarity=plane_error<.001, circular_rim=radial_error<.0015,
            visible_arc=coverage>1.5*np.pi)
        rows.append(dict(component=component, observed_rim_pixels=len(points),
            center_m=(origin+center2@axes[:2]).tolist(), normal_toward_camera=normal.tolist(),
            fitted_radius_m=radius, rim_plane_error_p95_m=plane_error,
            circle_error_p95_m=radial_error, observed_arc_rad=coverage, checks=checks,
            passed=bool(all(checks.values()))))
    candidates = sorted([r for r in rows if r['passed']], key=lambda r:-r['observed_rim_pixels'])
    return dict(scope=__doc__, candidate_found=len(candidates)==1,
        ambiguous=len(candidates)>1, candidate=candidates[0] if len(candidates)==1 else None,
        components=rows, source_radius_m=radius_m, yaw_observable=False,
        estimated_surface='Observed copper rim plane; not an assumed grasp or hidden coated-face datum',
        runtime_manipulation_qualified=False)
