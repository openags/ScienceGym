# Measurement Computing USB-TC reconstruction

This original metric asset follows the manufacturer's USB-TC manual: the
128.52 × 88.39 × 35.56 mm enclosure, blue recessed housing, four terminal blocks,
52 numbered pins, two CJC sensors, USB Type-B port and stacked status LEDs.
Each screw, clamp, wire-entry passage and terminal legend is separately named.

[Three-quarter view](evidence/three_quarter.png) · [Terminal detail](evidence/terminals.png)
· [USB face](evidence/usb.png) · [Top](evidence/top.png)
· [Editable Blender source](geometry/mcc_usb_tc.blend)
· [GLB](geometry/mcc_usb_tc.glb)

[Sources](sources.json) preserve two manual discrepancies and distinguish
documented identities from inferred dimensions. Manufacturer staff identified a
generic enclosure STEP file; direct retrieval was unavailable, so this asset
does not contain vendor CAD. Exact enclosure curves, terminal pitch, slot sizes,
clamp travel and USB engagement require hardware or further drawing validation.

[Interface coordinates](interfaces.json) identify all wire entries and driver
axes, the eight exact H/L pin pairs and USB insertion direction. Static checks
inspect the exported enclosure envelope, pin identities, 52 open wire passages,
52 recessed screw slots, internal clamp seats, shaft clearance, recessed head
travel and USB opening. They do not qualify screw engagement,
wire retention, thermocouple accuracy or robot execution.

Rebuild with `blender -b --python build.py`, then run `python validate.py`.
Validation uses NumPy, Trimesh and Rtree 1.4.1. The Blender builder also reads
the shared source pin table at `../cooling_scene_assets_v2/interaction_geometry.py`.
The system DejaVu Sans font is converted to mesh for the exported legends;
its notice is retained under `LICENSES/DejaVu-copyright.txt`. Original code and
geometry use the repository Apache-2.0 license. Manufacturer PDFs, photographs
and the unavailable enclosure CAD are not redistributed.
