# G1 sensor placement review

The native G1 D435i has nominal RGB and depth inspection views. The two D405
wrist cameras have a source-constrained mounting candidate that **remains on hold
for clamp-fit review**. Neither calibrated sensor streams nor accepted wrist
installation is claimed. The laboratory viewer hides these attachments by
default and offers an explicit candidate overlay and four inspection views.

## Provenance and reconstruction

`SOURCE.json` pins Unitree xr_teleoperate STEP parts, installation photos,
current Device.md, licenses and RealSense nominal frame descriptions. The
Unitree installation documentation describes Dex3 M4010; it does not establish
compatibility with Inspire FTP. The STEP filenames are misleading; current
Device.md download labels, embedded Chinese PRODUCT names and geometry agree:

| Source filename | Actual part |
| --- | --- |
| `left_wrist_D405_camera_mount.STEP` | Clamp half-ring |
| `right_wrist_D405_camera_mount.STEP` | Left camera bracket |
| `wrist_ring_mount.STEP` | Right camera bracket |

`convert_mounts.py` retains the original STEP solids and generates SI meshes
using 0.05 mm / 0.15 rad tessellation. A 1 micrometre vertex weld closes seams
between independently tessellated faces; collapsed triangles are removed.
`mount_geometry.json` records both STEP and mesh volumes, watertightness,
source hashes, cylindrical axes and planar faces. This is a derivative mesh,
not a claim of unchanged source triangulation.

`build.py` aligns the clamp axis and source half-ring, places the ring center at
an authored +36.5 mm in each `wrist_yaw_link`, then rotates it +90 degrees left / -90 degrees right to clear the pitch housing,
and uses the two 20 mm-pitch M3
camera bores plus the backplate plane to align the manufacturer's D405 mesh.
No commercial geometry is rescaled. Rotational clocking and camera roll are
explicit assembly choices, not manufacturer-calibrated extrinsics. Source
photos and STEP inputs remain available for inspection.

`check_fit.py` checks exact source triangle intersections at three finger
configurations. The above-wrist
placement avoids other links at these three poses; bracket/clamp intersections
with the parent wrist remain unresolved. Even intended clamp contact requires
mechanical review. `check_clocking.py` retains all 144 zero-pose trials per side,
including failed orientations. `failed_mount_fixture.json` preserves the
original side-mounted collision with the moving wrist housing as a regression
case. This finite search does not cover full arm motions. FCL
triangle contact depths are deliberately not interpreted as physical overlap
depths. Candidate attachment surfaces are additionally checked against other robot
links at all 47 recorded station postures; conservative boxes screen room and
furniture conflicts. Parent-wrist clamp contact remains unresolved throughout. Station IK now also screens the candidate attachments against other links
and external obstacles. Parent-wrist clamp contact is retained as an open
fit question; the candidate is still excluded from accepted installation and
transit qualification. Full containment, insertion trajectories, fasteners,
material/preload, cables, strain relief and loads are not qualified.

## Optical inspection

The native camera's `d435_link` comes from the official G1 URDF. ROS nominal
optical rotations and the D435 color offset are retained; treating that source
link as the real optical reference is still uncalibrated. Its housing already
exists in the G1 source mesh, so no duplicate D435 enclosure is added.
D405 color uses the left imager's nominal optical frame. Wrist depth remains
outside the selected channels.

The pinned October 2025 datasheet, table 3-49, gives nominal HD FOV values of
69 × 42 degrees (D435i RGB), 87 × 58 (D435i depth), and 84 × 58 (D405).
The current D405 product page instead lists 87 × 58. The preview follows the
pinned datasheet and exposes the conflict; accepted virtual intrinsics/extrinsics and their uncertainty model are still
required. No physical-hardware experiment is required for this demo.
Independent horizontal and vertical focal lengths are used for a 1280 × 720
ideal pinhole preview. Near/far clipping is an authored rendering choice, not
a device's usable measurement range.

The browser preserves full room/equipment occlusion and hides review labels.
RGB uses the viewer's ACES display transform after an HDR pass. Depth is ideal
geometric axial depth: black 0 m, white at the selected display range (default
1 m), and black for background without a hit. Transparent surfaces are treated as opaque;
there is no stereo correspondence, validity mask, distortion, exposure/noise,
rolling-shutter or timing model. Images are inspection artifacts, not actor
observations. Changing a pose marks the previous image stale until refreshed.

`viewer/lab_review_v1/check_sensors.py` compares all attachment and optical
frames with independent MuJoCo kinematics, checks image generation and
occluder preservation, and saves source-bound PNGs. This check does not promote
an unaccepted installation or count as a manipulation trial.

## Rebuild

Run `assets/cooling_lab_v1/rebuild_review.py`; it rebuilds camera and robot
inputs before this package, then checks the final scene and station poses.
Add its `--browser` argument for optical and laboratory screenshots. Dependencies
are pinned in `assets/cooling_lab_v1/requirements.txt`.
