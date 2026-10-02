# Whole-paper helical acoustic metamaterial operation-task design

See `EXPORT_SCOPE.md` for the public-copy boundary. This directory is a reviewable task design; referenced source archives and Hooke assets are not bundled.

This package converts Zhu et al.'s 2016 paper, Implementation of dispersion-free slow acoustic wave propagation and phase engineering with helical-structured metamaterials, into a task family spanning raw materials, manufacture, cell measurements, lens assembly, field scanning, archiving and reset. DOI: [10.1038/ncomms11731](https://doi.org/10.1038/ncomms11731). It is a hands-on operation-task design for ScienceGym; scientific readings may use explicitly labeled preset responses.

The deliverable covers the paper and specifies operation contracts, but is not an executable simulator. It defines 86 reusable operation templates, 7 hands-on families and 8 task configurations, referencing 6 existing acoustic asset types. Forty cells, sixty speakers and multiple measurement points are loop instances, not additional papers, independent experiments or unique asset types. No robot, printer, real acoustic source, acoustic solver or evaluation program was run.

The historical initial draft FIRST_ROUTE_TRANSMISSION.md and its old review/check reports are omitted from this public copy. This document and the JSON files contain the expanded design. Scientific evidence is retained as main-text/SI references, locators and historical byte hashes; source full text is not bundled.

## 1. Reading guide and file roles

- TASK_DESIGN.md: human-readable design, whole-paper scope and key limitations
- agent_visible.json: release only one selected goal, initial state, public material cards and condition cards; no reference action chain
- operations.json, branches.json, dependencies.json: evaluator-side operations, nested loops and required dependencies; not an exclusive sequence to imitate verbatim
- evaluator_reference.json: independent acceptance rules, failure conditions and test cases; never pass it to the evaluated agent
- specimen_cards.json: geometry/identity cards for Fig1, A/B and L01–L40, retaining all 40 SI Table1 rows
- asset_bindings.json: 63 roles bound to existing parts or unbuilt proxy interfaces
- provenance.json, coverage_matrix.json, nonmanual_scope.json: source locations, full-paper coverage and disposition of purely theoretical/numerical sections
- unknown_parameters.json, granularity_gaps.json: 17 source-unknown groups and execution-critical gaps
- mock_contract.json, lineage_contract.json: preset readings, raw records, condition signatures and entity-lineage contracts
- RELEASE_BOUNDARY.json: actor versus author/evaluator file boundary; no loader implemented
- EXPORT_SCOPE.md: public file/licensing boundaries and absent supporting assets

Use evidence IDs in provenance.json for source locations. Main-text block numbers are zero-based indices in archived blocks.json; SI pages are one-based PDF pages. The authoring review read all research text, captions, Methods and extracted text from all 21 SI pages, and inspected SI pages 4, 9 and 10 visually. It did not newly retrieve the paper, digitize curves or obtain author raw data.

## 2. Scientific identities and evidence granularity

1. Configurations and samples are not one universal geometry. Fig1 has four blades separated by 90 degrees, D=28 mm, d=6 mm, L=41 mm and P=9 mm. Spectrum/pulse sample A has L=12.15 mm, P=7 mm; B has L=13.49 mm, P=7.8 mm. The lens uses 40 distinct SI Table1 P/L pairs; copying Fig1 is insufficient. [a.fig1, a.dispersion, a.si_table]
2. Retain small differences. L02, L15 and L26 lengths are 12.14, 12.12 and 12.15 mm, not one rounded “approximately 12 mm” value. P=1000, 200 and 150 mm are not automatically correctable errors. P is one blade's axial advance over 360 degrees, not the spacing between four adjacent blades
3. Matching geometry does not establish shared physical identity. A matches L26 and B matches L16 in P/L, but the source does not establish reuse of the same objects. The whole-paper task defaults to 43 distinct entities: Fig1, A, B and forty lens cells. This is authored task inventory, not a claim about the authors' sample count. Explicit future reuse must preserve one sample_id, complete prior records and actual location
4. Inherit non-Fig1 dimensions cautiously. Methods supports lens D=28 mm. The A/B section reiterates common D without separately repeating its number; the existing tube asset's D=28 mm is labeled a task choice based on series context and the existing asset. Shaft diameter, blade thickness, outer wall and tolerances beyond Fig1 must not silently become source facts
5. The four-microphone method does not mean four simultaneously installed microphones. Methods describes moving one legacy Brüel and Kjær Type4958 quarter-inch microphone among four positions; SI Fig4 labels positions Mic1–4. Retain both descriptions and use one numbered probe sequentially. Do not substitute 4958-A or automatically create four probes. [a.tube, a.si_tube]
6. The 7 cm evidence has limited scope. SI Note2's separation between the two measurement positions on each side belongs to finite-element validation, not a complete physical-tube positioning specification. The existing asset's four-hole coordinates and 28.2 mm inner diameter are authored. Rebind sample faces, L and hole coordinates after every mounting; they are not original paper dimensions
7. Preserve manufacturing terminology. The material is Somos GP Plus, with equipment/resolution described as SLA300 and 75 micron. The source says laser sintering stereo-lithography. Do not resolve this mixed terminology into another confirmed technology or call 75 micron a verified layer thickness. [a.fabrication]
8. Separate the source self-healing demonstration from this task's evidence. Fig5c is simulated; Fig5d explicitly shows an experiment with a same-size aluminum-alloy obstacle. Cylinder diameter is 4 cm and source coordinates are (z,x)=(1.211,0.175) m. The task may specify this with/without-obstacle comparison, but preset fields do not experimentally re-prove self-healing. [a.obstacle]

Each operation separates the source-supported macro stage, newly authored action interfaces and unknown parameters. Grasps, insertion paths, clamps, cable routing, door interlocks, cleanup and recovery are authored, not recovered fine-grained author trajectories.

## 3. Task family and initial states

All eight configurations begin with sealed numbered inert raw-material proxies, empty build trays and stopped stations containing no task samples. Large plates and housings are laboratory equipment; pre-existing equipment does not imply pre-existing samples or results. The printer proxy accepts closed inert-stock cartridges without real resin exposure, washing or postcuring.

| Configuration | Hands-on objective | Independent result required |
| --- | --- | --- |
| FAB_FIG1 | Manufacture and inspect the Fig1 example | Raw-material-to-cell identity chain and archive location |
| TRANSMISSION_PAIR | Manufacture A/B and measure transmission spectra | Raw records for every sample, frequency, two loads and four positions |
| PULSE_PAIR | Compare air/A/B pulses | Three separate waveforms with the same receiver position and trigger conditions |
| CELL_40_CHARACTERIZATION | Manufacture and characterize forty distinct cells | Number-indexed transmission and phase records at 4170 Hz |
| LENS_BUILD | Manufacture, characterize and assemble the full lens | One-to-one mapping of forty slots/entities and assembly records |
| FIELD_BASELINE | Prepare lens, waveguide and synchronized array, then scan | Obstacle-free local-pressure records and mask over a limited region |
| FIELD_OBSTACLE_COMPARISON | Compare with/without obstacle on the same grid | Two independent field datasets and obstacle identity/placement evidence |
| WHOLE_PAPER_PRACTICAL | Connect the whole paper's practical operations | All required records, complete archiving and reset |

Exact spectrum grids, amplitudes, gains, triggers, pulse envelopes and scan-point tables are not fully reported; public condition cards must supply explicitly authored values. Preparation independent of missing inputs may proceed, but guessing values does not constitute a full reproduction. Task completion and scientific-result quality remain separate.

## 4. From raw stock to identifiable cells

Each task work order defaults to one inert simulated cell. This is authored discretization, not the paper's print-batch record.

1. Read full material name and lot; take a closed stock cartridge, empty tray and numbered carrier, place them in transport slots and record symbolic input allocation
2. Place the tray on the registration dock, bind geometry_id and tray slot, and open the printer-proxy door only in stopped/safe state
3. Support and insert stock and tray into their keyed docks, operate latches and verify the complete P/L work order rather than merely the name “helical cell”
4. Withdraw hands, close the chamber, read the interlock and start; independently observe processing completion and safe release before opening/unloading
5. Place the tray in the closed postprocessing handoff drawer and receive a receipt; real washing, curing and support-removal recipes remain unknown
6. Support the external sleeve on the release dock, release each part and place it in a padded carrier; do not grip thin blades or treat a display cutaway as a detachable shell
7. Inspect identity and defined envelope, separating source dimensions, authored tolerances and unchecked items; quarantine damaged/wrong parts
8. Attach entity cards outside carriers and save raw lot, work order, tray slot, geometry and entity IDs; return unused stock and reset the empty chamber

Closed-service internal manufacturing/postprocessing may be preset, but input loading, work-order selection, opening/closing, output receipt and identity checks cannot be bypassed by a “generate sample” button.

## 5. Impedance tube and two-load/four-position acquisition

The sample occupies 0<x<L. The source establishes an acoustic source at one end, an open or rubber-plug-sealed opposite end, and pressure measurement at four positions. Task interfaces, seals and clamping forces require separate authoring. [a.tube, a.si_tube]

- Stop output, support and open the sample interface, insert the correct cell using face labels, secure it and close the interface
- Connect DS345 FUNCTION, amplifier input/output, tube-end source and acquisition roles according to a port diagram. The tube speaker model is unspecified and must not automatically become the PUI array model
- Set DS345 with buttons/numeric input and read back frequency/units. An example asset display or button displacement is not a valid configuration receipt
- Physically move the rubber plug to establish open or rubber_sealed state; changing a data label is insufficient
- For each load, support the same probe, unclamp, lift along the hole axis, reseal the previous hole, move to the next, insert axially, secure and check the other three holes
- Read stability, enable output and acquire the current point; save and stop output before repositioning. The probe cannot move horizontally through tube walls
- Bind every raw record to sample_id, frequency, load, hole, scene coordinates, probe_serial, phase reference and acquisition card. source_active, signal_detected and record_valid are distinct events
- Each sample/frequency requires two loads times four positions: eight valid records with a consistent reference. Missing holes/loads or inconsistent phase references produce incomplete and a missing-measurement list
- PULSE Reflex Core is a processing role only. Name complex transmission t, magnitude |t| and energy ratio |t|² separately according to the contract. Without author raw waveforms, use clearly labeled mock data
- After each sample, withdraw the probe, cap holes, support/unload the cell and return it to its original carrier. Every geometry instance requires actual mounting/unmounting events

Record SI analytical/numerical validation separately; its complex speed, density, thickness and 7 cm spacing are not physical instrument settings.

## 6. Pulse controls cannot be replaced by transmission spectra

The source compares acoustic pulses centered at 4170 Hz through air and A/B. It reports approximately 4.745 ms in air, additional A/B delays of 0.206/0.216 ms, and effective speeds of approximately 50.3/52.8 m/s. These are source references, not target rewards the agent must reproduce. [a.pulse]

First remove all metamaterial and establish a genuinely empty path, fixing the same receiver probe in the public fixture. Preserve receiver coordinates, trigger, envelope and sampling cards across air/A/B. Stop output and exchange samples through an independent interface without moving the receiver. Trigger/save raw waveforms separately for each condition; remove the receiver only after the comparison.

Use one condition-card-defined arrival-time rule and retain ringing, clipping and invalid records. Sample-speed calculations must include propagation time through the short segment formerly occupied by air; do not simply divide L by additional delay. Visible receiver displacement requires a new valid matched comparison or a report that the comparison is invalid; do not combine mismatched waveforms into a delay claim.

## 7. Forty-cell characterization and lens assembly

Characterize all forty cells individually at 4170 Hz before numbered holder insertion. SI Fig9 specifies 6 cm center spacing. [a.lens_design, a.si_lens]

Place the holder on a long support first. For each slot, read its number and the cell's complete P/L/entity label, take the support sleeve, insert along the task path, close the clamp, read seating feedback, withdraw the sleeve and submit slot_id-to-sample_id mapping. Check all forty identities, directions, omissions, duplicates and characterization references. Transport the assembled lens in a long carrier supporting both ends, never by gripping one cell.

The source's phase design and parabolic trajectory are given design inputs, not a request for a new phase optimizer. A phase table supports ordering/comparison but cannot replace each entity's mounting, measurement and slot-insertion events.

## 8. Large-plate waveguide and sixty-source array

The source waveguide has two parallel 3 m x 3 m x 15 mm plates, a 28 mm gap and absorbing-foam boundaries. Sixty AS04004PR-R speakers, diameter 40 mm, form a line array at 44 mm spacing, synchronously driven by one DS345 and a laboratory amplifier. [a.field]

Move large plates only through task-defined support/lift interfaces. Unknown weight, material and load capacity do not justify ordinary-arm lifting. The robot operates spacers, edge catches and lift proxies from outside. Hiding the upper plate in a viewer does not open/remove the physical plate.

Every speaker has a speaker_id. Individually grip rear housings/frames without pressing cones, seat them, close proxy retaining rings, connect inert prefabricated wiring, provide strain relief and check channels. Real series/parallel topology, soldering, amplifier load and levels lack source support and must not become invented wiring instructions. Before changing from tube measurement to array use, stop output and physically disconnect the tube-source cable. The single MIC01 must leave its tube/pulse fixture and travel to the field scanner; it cannot occupy two stations. Finally check the same-signal/phase contract for all sixty sources. A master switch cannot replace these individual steps or establish real plane-wave uniformity.

Neither the source nor existing assets defines the 40 mm-speaker-to-28 mm-gap coupling adapter. An explicitly authored, checkable interface is required before field tasks can start.

## 9. Hard boundaries for probe access and scanning

The source measures pressure pointwise in the x-z plane over 2.3 m x 1.0 m. SI Fig10 says only part of the main lobe was scanned because of translation-stage limits. [a.field, a.si_scan]

Do not assume a robot arm fits inside a 28 mm gap, or that a narrow probe plus shaft/cable can pass through the upper plate. The design mounts the probe from outside and controls a scan support, but entry, shaft, cable routing, collision/reachability and coordinate frames still need explicit scene contracts. Their absence blocks execution regardless of an attractive waveguide mesh.

The existing scanner displays only 1.7 m long-axis and 2.0 m lateral travel; neither proves coverage of the source's 2.3 m dimension. The source does not fully specify rectangle-axis assignment, origin, endpoints, spacing or speed. Supply an authored point table, source-to-scene transform and reachability mask; mesh Y-up/Z-up conventions are not paper x/z coordinates.

Use external controls for pointwise movement, await position readback and stability, then acquire one local-pressure record. Every point includes coordinates, frequency, probe, lens version, sixty-source version, obstacle state, units and validity. After interruption, retain the acquired prefix, recheck conditions and resume missing points only; changed conditions require a new run_id. Do not fill unmeasured points with zero or claim full-field coverage.

PULSE Labshop is a processing role. Produce pressure-amplitude maps with coordinate masks. Preserve the paper's acoustic intensity wording as a source description, but without supported calibration/conversion do not claim real acoustic energy-flux intensity.

## 10. Obstacle conditions and paired comparison

Acquire the obstacle-free baseline first, then stop acquisition/sound and dock the probe. Use a defined plate-opening or separate access interface to support the 40 mm-diameter aluminum-alloy cylinder, map source (z,x)=(1.211,0.175) m into scene coordinates, secure it and recheck plate clearance/probe access. Diameter does not establish height, positioning tolerance or fixation. The existing asset's 28 mm height is authored.

Acquire the obstacle condition using the same grid, frequency, lens/array configuration and normalization. Preserve both independent datasets and compare only common valid regions. Reporting that two preset conditions were correctly acquired and compared is valid; claiming that these measurements again prove beam self-healing is not. Preserve the source Fig5d's experimental identity.

At completion, physically remove the obstacle, withdraw the probe, open the upper plate with support and unload the lens. obstacle visibility=false is not a return-to-carrier event.

## 11. Independent agent goals and evaluation

The evaluated agent receives goals, initial state, geometry and public conditions, and chooses feasible grasps, order and recovery. Reference routes, future readings, hidden faults and acceptance assertions stay evaluator-side. Accept valid alternatives satisfying dependencies rather than requiring fixed action text.

Evaluate environment-side entity locations, constraints, port graphs, stock-generation events, acquisition receipts and raw-record checks. Agent claims, function calls and attractive plots alone do not establish success.

Tests include a missing load/hole, changed probe serial, moved pulse receiver, swapped L02/L26 slots, unconnected source59, absent probe entry, out-of-travel points, reversed (z,x), and interrupted scanning. Faults need observable signs or public checks; do not penalize invisible hidden facts.

Complete lawful mock records may pass procedural evaluation even without paper trends. Conversely, perfect agreement with paper numbers fails if physical operations or raw records are absent. For missing critical interfaces, a safe stop and precise missing-input report may earn partial credit, but the overall result is partial_with_valid_blocker, not experiment completion.

## 12. Archiving, reset and current gaps

Archive samples in matching carriers or the complete lens holder, preserving one current location per entity. Quarantine damaged/unidentified objects. Append and retain read-only raw attempts, save derived results separately, and preserve failures/unmeasured masks. Disconnect by gripping connector housings; return tools, end plugs and hole caps to slots. Put inert remnants in covered simulated-waste compartments without inventing real resin cleaning/disposal recipes.

Finally verify stopped output/acquisition/motion, a docked probe, supported plates and agreement between archive index and physical locations. The six existing asset types are appearance/component-identity references only. Printer/postprocessing proxies, dynamic fixtures, interactive cables, scan entry, coupling adapters and independent feedback remain unbuilt; display transforms are not valid constraints.

Historical author checks and this static review checked operation/branch/source/unknown references, all forty SI parameter rows and archived asset identifiers. The public copy corrects A/B frequency-domain scope, loop-input references, scan-point placeholders, branch lineage rules and reference-asset backlinks. Old hashes and asset-availability reports do not validate this transformed copy. The whole-paper operation design can be handed off, but dynamic execution has not passed. Before instantiation, prioritize probe entry/full travel, large-plate support, the 40 mm-to-28 mm coupling adapter and sensor/constraint contracts, then perform action-level validation.
