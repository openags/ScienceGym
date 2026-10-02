# Thermoelectric Devices: A Whole-Paper-Driven Family of Long-Horizon Mobile Manipulation Tasks

> Public task-specification snapshot: source packets, scenes, models and runtime dependencies referenced below are not included. See ../../EXPORT_NOTES.md for current export boundaries. This is a design specification, not an executable or experimentally validated benchmark.

Source: [Composable neural emulators accelerate thermoelectric generator design](https://www.nature.com/articles/s41586-026-10223-1), Nature 652, 643–649 (2026), DOI 10.1038/s41586-026-10223-1.

This round reread the retained text of the 12-page main paper and 16-page SI, all figure captions, and Methods, and reexamined the pixels of Fig.3 on main-paper PDF p4 and Fig.21/22 on SI PDF p13. Source locations, file hashes, and asset provenance are recorded separately in provenance.json; not all plots have been digitized point by point. The initial draft FIRST_ROUTE_PAIRED.md is retained unchanged and is not a source authority; this document and its accompanying JSON supersede its incomplete scope.

## 1. Scope of This Deliverable

Starting with raw-material portioning, the scope includes three material routes, different interfaces/sintering/cutting orientations, segment joining, single-material-leg controls, a two-couple module, spatial contact resistance, and current/thermal-boundary measurements, along with recovery, archiving, and cleaning. All 7 branches in the source inventory have an explicit disposition: 6 contain hands-on work, and 1 purely computational family is expanded separately into 12 nonmanual records.

The task is organized into 15 configurations and 57 operation templates. The 6 manufacturing configurations correspond to three powders and three sintered billets; the 9 measurement configurations correspond to 6 material-by-length power comparisons, 1 contact scan, 1 segmented efficiency sweep, and 1 two-couple module sweep. These are not 15 papers, 15 independent experiments by the original authors, or 15 executed robot trajectories.

This stage uses explicitly labeled inert mock materials and preset scientific readings. No real equipment operation, thermal/electrical/powder processing, robot trajectories, physics simulation, TEGNet execution, or COMSOL execution has taken place. Existing reference assets remain unchanged.

## 2. Give the Agent a Goal, Not the Complete Reference Answer

Give the agent only one selected episode from agent_visible.json: its goal, raw-material cards, initial state, condition constraints, and public interfaces. For example:

> Starting from sealed raw materials of the correct compositions, empty jars, and unloaded stations, prepare a two-couple n–p thermoelectric module and obtain mock current, voltage, and cold-side heat-flow records associated with the sample identity under the specified thermal boundaries. Preserve unknown calibration status, save the objects and data, and reset the stations.

The initial state must not supply a finished module for the robot to measure directly. Materials, empty dies, unloaded fixtures, and empty measurement chambers may be prepositioned; processing outputs appear only after the physical inputs, correct work order, and equipment events have been completed.

operations.json, branches.json, evaluator_reference.json, and hidden mock fixtures belong to the evaluation side. Do not give the agent the complete process chain, hidden faults, and source answers of 9.3%/8.7% and 4.0/4.9 μΩ cm² together. Material and condition cards may contain source-reported dimensions/temperatures/durations as task constraints; unreported values remain unknown or explicitly authored, rather than being silently filled in as paper parameters.

Success primarily evaluates retrieval, support, transfer, alignment, loading/unloading, clamping, wiring, condition changes, data association, and closeout. Equivalent paths that are safe and preserve lineage are acceptable; scoring is not restricted to a single button sequence. Scientific curves may be preset, but pressing a button alone does not constitute valid acquisition.

## 3. Boundaries Between the Scene and Source Facts

WS_STOCK → WS_PREP/WS_ATMOSPHERE or WS_MELT → WS_MILL → WS_POWDER → WS_DIE/WS_SPS → WS_CUT → WS_JOIN or WS_MODULE → WS_CONTACT/WS_PEM → WS_DATA → WS_STORAGE/WS_CLEAN.

A MOVE must be inserted between different stations: grasp the numbered carrier's handle, move between stations, and place it in the destination slot; do not teleport objects. Small legs may have explicit enlarged manipulation proxies, while scientific geometry remains recorded as millimeter metadata; the enlargement factor must not be treated as the paper's sample dimensions.

The source supports the materials, macro-scale processing, and measurement categories. Transport carts, lid slots, die keyways, fixture knobs, cold-state handoff doors, proxy buttons, grasp poses, atmosphere certificates, stability events, and recovery and cleaning micro-actions are all designed by the task authors; they must not be represented as the original authors' actual operations.

Enclosed services still retain physical operations: load the correct input, close the external handoff interface, submit an object-bound work order, wait for processing to complete, then wait for safe release, open the permitted external port, and support and unload the output with the same lineage. High temperatures, pressing, powder dynamics, evacuation, and scientific responses are replaced by mock events. Closing off service internals does not establish that all manual micro-actions have been replicated; granularity_gaps.json lists the gaps stage by stage.

## 4. The Three Manufacturing Routes Are Not Interchangeable

### 4.1 P: MgAgSb Is Not an Additive-Free Pure Material

The full designation in Methods is MgAgSb + 0.625 wt% C18H36O2. The additive's specific isomer, purity, and addition sequence are not reported; do not automatically infer its name from the molecular formula. The Mg, Ag, and Sb raw materials and the additive all retain separate batches before forming the powder's child lineage. [Materials synthesis, main-paper PDF p8](https://www.nature.com/articles/s41586-026-10223-1.pdf#page=8)

STOCK/PREP_NEST/PORTION: Open each raw-material bottle separately, transfer material with a simulated scoop into a numbered tray/jar, and close and return each bottle individually. The source provides no actual batch mass, ball-to-powder ratio, or weighing tolerance; the task manifest explicitly assigns mock portions. Unknown portions are not converted into an executable real-world recipe.

VIAL_CLOSE/AR_HANDOFF/AR_RETURN: Close the jar and place it in the handoff box, load the box into the outer drawer of the Ar proxy, close the door, wait for a trusted sealing status, and retrieve it. The paper reports ball milling for 5 h in Ar; the appearance of an ordinary closed jar proves neither gas tightness nor an Ar atmosphere. Atmosphere status is supplied by environment events; the agent must not set it to true itself.

MILL_OPEN/SEAT/CLAMP/CLOSE/RUN/UNLOAD: Open the latch and lift the cover, support the jar while placing it in the task clamp seat, turn the clamping proxy, withdraw and close the cover, and select the 5 h work order for this batch. After completion, the equipment must stop and release; support the jar before loosening the clamp and retrieving it. Powder discharge comprises opening, transfer, portioning, and closing within the enclosed proxy area, retaining a remaining-material ledger.

### 4.2 N: The Abbreviation Hides In and Te

The main paper's abbreviation Mg3Bi1.4Sb0.6 actually corresponds to Mg3.2In0.02Sb0.595Bi1.4Te0.005. In/Te, excess Mg, and the Sb fraction must not be removed from raw-material, powder, or final-module lineage. N also undergoes ball milling in Ar for 5 h, but its powder, jars, and work orders differ from P's. The author-contribution statement indicates that N material was supplied by collaborators; the task's unified workbench must not be treated as evidence that the original work was manufactured in place by a single person. [Main-paper PDF pp8–9](https://www.nature.com/articles/s41586-026-10223-1.pdf#page=8)

### 4.3 B: Bi0.4Sb1.6Te3 Is Melted into an Ingot Before Ball Milling

B's Bi/Sb/Te is first portioned onto a tray, loaded into a quartz tube in a V-groove rack, and handed to the encapsulation proxy. TUBE_LOAD/MELT_LOAD/RUN/UNLOAD explicitly includes picking up the tube, loading material, cold-state loading, closing the door, waiting for completion and cooling, retrieving the rack, obtaining the ingot with the same ID through the tube-opening proxy, and then placing it in the B-specific ball-milling jar. The source reports melting at 1273 K for 12 h, followed by ball milling of the ingot for 1 h. [Materials synthesis, main-paper PDF p8](https://www.nature.com/articles/s41586-026-10223-1.pdf#page=8)

Quartz-tube dimensions, sealing method, furnace type, atmosphere, cooling, and actual tube-opening/ingot-retrieval actions are unknown. Do not add vacuum tube sealing, quenching, or crushing, or unconditionally transfer the P/N Ar atmosphere to B. B must not skip ingot melting and directly reuse the P/N 5 h ball-milling route.

## 5. Die Loading, Sintering, Cutting Orientation, and Subsamples

DIE_ASSEMBLE: Install the lower-punch and die-sleeve proxies and establish a pressing-axis orientation identifier that cannot be lost. P_STACK places Sb, P, and Sb layer by layer; B_STACK loads only B, without interface material. N uses stainless-steel interface powder; the task implements this as proxy layers at both ends, but their specific geometry and thickness are not reconstructed from the source.

DIE_CLOSE/SPS_LOAD/RUN/UNLOAD/DEMOLD: Insert the upper punch, secure the tray with stops, load it through the correct equipment's external interface, close the door and start, wait for process completion and cold-state release, retrieve the tray, return to the demolding slot, and remove each punch/die sleeve while supporting the billet. Source conditions:

- P: SPS-322LX, 573 K, 5 min, 60 MPa, Sb interfaces
- B: SPS-322LX, 693 K, 10 min, 60 MPa, no interface material
- N: SPS-1080 System, 973 K, 10 min, 60 MPa, stainless-steel interfaces

These are source work-order labels, not approved real-equipment SOPs. Die material/geometry, liners, heating and cooling, pressure trajectories, and demolding forces remain unknown. [TE generator fabrication, main-paper PDF p8](https://www.nature.com/articles/s41586-026-10223-1.pdf#page=8)

CUT_FIXTURE/SELECT/RUN/UNLOAD: Retrieve the orientation seat, place the billet, align its orientation, support both sides, select dimensions, withdraw hands and close the cover, start enclosed cutting, and place each leg into a separate compartment after stopping and release. P's Sb/P/Sb piece is cut parallel to the pressing direction, whereas B is cut perpendicular; N's cutting orientation is unreported and must not inherit the P rule. The source does not fully specify the local cutting-plane/long-axis engineering interpretation of "cut parallel/perpendicular"; the task fixture implementation is separately labeled authored.

Cutting outputs have independent child IDs, parent billets and original positions, orientations, dimension sources, and remaining-material and damage states. Manufacturing four legs requires two distinct P legs and two distinct N legs; the same ID must not occupy four slots. Actual yield/mass is unknown; the mock maintains only explicitly assigned portions and quantity ledgers.

## 6. Segmented Legs, Single Legs, and Two-Couple Modules Have Separate Routes

### 6.1 Segment Joining Includes Two Types of Interface

GA_SETUP loads P and B into the alignment fixture separately, with P's Sb end facing B's bare end. GA_APPLY retrieves the numbered inert Ga–In applicator proxy, transfers a simulated layer to the mating surface, and returns the tool. SEG_JOIN aligns the common axis, brings the pieces together against the stops, and retrieves them with their support after stabilization.

The final structure is Sb/P/Sb/Ga–In/B; MgAgSb/Bi0.4Sb1.6Te3 is only an abbreviation. Ga–In does not replace the Sb interface, nor is it a known solder for the two-couple Cu electrodes. Amount, Ga/In ratio, wetting/pressure/dwell, and actual surface treatment are unreported and must not be written as processes used by the authors. [Main-paper PDF p8](https://www.nature.com/articles/s41586-026-10223-1.pdf#page=8)

The source selects a P length of 0.5 of the total length. Interface thickness and whether the reported total length includes interfaces are unclear; do not use an additional "40 μm" to split the source length into exact core lengths. The task binds component dimensions separately during the segmented phase: finished pieces of 6.7/8.8 mm each use two half-length proxy components, and the 8 mm task with unknown source geometry uses 4+4 mm; interfaces are logical surfaces within the mock envelope and add no extra length. This is a task allocation implementing the 0.5 ratio and total-length constraint, not known actual core thicknesses.

### 6.2 Six Experimental Power-Density Comparison Configurations

In Fig.3i, the B single leg, P/B segmented leg, and P single leg each have total lengths of 6.7 and 8.8 mm, yielding six configurations. Their experimental cross sections and the specific thermal boundaries in that panel are not separately provided. The a=b=3.5 mm and c=7/8/9/10 mm in Fig.3d/e are computational dimensions and must not be transplanted into the physical sample geometries. [Fig.3, main-paper PDF p4](https://www.nature.com/articles/s41586-026-10223-1.pdf#page=4)

To make task clamping and controls executable, the six mock configurations use an explicitly authored 4×4 mm cross section and matched Th=473 K/Tc=293 K conditions; this does not claim to reconstruct the original boundaries of Fig.3i. The source lengths of 6.7/8.8 mm are retained. Termination/sample-preparation details for the single-material controls are not separately described. The task reuses the corresponding component-manufacturing prefixes but labels this as task reuse, without elevating it to the original authors' single-leg SOP.

### 6.3 Segmented Efficiency and Contact Scans Do Not Borrow Unreported Dimensions

The Fig.3j efficiency sweep uses Th=373, 473, 573, 593 K and Tc=293 K. The sample dimensions in this panel, and whether samples from Fig.3i were reused, are unknown. CONTACT_SEG and EFFICIENCY_SEG use explicitly authored 4×4×8 mm proxies with independent sibling lineages; the two panels are not forced into one purportedly validated sample. The horizontal axis of the contact-scan plot is not treated as a complete geometry measurement either.

### 6.4 The Two-Couple Module Preserves the P/N Dimension Difference

Each of the two P legs is 3.3×3.3×6.6 mm, and each of the two N legs is 2.9×2.9×6.6 mm. Do not duplicate and scale identical legs into an "approximately two-couple" module. MODULE_BASE retrieves the AlN plate and places the lower copper pieces and terminals; MODULE_LEGS places P1/N1/P2/N2 one leg at a time; MODULE_BRIDGE aligns the upper copper bridges and connects them with inert proxies; MODULE_RELEASE supports the plate, removes temporary positioning parts, and retrieves it into the transport rack. [Main-paper PDF pp5–6, 8](https://www.nature.com/articles/s41586-026-10223-1.pdf#page=6)

The source specifies AlN plates and copper electrodes, with an electrically series/thermally parallel architecture; exact copper-piece topology, plate thickness, joining method, thermal-contact materials, and assembly loads are unknown. The existing mesh's 10×10×0.8 mm AlN, 40 μm end skins, and copper topology are asset assumptions made during benchmark design, not paper-reported manufacturing dimensions. Module-explosion display controls must not be treated as real, repeatable, nondestructive desoldering.

## 7. S1331: The Actual Task Is to Acquire Resistance Along Position

CONTACT_MOUNT places the complete segmented sample horizontally in its seat, clamps it, registers the B→Ga–In/Sb→P spatial direction and origin, and connects task leads with the source off. CONTACT_PROBE moves the probe to the first point and lowers it until publicly visible contact feedback appears. CONTACT_SCAN acquires x, R, units, sample, and run number at every point, then raises, moves, and lowers the probe, preserving order across interfaces. At the end, stop the source, withdraw the probe, disconnect leads, and support the sample while unclamping and retrieving it. [Fig.3h, main-paper PDF p4; SI Fig.21, PDF p13](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-026-10223-1/MediaObjects/41586_2026_10223_MOESM1_ESM.pdf#page=13)

The actual probe count/circuit, contact force, current, spacing, position step, calibration, and fitting details are unknown; the integer grid from 0–8 mm in the JSON is only a mock coordinate system. Do not infer a four-probe SOP from a single apparatus photograph.

Sb/P and B/Ga–In/Sb are different interfaces within the same piece. The source contact resistivities of 4.0 and 4.9 μΩ cm² are reference facts, not two button values directly returned by the instrument. The raw quantity is R(x); deriving resistivity requires an interface-resistance processing method and area. If area/calibration is missing, save the curve and mark it unknown instead of filling the results with paper values.

## 8. Mini-PEM: Loading, Vacuum, Thermal Boundaries, and Pointwise Acquisition

PEM_PREP opens the chamber only when it is unloaded, source-off, cold, and safely vented, and installs the appropriate lower support for a leg/module. PEM_MOUNT supports the sample while placing it on the lower contact, then lowers the upper contact to task-ready status. The segmented sample's P/MgAgSb end is on the upper hot side, and its B end is on the lower cold side, consistent with the SI21 photograph. Actual loading force and thermal-interface materials are unknown.

PEM_WIRE connects the numbered ports one lead at a time and arranges the wiring, checking polarity/channels/calibration. PEM_SEAL closes the chamber, withdraws, starts the mock vacuum, and waits for the environment to provide vacuum_ready. PEM_BOUNDARY selects the conditions and waits for stability; the agent cannot declare vacuum/stability successful itself. The source measurements use a lower end at 293 K and an upper end at 373–593 K; Fig.3j and Fig.4h/i explicitly show the four conditions 373, 473, 573, 593 K. [TE generator measurement, main-paper PDF p8](https://www.nature.com/articles/s41586-026-10223-1.pdf#page=8)

Within each thermal boundary, PEM_CURRENT selects one task current point and waits for point-ready status, then PEM_ACQUIRE acquires the actual mock I/V/Qc (or raw heat-flow sensor voltage). Traverse the current points before changing thermal boundaries and restabilizing. The source current grid/dwell criterion is not provided; plot-axis ticks must not be treated directly as the complete experimental step sequence. Changing the boundary still involves the same object and a new condition ID, not a new independent manufacturing n.

At the end, PEM_POWERDOWN stops output/heating and cools; PEM_OPEN waits for trusted cold-state, venting, and safe-door-opening status; PEM_UNLOAD then disconnects leads, supports the sample, releases the upper contact, retrieves the sample, removes the lower support, and closes the empty chamber. Elapsed time does not mean an object can be touched; release must not be omitted simply because the mock program has finished.

## 9. Calculations Are Data Processing, Not Invented Manual Actions

P=I×V; η=P/(P+Qc). I in A and V in mV yield mW; units must be unified before calculating efficiency with Qc. P/area is valid only when a source-supported or explicitly mock cross section is registered; the module's external plate area must not be treated as the leg cross-sectional area. Take Pmax/ηmax over sampled points for each condition; without fitting, do not claim to have found the exact extrema of a continuous curve.

Heat-flow units require particular fidelity: Fig.2a labels Q0 in mV, Fig.2b labels it in W, and Methods describes cold-side heat flow; this is an unresolved inconsistency in the source figure labels. Fig.2 is computational and therefore does not establish that Mini-PEM outputs a particular mV sensor signal. If the task supplies a raw mV heat-flow channel without calibration, preserve the raw signal and leave η unknown; only explicitly calibrated mock Qc[W] supports mock efficiency. The two example types are separated in mock_contract.json, without silently changing mV to W.

The 9.3% segmented efficiency, 8.7% two-couple efficiency, and 4.0/4.9 μΩ cm² contact resistivities are not numerical rewards for mechanical operations. A "correct number" without a valid acquisition event fails; an unknown or poorer result after valid acquisition does not automatically constitute an operation failure.

## 10. Disposition of All Purely Computational and Literature Content

nonmanual_scope.json retains 12 categories: model data/training, material generalization, out-of-domain and new materials, segmented geometry, constant heat flux, electrical/thermal contact parasitics, n–p geometry, couple-count scaling, complex combinations, and literature comparisons. These cover the computational portions of main-paper Fig.1–4, ED1–3, SI1–20, and 22–26; SI21 separately belongs to the actual measurement apparatus.

- Scaling to 1/2/4/8/16/32 couples is a computation in SI22; only actual manufacture of the two-couple module is reported
- Mg3Sb1.5Bi0.5–SnS, segmented n legs and GeTe, three-segment and segmented p legs, and all material combinations do not become additional physical specimens
- The ED3 thermal-contact-resistivity sweep does not generate an unreported experimental thermal-resistance instrument
- zT/PF curves do not permit the task to invent actual Seebeck/XRD/thermal-conductivity measurement procedures
- Literature devices/material properties are references and cannot generate samples described as "new controls made in this paper"
- The computational convention of converting n/p voltages to positive values does not authorize altering measured polarity

## 11. Recovery and Cleaning Are Actions Too

Before adding the wrong material, close its lid, return it, and retrieve the correct material; after addition, isolate the mixture and start a new batch without deleting parent materials. If clamping is insecure, stop/release first, then support and reinstall. After cutting in the wrong orientation, rotating a label cannot restore the piece; isolate it and manufacture it again. An incorrectly joined Ga–In layer, broken leg, or unknown damage after bonding cannot be repaired nondestructively through display separation.

Record a missed contact point as invalid, stop the source and raise the probe before repositioning, and create a separate remeasurement event. Thermal drift interrupts the current acquisition; retain the object's history and create a new attempt after restabilizing. Save raw data even when calibration is missing; do not substitute reference-figure points. If release status does not arrive, keep the equipment closed and report the blocker.

ARCHIVE separates unused, measured, probe-contacted, damaged, and unknown items into compartments, seals remaining powder/legs/offcuts, and reconciles quantities. CLEAN returns each die sleeve, punch, stop, simulated scoop, carrier, and lead; seals powder, metal, and quartz-tube proxy waste in separate boxes for handoff; wipes permitted surfaces and puts away the wipes; and leaves empty, closed stations. It does not disperse powder, sweep exposed broken tubes, or improvise chemical cleaning solutions.

## 12. Existing Assets and Missing Interfaces

asset_bindings.json binds 66 asset-role categories operation by operation. SPEX8000D and two-couple module meshes already exist, and their genuinely existing part IDs are reused; other roles are task asset requirements only, without a claim that they have been built.

The SPEX workstation assessment remains LIMITED: an approximately 7 mm AABB gap exists between jars and fixtures, cover-shell contact is unresolved, and gas tightness/clamping/continuous motion/robot reachability are unvalidated. Existing cover opening/jar lifting/button pressing are static displays. If a dynamic task uses a new mock positioning seat, it must be labeled authored and implemented separately; current images cannot establish successful grasping and loading.

File entry points: agent_visible.json supplies single-episode goals; operations.json and branches.json supply reference actions and branches; material_cards.json, lineage_contract.json, and control_packages.json maintain identity and controls; mock_contract.json and evaluator_reference.json constrain readings and acceptance; asset_bindings.json, unknown_parameters.json, and granularity_gaps.json record implementation needs; coverage_matrix.json and provenance.json audit whole-paper scope.

This package has reached "whole-paper task design and source-content routing ready," not "real experiments/robot execution/replication of all manual micro-actions ready." The next step is to implement the external operation interfaces for a selected episode and validate trajectories; this round does not automatically elevate the design into an executed asset or a reproduced scientific result.
