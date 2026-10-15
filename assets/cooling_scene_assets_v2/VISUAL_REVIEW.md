# Author visual and geometry review

This record is an author self-review, not independent acceptance. Reference images
and manual illustrations were inspected locally; only new renders and geometry
are distributed. The ten scene roots include four views/configurations of one
custom apparatus family and six commercial instrument reconstructions. They are
not ten completed experiments or ten independently verified devices.

| Object | Evidence used | Implemented features | Unresolved fidelity/operation limits |
| --- | --- | --- | --- |
| Paired cooler | SI Figure 1 photographs, sections and Note 2 | Two foam layers, copper disk, separate film layers/spacer, support tube, polished shield/aperture, Mylar surfaces, slotted frame, hollow uprights, continuous track, retained lead bank | Cover load path, exact reflector datum, actual track curve, sensor contacts, coatings and film mechanics |
| Fixed-band variant | SI Figure 6 and Note 6 | Separate continuous 60 mm band replacing the moving disk | LDPE geometry/configuration distinction and site/date sweep not yet implemented |
| Exploded stack | SI Figure 1 assembly sequence | Separated inspection layers with original component identities | Display-only pose, not a stable physical state or a robot assembly animation |
| Keithley 2425 | Exact 2425 dimension sheet; applicable 2400-series user manual Fig 1-1 | Correct chassis envelope; display, function/operation/range keys, four-wire ports, output/power controls, handle, feet and vents | User manual explicitly illustrates a generic family panel; exact 2425 external mesh, connector centers and actuation remain unverified |
| USB-TC | Manufacturer manual pp7-8,16-17 | Metric enclosure dimensions, 52 terminals, CJC markers and USB interface | Terminal enclosure/placement still requires photographic verification; no electrical backend |
| Thermo A25 | Manufacturer dimensions and controller table | Open bath well, separate lid/handle, reference probe envelope, copper block, display and controls | AC150 head is inferred; probe geometry, liquid level, controller placement and exact front styling are not accepted |
| Cary5000/DRA2500 | Agilent instrument/accessory photographs and site guide | Correct envelope, asymmetric sample bay, separate lid/front door, sphere housing, reference/sample port and plug | Accessory dimensions, holder fit, door trajectory and historical-generation details remain inferred |
| Nicolet6700/IntegratIR | Thermo brochure cover/p2, user-guide sample compartment; PIKE DTGS manual | Split optics housings, central compartment, ribs, scan keys, accessory floor, upward 18 mm port, gold reference/cap, selector, detector cable and purge interface | Overall envelope is an approximation; DTGS variant is a selected hypothesis; angular accessories are not modeled |
| EKO STR-32G | EKO manual Figures 5-1 and 9-2 | Body, azimuth mount, opposed elevation flanges/bolt pattern, GPS, sun sensor and rear connectors | Mount is inferred; no pyrheliometer/pyranometer geometry or tested tracking joints |

Native-to-GLB review found that Blender's default exporter omitted curve wires
and text meshes. `export_geometry.py` now converts those parts explicitly, and
the validator requires every authored part ID to have a mesh in the GLB.
Lossless buffer deduplication preserves all nodes and their part identities.

The task supplies a specific cover-support reconstruction: the lower tensioned
film contacts the PE tube rim and carries the outer spacer while the loading jig
remains retained until the attachment, sag and stability are qualified. This is
`INF_COVER_SUPPORT`, not a source claim. The displayed flat film is an unloaded
approximation and cannot validate that hypothesis. A peripheral retaining fixture
is an alternative whose additional thermal path must be disclosed.

No collision/contact, gravity/support, reachability or thermal/optical simulation
has been run. In particular, a believable render cannot resolve the cover support
gap or qualify a robot grasp. These remain explicit review failures before this
can serve as a validated equipment template for the larger dataset.

Procedural wrinkle/bump shading is native to Blender and has not been baked into
GLB textures; the GLB preserves metric geometry and basic material parameters.
