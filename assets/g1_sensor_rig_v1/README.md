# G1 sensor placement review

The native G1 D435i has nominal RGB and depth inspection views. The D405
candidate now uses a separately identified G1 collar derivative with standard
fasteners. The original undersized source collar remains available as a failed
baseline. Rigid geometry clearance is checked; compliant lining, retention,
cables and dynamic loads remain open. No accepted wrist installation or actor
sensor stream is claimed. The viewer hides the candidate by default.

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

`build_adapters.py` retains the official bracket's camera arm above CAD
Y = 31 mm and replaces its collar with matched halves. The original 30 mm
bracket bore and inward fastening tabs intersect the G1 wrist. The new bore
radius is 31.2 mm, outer radius 38.5 mm, width 10 mm, split gap 1 mm and new
M3 clearance axes are at CAD X = ±40 mm. These are authored dimensions, not an
official Unitree or Inspire part. Printable STEP and SI STL files, source hashes,
full-density PA12 mass estimates and the hardware bill are in `adapter.json`.
No robot, hand or camera geometry is scaled or reshaped.

`build.py` places the ring at wrist X = +36.5 mm, clocked +90 degrees left /
−90 degrees right. The source backplate and two 20 mm-pitch camera bores retain
the camera transform. Each wrist has two M3×6 camera screws and two M3×20 collar
screws with four washers and two nuts. Camera insertion is independently checked
at 3 mm against the manufacturer's 4 mm maximum. Hex sockets, nut bores and
washers are geometry; threads use major envelopes, not a helical contact model.
`hardware_sources.json` records the nominal dimensions and material assumptions.

`check_fit.py` checks the attached models against source robot triangle meshes
at three finger configurations and all 68 station postures. The adapted rigid
parts have no robot surface intersections in these checks. Clipping the wrist
triangles to the 10 mm collar band gives a 30.4942 mm maximum radial envelope;
the rigid bore therefore reserves at least 0.7058 mm radial space. This is a
bound on the source mesh, not a production tolerance or clamp-force guarantee.
The clearance is reserved for a compliant lining whose preload and retention
are still unqualified. Station IK rejects rigid parent-wrist intersections as
well as intersections with other links; there is no parent-link exemption in
the position-candidate acceptance predicate.

The two unfastened halves have 33-point radial removal-path checks per wrist.
These discrete checks exclude fastener insertion and do not establish a
continuous assembly trajectory. `check_clocking.py` and
`failed_mount_fixture.json` retain the original geometry and failed side-mount
case. The original undersized collar is also required to fail at the revised
orientation. FCL triangle contact depths are not used as penetration distances.
Full containment, compliant contact, optical calibration, cable routing,
fastener preload, dynamic loads and complete motion qualification remain open.

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
