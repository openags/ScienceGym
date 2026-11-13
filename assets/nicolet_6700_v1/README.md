# Nicolet 6700 bare instrument

This original reconstruction uses the 2007 manufacturer specification for the
692 × 655 × 254 mm instrument envelope and 210 × 260 × 200 mm sample bay.
The previous scene's 690 mm width and oversized 285 × 340 mm bay are corrected.
[sources.json](sources.json) records the manufacturer-authored documents,
photograph review, hashes, CAD search and inferred dimensions.

The bay is physically open with its selected cover removed. The side housings,
ribbed rear cover, detector caps, four exposed scan keys, recessed ventilation,
mount sockets, cover and handle are separate named parts. Native Blender and
GLB files preserve metre units. [interfaces.json](interfaces.json) records the
bay datum and control locations; each part records its geometry basis.

The dark central housings in several manufacturer photographs are installed
Smart accessories. They are not used as the bare instrument or the IntegratIR.
No optical accessory is included here. The cover hinge, handle, mounting sockets
and rear connectors remain selected unmeasured geometry. This asset needs
interface qualification before a robot can receive manipulation credit; its
static geometry checks alone do not provide that credit.

Build with Blender 2.82 using `blender -b --python build.py`, then run
`python validate.py` in the tested ScienceGym Python environment. Four generated
views under `evidence/` show the front, rear, open bay and scan controls.
Manufacturer documents and photos are referenced, not redistributed or used
as textures. The packed label font's license is in `FONT_LICENSE.txt`.
