# Thermoelectric Devices: Initial Task Draft from Raw Materials to Two-Couple Module Measurement

Source: Composable neural emulators accelerate thermoelectric generator design, Nature, DOI 10.1038/s41586-026-10223-1. This draft is based on the retained main-paper Methods (PDF p8), main-paper device-dimension inventory, and SI Fig21 (PDF p13). The main-paper Methods and SI apparatus figure have been reread; whole-paper task mapping is not yet complete, so this cannot count as another completed paper.

## Goal Given to the Robot

Starting from materials sealed with their identities, prepare the specified two-couple n–p thermoelectric device, obtain object-traceable measurement records under different thermal boundaries and task current conditions, then unload, archive, and clean up. Scientific readings are supplied by an explicit simulated-data interface; this stage does not require calculating actual material performance.

The initial state contains no finished module. The preparation bench holds sealed material batches, empty task containers, an AlN support plate, and copper electrodes; the ball-milling, sintering, cutting, assembly, and measurement stations are each idle. Actual atmosphere containers and equipment interlocks are not yet validated; all operations are static task designs.

## Evaluation-Side Reference Operation Chain

1. Go to the material cabinet and retrieve the correct p-type and n-type material batches, placing them in separate transport slots. Preserve the paper's mapping between full composition names and abbreviations; do not remove the MgAgSb additive or the n-type material's actual dopant composition from lineage
2. At the weighing/portioning proxy bench, open and close the labeled material containers individually, transfer the task-specified portions into their respective ball-milling containers, close the lids, and move away remaining material. Task portions are inputs labeled with provenance/unknown status, not invented unreported recipes
3. Hand the containers to the enclosed Ar-atmosphere interface labeled as a task design. The inert state is supplied only by the environment, not by the robot writing a Boolean itself. The current standard ball-milling jar cannot be claimed to be gas-tight; the real interface remains missing
4. Go to the SPEX 8000D visual-reference station, open the cover, seat the two container types separately, complete clamping, withdraw hands, close the cover, select the batch work order, and start. Mechanical actions and clamping mechanisms are design proxies; actual mounting contact has not been validated
5. Wait for nonphysical processing-completion and safe-release events, open the cover, support and retrieve the jars, and move them to the enclosed discharge bench. Each powder output retains its material and parent-jar identity; a wrong batch or dropped item enters isolation rather than being relabeled
6. Retrieve the p-type batch and Sb interface material, and establish the source-supported layer order at the die-loading proxy bench. Place the die tray in the SPS-322LX sintering proxy station, close the door/start/wait for cooling release, and retrieve a billet with a traceable pressing direction
7. Separately retrieve stainless-steel interface material for the n-type batch and use an independent SPS-1080 work order, without reusing the p-type interface or process labels. Actual die-assembly details are unreported and remain proxy interfaces
8. Support the billet in the cutting-positioning seat, select the corresponding leg dimensions, and process the task shapes. Target p-leg dimensions are 3.3×3.3×6.6 mm; n-leg dimensions are 2.9×2.9×6.6 mm. The two dimension sets cannot be unified into identical legs by overall proportional scaling
9. Distribute the small cut legs into a compartment tray with orientation markings, preserving source-supported processing orientations. The module n legs must not arbitrarily inherit the p-type branch's cutting direction; unspecified local details remain unknown
10. Transport the AlN plate, copper electrodes, two p legs, and two n legs to the assembly bench. Use positioning fixtures to grasp, place, and align them in sequence to form a two-couple module. Specific electrode geometry, plate thickness, and interface-joining methods are unreported or pending verification; do not fill them in as soldering processes used by the authors
11. Remove temporary positioning parts, support the assembled module in its carrier, and record the four leg identities, orientations, and electrode topology. Where the task requires a specified series circuit, this is an evaluation-scene setting; appearance alone cannot demonstrate complete reconstruction of the source's wiring details
12. Move to the Mini-PEM visual/functional-role proxy station. When cold, safely unloaded, and with the chamber permitted to open, place the module, adjust the upper and lower contacts, connect the measurement leads, and check hot-end/cold-end and polarity labels
13. Withdraw hands, close the chamber, and execute the virtual equipment program for evacuation/thermal-boundary stabilization. The source uses an upper hot end, lower cold end, and vacuum measurement; actual vacuum plumbing, clamping pressure, and stability criteria are not supplied, so proxy settings cannot be treated as real-world operating specifications
14. At each specified thermal boundary, traverse the task current conditions, saving raw I, V0, and cold-side Q0 channels with the corresponding module/time/boundary. Preset records are kept separate from paper-value references; pressing a button does not directly establish valid data
15. Preserve current history before changing boundaries; do not represent a condition sweep on the same module as independent manufacturing replicates. Literature devices mentioned in the source serve only as documentary comparisons; do not generate new successful experimental records for them in this paper
16. At the data station, calculate P=I×V0 and η=P/(P+Q0), and extract the maximum values for each boundary; records bound to acquisition events must exist first. Uncalibrated mV channels must not arbitrarily be treated as W; retain raw signals, calibration status, and distinctions between physical quantities
17. At the end, shut down the drive and heating, wait for trusted cooling, unloading, and chamber-openability events, open the chamber, support the module, disconnect the leads, and then retrieve the sample
18. Archive the module and remaining legs in compartments by unused/measured/damaged status, return electrode fixtures, seal powder remnants and waste containers, clean the bench, and leave the equipment empty and closed

## Same-Paper Branches Still Requiring Completion

- The Bi0.4Sb1.6Te3 route of quartz-tube melting followed by ball milling cannot reuse the direct ball-milling route above
- Different cutting orientations for Sb/MgAgSb/Sb and Bi0.4Sb1.6Te3 in segmented devices, Ga–In joining, different segment lengths, and single-material controls
- S1331 spatial contact-resistance-distribution measurement, with contact resistivity treated as a derived quantity
- Comparisons of different dimensions and thermal boundaries for single legs, segmented legs, and two-couple modules
- Purely computational TEGNet/COMSOL, SI multi-material/multi-couple-count designs, and literature comparisons count only as documentary/computational branches, without invented new physical experiments

Even a complete macro-stage representation does not replicate every manual micro-action. For hot zones, powder atmospheres, and sintering internals, only loading/handoff/unloading is currently designed; fine-grained interfaces still require completion one by one. This draft includes no robot execution, physics simulation, or real equipment operation.
