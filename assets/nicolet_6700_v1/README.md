# Nicolet 6700 bare instrument

This original reconstruction uses the 2007 manufacturer specification for the
692 × 655 × 254 mm instrument envelope and 210 × 260 × 200 mm sample bay.
The previous scene's 690 mm width and oversized 285 × 340 mm bay are corrected.
[sources.json](sources.json) records the manufacturer-authored documents,
photograph review, hashes, CAD search and inferred dimensions.

The bay has a hinged top cover, a separate sliding sample-access window and a
fixed front wall. The manual's printed pages 51 and 92 establish that component
separation; the earlier inferred L-shaped moving front wall is corrected.
The side housings, ribbed rear cover, detector caps, four exposed scan keys,
recessed ventilation, optical ports, mount sockets and handles are separate named parts. Native Blender and
GLB files preserve metre units. [interfaces.json](interfaces.json) records the
bay datum and control locations; each part records its geometry basis.

The Detector/Motors and Auxiliary connectors are on the sample bay's interior
rear wall, with two rows totaling 15 female contacts each and a separate purge
outlet. This corrects the former exterior rear detector-socket approximation.
No optical accessory is included. Standard cover geometry and installed Smart
accessories are kept distinct. Hinge datum, slider travel, handles, socket sizes,
mounts and rear power/USB details remain unmeasured geometry. This asset needs
interface qualification before a robot can receive manipulation credit; its
static geometry checks alone do not provide that credit.

The selected mechanical reconstruction gives the cover skirts 0.5 mm running
clearance per side and a 1 mm gap between the front lip and bay liner. Its
150 × 100 mm sample opening, 158 × 108 mm sliding pane
and 104 mm travel fit inside the hinged frame. These local dimensions are
inferred, not manufacturer specifications. The simulation import check sweeps
136 cover angles at three slider positions and rejects case interpenetration.

Build with Blender 2.82 using `blender -b --python build.py`, then run
`python validate.py` in the tested ScienceGym Python environment. Four generated
views under `evidence/` show the front, rear, open bay and scan controls.
Manufacturer documents and photos are referenced, not redistributed or used
as textures. The packed label font's license is in `FONT_LICENSE.txt`.
