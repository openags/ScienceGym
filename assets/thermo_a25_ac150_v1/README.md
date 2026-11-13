# Thermo A25 with selected AC150 controller

This is an original, manufacturer-informed reconstruction of the A25 bath
named in the cooling paper. **AC150 is a compatible selected configuration;
the paper does not identify its controller.** No manufacturer CAD was found
in the recorded search. Manufacturer photographs and manuals are linked in
[sources.json](sources.json), with hashes for the exact referenced files.

The model contains a separate liftable lid and open grip, front carrying-handle
recess, drain bore and cap, open ventilation grids, stainless reservoir,
controller bridge, seven separate AC150 keys, temperature cutout, rear power
controls and circulation fittings. [interfaces.json](interfaces.json) records
approach axes and source versus selected dimensions. The native Blender file
retains editable text; the GLB contains inspectable part meshes.

The selected case envelope is 273 × 483 × 749 mm, excluding projecting fittings.
The manual gives a 173 × 184 × 200 mm working region. The product page instead
lists 711 mm overall height and 204 mm working depth. Those conflicts remain
explicit: the reconstruction uses the manual's AC150/AC200 configuration table.
Only the manufacturer gallery photograph visibly labeled **A25** is used for
its exterior; other gallery images depict different bath models.

The 515 mm rim height, local wall/radius dimensions, lid clearance, control
travel and hidden reservoir extension are inferred. The manual specifies
22–57 mm of clearance below the rim; for the selected 200 mm depth this means
143–178 mm of water depth. This corrects the earlier task-card underfill range.
The source's 7–12 L capacity is retained separately from the inferred hidden
cavity. Internal immersion parts represent clearance, not validated pump or
heater construction. AC200-only USB and multifunction ports are omitted.

[geometry_checks.json](geometry_checks.json) checks the exported envelope,
working region, reservoir surfaces, lift path, grip, drain and control identities.
These are static geometry checks. Liquid, thermal/electrical response and robot
operation require separate simulation evidence.

Run `build.py` inside Blender, then `python validate.py` with NumPy, trimesh and
rtree installed. The embedded DejaVu font retains its [license](FONT_LICENSE.txt).
The manufacturer reference documents and photographs are not redistributed.
