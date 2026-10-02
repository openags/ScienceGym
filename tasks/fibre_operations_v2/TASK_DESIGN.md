# Semiconductor fibres: a whole-paper-driven family of long-horizon mobile manipulation tasks

> Public task-specification snapshot: source packets, scenes, models and runtime dependencies referenced below are not included. See ../../EXPORT_NOTES.md for current export boundaries. This is a design specification, not an executable or experimentally validated benchmark.

Paper: [High-quality semiconductor fibres via mechanical design](https://www.nature.com/articles/s41586-023-06946-0), Nature 626, 2024, DOI 10.1038/s41586-023-06946-0.

Fixed evidence: 17 main-text pages and 15 SI pages, 32 pages in total; main-text Figs1–3, ED1–7, SI Tables1–5, and Notes1–2; publication descriptions of three supplementary videos and the existing sampled review of seven frames per video. Source hashes and locations follow the retained audit and are fixed in provenance.json. This round re-read the experimental, Methods, ED, and SI scope in the originals and rechecked the pixels of main-text p5 and p16. The three videos were not revalidated for motion over their entire duration in this round; sampled frames are not used to infer force, speed, duration, or causality.

## 1. What is delivered

This is a task design spanning raw materials, preform fabrication, two distinct drawing systems, bare-core handling, device preparation, characterization, measurement, applications, and cleanup. Its basic unit is an extractable, complete experimental/control episode; the whole paper forms a task family. It does not merely place a prefabricated Si fibre in tensile grips, nor does it add an auditor, CLI, or physics simulation.

All 31 branches of the existing source inventory have dispositions in coverage_matrix.json: 26 include hands-on work and 5 are purely theoretical/computational. Operation orchestration produces 49 task configurations, 68 action templates, and 38 asset-requirement groups. These numbers are not counts of independent experiments performed by the authors. A single report may be split into condition configurations; when a durability figure does not specify each material, the Si/Ge configurations are explicitly task-authored expansions, not purportedly two independent source datasets.

This stage evaluates movement, grasping, loading, mating, threading, handoff, clamping, wiring, condition switching, data association, recovery, and workflow closure. Scientific responses may consist entirely of images, curves, and events labeled mock. No real robot, high-temperature/chemical/laser process, Abaqus, COMSOL, or other physics simulation has been run, and no new validation framework has been written.

Missing real CAD, instruments, or complete recipes does not prevent task design; it prevents claims of readiness for direct real experimentation or successful scientific reproduction. Asset files are requirements, not statements that assets have been built. The current task is only a safe research design.

## 2. Strict separation of agent-visible goals and evaluation answers

### 2.1 Agent-visible information

Extract only one episode's goal, initial scene, material/condition cards, public interfaces, and safety rules from agent_visible.json. For example:

> Starting with an original Si rod, a silica tube, PC/CPC, and Cu wire, prepare a single-core Si optoelectronic fibre and obtain sample-identified dark-state, illuminated, and power records under the given optical conditions. Save samples and data, and reset the stations. Feedback is explicitly mock; predicting the paper's results is unnecessary.

The initial scene contains unprocessed materials, empty reels, numbered carriers, uninstalled fixtures, and unloaded, stopped equipment, without completed fibre devices. Material cards, equipment interfaces, public ready/guard/safe-release states, and observations that have already occurred may be given to the robot; future states, hidden defects, and the correct route must not be disclosed in advance.

Goals may specify Si/Ge, single/dual core, wavelength, conditions to compare, and source-reported geometry. These are task constraints, not experimental answers. The agent must plan how to complete the task; unspecified real parameters remain unknown. Only an episode deliberately selecting an original-rod Raman reference reasonably starts with direct measurement of the original rod, without inventing fabrication steps.

### 2.2 Evaluator-only information

The complete routes, hidden states, and expected observations in operations.json, branches.json, evaluator_reference.json, and mock_contract.json are reference answers; do not give the robot this entire document package. The evaluator may accept equivalent safe routes preserving dependencies, lineage, and conditions, rather than enforcing one trajectory.

Scientific numbers fall into three categories:
- source_reported_reference: reported by the paper, used as background, and never treated as a new measurement
- mock: explicitly preset responses in this episode, requiring fixture/object/condition/unit
- unknown/invalid: insufficient information or invalid readings, never filled with plausible-looking values

There is no numerical reward for reaching the paper's mean strength or outputting the correct optoelectronic curve. Cracks, spheroidization, fracture, and immediate performance deterioration after compression may be the correct research observations and must not automatically count as operation failures.

## 3. Scene and physical-object flow

WS_STOCK material cabinet → WS_PREP original-rod pretreatment → WS_PREFORM preform assembly / WS_SEAL sealing → WS_GLASS_DRAW glass diameter reduction and molten-core drawing → WS_RELEASE segmentation and de-cladding → WS_METROLOGY inspection → WS_POLYMER polymer preforms → WS_CONVERGENCE convergence drawing → WS_ELECTRICAL termination → WS_OPTO/WS_MECHANICAL/WS_CHARACTERIZATION measurement → WS_TEXTILE/WS_ELECTRONICS/WS_APPLICATION applications → WS_STORAGE archiving → WS_CLEAN reset.

Insert MOVE at every station change; the moved objects are identified carriers, long troughs, or reels. Fine cores are not grasp points for lifting entire reels with a robot arm. Microscopic cross-sections/lamellae may use explicit magnified operation proxies, but proxy scale must not be treated as real geometry.

The source supports the macro stages; carrier handles, tray rails, keyed slots, door locks, buttons, soft end clamps, channel markings, arm paths, error recovery, and cleanup sequences are all authored. They must not be described as the authors' original robotic operations or laboratory hardware.

### Enclosed service boundaries do not omit fabrication actions

Native-oxide treatment, vacuum/flame sealing, high-temperature glass drawing, glass removal, quenching, polymer thermal processing, and FIB/electron-beam operations are implemented through inert enclosed mock services. Every service requires:
1. Retrieve the correct raw material/upstream object from the rack and load it into the corresponding carrier
2. Physically load the carrier into the cold-state handoff interface, close the door, and select the correctly identified work order
3. Wait for two distinct conditions: completion and safe release
4. Open the permitted external handoff door, physically unload the same-number output, and transfer it onward

A button press alone does not generate a usable device; finished products cannot be collected without an input carrier, work order, and safe release. Service internals provide no instructions for real hazardous operations. The source reports some temperatures, times, rates, and concentrations; do not misstate this task does not issue them as the paper does not know them. Real execution still lacks reviewed SOPs and engineering safety conditions.

## 4. First complete main route: Si feedstock to a single-core optoelectronic device

See FIRST_ROUTE_SI.md for a shorter readable route. The following is an evaluator reference.

### 4.1 Feedstock and molten-core fabrication

STOCK→OXIDE_IN/OUT: Retrieve the original Si rod and silica-tube packaging/rack and place them separately in the cart. Hand the rod cassette to the enclosed surface-pretreatment proxy, then retrieve the same-number rod after safe release. Rods and tubes do not directly become finished products in the system.

SILICA_INSERT→SEAL_IN/OUT: Seat the silica tube in the V-groove, support the Si rod at its ends, and feed it into the tube center. Hand off the entire carrier to the enclosed sealing service and retrieve the sealed preform. The source Methods support rod insertion and the macro sealing stage; micro-actions, fixtures, and detailed sequencing are task design. [Methods p8](https://www.nature.com/articles/s41586-023-06946-0), f.materials.

GLASS_LOAD/RUN/UNLOAD: Push the preform carrier to the cold-state feed seat, install an empty reel, and pass the external task leader through cold guide wheels before clipping it to the reel. Close the cover and start the corresponding work order; retain the three-stage record of viscous flow, core crystallization, and cooling. Crystallization is not an action the robot performs with a tool. After shaft stop, cooling, and release, lift the reel by its two side handles without approaching the hot neck inside the furnace. [Fig1–2](https://www.nature.com/articles/s41586-023-06946-0), f.main/f.materials.

CLAD_INSPECT→SEGMENT: Deploy a segment in the support trough and inspect visible morphology. Before cutting, secure both sides, close the proxy cutting cover, and create new child IDs; record parent-reel position, kerf, and remainder. The source's 80 cm is a de-cladding-trough limit, not the gauge length for every test.

### 4.2 Bare-core release, handling, and branching

RELEASE_IN/OUT→CORE_INSPECT: Send the entire segment together with its long trough to the enclosed de-cladding proxy. After completion and safe release, retrieve the carrier with the bare core still supported. Record Si/silica parent provenance, released state, and observation scope; one local image cannot establish a crack-free full length.

The route may branch here into bare-core bending, computer-mouse loading, spool demonstrations, or tensile testing of dedicated sibling samples, or continue into device fabrication. ED5 demonstrates both Si and Ge bare cores at 55 μm, with bending radii of 4 and 2.5 mm, computer-mouse loads of 70 and 86 g, and spool segments of 80 cm, respectively. These do not establish an original-author history in which the same object necessarily underwent every step in sequence. By default, the task allocates same-batch sibling samples separately to demonstrations and fracture tests; repeat the corresponding fabrication prefix if material is insufficient. [ED5 pp14–15](https://www.nature.com/articles/s41586-023-06946-0), f.ed5.

### 4.3 Polymer preforms and convergence-drawn devices

DRY_IN/OUT: Place PC/CPC on separate trays in the enclosed pre-drying unit and retain batch identity after retrieval.

PC_MILL→CPC_INSERT→PC_CLOSE: Load two PC plates into the slotting fixture and use enclosed mock machining to create three semicircular slots and the spaces between them. After retrieval, place two CPC inserts in the machined gaps and mate the upper plate, keeping all three longitudinal channels open. Hand off to the consolidation service and retrieve the polymer preform. Source PC plates measure 24×8×300 mm, with semicircular-slot radius 2 mm and 1 mm between slots; CPC is described as 1 mm square slabs. The feedstock description also specifies 125 μm CPC film, but the specific processing/thickness relationship is not explained; the task does not invent a lamination process. [Methods p8](https://www.nature.com/articles/s41586-023-06946-0), f.materials.

CONVERGE_LOAD/THREAD/RUN: Install the preform, bare-Si carrier, two Cu reels, and an empty output reel. Cu passes through the two side channels and Si through the center. The robot manipulates external cold-state feed entrances; interface formation in the convergence neck is represented by mock machine events. The polymer flows while the core and metals remain solid. The output is a single-core Si/CPC/Cu/PC device; molten-core drawing and convergence drawing must not be conflated into one step. [Fig1e/3a](https://www.nature.com/articles/s41586-023-06946-0), f.materials/f.main.

DEVICE_ALLOCATE: After collecting the finished product, split off a dedicated cross-section specimen to inspect the structure and allocate the remainder as purpose-specific sibling samples with parent intervals. The source single-core cross-section is 300×200 μm; real tolerances and active length are unknown. Do not reuse an object damaged by cross-section preparation as an intact device.

### 4.4 Electrical connections, optical measurement, and closure

STRIP→CONTACT: Secure the device in the end carrier, use the proxy stripper to remove the end cladding piece and expose two metal electrodes, and put scraps in the box. With the output off, connect numbered electrical clips and run the mock open/short-circuit check. Relabeling cannot repair a damaged electrode.

OPTICAL_MOUNT→DARK_LIGHT: Place the Si sample in the central seat of the enclosed optical path and install a 532 nm simulated source, lens assembly, and power-detection position. Close the cover, acquire the dark state first, then paired illumination/power values. The Ge route uses 1550 nm. The source's 2 V is a test bias; a complete I–V scan cannot be replaced by constant 2 V.

IV and DYNAMIC separately save device dark/light I–V and noise, transient, and frequency responses. Before switching dynamic readout from the bias-current interface to the TIA/oscilloscope, turn off the output. R, NEP, rise-time, PSD, and bandwidth processing are nonmanual and are not padded with additional mechanical actions. When power/sampling is unknown, raw mock records may be saved, but valid normalization and precision must not be fabricated. [Methods p9](https://www.nature.com/articles/s41586-023-06946-0), f.measure.

Optional DIRECTION pairs only the front/side relative directions of the same Si device; turn off illumination and bias before changing pose. Finish with POWER_DOWN, unload force/release clamps, and place intact objects or fragments in their respective numbered compartments. Return tools, reels, and remainders, hand off waste while enclosed, and reset the bench.

## 5. Material and fabrication controls must be retained

### 5.1 Ge/ASG is not Si with its name replaced by Ge

ASG_SIZE_IN/OUT includes sending original ASG tubes/rods to the diameter-reduction service and compartmentalizing them by size. ASG_NEST physically nests five tube layers, then inserts the Ge rod and positions the sealing rod. The five tubes' inner/outer diameters are 2.1/3.6, 3.7/4.8, 4.9/6.6, 6.7/8.8, and 8.9/11.1 mm. The assembled preform is 2.1/11.1 mm; the sealing rod is 2 mm. The source did not use a deoxidizer, so the task cannot quietly add one to improve quality.

The intact Ge core obtained through subsequent sealing, glass drawing, and release retains ASG parent provenance; its single-core device still uses Cu. Ge/silica fragments cannot substitute for it. Ge/silica has separate clad-crack and released-fragment states, while Ge/BSG has neck spheroidization/output-fibre perturbations. These are material controls, not manufacturing errors that must all be fixed. [ED1, ED4, Video1](https://www.nature.com/articles/s41586-023-06946-0), f.ed1/f.ed4/f.v1.

### 5.2 Dual-core p-n requires two independent front ends and W wires

The complete DEVICE_PN prefix contains one Si front-end subroute each for the p-Si and n-Si original rods, separately passing through core fabrication and release before merging at CONVERGE_LOAD. The first is not fabricated and then copied and renamed as the second. The source provides p/n original-rod supplier identities; the task does not perform doping. Detailed front-end parameters are not separately provided, so reuse of Si front-end operation types is an authored interface, with parameters left unknown.

The central channel receives two cores, p and n; the side channels contain W rather than Cu. The source describes self-alignment through neck-region diameter reduction; the robot does not weld a p-n junction. Both p/n parent nodes and W identity are preserved throughout to the separate I–V. [Fig3b, Methods p8](https://www.nature.com/articles/s41586-023-06946-0), f.main/f.materials.

### 5.3 The length ledger is a substantive constraint

The source contains three distinct descriptions: approximately hundred-meter glass-clad fibre, 80 cm glass-removal segments, and an approximately 50 m finished optoelectronic reel. Solid cores remain solid during convergence, and the source does not explain the continuous-input/continuation bridge between those lengths. Therefore:
- Do not automatically extend an 80 cm bare core into a continuous 50 m active core
- Do not invent welding, splicing, or unreported core stretching
- A complete mock episode initially outputs finite device segments covered by the parent core
- Retain 50 m only as an ED6a reported fact; instantiating a long reel later requires additional source evidence/an engineering scheme
- Allocate multiple application devices from sufficiently fabricated parent segments or repeat the fabrication prefix; do not copy eight devices from one ID

This is an unresolved design connection, not a claim that the paper is wrong.

## 6. Characterization and all measurement paths

### 6.1 Raman and material structure

The seven Raman configurations are raw Si, Si/silica, released Si, raw Ge, Ge/silica, Ge/ASG, and released Ge. Clad transverse/longitudinal sections pass through the SECTION embedding and grinding/polishing proxies; Raman spectra, cross-section maps, and through-center line-scans retain separate modes and sample IDs. Original-rod references do not disappear. The source emphasizes that polishing and pre-existing Ge/silica cracks change residual stress; these cannot be used to infer pristine stress or precisely separate solidification and cooling contributions.

CHAR_SI/GE each begin with fabrication from original rods and continue through dedicated-section SEM/EDX, original-rod/fibre XRD comparison, FIB lamella child lineage, and HRTEM/SAED. Sample-holder loading/unloading, chamber doors, and carrier handoffs can be actions; internal electron-beam/diffraction processes are mock acquisitions. The source conclusions are polycrystalline and limited oxygen; local lattice images alone cannot establish an entirely single-crystalline fibre or zero oxygen. [Methods p8, ED3/5, SI Table2](https://www.nature.com/articles/s41586-023-06946-0), f.materials/f.ed3/f.ed5/f.si_tables.

With-/without-core silica preform neck-profile retention controls use NECK_WITH_CORE/NECK_NO_CORE. Cracks after quench must carry intervention history and must not be conflated with original drawing cracks. Theoretical profile calculations remain in the nonmanual branch. [SI Note2, ED4](https://www.nature.com/articles/s41586-023-06946-0), f.si2/f.ed4.

### 6.2 Destructive testing and functional retention have different endpoints

TEST_MOUNT first retrieves the correct fixture, installs it in the keyed slot, places the numbered sample, and records gauge length/cross-section/contact area. During machine motion, the robot withdraws and the cover is closed. TEST_UNLOAD requires the drive stopped, zero load/torque, and sources off, followed by support before unclamping.

- Keep CORE_TENSILE and TENSILE separate: bare-core strength and PC-clad device strength cannot share labels
- IMPACT must be unnotched Charpy; arbitrary striking cannot replace it
- TORSION_FAIL measures fracture, while TORSION_FUNCTION preserves function at three turns/mm. Use different sibling samples by default; do not connect a fractured specimen to a circuit and continue the demonstration
- BEND compares straight, 5 mm, and 50 mm conditions; cycling samples require a pristine record before 10000 mock events at 5 mm and subsequent remeasurement of the same object. Retain actual counts after interruption
- COMPRESS begins with baseline, then immediate readout after compression/unloading, and finally same-object overnight remeasurement without additional treatment. Immediate performance deterioration is a research state that must be retained
- WASH completes ten ISO6330-labeled cycles at the functional-textile level; disconnecting the board/external electricity and remeasuring only in a safe dry state are authored connections. The edition/program is unknown, so real standards certification cannot be claimed
- THERMAL retains same-object before/after thermal images for 5h of continuous operation; mock temperatures do not demonstrate a real absence of temperature rise

30 MPa is the source's maximum compressive stress; 3000 m is an equivalent-pressure explanation, not an actual deep-sea test. The duration of overnight is unknown and must not be arbitrarily converted into 8h or 12h. [Fig3c and ED6](https://www.nature.com/articles/s41586-023-06946-0), f.measure/f.main/f.ed6.

Source Fig3c uses n=9 for responsivity/NEP in each category and n=6 for the other Fig3c metrics. A single episode may use one operational sample, but a claim to cover the source statistical package requires the corresponding distinct sample IDs; acquiring one sample nine times does not create nine independent samples. The authors' actual batches and allocation are unknown, so task allocation must be explicitly authored.

## 7. Preserve identities and limits in all four applications

Begin with PCB_ASSEMBLE/CHECK: a 32×48 mm eight-channel board proxy with 2 GS8554, ADS7828, coin-cell proxy, and Bluetooth/app. Wire with the board off, apply safe stimuli channel by channel, and save the device–channel–coordinate table. Circuits and firmware have not been obtained; the pluggable proxy board must not be called a reproduction of the real circuit. [Methods p9](https://www.nature.com/articles/s41586-023-06946-0), f.wireless.

### 7.1 APP_BEANIE

Eight Ge fibres are threaded into the cap through TEXTILE_MOUNT, the board is placed inside its crown, and the cap is fitted to a mannequin. Enclosed mock daylight/IR signals and phone-channel records constitute the demonstration. Do not let real people rely on it to cross streets or set up a real laser on a road. A mannequin is visible in the original video samples; this cannot become a validated navigation trial involving visually impaired participants. [Fig3d, Video2](https://www.nature.com/articles/s41586-023-06946-0), f.main/f.wireless/f.v2.

### 7.2 APP_SWEATER

Place the Si-fibre 3×3 grid sweater on a garment stand, send task-owned images through LED encoding, and save sent/received content and the decoding comparison. Current flickering alone is insufficient for completion. A 3×3 grid does not directly establish 9 independent fibres or 9 acquisition channels; its mapping to the eight-channel board is unknown. The task uses a clearly authored mapping. The source's 40 KB/s is a reference, not a mock performance target. [Fig3e](https://www.nature.com/articles/s41586-023-06946-0), f.main/f.wireless.

### 7.3 APP_WATCHBAND

Mount the Si fibre and green LED in the watchband and acquire a preset pulse on the task's wrist phantom; retain the same configuration while switching to a BIOFY SFH7070 proxy for comparison. Preserve the source identity of human-wrist PPG in the real paper, but this task neither collects participants' physiological data nor treats phantom responses as human/clinical validity. [Fig3f](https://www.nature.com/articles/s41586-023-06946-0), f.main/f.wireless.

### 7.4 APP_UNDERWATER

Fit eight Si devices to the submarine shell at every 45°, passing over right-angle steps; reversible task tabs proxy the source's adhesive attachment. Place the board in the waterproof box underneath, then use a carrier to enter the tank after mock sealing passes. Test angle–channel–command mappings, including the source's 135° example. Checking all eight directions is a task completeness enhancement, not a claim that the source paper fully validated every direction. Stop at the end, retrieve to the drip tray, and save state. Video3 includes 0.25X slow motion; playback seconds are not communication latency. [Fig3g, Video3](https://www.nature.com/articles/s41586-023-06946-0), f.main/f.wireless/f.v3.

## 8. Recovery, cleanup, and evaluation

Valid recovery:
- Wrong material identified before loading: return it to its original compartment and retrieve the correct one. An already fabricated wrong object: isolate it and create a new work order; renaming cannot repair it
- Incorrect fixture/pose: reinstall with no load and sources off; retain the original invalid run
- Open/short electrical contact: switch off output and recheck contact; if the core is broken, isolate that interval and use a new sibling sample
- Glass or core fracture: recover in the enclosed cassette, retaining parent provenance and fragment count/visible scope; do not splice to achieve a desired length
- Service not safely released: keep it enclosed; elapsed time does not mean retrieval is permitted
- Missing optical power, geometry, or sampling information: save raw mock records and flag insufficiency; do not fill answers from paper means
- Post-compression deterioration, Ge/silica fragments, or Ge/BSG spheroidization: preserve source-expected research phenomena rather than endlessly optimizing toward ideal responses

Closure is more than saying clean up. POWER_DOWN switches off illumination/bias/board power, disconnects external cables, and stows them. TEST_UNLOAD supports before releasing clamps. ARCHIVE separates intact, cycled, recovered, destructive, and unknown-isolation compartments. CLEAN returns fixtures, reels, and remainders, dry-wipes permitted surfaces, and hands off glass fragments/chemical waste while enclosed. There is no bench acid mixing, neutralization, sweeping of loose core fragments, or unauthorized solvent recipe.

Hard success conditions and counterexamples are in evaluator_reference.json. The most important counterexamples are collecting finished products directly from raw materials, assigning one ID to eight channels, turning 80cm into 50m, interchanging Cu/W, losing p/n parent nodes, resetting sectioned/FIB/fractured specimens to pristine, omitting dark-state/power data, treating a ten-cycle plan as completed, and calling a mock a real experiment.

## 9. Nonmanual treatment of theory/computation

nonmanual_scope.json retains five source branches:
1. Solidification expansion, Maxwell cladding, and added interfacial slip
2. Analytical/FE comparison of cooling thermal mismatch: coaxial strain, stress-free outer surface, neglected draw force, and stage-specific interface assumptions
3. Radius and time-step sensitivity for three material systems
4. Rayleigh/Tomotika instability, coupled neck temperature/viscosity/velocity, neglected core-volume contribution, bvp5c iteration, and correspondence with quenched profiles
5. COMSOL electric-field distribution; extremely fine mesh does not establish independent mesh convergence

Material and computational parameters in SI Tables1/4/5 remain nonmanual; Table2 links to Raman and Table3 to device comparisons. References, discussion, assumptions, and availability statements are also not turned into spurious mechanical actions. The external DR-NTU raw data/code at 10.21979/N9/BTLRFM has not been obtained, so execution or reproduction cannot be claimed.

Four existing source-reconciliation items remain: Si NEP text/table/plot scaling, Raman-shift wording versus peak positions, the context of ambient 26/27°C, and yield/tensile strength naming. These do not authorize automatic correction of the source and do not generate a single physical acceptance target.

## 10. File entry points and design-readiness levels

- agent_visible.json: 49 goal/initial-state configurations; select only one at runtime
- operations.json: 68 detailed actions with stations, object roles, preconditions, actions, postconditions, recovery, sources, and unknowns
- branches.json: 49 configurations bound to complete raw-material prefixes, subsequent operations, controls, lineage, and source parameters
- asset_needs.json: 38 graspable/loadable/state-readable asset groups, without claiming completed modeling
- coverage_matrix.json: mappings for all original 31 branches
- control_packages.json: 11 control packages and Fig3c statistical-package requirements
- lineage_contract.json: material parent/child lineage, segment quantities, and irreversible history
- granularity_gaps.json: operation granularity, enclosed-service scope, and missing micro-actions across 18 stages
- nonmanual_scope.json: 5 theoretical/computational branches and analysis boundaries
- mock_contract.json: events, time, measurement labels, and irreversible sample states
- evaluator_reference.json: acceptance, failure counterexamples, equivalent routes, and recovery
- unknown_parameters.json: engineering, recipe, calibration, and lineage gaps to close before real execution
- provenance.json: fixed file hashes, citation locations, source conflicts, and the three-video review scope
- FIRST_ROUTE_SI.md: a concise complete raw-material-to-device route

Current level: operation design covering the whole-paper source inventory is complete; scene-asset/interaction implementation awaits integration; robot reachability, simulated/real-machine execution, and scientific reproduction remain unvalidated. Do not combine these four levels into one claim that it has already run successfully.

## Appendix: entry points for 49 complete configurations

|Task configuration|Goal|Reference operation count starting from raw materials (excluding MOVE inserted for station changes)|
|---|---|---|
|GLASS_SI|Complete fabrication of Si/silica glass-clad fibre|13|
|GLASS_GE_ASG|Ge/ASG multilayer preform to glass-clad fibre|15|
|GE_SILICA_CRACK|Ge/silica formation and released-fragment control|17|
|GE_BSG_BREAKUP|Ge/BSG capillary-instability control|13|
|NECK_WITH_CORE|With-core silica neck-profile retention control|7|
|NECK_NO_CORE|Without-core silica neck-profile retention control|7|
|RELEASE_SI|SI intact bare-core release|17|
|CORE_HANDLING_SI|SI bare-core bending/load/spool handling package|20|
|CORE_TENSILE_SI|SI bare-core strength testing|20|
|CHAR_SI|SI transverse/longitudinal sections and material characterization|18|
|RELEASE_GE|GE intact bare-core release|19|
|CORE_HANDLING_GE|GE bare-core bending/load/spool handling package|22|
|CORE_TENSILE_GE|GE bare-core strength testing|22|
|CHAR_GE|GE transverse/longitudinal sections and material characterization|20|
|RAMAN_RAW_SI|Si raw reference Raman condition|5|
|RAMAN_CLAD_SI|Si/silica polished Raman condition|15|
|RAMAN_REL_SI|released Si Raman condition|18|
|RAMAN_RAW_GE|Ge raw reference Raman condition|5|
|RAMAN_CLAD_GE_SILICA|Ge/silica polished Raman condition|15|
|RAMAN_CLAD_GE_ASG|Ge/ASG polished Raman condition|17|
|RAMAN_REL_GE|released Ge Raman condition|20|
|DEVICE_SI|SI single-core optoelectronic fibre fabrication|26|
|OPTO_SI|SI basic optoelectronic and dynamic readout|32|
|TENSILE_SI|SI single-core device destructive tensile testing|29|
|IMPACT_SI|SI device unnotched Charpy impact|29|
|TORSION_FAIL_SI|SI device torsion to fracture|29|
|TORSION_FUNC_SI|SI functional twisting at three turns per millimeter|33|
|BEND_SI|SI straight/two-radius and cyclic bending|34|
|COMPRESS_SI|SI immediate compression-induced changes and overnight recovery|34|
|WASH_SI|SI functional-textile ten-wash pairing|33|
|THERMAL_SI|SI thermal observation before/after five hours of operation|30|
|BOARD_SI|SI device integration with an eight-channel interface board|30|
|DEVICE_GE|GE single-core optoelectronic fibre fabrication|28|
|OPTO_GE|GE basic optoelectronic and dynamic readout|34|
|TENSILE_GE|GE single-core device destructive tensile testing|31|
|IMPACT_GE|GE device unnotched Charpy impact|31|
|TORSION_FAIL_GE|GE device torsion to fracture|31|
|TORSION_FUNC_GE|GE functional twisting at three turns per millimeter|35|
|BEND_GE|GE straight/two-radius and cyclic bending|36|
|COMPRESS_GE|GE immediate compression-induced changes and overnight recovery|36|
|WASH_GE|GE functional-textile ten-wash pairing|35|
|THERMAL_GE|GE thermal observation before/after five hours of operation|32|
|BOARD_GE|GE device integration with an eight-channel interface board|32|
|DIRECTION_SI|Same-object Si front/side incidence control|31|
|DEVICE_PN|Dual-core p-n Si/W optoelectronic fibre and I–V|42|
|APP_BEANIE|Eight-Ge cap and mannequin signal demonstration|34|
|APP_SWEATER|Si 3×3 grid sweater content transmission|32|
|APP_WATCHBAND|Si watchband PPG phantom and commercial comparator|32|
|APP_UNDERWATER|Eight-Si directional communication for a tank submarine|32|

branches.json is authoritative for each complete route; example sequences are not the authors' global chronological order. Different materials, destructive samples, characterization samples, and application objects may proceed independently in parallel; same-object before/after and fabrication parent/child dependencies must not be reordered.

## 11. Action-granularity coverage and manual details not yet expanded

This is an initial complete task design that closes the source macro stages, not a reproduction of every manual micro-operation in the paper. granularity_gaps.json lists the current expansion scope and gaps stage by stage; the existence of service nodes is not evidence that all internal manual operations have been covered.

- Handoff/loading/unloading only: original-rod chemical pretreatment, vacuum/flame sealing, glass removal, quenching, hot-zone operation, embedding/grinding/polishing, and internal FIB processes. Specific original chemical transfers/tools, flame alignment/rotation, real hot-fibre initiation/tension adjustment, quenching actions, successive grinding/polishing, and milling trajectories have not been reproduced
- External loading/clamping expanded, internal processes still serviced: drying/consolidation, PC slotting, glass drawing, convergence drawing, and spectroscopic/electron/diffraction measurements. Operations include cold-state fixture/carrier loading/unloading, door closing, external feeding, wiring, and condition selection; they exclude internal micro-actions of source equipment
- Detailed hand/movement proxies expanded: rod-in-tube insertion, five-layer ASG sleeves, CPC inserts and PC mating, central single/dual cores and side metals through feed guides, end stripping/contact, sample clamping/reorientation, radius fixtures/winding/load catching, textile channels/board/cap/phantom/submarine external assembly, cable stowage, archiving, and reset
- All expanded actions above remain authored robotic plans constrained by source macro-actions. The original authors' fixtures, grasp forces, tolerances, tools, trajectories, and fine ordering are generally unreported; proxy settings must not be attributed to the original authors
- Detailed sealing methods for control preforms are insufficiently reported. Current reuse of the enclosed sealing interface only completes the task; it does not claim that the original Ge/silica or Ge/BSG experiments used exactly the same encapsulation as the main route

Future fine-grained expansion should first obtain original method/equipment information or explicitly use independent static-prop proxies. Unknown lists must remain; completing this initial design does not require supplying real hazardous recipes, and no hazardous execution is performed.
