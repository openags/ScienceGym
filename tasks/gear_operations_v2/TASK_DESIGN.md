# Gear metamaterials: whole-paper robot-task design

## Status and scientific scope

This is an original, gated design for Fang and colleagues, “Programmable gear-based mechanical metamaterials,” Nature Materials 21, 869–876 (2022), DOI 10.1038/s41563-022-01269-3. It describes 18 physical branch templates, 19 specimen families, eight preparation routes and 69 reusable operation contracts. Seven numerical branches and two required analysis/comparison obligations are represented separately. These counts describe authored contracts, not executed trials.

The inspected main deposit is the journal version-of-record PDF obtained from the Hong Kong Polytechnic University institutional repository, corroborated by Europe PMC full-text XML. The publisher-hosted written supplement is author-provided and unedited. The inherited source audit covers the complete main article and Methods, all five main figures, all 27 SI PDF pages, 23 SI figures and two SI tables. The five video legends and eight distributed keyframes per acquired video were reviewed. Full-motion and audio inspection are not claimed. No publisher authorization redirect was retried, and no new correction/version search is claimed beyond the lawful packet.

This package contains no source PDFs, source text dumps, pictures, video frames, raw datasets or reconstructed meshes. Source-access facts and hashes are in `provenance.json` and `source_access_audit.json`. CC BY 4.0 is recorded for the main article; third-party picture exceptions remain relevant, including the stock image credited in SI Fig. 19a. Only original English task descriptions and bookkeeping code are included.

## Experimental program and specimen identities

The physical program includes:

- Separate 5×5 metallic Taiji compression families for P+(3°) and P−(15°), plus a steel-frame-only control
- A 5×6 micro-Taiji integrated-fabrication demonstrator, a 4×4 compression specimen and a 5×5 motor-actuated specimen
- Steel planetary 3×3 compression and 2×2 tension specimens
- Macro-polymer planetary 6×6 compression, 2×6 tension and separately identified 6×6 actuation specimens
- Micro-polymer planetary 3×4 compression, 2×3 tension and separately identified 3×4 actuation specimens
- A finite 3×3 Taiji shear fixture
- A 4×4-metacell aluminum-gear/rubber-frame shape-morphing structure and its rubber-frame control
- A 3×3 impact-isolator specimen family handled only through a qualified guarded service

Identical shapes do not imply a shared historical specimen. The source does not provide serial identities or sufficient repeat counts. Each episode must allocate actual specimen IDs, component lots, bounded conditions and repeats. The 4×4 macro-Taiji demonstrator seen in sampled Video 1 is an additional illustrative family. It is never merged with the 5×5 quantitative family. A person standing on a plate supplies neither an inferred load magnitude nor a safe robot test prescription.

Component materials are explicit: metallic Taiji gears and steel frames have separate material roles; micro-Taiji test/actuation assemblies include steel micro shafts; soft assemblies bind aluminum gears and rubber frame/shaft components. The impact polymer's approximate 2.0-GPa declaration is not the general macro-polymer 2.5-GPa resin declaration.

## Physical operation contracts

`operations.json` gives each operation an actor, manipulated objects, tool, station/interface, observable preconditions, action, device-owned process, postconditions, receipts, source evidence, unknown gates and recovery boundary. Robot manipulation is authored, even when its scientific purpose is source-grounded. No autonomous historical experiment is asserted.

Preparation is first-class work. The routes identify incoming lots, bind certified drawings, stage and retrieve qualified fabrication jobs, inspect parts, preserve micro-Taiji phase with a surrounding box before baseplate removal, remove macro-polymer print support, install/capture shafts, assemble separate frames and transmission layers, and inspect topology and meshing. The placement of micro-shaft attachment after constrained plate release is an authored sequence requiring qualified choreography, not a recovered source instruction.

Every physical-station change uses an explicit supported-carrier transfer. No grasp pose, carrier dimension, insertion force, calibration sample count or collision path is invented. Current geometry, grasp regions, payload, limits and station frames must come from qualified input cards. In-situ imaging is a logical observer: it cannot move a mounted specimen to another station.

The loading routes explicitly select and inspect compression platens, tail clamps, the shaft-mounted roller-guided shear fixture, or diagonal right-angle grooves. They bind actual geometry and boundary conditions to calibration, mounting and zero receipts; arm synchronized acquisition; execute bounded device-owned cycles; seal raw records; unload; release under support; inspect for damage; and clean/store. Tension tails and compression ring blocks cannot be exchanged by label. Boundary friction and finite specimen dimensions remain part of interpretation.

Actuation includes coupler attachment, electrical mapping, home/phase verification, acquisition-ready acknowledgement, bounded motor commands, observations, stopped-motion/isolation evidence, raw-data sealing and supported release. Commands or pulse frequency are not calibrated achieved angles. Missing motor mapping and synchronization tolerances stay gated.

Impact is intentionally a closed qualified-service contract. The source reports a 10-kg mass and 20-mm release gap. Those are source conditions, not instructions for a general robot to lift or drop a mass. The approved enclosed service exclusively owns mass handling, arm/release/reset, independent guards and safe-access readbacks. Retrieval requires its current safe-release proof. The authored allocation treats each impacted object as terminal and quarantines it; this conservative policy is not attributed to the source. Subsequent conditions require distinct specimens.

## Dependency, repetition and completion

`branches.json` separates reusable preparation from per-condition actions. Recipes express an authored valid order rather than the authors' historical chronology. Each occurrence must bind campaign, branch, specimen/version, condition, attempt, cycle/repeat and occurrence index. Reconfiguration requires physical indexing and a new measured phase state, followed by current mounting and zero checks. Repeated cycles and angles do not increase independent specimen count.

Missing cycle counts are neither zero nor one. A qualified finite schedule is required. At least one usable cycle after the excluded initial cycle is an authored data-validity minimum, not a recovered source repetition count. A branch with unresolved dependencies cannot be execution-ready, while an unrelated branch may be separately qualified. Outsourced fabrication can be declared, but it must supply equivalent material, geometry and service receipts and cannot be presented as robot-performed fabrication.

A selected branch episode does not establish whole-paper execution. Whole-paper physical scope requires all 18 branch obligations, eligible measured hysteresis analysis, comparison/archive completion and all five control packages. Numerical reproduction is separate and has its own unavailable solver/input requirements.

## Analysis and nonphysical boundaries

Young-modulus fitting excludes the initial cycle and uses qualified intervals near maximum strain. The paper's modulus error bars reflect changing slope-fit intervals. They are not independent-specimen standard deviations, and repeated cycles do not establish between-batch reproducibility.

The finite shear fixture produces generalized finite-structure stiffness, G′. The displacement/loaded-span and slope/axial-width normalization must use measured geometry. Periodic-cell shear modulus G is a different modeled quantity; the two must not be equated simply because an expression has the same algebraic form.

Soft-lattice sequential slips and oscillations are observable behavior. They cannot be removed automatically as sensor noise or forced mechanically through a jam. The diagonal-load transform is a qualified analysis input, not an invented reconstruction. Measured damping uses enclosed hysteresis area divided by the loading-curve-to-strain-axis area, with cycle and strain-amplitude provenance. SI Fig. 22 contains experimental points as well as an FEA curve; both are represented with different parents.

The seven numerical branches retain 2D/3D distinctions, bonded versus nonlinear contacts, simplified teeth-free models, polarity/phase sweeps, boundary sensitivity, finite versus periodic shear, and tooth versus shaft-hole friction. No simulation was run. The literature comparison, pylon/wing/robot-skeleton proposals, skin illustration and design catalog are dispositions, not fabricated quantitative experiments.

## Unresolved source facts and execution inputs

The micro-planetary sun radius is 0.6 mm in main prose and 1.2 mm in SI Table 1. The table prints a planetary radius of 0.06 mm. The table's ring-module row also conflicts with the same-module meshing requirement and may refer to another gear layer. This package neither repairs decimals nor relabels the row. A certified dimensional drawing and accepted metrology, or author clarification incorporated into such a drawing, is required. A material certificate or analysis declaration cannot close a dimensional fabrication gate.

The main's copper wording and SI's brass/copper-alloy wording both remain. The steel planetary measured 46× prose and theoretical 73× plot annotation stay separate. The frame's 2.0±0.4 MPa report and 2.06 MPa main value are not silently equated. Correct figure IDs accompany the source's mistaken cross-references.

The 18 open input categories cover allocation, materials, CAD, planetary geometry, fabrication, robot handling, phase, fixtures, calibration, loading, acquisition, motors, impact service, analysis, reuse, cleanup and numerical decks. `unknown_parameters.json` records their consequences and qualification roles. No concrete operator or provider has accepted those roles.

## Verification and release interpretation

The tests exercise static source/contract consistency and synthetic receipt bookkeeping, including negative cases for specimen conflation, material/component substitution, unresolved geometry, missing preparation, phase/fixture/calibration errors, initial-cycle fitting, wrong error bars, modeled physical parents, motor capture omissions, impact guards/reuse, observation teleportation and false whole-paper completion.

Synthetic positive examples are explicitly labeled and contain no physical force/displacement traces. Their arbitrary toy counts and tolerances are not proposed laboratory settings. The synthetic checker enforces the declared handling recipe, while allowing derived analysis after its raw parent and repeated in-situ images. It does not yet implement arbitrary equivalent physical routes. The checker is not a trusted event logger, hardware evaluator or robot runtime, and passing it cannot establish feasibility or scientific replication. The actor projection is specified but unimplemented: reference outcomes, future observations, hidden faults, evaluator routes and answer keys must not be provided to a future task actor.

Only the exact authored files in `EXPORT_ALLOWLIST.json` are eligible for later integration. No public write, new physical asset, screenshot review, numerical reproduction or physical experiment was performed. See `VERIFICATION.json` and the independent review for the final check scope and remaining limitations.
