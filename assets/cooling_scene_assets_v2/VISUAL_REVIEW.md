# Author visual and geometry review

This record is an author self-review, not independent acceptance. Reference images
and manual illustrations were inspected locally; only new renders and geometry
are distributed. The eleven scene roots include five views/configurations of one
custom apparatus family and six commercial instrument reconstructions. They are
not eleven completed experiments or ten independently verified devices.

| Object | Evidence used | Implemented features | Unresolved fidelity/operation limits |
| --- | --- | --- | --- |
| Paired cooler | SI Figure 1 photographs, sections and Note 2 | Two foam layers, copper disk, separate film layers/spacer, support tube, polished shield/aperture, Mylar surfaces, slotted frame, hollow uprights, continuous track, retained lead bank | Cover load path, exact reflector datum, actual track curve, sensor contacts, coatings and film mechanics |
| Fixed-band variant | SI Figure 6 and Note 6 | Separate continuous 60 mm band replacing the moving disk and two nominal 50 micrometre LDPE films | Film optical material/attachment mechanics and site/date sweep remain unqualified |
| Exploded stack | SI Figure 1 assembly sequence | Separated inspection layers with original component identities | Display-only pose, not a stable physical state or a robot assembly animation |
| Keithley 2425 | Exact 2425 dimension sheet; applicable 2400-series user manual Fig 1-1 | Correct chassis envelope; display, function/operation/range keys, four-wire ports, output/power controls, handle, feet and vents | User manual explicitly illustrates a generic family panel; exact 2425 external mesh, connector centers and actuation remain unverified |
| USB-TC | Manufacturer manual pp7-8,16-17 | Metric enclosure dimensions, two 26-pin banks split by CJC gaps, 52 numbered terminals with screws/wire entries, USB interface | Figure2/Table14 topology inspected; connector pitch, wire-entry shape and fine-wire transition remain unqualified; no electrical backend |
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

## October 17 contact audit

The USB-TC p8 diagram and p17 pin table agree on 52 pins, despite contradictory
row-count prose on p8. The new original geometry follows that numbered topology.
Each used CnH/CnL pin has an exact part, screw and wire-entry identity in the task's
`daq_terminal_contract.json`. Probe wire and terminal gauge mismatch is retained
as a required transition-design check, not silently declared compatible.

The separate `COOLER_THERMAL_MAP` root has seven inferred contacts bound to actual
component IDs. Two additional probes correspond to near-axis insulation points,
not unrelated external surfaces. Probe recesses and lead channels have not been
cut into the foam meshes. The contact cutaway removes the front half of selected foam/cover/shield
parts for inspection; the complete parts remain in the native scene and GLB. Positions, junction size, attachment and azimuth remain hypotheses.
The source's plotted temperatures are not rendered as observations.

Terminal wire-entry cavities, driver slots and the USB Type-B shell now have open geometry. Their local dimensions remain reconstruction choices pending connector metrology.

Authored cavity checks: `inspect_interaction_geometry.py` verifies open central wire-entry axes and recessed driver slots at all 52 terminals, plus the open USB shell. The hash-bound receipt is `geometry/interaction_checks.json`. These checks do not qualify insertion clearance, grasping or electrical behavior.
