# Chiral metamaterials: a whole-paper-driven family of long-horizon mobile-robot tasks

> Public task-specification snapshot: source packets, scenes, models and runtime dependencies referenced below are not included. See ../../EXPORT_NOTES.md for current export boundaries. This is a design specification, not an executable or experimentally validated benchmark.

Paper: Large recoverable elastic energy in chiral metamaterials via twist buckling, Nature, DOI 10.1038/s41586-025-08658-z. The fixed sources are the main text, SI, figures/tables, and seven supplementary videos retained by the existing audit.

## 1. Task design objectives

This deliverable converts the complete reported physical work into a TASK DESIGN extending from the material shelves through post-experiment archiving and cleanup. The robot must handle material containers, print trays, specimen components, assembly locators, boundary fixtures, loading equipment, and specimen storage slots across stations, preserving material, object, cycle, and condition identities. This is neither a single-point demonstration of placing a prepared rubber specimen between platens nor a new audit tool or CLI.

Scientific responses may be supplied by state/data fixtures explicitly labeled mock; solving actual deformation or predicting energy is not required at this stage. Design acceptance concerns long-horizon operations, dependencies, object states, controls, and recovery from exceptions, rather than forcing curves to match the paper's values. No robot, physics simulation, ANSYS, or real hardware is currently being run. Unknown process, CAD, and calibration details limit readiness for future real execution without preventing delivery of the complete task design.

The whole paper forms a task family. Rubber/TC4, geometry/thickness/layer-count/boundary controls can be selected independently; an episode may select a complete branch, a control package, or a material family. Do not invent a global author chronology requiring rubber before metal.

## 2. Agent-visible and evaluator-only information

### For the robot: goals, initial scene, and observations

Example task:

> Using the laboratory's existing rubber feedstock and equipment, fabricate and assemble the specified 3×3 chiral lattice, then observe compression and repeated loading with internal twisting permitted. Associate specimen identity with loading/unloading records and final state, save the specimen in the designated slot when finished, and restore the stations. Preset mock observations and responses are currently used; the goal is to obtain records with explicit conditions and traceable object states, without predicting the paper's energy values.

The agent receives the selected configuration parameter card/necessary source excerpts, material and equipment inventories, permitted equipment interfaces and safety rules, visible labels, queryable equipment states, and observations returned during the process (currently preset mock feedback, always labeled mock). The initial scene includes sealed feedstock cartridges, empty build trays, unassembled tooling, an empty testing station, and archive slots, rather than defaulting to a completed specimen. The robot must plan transport, fabrication, assembly, testing, and closing work itself.

### For the evaluator only: routes, hidden states, and criteria

The reference operations below, complete branches.json dependencies, correct object lineages, mock scheduling, hidden damage/jamming flags, terminal-state oracle, and recovery answers are evaluator-side materials and must not be given to the robot wholesale as its prompt. The reference route describes the intended closed workflow; robot reachability/executability has not been verified. A unique trajectory is not required; safe, equivalent pick-and-place orders and paths are acceptable.

Hard success conditions:

1. Use the correct material through fabrication and release; do not conjure specimens or skip fabrication
2. Configurations requiring layering must actually include component pick-and-place, interface alignment, top-plate installation, and temporary-tooling removal
3. The mounted object must match its material, dimensional family, and boundary; do not confuse free twisting with rotation locking, or boxed with unboxed conditions
4. The testing machine drives compression; the robot arm leaves the hazard zone during motion; fully unload and retract before specimen removal
5. Bind data to specimen, condition, and cycle. Separate first loading, residual states, and subsequent same-specimen cycles for metals; four specimens differ from four cycles on one specimen
6. Bulging, layer-by-layer buckling, low response, contact, and plastic residual deformation are observable research phenomena, not automatic failures for deviating from an ideal curve
7. On exceptions, stop safely, quarantine/redo, and retain history; do not relabel damaged/cycled parts as fresh specimens
8. Finally archive or explicitly quarantine specimens; leave machines unloaded, tooling and leftover materials returned, and no specimens abandoned in the experimental space

A control package requires completion of all its conditions, with correct associations between changed factors and records. Paper results such as 6.09J serve only as reported reference fixtures, not physical targets the robot must achieve. One button press, an attractive model, or mock output cannot establish actual scientific reproduction.

## 3. Stations and object flow

WS_STOCK material cabinet → WS_RUBBER_PRINT or WS_TC4_PRINT material-specific printer → WS_POST postprocessing/release → WS_ASSEMBLY applicable assembly → WS_METROLOGY mass/dimensions → WS_TEST boundaries and cycles → WS_STORAGE archiving/quarantine → WS_CLEAN cleanup and reset. WS_DATA handles only nonmanual data handoff and comparison.

Physical interfaces include sealed cartridges, graspable trays, doors/rails/panels, numbered compartment boxes, end-plate/ring grasping areas, locating combs, reversible joining tabs, upper and lower platens, a guard, removable lateral boxes, anti-rotation arms, a camera, archive slots, wipes, and sorted scrap bins. These are task-design surrogates; specific brands and mechanical precision have not been established. For the scene/coarse assets, see ../../scenes/chiral_scene_plan_v2/SCENE_PLAN_ZH.md (path within the deliverable package).

The full fabrication chain consists of retrieving material, loading material and the build tray, closing the door and starting, receiving mock completion and safe release, retrieving the build, postprocessing, and releasing specimens. The actual printing technology, feedstock form, temperature/layer thickness/curing/heat treatment are unknown. A sealed TC4 cartridge avoids assuming an actual exposed-powder/wire route; an enclosed postprocessing service interface does not establish that the paper reported depowdering, cutting, or sandblasting.

All transport grasps load-bearing plates, end rings, or thick nodes, without using thin rods to carry the whole specimen's weight. Joining tabs, locating combs, orientation marks, grasping sites, and their sequence are authored. Rods being fixed to rings does not authorize assuming that the authors glued, welded, or screwed individual rods into place.

## 4. Complete main case: from rubber feedstock to archiving

### R01 rubber chiral array

This is a task design that can be instantiated for a mobile robot, not a recording of the authors' original operations or a claim of physical execution. Scientific responses are supplied by state/curve fixtures labeled mock. Transport, door handles, cartridges, trays, locators, grasping interfaces, and cleanup order are connecting actions supplied by this task's author.

### Specimen and goals

- Sources: main-text PDF p5 Fig4a/Experiments, p9 Samples, p10 Experiments, p20 ED10a, p21 Table1 row1, Video4
- R01: rubber circular-rod chiral array, 3×3 in-plane layout; unit N=8, r=1.5 mm, R=7.5 mm, α0=5°, h0=30 mm; whole-specimen envelope 65×65×72 mm
- This task uses 3×3 in-plane positions × upper/lower mirrored units, giving 18 task half-units: the two layers shown in ED10a are consistent with the table's Nbk=144 and 8 rods per unit. This is a geometry interpretation and task decomposition supported by images and arithmetic, not proof of 18 known independently detachable physical parts or a manufacturing BOM listed in the original text
- Build goal: start from a rubber-specific cartridge, fabricate separate units, assemble, compress/unload/reload, and finally archive the specimen and reset the stations
- This task selects ε=0.25 as the mock loading endpoint because it is row1's reported comparison endpoint; it is not the authors' known maximum strain over the full loading sequence. Two loadings are the default task-design value; the paper's total cycle count is unknown

### Continuous operational narrative

1. At WS_STOCK, grasp the handle of the rubber-specific cartridge labeled R01 and place it in the transport tray; place an empty build tray in another slot on the same cart. Do not mistakenly select a TC4 cartridge. Rubber formulation/batch/printing technology are unknown; the cartridge is a generic task surrogate
2. Move to WS_RUBBER_PRINT. Open the printer door, insert the cartridge into the material slot, and push the build tray fully along the rails; withdraw the hand and close the door. Select the R01 work order on the panel and press start. The work order explicitly requires separate chiral units; do not substitute putting a prefabricated whole array directly into the tester for fabrication
3. After mock printer completion, confirm that the door interlock has released, open the door, grasp the tray handles, remove the entire tray, and carry it to WS_POST. Grasp parts only once the tray and units are in touch-safe/releasable states; actual temperature, curing time, layer thickness, equipment, and process parameters remain unknown
4. Stabilize the tray in the postprocessing holder. Remove units individually through this scene's releasable interfaces and place them in the R01 numbered compartment box. If the instance enables removable task support tabs, first grasp and pull off the tabs and place them in the designated scrap bin; this support structure and removal method are authored, with no claim that the paper used them. Any necessary actual curing/cleaning/postprocessing recipe awaits external input; do not invent chemical recipes
5. Carry the compartment box and bottom and top load-bearing plates to WS_ASSEMBLY. Place the bottom plate in the 3×3 locating base; grasp units by their rigid rings in (i,j) order and place them at the 9 bottom-layer positions. Then align and place the second layer on each of the 9 columns. The 18 half-unit pick-and-place actions are actual object iterations, not 18 independent scientific experiments
6. Install removable temporary locating combs, complete the scene-provided reversible ring-to-ring joints, and place the top plate; withdraw the locating combs in sequence. The joints/sequence are task-design surrogates; the source connection method is unknown. Do not invent individual adhesive bonding, welding, or threaded assembly by the authors. Position unit orientations according to the scene recipe marks; actual CAD and chiral-orientation pairing remain undetermined. After assembly, the intermediate rings in all 9 columns must remain independently rotatable; transport fixtures must not bridge and lock them
7. At WS_METROLOGY, place the whole specimen on the balance, then on the dimensional locating station, measuring overall height and projected dimensions at the marked envelope contact surfaces; grasp rigid rings to avoid compressing soft rods. Record specimen identity, whole mass, and dimensions. The measurement method is an authored connecting action; do not treat whole-specimen mass as buckling-rod mass. Preserve mock readings separately from literature values
8. Place the whole specimen in a transport tray with bottom support and carry it to WS_TEST. With the upper platen retracted and the guard open, use a two-finger grasp/support under the bottom load-bearing plate to retrieve the specimen and place it in the lower-platen locating area; remove the transport fixture. Install neither a lateral-confinement box nor an intermediate-ring anti-rotation arm. Independent twisting is provided by the specimen's own degrees of freedom, without assuming a commercial rotating loading head/bearing
9. Aim the side camera at the specimen and capture its initial shape. Withdraw the robot end effector, close the guard, select R01 and this cycle's ID on the control panel, and start compression. The robot must not replace the testing machine by pressing the specimen by hand or approach moving platens. Load to the mock task's comparison strain of 0.25 and save force/displacement records and independent-twisting states; this is not an actual mechanical solution at present
10. Press unload and wait for the platens to lose contact. Record post-unloading height/shape, then perform the second loading and unloading on the same specimen. Do not call these two task cycles the authors' actual cycles 1 and 2; the rubber table has no dedicated first-loading energy, so do not invent a first/repeated difference
11. After full unloading, upper-platen retraction, and door-interlock release, open the guard, support the bottom plate, and return R01 to its numbered transport slot. Carry it to WS_STORAGE and place it in the R01 archive slot. If it was dropped, incorrectly grasped by soft rods, or suffered ring jamming, move it to quarantine and record the state; do not continue using its original "undamaged" identity
12. At WS_CLEAN, remove and return temporary locating combs/transport fixtures, put away unused cartridges, clear surrogate print supports and bench debris, and wipe the tray and bench. The current design uses a clean dry wipe as its cleaning medium; do not invent a solvent procedure from the paper. Close the machine door, leave the testing platen safely retracted, and clear the area

### Acceptable completed state

Material has passed through the printing station rather than appearing from nowhere; 18 surrogate units have been transferred through compartments and assembled; the array boundary retains free twisting; each of the two mock loadings has loading/unloading records; the gripper stays outside the platen hazard zone during testing; and the final specimen is in the R01 archive slot, removable tooling has been returned, and the testing machine is unloaded. Paper values such as energy 20.02 kJ/m³ may only be labeled reported fixtures, not results already measured by the robot or physical quantities this task must predict.


## 5. TC4: from fabrication to preservation of cycle states

Retrieve a sealed TC4 cartridge and an empty build box → load material and box into the dedicated printer, close the door, and start → retrieve the box after fabrication → transfer the build box to the enclosed postprocessing unit, complete the surrogate recipe, and safely release → grasp end rings/end plates to place metal parts into compartments.

Circular-rod and square-beam chiral specimens require placing the lower half-unit on the base, aligning the upper half-unit, completing reversible joining, placing the top plate, and removing temporary locating tooling. The two layers are figure-supported task geometry; actual part decomposition/joints are unknown. Transfer prisms and single-layer rotation-locked specimens directly as printed lattices/units, without inventing rod-by-rod lattice construction.

After weighing and dimensional operations, carry specimens to the tester. Remove ring-bridging constraints for freely chiral specimens; install lateral boxes for rod-based prisms; install anti-rotation arms on rotation-locked specimens while retaining axial motion. The specific lateral-box boundary for plate-based prisms is not separately specified. The default without an added box is an authored task choice, not a fact that the original authors used no box, and does not add a plate-based boxed/unboxed experimental pair.

Every metal instance must preserve: fresh specimen with straight rods → first loading → residual plasticity/increased α0/slight rod bending after unloading → reloading/unloading of the same specimen within the amplitude → removal and archiving as a cycled specimen. Do not call the entire initial input area recovered elastic energy; Fig4h,j use first-loading reference values, while the repeated-loading column in Table1 is stored separately.

The chiral1/2/3/4 labels in ED10g are individually addressable; chiral2 is used in the main Fig4. Four displayed specimens do not establish four independent manufacturing batches, nor four cycles on one specimen. Separate task objects are created by default; sharing with M12 requires an explicit identity_alias and preserved cycle history.

Do not merge table rows 16 and 17: table row16 has ε=0.014, while the ED10 FE equal-local-stress point is ε=0.012; the freely chiral table value is ε=0.036, while the FE point is ε=0.037. Preserve each original value. Local Mises stress comes from FE, not an experimental sensor. Transcribe table row17's Nbk=21 as given; do not conceal its difference from the nominal 20 rods by deleting/adding rods.

## 6. All condition families and their essential differences

Every row fully reuses "feedstock→fabrication→release→applicable assembly→metrology→mounting→observation/cycles→removal→archiving and cleanup." The 28 records include conditions, overlapping figure/table labels, four displayed specimens, and a tool demonstration; they are not a claim of 28 independent experiments by the authors.

|Task ID|Configuration and source parameters|Boundary/assembly differences|Observations, endpoints, and identity qualifications|
|---|---|---|---|
|R01|rubber chiral rod / table row1; source_table_row=1; primitive_dimension_mm=1.5; dimension_meaning=r; envelope_mm=[65, 65, 72]; reported_comparison_strain=0.25; Nbk=144; whole_density_kg_m3=290.27; N_per_unit=8; R_mm=7.5; alpha0_deg=5; h0_mm=30; array_plan=[3, 3]|free_internal_rotation; rubber_array_3x3x2_surrogate|3×3 in-plane layout, two layers shown; the 18 parts are a task decomposition supported by the figures and 144/8, not a source BOM; Grasp the bottom plate/rigid rings for transport and remove all transport fixtures bridging rings; install neither anti-rotation arms nor a lateral box; mock endpoint=0.25|
|R02|rubber prism rod / table row2; source_table_row=2; primitive_dimension_mm=1.5; dimension_meaning=r; envelope_mm=[100, 130, 100]; reported_comparison_strain=0.25; Nbk=160; whole_density_kg_m3=222.46; prism_theta_deg=40; parallel_rod_spacing_mm=10|lateral_box; printed_single_object|The two-layer in-plane curve is associated with the main figure, but whether R_PRISM_L2 and the row2 object are identical is unconfirmed; task instances are separate by default; mock endpoint=0.25|
|R03|rubber octahedral rod / table row3; source_table_row=3; primitive_dimension_mm=1.5; dimension_meaning=r; envelope_mm=[104, 104, 151]; reported_comparison_strain=0.25; Nbk=216; whole_density_kg_m3=85.05|no_added_box_authored; printed_single_object|Preserve layer-by-layer asynchronous buckling as an observation category; do not correct actual instability into synchronous motion; Video6 gives no radius; do not claim the video separately shows both r1.5 and r2 specimens; mock endpoint=0.25|
|R04|rubber octahedral rod / table row4; source_table_row=4; primitive_dimension_mm=2; dimension_meaning=r; envelope_mm=[104, 104, 151]; reported_comparison_strain=0.25; Nbk=216; whole_density_kg_m3=111.38|no_added_box_authored; printed_single_object|Preserve layer-by-layer asynchronous buckling as an observation category; do not correct actual instability into synchronous motion; Video6 gives no radius; do not claim the video separately shows both r1.5 and r2 specimens; mock endpoint=0.25|
|R05|rubber Kelvin rod / table row5; source_table_row=5; primitive_dimension_mm=1.5; dimension_meaning=r; envelope_mm=[185, 185, 205]; reported_comparison_strain=0.25; Nbk=176; whole_density_kg_m3=10.6|no_added_box_authored; printed_single_object|Perform the full fabrication, mounting, and removal sequence even when the energy is extremely small; do not classify a low response as an omission/failure; Do not impose an ideal first-order bending mode; mock endpoint=0.25|
|R06|rubber Kelvin rod / table row6; source_table_row=6; primitive_dimension_mm=2; dimension_meaning=r; envelope_mm=[185, 185, 205]; reported_comparison_strain=0.25; Nbk=176; whole_density_kg_m3=17.55|no_added_box_authored; printed_single_object|Perform the full fabrication, mounting, and removal sequence even when the energy is extremely small; do not classify a low response as an omission/failure; Do not impose an ideal first-order bending mode; mock endpoint=0.25|
|R07|rubber prism plate_thickness / table row7; source_table_row=7; primitive_dimension_mm=3.2; dimension_meaning=t; envelope_mm=[20, 52, 44]; reported_comparison_strain=0.25; Nbk=4; whole_density_kg_m3=517.92|no_added_box_authored; printed_single_object|The lateral-box boundary for the plate-based prism is not separately specified; no added lateral box is the default task choice and can be replaced if an actual recipe is supplied, but does not establish that the original authors used no box; Do not conflate this with the rod-based prism geometry; mock endpoint=0.25|
|R08|rubber tensegrity rod / table row8; source_table_row=8; primitive_dimension_mm=1.5; dimension_meaning=r; envelope_mm=[94, 94, 110]; reported_comparison_strain=0.4; Nbk=48; whole_density_kg_m3=18.11|no_added_box_authored; printed_single_object|Instantiate all four radii separately; Video7 is not assigned to any particular radius; 0.4 is the reported comparison endpoint; retain the qualification about neighboring-rod contact beyond 0.4; mock endpoint=0.4|
|R09|rubber tensegrity rod / table row9; source_table_row=9; primitive_dimension_mm=2; dimension_meaning=r; envelope_mm=[94, 94, 110]; reported_comparison_strain=0.4; Nbk=48; whole_density_kg_m3=32.2|no_added_box_authored; printed_single_object|Instantiate all four radii separately; Video7 is not assigned to any particular radius; 0.4 is the reported comparison endpoint; retain the qualification about neighboring-rod contact beyond 0.4; mock endpoint=0.4|
|R10|rubber tensegrity rod / table row10; source_table_row=10; primitive_dimension_mm=2.5; dimension_meaning=r; envelope_mm=[94, 94, 110]; reported_comparison_strain=0.4; Nbk=48; whole_density_kg_m3=49.28|no_added_box_authored; printed_single_object|Instantiate all four radii separately; Video7 is not assigned to any particular radius; 0.4 is the reported comparison endpoint; retain the qualification about neighboring-rod contact beyond 0.4; mock endpoint=0.4|
|R11|rubber tensegrity rod / table row11; source_table_row=11; primitive_dimension_mm=3; dimension_meaning=r; envelope_mm=[94, 94, 110]; reported_comparison_strain=0.4; Nbk=48; whole_density_kg_m3=70.37|no_added_box_authored; printed_single_object|Instantiate all four radii separately; Video7 is not assigned to any particular radius; 0.4 is the reported comparison endpoint; retain the qualification about neighboring-rod contact beyond 0.4; mock endpoint=0.4|
|M12|TC4 chiral rod / table row12; source_table_row=12; primitive_dimension_mm=0.6; dimension_meaning=r; envelope_mm=[20, 20, 64]; reported_comparison_strain=0.036; Nbk=40; whole_density_kg_m3=593.75; N_nominal_per_unit=20; R_mm=7.5; alpha0_deg=5; h0_mm=30|free_internal_rotation; tc4_two_layer_surrogate|Assemble the two layers before mounting; NBk40 is consistent with 20/layer; the detachable interface remains authored; Separate the first loading from the residual state and subsequent cycles; mock endpoint=0.036|
|M13|TC4 chiral square_beam_b_equals_t / table row13; source_table_row=13; primitive_dimension_mm=1.2; dimension_meaning=b=t; envelope_mm=[20, 20, 64]; reported_comparison_strain=0.036; Nbk=40; whole_density_kg_m3=621.09|free_internal_rotation; tc4_two_layer_surrogate|Assemble the two layers before mounting; NBk40 is consistent with 20/layer; the detachable interface remains authored; Separate the first loading from the residual state and subsequent cycles; mock endpoint=0.036|
|M14|TC4 prism rod / table row14; source_table_row=14; primitive_dimension_mm=0.6; dimension_meaning=r; envelope_mm=[25, 105, 45]; reported_comparison_strain=0.036; Nbk=64; whole_density_kg_m3=456.3; prism_theta_deg=40; parallel_rod_spacing_mm=3|lateral_box; printed_single_object|; mock endpoint=0.036|
|M15|TC4 prism plate_thickness / table row15; source_table_row=15; primitive_dimension_mm=1.2; dimension_meaning=t; envelope_mm=[20, 52, 44]; reported_comparison_strain=0.036; Nbk=4; whole_density_kg_m3=718.97|no_added_box_authored; printed_single_object|The lateral-box boundary for the plate-based prism is not separately specified; no added lateral box is the default task choice and can be replaced if an actual recipe is supplied, but does not establish that the original authors used no box; Do not conflate this with the rod-based prism geometry; mock endpoint=0.036|
|M16|TC4 rotation-locked chiral/nonchiral bending rod / table row16; source_table_row=16; primitive_dimension_mm=0.6; dimension_meaning=r; envelope_mm=[20, 20, 32]; reported_comparison_strain=0.014; Nbk=20; whole_density_kg_m3=593.75; N_nominal_per_unit=20; R_mm=7.5; alpha0_deg=5; h0_mm=30|rotation_locked; printed_single_object|Apply the anti-rotation constraint to the ring degree of freedom; do not uniformly lock all chiral columns; Whether row16 and 17 reuse the same object is unknown; separate fresh specimens are the task default to keep first-loading histories traceable; Preserve table ε0.014; store ED10 FE equal-stress ε0.012 separately without merging or correcting them; mock endpoint=0.014|
|M17|TC4 rotation-locked chiral/nonchiral bending rod / table row17; source_table_row=17; primitive_dimension_mm=0.6; dimension_meaning=r; envelope_mm=[20, 20, 32]; reported_comparison_strain=0.036; Nbk=21; whole_density_kg_m3=593.75; N_nominal_per_unit=20; R_mm=7.5; alpha0_deg=5; h0_mm=30|rotation_locked; printed_single_object|Apply the anti-rotation constraint to the ring degree of freedom; do not uniformly lock all chiral columns; Whether row16 and 17 reuse the same object is unknown; separate fresh specimens are the task default to keep first-loading histories traceable; Transcribe the original table's Nbk=21 as given; do not conceal the discrepancy with the nominal 20-rod geometry by removing/adding rods; mock endpoint=0.036|
|R_SMALL20|20° small rubber chiral specimen; alpha0_deg=20; R_mm=5.5; rod_diameter_mm=1.8; h0_mm=20; force_axis=4 × F1rod (N)|free_internal_rotation; printed_single_object|Not the 30mm main specimen; this mock selects 0.25 only as a task endpoint; the authors' complete protocol is unknown; mock endpoint=0.25|
|R_SMALL50|50° small rubber chiral specimen and contact observation; alpha0_deg=50; R_mm=6; rod_diameter_mm=1.7; h0_mm=20; force_axis=4 × F1rod (N); reported_contact_above_strain=0.3|free_internal_rotation; printed_single_object|The mock selects 0.35 to include the ε>0.3 contact state; this endpoint is authored, not a reported maximum from the authors; Contact is a research phenomenon rather than a failure requiring repair; do not extrapolate post-contact results as validation of a no-contact model; mock endpoint=0.35|
|R_PRISM_L1|Single-layer rubber prism in-plane control; layers=1; one_layer_structure=two half metacells|no_added_box_authored; printed_single_object|Retain the geometry of one layer and two half-cells; the exact lateral fixture is unknown, and the single-layer default without a box is a design choice; mock endpoint=0.25|
|R_PRISM_L2|Two-layer rubber prism in-plane control; layers=2|lateral_box; printed_single_object|Retain the condition association with row2; use a separate task object by default without fabricating evidence of object reuse; mock endpoint=0.25|
|R_PRISM_L4|Four-layer rubber prism in-plane control; layers=4|lateral_box; printed_single_object|ED9c explicitly shows four layers in a box; do not implement only the final two-layer control; mock endpoint=0.25|
|R_PRISM_UNBOXED|Two-layer rubber prism bulging without lateral confinement; layers=2|unboxed_control; printed_single_object|Move the lateral-box walls back to the rack before testing, preserving lateral free space; Do not reconfine a bulging specimen to improve its apparent performance; keep unboxed and boxed curves separate; mock endpoint=0.25|
|R_TOOL_DEMO|Separate demonstration of the tool interaction visible in Video5; |unboxed_control; printed_single_object|Video5 shows approach/interaction/withdrawal at approximately 4.66–5.50 seconds; tool identity, direction/force/purpose, and association with quantitative curves are unknown; Use a separate demonstration object and isolated records; do not mix the intervention into the pure comparison records of R_PRISM_UNBOXED; The mock uses a blunt soft-tipped probe and a discrete contact event only to supply an action interface, without attributing the instability to author intervention; mock endpoint=fixture terminal event|
|M_CHIRAL1|TC4 displayed sample chiral 1; source_trace_label=chiral 1; source_used_in_main_Fig4=False|free_internal_rotation; tc4_two_layer_surrogate|A four-specimen display and repeated cycles on the same specimen are two different kinds of repetition; Use M12 geometry as a task surrogate; the complete geometry/manufacturing-batch correspondence of each actual curve is unknown; An explicit identity_alias must be provided before sharing an object with M12; do not claim object identity by default; mock endpoint=fixture terminal event|
|M_CHIRAL2|TC4 displayed sample chiral 2; source_trace_label=chiral 2; source_used_in_main_Fig4=True|free_internal_rotation; tc4_two_layer_surrogate|A four-specimen display and repeated cycles on the same specimen are two different kinds of repetition; Use M12 geometry as a task surrogate; the complete geometry/manufacturing-batch correspondence of each actual curve is unknown; An explicit identity_alias must be provided before sharing an object with M12; do not claim object identity by default; mock endpoint=fixture terminal event|
|M_CHIRAL3|TC4 displayed sample chiral 3; source_trace_label=chiral 3; source_used_in_main_Fig4=False|free_internal_rotation; tc4_two_layer_surrogate|A four-specimen display and repeated cycles on the same specimen are two different kinds of repetition; Use M12 geometry as a task surrogate; the complete geometry/manufacturing-batch correspondence of each actual curve is unknown; An explicit identity_alias must be provided before sharing an object with M12; do not claim object identity by default; mock endpoint=fixture terminal event|
|M_CHIRAL4|TC4 displayed sample chiral 4; source_trace_label=chiral 4; source_used_in_main_Fig4=False|free_internal_rotation; tc4_two_layer_surrogate|A four-specimen display and repeated cycles on the same specimen are two different kinds of repetition; Use M12 geometry as a task surrogate; the complete geometry/manufacturing-batch correspondence of each actual curve is unknown; An explicit identity_alias must be provided before sharing an object with M12; do not claim object identity by default; mock endpoint=fixture terminal event|

## 7. Control packages, cycles, and data handoff

- Rubber geometry package: R01–R11. Retain circular-rod and plate-based prisms, two octahedral radii, two Kelvin radii, and four tensegrity radii. The table's energy-comparison endpoint is 0.25 for R01–R07 and 0.4 for R08–R11; do not describe all as comparisons at the same global strain
- Layer-count/lateral-confinement package: R_PRISM_L1/L2/L4 compare in-plane deformation; separately compare two-layer boxed specimens with R_PRISM_UNBOXED bulging. A single layer comprises two half-cells. Four layers in a box are not disposable duplicate data; do not repair an unboxed control into a boxed condition because of instability
- Video5 tool demonstration: fabricate/retain a separate object for R_TOOL_DEMO. Preserve the visible manual actions as "retrieve soft-tipped surrogate tool→approach→symbolic contact→withdraw→return." The 4.66–5.50 seconds only locate the video segment, not the duration of tool motion; purpose, force, direction, and association with quantitative curves remain unknown. Any actual approach under load requires separate engineering safety design; the guard is not bypassed here
- Small-specimen package: R_SMALL20 and R_SMALL50 use their respective geometries and a 20mm reference height; the plotted force axis is 4×F1rod. The 50° contact at ε>0.3 must be recordable; this task selects 0.35 as the mock demonstration endpoint without claiming it is the source's loading protocol
- TC4 geometry/cycle package: M12–M17 retain first-loading/post-unloading residual/repeated columns. M_CHIRAL1–4 are displayed-specimen identities that can be sampled individually for evaluation; they need not all be included in one long episode
- TC4 boundary package: combine the distinct endpoints for freely rotating M12 and rotation-locked M16/M17 separately. Equal global strain and equal local stress are two kinds of comparison; local-stress references come from the nonmanual FE branch

The data package includes at least object_id, component_ids, material, condition_id, boundary, geometry_basis, cycle_id/phase, force/displacement (typed as mock or measured), image/state, reference_height, area/volume_basis, whole_mass, buckling_mass_basis, and source_tag. Values not supplied remain null/unknown; do not fill new measurement fields with literature values.

Equivalent strain/stress, stiffness, plateau strength, volumetric energy, and energy/buckling-component mass are nonmanual calculations. Whole-specimen mass includes nonbuckling parts and cannot replace the buckling-mass denominator. Keep the meanings of initial energy, repeated-loading energy, and recoverable unloading energy distinct; do not fabricate the authors' original traces through reintegration/fitting here.

## 8. Failure and recovery are part of the task

|Observable exception|Permitted recovery|Facts that must be preserved|
|---|---|---|
|Cartridge key/material label mismatch|Retrieve it, return it to its original slot, and select the correct material; quarantine incorrect parts if already fabricated|Do not merely relabel; do not pass incorrect material|
|One component is missing after print completion|Mark the missing location, remanufacture a replacement component, and associate a new component_id|Do not conjure a replacement or skip build dependencies|
|Deformation or dropping caused by grasping soft rods|Stop, support load-bearing regions, move to quarantine, and fabricate a replacement|Preserve the damaged object's original identity; do not keep using it as an undamaged fresh specimen|
|Locating comb/transport fixture bridges intermediate rings|Remove it while unloaded; return to the assembly table if necessary|Free twisting must not depend on greater force to force constraints apart|
|Wrong lateral box or anti-rotation arm installed|Return it to the tooling rack before starting and reset according to the condition|Do not label data as the correct condition when acquired under an incorrect boundary|
|Camera occlusion|Move the camera and recapture the initial or current state|Do not alter an established boundary to improve framing|
|Bulging/layer-by-layer instability/low response/50° contact|Preserve the observation and unload according to task endpoints and safety events|These may be research results; do not automatically "repair" them into ideal modes|
|Acquisition loss|Stop and save the invalid segment; repeating requires a new run/cycle identity|After losing a metal specimen's first cycle, do not pass the next cycle off as its first; a fresh specimen is required to acquire a first cycle again|
|Jamming persists after unloading|Keep the guard closed and confirm full unloading; support and lift after releasing removable surrogate constraints|Do not count recovered energy while prying or reach into moving platens|
|Archive slot occupied|Use the branch's backup slot or a quarantine slot|Do not overwrite another specimen's identity or reset a cycled specimen as fresh|

The task may use explicit, observable faults to test recovery planning, but must not demand impossible inferences about faults that are neither visible nor queryable to the agent. The hidden oracle judges actual state only; necessary identification signals are exposed through labels, equipment errors, or observation feedback.

## 9. Handling theoretical/nonmanual content

All 77 source-coverage units are included in coverage_matrix.json, but not all count as hands-on operations. Theory, FE, and analysis separately retain: buckling of vertical/imperfect rods; oblique rods and normalization; general 3D chiral linear relations; in-plane/out-of-plane bending, in-rod twisting, axial compression, and helix corrections; radius/angle/thickness comparisons; thick-rod boundaries; two nonlinear micropolar models; three staged FE controls; numerical lattice/cross-section comparisons; and TC4 equal-stress/equal-strain FE.

These are reference inputs/data handoffs in nonmanual_scope.json, without requiring the robot to fabricate a "2° imperfect-rod experiment." Videos1–3 are numerical demonstrations and do not add reported physical fabrication branches for crossed beams or wide flat beams. The SI supplies no additional fabrication recipe. Low-frequency vibration isolation, impact protection, actuators/twist modulation, jumping, and energy-storage devices are proposed applications without independent physical experiments to convert, and are explicitly excluded.

Design rationales in Methods and Fig3 may influence configuration cards, but must not fabricate the original authors' complete parameter-search history. Do not conflate displayed figure/table relationships or task-author-arranged operational dependencies with the authors' actual timeline.

## 10. Unknown parameters do not remove steps

CAD, printing processes, formulations/batches, postprocessing, assembly joints, actual lateral-box/rotation-locking details, rate/preload/calibration/sampling/total cycle count, original measurement traces, and the purpose of the Video5 tool all remain unknown. Each currently has an action interface, state inputs/outputs, and an explicit surrogate; see unknown_parameters.json. These do not prevent design coverage from being completed; future physical execution requires engineering configuration and validation, and no current readiness is claimed.

Files in this directory:

- TASK_DESIGN.md: self-contained task family, main case, condition differences, failure recovery, operations, and coverage appendices
- FIRST_ROUTE_RUBBER.md: independently readable end-to-end rubber case
- operations.json: operation templates with objects, locations, preconditions/actions/postconditions, recovery, and source labels
- branches.json: complete condition parameters, object/cycle bindings, assembly/boundary differences, and full-chain sequences
- assets.json: action targets/grasping-interface requirements; specific scene files are in the sibling chiral_scene_plan_v2
- dependencies.json: within-branch material/action dependencies and cross-condition data joins, without a fabricated global author timeline
- coverage_matrix.json: item-by-item mapping of the original 77 source units with explicit hands-on/mixed/nonmanual classifications
- nonmanual_scope.json: separate classification of theory, FE, analysis, and proposed applications
- unknown_parameters.json / mock_contract.json: unknowns and surrogates, event interfaces, and prohibited inferences
- provenance.json / design_validation.json: input hashes and a one-time static completeness check, not a new CLI

## Appendix A: complete operation contracts (initial design, reachability/executability unverified)

The following are evaluator-side reference actions. {branch} binds to each condition's own object and parameters from the preceding section; material_printer resolves to the corresponding printer station by material. Select actual actions according to the condition's operation_sequence; do not apply every fixture action to every specimen. Actions are templates; iterating over 18 task half-units or same-specimen cycles counts object operations, not scientific experiments.


### FAB01 Retrieve material-specific feedstock and an empty build tray

Location: WS_STOCK; Targets: material_cartridge, transport_tray, build_tray; Object: this branch's object/condition ID

Preconditions: branch material and object identity bound; empty cart slots

Actions: Grasp the cartridge handle, retrieve the sealed cartridge from its designated rubber or TC4 shelf slot, and place it in the transport slot; Slide the empty build tray into another slot and drive the cart to the printer station for that material

Postconditions: correct material cartridge and tray at selected printer; no TC4/rubber cross-use

Recovery: Return incorrect material to its original slot and retrieve the correct material if not yet loaded; send cartridges of unknown identity to quarantine

Sources and design: The paper uses rubber and TC4 materials in 3D printing. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: Feedstock form, formulation, batch, and supplier

### FAB02 Open the printer chamber and load the cartridge

Location: material_printer; Targets: printer_door, material_cartridge, material_port; Object: this branch's object/condition ID

Preconditions: printer idle; door interlock released; FAB01 done

Actions: Grasp the door handle and open the chamber door; Slide the cartridge along the scene's keyed slot until seated; close the separate feed cover

Postconditions: material cartridge docked; no loose stock on floor

Recovery: If the cartridge jams, return it to the tray; do not force it in or open the sealed TC4 cartridge

Sources and design: Material-specific 3D printing is reported. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: Actual printing process and equipment; do not assume melt/resin/powder-bed technology

### FAB03 Insert the build tray and start printing for this branch

Location: material_printer; Targets: build_tray, printer_door, printer_panel; Object: this branch's object/condition ID

Preconditions: FAB02 done; branch build recipe surrogate available

Actions: Grasp the tray handle and slide it onto the build rails; Withdraw the hand, close the chamber door, select this branch's build work order on the panel, and press start

Postconditions: machine in printing state; build job binds components to object lineage

Recovery: Do not start with the door open; cancel and reselect an incorrect work order before fabrication; quarantine an incorrectly fabricated part rather than relabeling it

Sources and design: Separate chiral units and other rod/beam/plate lattices are fabricated by 3D printing. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: CAD, print orientation, layer thickness, temperature/power, speed, and supports are all unknown

### FAB04 Remove the completed build tray from the printer chamber

Location: material_printer; Targets: printer_door, build_tray, printed_components; Object: this branch's object/condition ID

Preconditions: print fixture emits completed; safe_to_touch and door_release events; not based on elapsed wall-clock alone

Actions: Open the door, grasp the tray handle, and slide the tray out along the rails; Keep the tray level, place it in the transport slot, and move to the postprocessing station

Postconditions: completed build at WS_POST; manufacturing stage cannot be skipped

Recovery: Quarantine missing/broken parts together with the tray; reprint only as a new build authorized by an external mock work order, producing new lot/object ID

Sources and design: The printing stage produces fabricated specimens. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: Actual cooling, curing, depowdering, and release times

### POST_R Release rubber parts and place them in compartments

Location: WS_POST; Targets: build_tray, post_holder, release_tabs, component_tray; Object: this branch's object/condition ID

Preconditions: rubber branch; FAB04 done; safe_to_release event

Actions: Lock the build tray into the postprocessing locating base; If this design enables support tabs, grasp each tab, remove it at the prefabricated easy-release interface, and place it in the corresponding scrap bin; Grasp unit rings or rigid lattice nodes, remove the parts from the tray, and place them individually in the numbered compartment box

Postconditions: rubber components free and sorted; unused/removed supports in bin

Recovery: If thin rods are flattened/torn, stop grasping the rods and grasp the rings instead; quarantine damaged parts and remanufacture replacements while retaining the original IDs

Sources and design: The original text establishes only rubber 3D printing; it does not report the release method. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: Actual washing, curing, demolding/support workflows; task-level removable tabs are not source facts

### POST_M Transfer the TC4 build to enclosed postprocessing and retrieve the parts

Location: WS_POST; Targets: build_tray, closed_post_cell, post_panel, component_tray; Object: this branch's object/condition ID

Preconditions: TC4 branch; FAB04 done

Actions: Insert the build box into the enclosed postprocessing unit and close the door; Press the postprocessing button for this work order; the mock releases specimens through a completion event, with the actual recipe supplied externally; Only after safe release, remove the inner tray, grasp rigid end rings/end plates, and place the metal parts in numbered slots

Postconditions: metal components released with no loose process media; postprocessing state retained in lineage

Recovery: Do not bypass the door interlock before postprocessing release; if a specimen is flagged for burrs/residual supports, return it to processing and wait rather than mounting it in the tester

Sources and design: TC4 printing is reported; the postprocessing interface is a reasonable task connector. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: Do not claim the authors used any specific depowdering, heat treatment, cutting, or sandblasting; temperature/residue criteria remain to be determined

### ASM01 Place the bottom plate and assembly locators

Location: WS_ASSEMBLY; Targets: base_plate, assembly_nest, alignment_comb; Object: this branch's object/condition ID

Preconditions: released components at assembly station; assembly recipe bound

Actions: Place the bottom load-bearing plate in the assembly table's locating base; Insert temporary locating combs into the locating holes and move the compartment box within reach

Postconditions: base plate supported; component slots accessible

Recovery: If the locating base is misplaced, lift the bottom plate and reposition it; do not use bent rods as locating stops

Sources and design: Separate chiral units must be assembled into a layered structure. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: Actual positioning/connection tooling

### ASM02 Place the first layer of separate units

Location: WS_ASSEMBLY; Targets: chiral_unit, base_plate, assembly_nest; Object: this branch's object/condition ID

Preconditions: ASM01 done; bottom slots empty

Actions: Grasp the rigid ring of a unit from the compartment box according to the recipe coordinates; Keep the orientation mark facing the corresponding symbol, lower vertically into each bottom-layer seat, and release

Postconditions: bottom layer occupied; no bending-member gripped or broken

Recovery: If orientation is wrong before joining, lift and replace; quarantine dropped parts; use new component IDs for replacements

Sources and design: Layered chiral geometry shown in the figures; rubber 3×3 in-plane array. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: Actual manufactured-part boundaries and paired chirality orientations

### ASM03 Stack the second layer and align the interfaces

Location: WS_ASSEMBLY; Targets: chiral_unit, interface_ring, alignment_comb; Object: this branch's object/condition ID

Preconditions: ASM02 done; matching upper pieces

Actions: Grasp an upper-layer end ring and align it with the joining site on the placed lower layer; Seat it according to the task recipe's mirror/orientation marks; temporarily retain the locating combs to prevent tipping

Postconditions: two-layer arrangement stable; each pair has declared lineage

Recovery: If it cannot seat, lift it back into the tray and correct alignment; do not distort rods to force assembly

Sources and design: Fig4a/b and ED10a/b/c show layering; the original text describes assembly from separate units. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: Part count and actual connection form; 18=144/8 is a figure-supported task decomposition

### ASM04 Complete reversible joining and place the top plate

Location: WS_ASSEMBLY; Targets: interface_ring, cap_plate, surrogate_clip; Object: this branch's object/condition ID

Preconditions: ASM03 done

Actions: Clip reversible joining tabs into the task interfaces on the thick rings; do not bond individual rods; Grasp the top load-bearing plate, align it with the end seats, and lower it so that it bears on all column end faces

Postconditions: assembly can be lifted by designated support; interfaces seated

Recovery: If a joint is not seated, remove the top plate and redo it; do not fill unknown details with permanent adhesive/welding

Sources and design: Assembly of layered structures is reported. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: Joints/fastening torque/adhesive bonding/welding are all unreported

### ASM05 Remove temporary locating tooling and free the intermediate rings

Location: WS_ASSEMBLY; Targets: alignment_comb, transport_support, interface_ring; Object: this branch's object/condition ID

Preconditions: ASM04 done

Actions: Pull out the locating combs in sequence and return them to the tool rack; Install a transport support that holds only the bottom plate without bridging the intermediate rings; clear the upper grasping space

Postconditions: independent middle-ring degrees of freedom remain unbridged; fixture removed from deforming volume

Recovery: If tooling is difficult to extract, first support the bottom plate again and release the load; do not pull thin rods; if locked, remove the tooling again before transport

Sources and design: Chiral deformation requires relative twisting; this does not establish a commercial rotating loading head. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: 

### MET01 Place the specimen on the balance and retrieve it

Location: WS_METROLOGY; Targets: balance, specimen, weighing_tray; Object: this branch's object/condition ID

Preconditions: finished specimen; scale empty; mock mass fixture bound

Actions: Place the empty tray on the balance and tare it; Support the end plate/rigid nodes, place the specimen at the tray center, read the indication, and return it to the numbered tray

Postconditions: whole_mass measured_mock field distinct from published and buckling mass; sample not squeezed

Recovery: For range/drift errors, retain the specimen and mark readout_invalid; do not copy literature values as new measurements

Sources and design: The paper distinguishes whole-specimen density from buckling-component mass; the weighing operation is unreported. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: The authors' weighing method and calibration

### MET02 Measure the envelope and reference height at the dimensional base

Location: WS_METROLOGY; Targets: measurement_nest, caliper, specimen; Object: this branch's object/condition ID

Preconditions: MET01 done

Actions: Place the specimen in the dimensional base, touch the end-plate outer edges with a measuring rule/calipers, and record length, width, and overall height; Retrieve the specimen; retain unit h0/rod L0 separately from overall H, without applying a clamping load to soft rods

Postconditions: reference H/A/V lineage declared; caliper returned

Recovery: If clamping deforms the soft body, release and repeat the reading without compression; if unmeasurable, retain unknown rather than forcing h0=overall H

Sources and design: Whole-specimen and unit normalizations use different denominators. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: Actual geometry-measurement method, errors, and source of the buckling-mass denominator

### TEST01 Transport the specimen by tray to the testing station

Location: WS_TEST; Targets: transport_tray, specimen, tester_stage; Object: this branch's object/condition ID

Preconditions: specimen prepared; machine unloaded and stopped

Actions: Place the specimen end plate in the transport support, retract the robot arm, and move to the testing station; Place the transport tray in the loading staging area and approach from the side with the robot arm

Postconditions: sample staged at tester; identity persists across transport

Recovery: If tipping or collision occurs, quarantine the tray and end this undamaged branch

Sources and design: The specimen must be mounted in a compression device; the transport route is authored. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: 

### TEST02 Open the guard, retract the platen, and clear the loading area

Location: WS_TEST; Targets: guard, tester_panel, upper_platen, removable_fixture; Object: this branch's object/condition ID

Preconditions: machine idle and zero stored-load event; sample outside machine

Actions: Execute safe retraction on the panel; Open the guard, remove the previous condition's lateral-box walls/anti-rotation arms to the rack, and wipe away visible debris on the contact surfaces

Postconditions: clear loading volume; no inherited boundary from previous branch

Recovery: Do not reach in before unloading; if sensors/interlocks disagree, stop the current physical interface rather than skip the stage

Sources and design: Compression boundary control is reported; the safe specimen-loading workflow is authored. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: 

### TEST03 Seat the specimen on the lower platen

Location: WS_TEST; Targets: specimen, lower_platen, transport_support; Object: this branch's object/condition ID

Preconditions: TEST02 done; upper clearance adequate

Actions: Grasp the bottom end plate/ring or thick nodes on both sides and place the specimen on the task locating mark at the center of the lower platen; Release the transport support and remove it from the loading area; do not use the gripper as a boundary constraint

Postconditions: sample seated with declared orientation; robot released specimen

Recovery: If not seated stably, lift and reseat; do not force a tilted specimen flat with the platen

Sources and design: The specimen sits between opposing loading surfaces. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: 

### BND_BOX Install the lateral-confinement box

Location: WS_TEST; Targets: lateral_box_base, removable_box_walls, specimen; Object: this branch's object/condition ID

Preconditions: TEST03 done; branch requires lateral_box

Actions: Take sidewalls of the corresponding height from the tooling rack and insert them individually into the base-frame slots; Close the task latches; keep the upper platen's travel clear while the sidewalls suppress bulging in the target lateral direction

Postconditions: boxed condition set; loading direction unblocked

Recovery: If the wrong height is used or a sidewall intersects the loading travel, return it to its slot and select the correct version

Sources and design: p10, ED9c, and ED10e support lateral-box confinement. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: Box clearance, friction, and mounting form; do not present task values as original-text values

### BND_FREE Remove ring-bridging constraints and preserve chiral degrees of freedom

Location: WS_TEST; Targets: interface_ring, transport_clip, rotation_lock; Object: this branch's object/condition ID

Preconditions: TEST03 done; branch free_internal_rotation

Actions: Remove remaining transport clips/anti-rotation arms from near the rings and place them on the tooling rack; Withdraw temporary lateral supports, retaining end-face loading and space for relative rotation of the internal rings

Postconditions: free internal twist boundary; no added rotary platen claim

Recovery: If a ring is jammed, remove the specimen and return it to the assembly table; do not force twisting through greater compression

Sources and design: Boundary permitting rotational chiral deformation. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: 

### BND_LOCK Install the anti-rotation tooling

Location: WS_TEST; Targets: rotation_lock, specimen_end_ring, fixture_socket; Object: this branch's object/condition ID

Preconditions: TEST03 done; locked-chiral branch

Actions: Take the anti-rotation arm from the rack and key it to the task end-ring interface and frame mount; Fasten the reversible locking tab, retaining axial compression travel while constraining relative rotation

Postconditions: rotation_locked condition; not mislabeled free chiral

Recovery: If the locking tab is not seated, remove and reinstall it; if unresolved, this condition has no valid output

Sources and design: Non-rotatable chiral specimens exhibit nonchiral bending. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: The original authors' rotation-locking fixture is unknown; the sliding keyed connection is a surrogate

### BND_OPEN Remove the lateral box and keep the sides open

Location: WS_TEST; Targets: removable_box_walls, tool_rack; Object: this branch's object/condition ID

Preconditions: TEST03 done; unboxed or no-added-box branch

Actions: If sidewalls remain in the loading area, remove them individually and return them to the rack; Move the camera and tool rack outward so lateral bulging/layer-by-layer buckling does not collide with task furniture

Postconditions: lateral deformation region clear; boundary explicitly open

Recovery: If a side still contacts tooling, stop and remove the interference; do not treat interference as material behavior

Sources and design: The laterally unconfined prism is a reported control; other choices without an added box follow the branch notes. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: 

### OBS01 Position the camera and capture the initial shape

Location: WS_TEST; Targets: camera, camera_stand, specimen; Object: this branch's object/condition ID

Preconditions: boundary set; machine idle

Actions: Adjust the camera mount so the field of view includes all layers and end plates; Capture the current shape: material/specimen/cycle/boundary IDs and chiral angle, rod shape, and layer state

Postconditions: initial image fixture linked; camera outside moving volume

Recovery: For occlusion, move the camera and recapture; do not rotate a specimen whose boundary has already been set

Sources and design: The paper includes deformation images/videos; camera model and positioning method are unknown. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: 

### TEST04 Close the guard and configure the loading program

Location: WS_TEST; Targets: guard, tester_panel; Object: this branch's object/condition ID

Preconditions: OBS01 done; robot retracted from pinch zone

Actions: Close the guard; Select the branch and condition on the panel and set this task's endpoint event/strain and cycle label; leave speed/sampling rate as unknown parameter slots

Postconditions: guard closed; mock cycle armed; scientific recipe not fabricated

Recovery: If a control ID is wrong, clear and reselect before starting; do not run real mode with a missing recipe, while retaining the complete actions in the task design

Sources and design: Cyclic compression is source-supported; specific control inputs are task choices. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: Rate, preload, hold time, sampling rate, calibration, and stopping tolerance

### LOAD Trigger one compression and record deformation

Location: WS_TEST; Targets: tester_panel, upper_platen, camera; Object: this branch's object/condition ID

Preconditions: TEST04 done; load identity bound; guard closed

Actions: Press the start-compression button; keep the robot outside the platen hazard zone; The mock testing machine decreases platen spacing axially until the branch target event, while force/displacement/image events are received

Postconditions: load segment stored for this object/cycle/boundary; observed mode retained without forcing ideality

Recovery: An incorrect boundary/object slippage/drop triggers a stop; target bulging, contact, or asynchronous buckling is retained as a normal observation rather than classified as failure

Sources and design: Compression buckling and deformation observations are source facts. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: Comparison strain is not the complete actual loading endpoint; do not infer curves or rates from video duration

### UNLOAD Unload and separate the platens

Location: WS_TEST; Targets: tester_panel, upper_platen; Object: this branch's object/condition ID

Preconditions: load terminal event; guard closed

Actions: Press unload to retract the upper platen until the external load is removed; Continue recording the unloading segment and finish the cycle after zero_load and safe_clearance events

Postconditions: unloading segment separate from loading; safe unloaded specimen state

Recovery: If jamming occurs during unloading, keep the guard closed and stop the drive; do not pry the specimen while counting recovered energy

Sources and design: Cyclic compression, rubber rebound, and TC4 unloading are source-supported; the videos do not fully show unloading of every specimen. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: 

### OBS_RESIDUAL Capture the post-unloading residual state

Location: WS_TEST; Targets: camera, specimen, tester_panel; Object: this branch's object/condition ID

Preconditions: UNLOAD done; no external load

Actions: Keep the specimen positioned in the machine and capture the end rings, rod shape, and residual height; For metals, record residual plasticity/α0 changes after the first unloading separately; for rubber, retain the current degree of recovery rather than overwriting it as perfect restoration

Postconditions: post-unload state exists; pristine state not reused after metal first cycle

Recovery: Do not present a photo taken before unloading as a residual state; wait again for the unloading event and recapture

Sources and design: Residual plasticity and increased angle after the first TC4 cycle are source facts. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: 

### RELOAD Subsequent compression/unloading of the same object

Location: WS_TEST; Targets: tester_panel, camera, specimen; Object: this branch's object/condition ID

Preconditions: UNLOAD and OBS_RESIDUAL done; same object remains seated; cycle_index incremented

Actions: Without removing or replacing the specimen, select the next cycle on the panel and retain this condition's boundary and target amplitude; Repeat LOAD→UNLOAD→OBS_RESIDUAL, saving separate segments; the default total of 2 cycles is an authored minimum demonstration

Postconditions: repeat segment separately addressable; same object lineage for repeats

Recovery: If the object or amplitude changes, create a new condition/run rather than calling it a repeat on the original same specimen

Sources and design: Repeatability in subsequent cycles is source-supported; the total cycle count is unknown. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: Repeat count and long-term fatigue/durability are unreported

### TEST_REMOVE Open the guard, support the specimen, and remove it

Location: WS_TEST; Targets: guard, specimen, rotation_lock, box_walls, transport_tray; Object: this branch's object/condition ID

Preconditions: UNLOAD completed; safe_clearance and zero_load; guard release

Actions: Open the guard, first support the bottom plate/thick nodes, then release the anti-rotation clamp or detach the removable lateral-box walls; Lift the specimen vertically into its original numbered transport slot and retract the robot arm

Postconditions: machine empty; object retains complete cycle history

Recovery: Do not pull hard on an adhering specimen; fully unload again, release surrogate contact laterally, then support and lift; quarantine damage

Sources and design: Specimen removal is an authored connecting action closing the workflow. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: 

### ARCHIVE Deliver the specimen to its numbered archive slot

Location: WS_STORAGE; Targets: transport_tray, archive_slot, quarantine_slot; Object: this branch's object/condition ID

Preconditions: TEST_REMOVE done

Actions: Move the tray to the corresponding material rack; Place intact specimens in archive slots, retaining cycled/residual labels for metals; put intervention-demo specimens in dedicated demonstration slots and damaged/unknown-history specimens in quarantine slots

Postconditions: sample archived or quarantined; no reclassification as pristine

Recovery: If a slot is occupied, use this branch's backup slot; do not overwrite another specimen's identity

Sources and design: The authors' specific storage procedure is unreported; state preservation is a task requirement. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: 

### CLEAN01 Clear station debris and return tooling

Location: WS_CLEAN; Targets: dry_wipe, waste_bins, tool_rack, transport_tray; Object: this branch's object/condition ID

Preconditions: machine unloaded; sample archived

Actions: Sort surrogate supports/scraps into scrap bins by material; Use a clean dry wipe on the tray, assembly table, and accessible platen surfaces; Return locating combs, lateral-box walls, anti-rotation arms, and camera tools to their marked slots

Postconditions: empty clean work surfaces; tools stowed; no specimen disposed accidentally

Recovery: Keep unknown residues enclosed and quarantined for handling; do not independently use solvents/compressed air to clean TC4 process powder

Sources and design: Closing work is supplied by the task author; the paper does not describe a cleaning recipe. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: 

### CLEAN02 Recover leftover material and reset the machines

Location: WS_CLEAN; Targets: material_cartridge, printer_door, tester_panel, cart; Object: this branch's object/condition ID

Preconditions: manufacturing inactive; CLEAN01 done

Actions: Press the release button, retrieve the partially used sealed cartridge, and place it in its dedicated leftover-material slot; Close the printer chamber door, leave the platen safely retracted, and return the empty transport cart

Postconditions: materials accounted; printer closed; tester safe idle; workspace reset

Recovery: Do not force open a chamber still processing; remain in the waiting state until safe release

Sources and design: The task's closed-loop reset is authored. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: 

### HAND_TOOL Retrieve the demonstration probe, approach, interact, and withdraw

Location: WS_TEST; Targets: blunt_probe, specimen, tool_rack; Object: this branch's object/condition ID

Preconditions: R_TOOL_DEMO only; dedicated object; fixture-controlled pause; no real loaded-machine access without separate engineering safety design

Actions: Take the mock soft-tipped probe from the rack and approach the lattice through the side demonstration opening; Trigger one tool_contact event at the scene-designated contact point, then withdraw and return the probe to the rack; Continue recording the bulging state during the demonstration; tool_contact does not automatically imply that it caused the bulging

Postconditions: approach/contact/withdraw events recorded; demonstration tagged intervention; no pollution of quantitative unboxed curves

Recovery: If the contact point/motion is unknown, retain only the symbolic task path without inventing force amplitude; if real testing prohibits entry, keep the guard closed and use a dedicated remote tool interface

Sources and design: Handheld tool interaction is visible in Video5 at approximately 4.66–5.50s. The specific grasping, transport, mechanisms, buttons, and discrete states are authored connectors. Unknowns: Tool type, purpose, direction, force, and causal relationship to the curve are unknown

## Appendix B: explicit coverage of 77 source units

Purely nonmanual items are covered by N. records, without inflating counts with mechanical actions. Mixed items point to both necessary hands-on stages and theory/analysis. The JSON provides complete operation-template lists; readable branch/stage locators are provided here.

|Source unit|Locator|Category|Corresponding operations/conditions|Nonmanual records|
|---|---|---|---|---|
|main.intro|Abstract/introduction|nonmanual_only|No manual action|N.A.mechanism, N.X.applications|
|main.buckling|Buckling of chiral and non-chiral rods|nonmanual_only|No manual action|N.T.rod, N.T.oblique, N.T.linear, N.T.twist, N.T.geometry, N.T.thick|
|main.mechanism|Mechanism analysis|nonmanual_only|No manual action|N.T.twist, N.T.phased, N.T.micropolar, N.A.mechanism|
|main.performance|Performance comparison|nonmanual_only|No manual action|N.T.lattice, N.T.section, N.T.oblique|
|main.experiments|Experiments|mixed_hands_on_and_nonmanual|ASM01, ASM02, ASM03, ASM04, ASM05, FAB01, FAB02, FAB03, FAB04, POST_M, POST_R|N.P.design, N.A.rubber, N.A.tc4_cycles, N.A.tc4_match, N.A.layers, N.A.small|
|main.conclusions|Conclusions|nonmanual_only|No manual action|N.A.mechanism, N.X.applications|
|methods.fea|Finite element analysis|nonmanual_only|No manual action|N.I.models, N.T.tc4_match|
|methods.buckling|Bending buckling mode / compression buckling / parameter generalization|nonmanual_only|No manual action|N.T.rod, N.T.oblique, N.T.thick|
|methods.chiral|Analytical model / stress evaluation|nonmanual_only|No manual action|N.T.linear, N.T.twist|
|methods.metrics|Performance evaluation|mixed_hands_on_and_nonmanual|MET01, MET02|N.I.denominators, N.A.reduce, N.T.oblique, N.T.lattice|
|methods.samples|Samples|mixed_hands_on_and_nonmanual|R_SMALL20, R_SMALL50|N.I.design, N.I.material, N.P.design|
|methods.experiments|Experiments|mixed_hands_on_and_nonmanual|BND_BOX, BND_FREE, BND_LOCK, BND_OPEN, LOAD, OBS01, OBS_RESIDUAL, RELOAD, TEST02, TEST03, TEST04, UNLOAD|N.A.tc4_cycles, N.A.layers, N.I.acquisition, N.I.fixtures|
|methods.availability|Data/code availability|mixed_hands_on_and_nonmanual|LOAD, OBS01, OBS_RESIDUAL, RELOAD, TEST04, UNLOAD|N.I.models, N.I.acquisition|
|figure.Fig1|Fig1|mixed_hands_on_and_nonmanual|ASM01, ASM02, ASM03, ASM04, ASM05|N.T.rod, N.T.linear, N.T.twist, N.T.lattice, N.A.reduce|
|figure.Fig2|Fig2|nonmanual_only|No manual action|N.T.rod, N.T.oblique, N.T.geometry, N.T.twist|
|figure.Fig3|Fig3|nonmanual_only|No manual action|N.T.lattice, N.T.section, N.P.design|
|figure.Fig4|Fig4|mixed_hands_on_and_nonmanual|R01, R02, R03, R07, R08, R11, M12, M13, M14, M15, M16, R_SMALL20, R_SMALL50|N.A.rubber, N.A.tc4_cycles, N.A.reduce|
|figure.ED1|ED1|nonmanual_only|No manual action|N.T.oblique, N.T.linear, N.T.twist|
|figure.ED2|ED2|nonmanual_only|No manual action|N.T.rod, N.T.oblique|
|figure.ED3|ED3|nonmanual_only|No manual action|N.T.geometry|
|figure.ED4|ED4|nonmanual_only|No manual action|N.T.geometry, N.T.twist|
|figure.ED5|ED5|nonmanual_only|No manual action|N.T.geometry, N.T.lattice|
|figure.ED6|ED6|nonmanual_only|No manual action|N.T.thick|
|figure.ED7|ED7|nonmanual_only|No manual action|N.T.phased|
|figure.ED8|ED8|nonmanual_only|No manual action|N.T.lattice|
|figure.ED9|ED9|mixed_hands_on_and_nonmanual|R02, R03, R04, R05, R06, R07, R08, R09, R10, R11, R_PRISM_L1, R_PRISM_L2, R_PRISM_L4, R_PRISM_UNBOXED|N.A.layers|
|figure.ED10|ED10|mixed_hands_on_and_nonmanual|M12, M13, M14, M15, M16, M17, M_CHIRAL1, M_CHIRAL2, M_CHIRAL3, M_CHIRAL4|N.T.tc4_match, N.A.tc4_match|
|table.row1|Extended Data Table1 row1|mixed_hands_on_and_nonmanual|R01|N.A.reduce|
|table.row2|Extended Data Table1 row2|mixed_hands_on_and_nonmanual|R02|N.A.reduce|
|table.row3|Extended Data Table1 row3|mixed_hands_on_and_nonmanual|R03|N.A.reduce|
|table.row4|Extended Data Table1 row4|mixed_hands_on_and_nonmanual|R04|N.A.reduce|
|table.row5|Extended Data Table1 row5|mixed_hands_on_and_nonmanual|R05|N.A.reduce|
|table.row6|Extended Data Table1 row6|mixed_hands_on_and_nonmanual|R06|N.A.reduce|
|table.row7|Extended Data Table1 row7|mixed_hands_on_and_nonmanual|R07|N.A.reduce|
|table.row8|Extended Data Table1 row8|mixed_hands_on_and_nonmanual|R08|N.A.reduce|
|table.row9|Extended Data Table1 row9|mixed_hands_on_and_nonmanual|R09|N.A.reduce|
|table.row10|Extended Data Table1 row10|mixed_hands_on_and_nonmanual|R10|N.A.reduce|
|table.row11|Extended Data Table1 row11|mixed_hands_on_and_nonmanual|R11|N.A.reduce|
|table.row12|Extended Data Table1 row12|mixed_hands_on_and_nonmanual|M12|N.A.reduce|
|table.row13|Extended Data Table1 row13|mixed_hands_on_and_nonmanual|M13|N.A.reduce|
|table.row14|Extended Data Table1 row14|mixed_hands_on_and_nonmanual|M14|N.A.reduce|
|table.row15|Extended Data Table1 row15|mixed_hands_on_and_nonmanual|M15|N.A.reduce|
|table.row16|Extended Data Table1 row16|mixed_hands_on_and_nonmanual|M16|N.A.reduce|
|table.row17|Extended Data Table1 row17|mixed_hands_on_and_nonmanual|M17|N.A.reduce|
|si.variables|Supplementary Note variables List of variables|mixed_hands_on_and_nonmanual|MET01, MET02|N.T.rod, N.T.twist, N.I.denominators|
|si.1.1|Supplementary Note 1.1 Vertical rods|nonmanual_only|No manual action|N.T.rod|
|si.1.2|Supplementary Note 1.2 Summary and analytical examples|nonmanual_only|No manual action|N.T.rod|
|si.1.3|Supplementary Note 1.3 Oblique rods|nonmanual_only|No manual action|N.T.oblique|
|si.1.4|Supplementary Note 1.4 Nonchiral lattice model|nonmanual_only|No manual action|N.T.oblique|
|si.2|Supplementary Note 2 General3D chiral / linear model|nonmanual_only|No manual action|N.T.linear|
|si.3.1|Supplementary Note 3.1 In-plane bending|nonmanual_only|No manual action|N.T.twist|
|si.3.2|Supplementary Note 3.2 Out-of-plane bending|nonmanual_only|No manual action|N.T.twist|
|si.3.3|Supplementary Note 3.3 In-rod twisting|nonmanual_only|No manual action|N.T.twist|
|si.3.4|Supplementary Note 3.4 Helix correction|nonmanual_only|No manual action|N.T.twist|
|si.3.5|Supplementary Note 3.5 Pure compression shortening|nonmanual_only|No manual action|N.T.twist|
|si.3.6|Supplementary Note 3.6 Compatibility|nonmanual_only|No manual action|N.T.twist|
|si.3.7.1|Supplementary Note 3.7.1 Force equilibrium|nonmanual_only|No manual action|N.T.twist|
|si.3.7.2|Supplementary Note 3.7.2 Energy method|nonmanual_only|No manual action|N.T.twist|
|si.3.8|Supplementary Note 3.8 Combined theory / iteration / stress|nonmanual_only|No manual action|N.T.twist|
|si.4.1|Supplementary Note 4.1 Micropolar introduction|nonmanual_only|No manual action|N.T.micropolar|
|si.4.2|Supplementary Note 4.2 Constitutive reduction|nonmanual_only|No manual action|N.T.micropolar|
|si.4.3|Supplementary Note 4.3 Free rotation / two nonlinear models|nonmanual_only|No manual action|N.T.micropolar|
|figure.S1|FigS1|nonmanual_only|No manual action|N.T.rod|
|figure.S2|FigS2|nonmanual_only|No manual action|N.T.oblique|
|figure.S3|FigS3|nonmanual_only|No manual action|N.T.linear|
|figure.S4|FigS4|nonmanual_only|No manual action|N.T.twist|
|figure.S5|FigS5|nonmanual_only|No manual action|N.T.twist|
|figure.S6|FigS6|nonmanual_only|No manual action|N.T.twist|
|figure.S7|FigS7|nonmanual_only|No manual action|N.T.twist|
|figure.S8|FigS8|nonmanual_only|No manual action|N.T.micropolar|
|video.1|Supplementary Video 1|nonmanual_only|No manual action|N.T.section, N.T.rod|
|video.2|Supplementary Video 2|nonmanual_only|No manual action|N.T.section, N.T.twist|
|video.3|Supplementary Video 3|nonmanual_only|No manual action|N.T.section|
|video.4|Supplementary Video 4|hands_on_route|R01||
|video.5|Supplementary Video 5|mixed_hands_on_and_nonmanual|R_PRISM_L4, R_PRISM_UNBOXED, R_TOOL_DEMO|N.A.layers|
|video.6|Supplementary Video 6|hands_on_route|R03, R04||
|video.7|Supplementary Video 7|hands_on_route|R08, R09, R10, R11||


## Delivery status and boundaries

This is an initial task design covering the whole paper; all source units have a disposition and all physical conditions have operational designs from materials through closing work. The action interfaces have not yet been implemented as complete robot tasks, and the full scene/interaction asset set is not yet built; existing static coarse assets are not executable fabrication/assembly mechanisms. Design coverage, scene assets, robot reachability/execution, and scientific reproduction are four separate axes. The permitted next step is to implement task interfaces and evaluation from this specification; no physics simulation is started here.
