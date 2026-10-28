# Cary 5000 and legacy extended sample compartment

This original reconstruction follows Agilent's instrument photographs and
manufacturer dimensions: 1020 × 710 × 380 mm and 91 kg. The wide left housing,
narrower right housing, sliding sample lid, removable front wall and front
power controls are modeled separately. Small control, fitting and front-panel
projections use inferred dimensions; the validator reports their complete
bounding envelope separately from the source-sized main housing.

The accessory is the legacy **0010079800** extended compartment, selected to
match the legacy internal DRA. Its manual gives an internal width of 154 mm,
height of 212 mm and depth of 170 mm, with approximately 180 mm added to the
instrument depth. A later flyer describes a different assembled-compartment
size; these statements are kept distinct in [sources.json](sources.json).

The extension base and cover are separately removable. Two keyhole pins locate
the base after removal of the instrument front wall. The manual's access
sequence is: retract the main lid, lift and unhook the extension cover, slide
it onto the distal hinge bar, then tilt it away. The selected hook shapes,
clearances and lid travel are inferred. The 6 mm hose fittings have real open
passages. The module and instrument interior are available through the asset
inspector's interior toggle.

[interfaces.json](interfaces.json) records these affordances and their
inference status. The geometry validator checks exported solids, dimensions,
open passages, separate parts and sampled lid clearance. These static checks
do not qualify contact dynamics, installation or optical alignment. The
internal DRA is a separate 5 kg asset; the 91 kg instrument starts supported
and stationary.

Generated Blender/GLB files and renders are original. Referenced manuals and
photographs are not redistributed or used as textures. The packed label font
license is in [FONT_LICENSE.txt](FONT_LICENSE.txt). Rebuild with Blender 2.82:
`blender -b --python build.py`, followed by `python validate.py` in the
simulation's Python environment with NumPy, trimesh and rtree.
