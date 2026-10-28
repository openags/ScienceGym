"""Observe the source Nicolet's four blue keys in native head RGB and depth.

Color is a property of the existing instrument, not an added marker. The
declared key order and spacing are object-relative priors. No placement,
simulator segmentation, device joints or evaluator data are inputs.
"""
from itertools import combinations

import mujoco
import numpy as np
from scipy import ndimage


class KeyRowObservation:
    labels = ['SAMPLE', 'BACKGROUND', 'OK / ENTER', 'STOP']

    def __init__(self, model, data):
        self.m, self.d = model, data
        self.depth_camera = model.camera('head_depth').id
        self.rgb_camera = model.camera('head_rgb').id

    def observe(self, rgb, depth):
        if rgb is None or depth is None:
            return None
        rgb = np.asarray(rgb, dtype=float); depth = np.asarray(depth)
        if rgb.shape != (360, 640, 3) or depth.shape not in {(180, 320), (360, 640)}:
            raise ValueError('Unexpected native head image shapes')
        red, green, blue = rgb.transpose(2, 0, 1)
        mask = (blue > red*1.5+2) & (blue > green*1.15+1) & (blue > 8)
        labels, count = ndimage.label(mask)
        blobs = []
        for label in range(1, count+1):
            y, x = np.where(labels == label)
            if not 20 <= len(x) <= 800:
                continue
            width, height = np.ptp(x)+1, np.ptp(y)+1
            if min(width, height) < 4 or not .25 < width/height < 4:
                continue
            blobs.append(dict(label=label, area=len(x), center=np.array([x.mean(), y.mean()])))
        blobs = sorted(blobs, key=lambda b: -b['area'])[:16]
        candidates = []
        for group in combinations(blobs, 4):
            group = sorted(group, key=lambda b: b['center'][0])
            points = np.array([b['center'] for b in group]); areas = [b['area'] for b in group]
            gaps = np.linalg.norm(np.diff(points, axis=0), axis=1)
            if min(gaps) < 10 or max(gaps)/min(gaps) > 1.25 or max(areas)/min(areas) > 2:
                continue
            _, _, vt = np.linalg.svd(points-points.mean(axis=0), full_matrices=False)
            residual = np.max(abs((points-points.mean(axis=0)) @ vt[-1]))
            if residual < 1.5:
                candidates.append((residual + np.std(gaps), group))
        if not candidates:
            return dict(accepted=False, reason='four_key_row_not_visible', blue_blobs=len(blobs))
        _, row = min(candidates, key=lambda r: r[0])
        h, w = depth.shape
        fy = h/(2*np.tan(np.deg2rad(self.m.cam_fovy[self.depth_camera])/2))
        y, x = np.mgrid[:h, :w]
        pixels = np.stack([(x+.5-w/2)*depth/fy, -(y+.5-h/2)*depth/fy, -depth], axis=-1)
        valid = np.isfinite(depth) & (depth > .05) & (depth < 2.)
        camera = self.d.cam_xmat[self.depth_camera].reshape(3, 3)
        cloud = pixels[valid] @ camera.T + self.d.cam_xpos[self.depth_camera]
        color_rotation = self.d.cam_xmat[self.rgb_camera].reshape(3, 3)
        local = (cloud-self.d.cam_xpos[self.rgb_camera]) @ color_rotation
        color_fy = 360/(2*np.tan(np.deg2rad(self.m.cam_fovy[self.rgb_camera])/2))
        projection = np.c_[320 + local[:, 0]/(-local[:, 2])*color_fy-.5,
                           180 - local[:, 1]/(-local[:, 2])*color_fy-.5]
        ix = np.rint(projection).astype(int)
        visible = (local[:, 2] < -.05) & (ix[:, 0] >= 0) & (ix[:, 0] < 640) & (ix[:, 1] >= 0) & (ix[:, 1] < 360)
        ids = np.zeros(len(cloud), dtype=int)
        ids[visible] = labels[ix[visible, 1], ix[visible, 0]]
        selected = np.isin(ids, [b['label'] for b in row])
        samples = cloud[selected]
        if len(samples) < 20:
            return dict(accepted=False, reason='insufficient_key_depth_samples', points=len(samples))
        rng = np.random.default_rng(851); best = None
        for _ in range(160):
            a, b, c = samples[rng.choice(len(samples), 3, replace=False)]
            n = np.cross(b-a, c-a); length = np.linalg.norm(n)
            if length < 1e-9: continue
            n /= length
            if abs(n[2]) < .6: continue
            # The unmixed ideal-depth buffer resolves the flat cap plane.
            # A wider band also admitted bevel points, tilting the fitted
            # normal enough to bias the extrapolated window-grip position.
            error = abs((samples-a)@n); inliers = error < .00005
            score = (int(inliers.sum()), -float(np.median(error)))
            if best is None or score > best[0]: best = (score, inliers)
        if best is None or best[1].sum() < 16 or best[1].mean() < .65:
            return dict(accepted=False, reason='key_cap_plane_not_supported', points=len(samples))
        surface = samples[best[1]]; center = surface.mean(axis=0)
        _, singular, vt = np.linalg.svd(surface-center, full_matrices=False)
        normal = vt[-1]
        if normal[2] < 0: normal *= -1
        if singular[1] < .006:
            return dict(accepted=False, reason='key_cap_plane_degenerate')
        targets = []
        for blob in row:
            u, v = blob['center']
            ray = color_rotation @ np.array([(u+.5-320)/color_fy, -(v+.5-180)/color_fy, -1.])
            origin = self.d.cam_xpos[self.rgb_camera]
            distance = np.dot(center-origin, normal)/np.dot(ray, normal)
            targets.append(origin+distance*ray)
        targets = np.asarray(targets)
        spacing = np.linalg.norm(np.diff(targets, axis=0), axis=1)
        if max(abs(spacing-.049)) > .004:
            return dict(accepted=False, reason='row_spacing_mismatch', spacing_m=spacing.tolist())
        direction = targets[-1]-targets[0]; direction /= np.linalg.norm(direction)
        return dict(accepted=True, buttons={label:p.tolist() for label,p in zip(self.labels, targets)},
                    outward_normal=normal.tolist(), row_direction=direction.tolist(),
                    spacing_m=spacing.tolist(), cap_plane_points=len(surface),
                    plane_residual_m=float(np.max(abs((surface-center)@normal))),
                    pixel_centers=[b['center'].tolist() for b in row],
                    source='native_head_rgb_controls_with_native_depth_cap_plane')
