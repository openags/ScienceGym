# Reprogrammable mechanical logic: whole-paper design coverage

## Claim and source boundary

This independent ScienceGym contribution describes robot-oriented operations for the physical program reported by Mei et al., Nature Communications 12, 7234 (2021), DOI [10.1038/s41467-021-27608-7](https://doi.org/10.1038/s41467-021-27608-7). It is original task-design material. It contains no publisher text dump, source figure pixels, original movie, CAD, or reconstructed source measurements.

The source packet is incomplete. The main article's narrative, Methods and captions were read in publisher HTML. The retained main snapshot originally skipped a middle range; the canonical public HTML was reread for lines 102–167. All 17 SI pages were read as text and inspected in retained page contact sheets. The one-page movie-description file was read. Main figure panels and all nine movie contents are uninspected. The main PDF identity-provider redirect route remains stopped; no retry or bypass was attempted. Source-complete, execution-ready and scientific-replication labels are false.

Inspection of text establishes reported experiments and qualitative mechanisms. It does not supply all manufacturing geometry, exact main-figure instruction masks, wiring details, loading rates, source voltage, switch speed, storage duration, readout thresholds, uncertainty or robot trajectories. These remain explicit gates. A qualified future implementation may close a gate; it must preserve the distinction between recovered source facts and authored implementation choices.

## Program map

The 14 physical-design routes cover preparation as well as measurement:

1. MACRO_SIGNAL: issue TPU and rigid resin, fabricate separate beam and rigid-part jobs, identify, glue, cure, lubricate and assemble supported signal elements
2. MEMORY_PREP: prepare and mount the separately identified bistable instruction-memory elements under a qualified recipe; missing memory fabrication details are not borrowed silently from signal fabrication
3. NORMAL_TEST: calibrate the force/displacement chain, mount and measure the normal signals, release and inspect
4. SMALL_TEST: the corresponding small-signal measurement, with a separate role and allocation
5. MEMORY_TEST: the bistable-memory response measurement, with separate reset/acceptance criteria
6. ARRAY_PREP: prepare the AU, ReIM, electromagnets, circuit, slide-switch contacts and synchronized state readout
7. NOR: the four Boolean input alternatives, each independently initialized
8. NOT: both input alternatives with its own verified instruction mask
9. OR: all four alternatives with its own mask
10. AND: all four alternatives with its own mask
11. DEFECT_ROUTING: physically reported parity-bridged transmission/bifurcation, with explicit topology and custody
12. VOLATILE_STORAGE: write, maintain the two-row pair, release upstream signals, read retention, archive and clear
13. MECHANICAL_NOR: separate mechanically loaded three-element proof, with its own memory/loading/readout qualification
14. MESOSCALE_FAB: scale-specific UTL printing and inspection only

These are design route counts, not experiment or execution counts. The branch membership lists are not the authors' historical chronology. Dependencies constrain compatible occurrences. Shared preparation can be retained for downstream work using a verified handoff rather than repeatedly fabricated. Cleanup occurs on final station release, abort, or campaign completion; it must not erase a state that an active storage observation still needs.

Twelve nonmanual dispositions cover the FEM model, numerical NAND, alternate planar NOR, half adder, large crossover, compact crossover, S-R latch, explanatory two-instruction strategy, perfect-topology routing illustration, roller-array illustration, future microscale/MEMS proposal, and source-described storage read/rewrite extension. No physical completion record can count one of these as a reported experiment. Fig7a–c supports volatile retention; Fig7d is not silently promoted to a second full sequential-computing experiment. SI Fig5d supports the three-element mechanical NOR, not a fabricated roller-driven array.

## The three different state systems

Signal elements in the AU are monostable. Their geometric bit is defined relative to the line joining sleeve-center datums: midpoint above is 0 and below is 1. A qualified deadband is required. Near the datum, occluded or uncalibrated observations remain unknown. Returning a switch to its initial position is a command; actual unloaded signal0 observations establish reset.

ReIM instruction memory is bistable and remains a separate entity from the AU. SI gives a 62 mm fabricated beam installed between supports 60 mm apart. Upward/downward buckles represent on/off in the electrical variant. Reprogramming changes the instruction revision. Resetting transient signals does not itself erase the persistent instruction. The horizontal mechanical-memory variant uses passage obstruction; its geometry and programming tool are separately qualified.

Volatile storage uses two adjacent signals in different rows with maintained excitation. One held signal cannot generally preserve 0 once neighboring constraints release. Retention compares a post-write, pre-upstream-release baseline against the later observation from the same uninterrupted hold epoch. Both storage rows remain powered throughout. Snapshot images alone cannot prove continuity; a scoped event-stream continuity receipt is required. An interruption closes or invalidates the epoch, and a new write requires a new baseline. Clearing releases both rows and verifies reset.

## Robot and automatic-device boundary

The 55 reusable operations identify actor, object roles, station, preconditions, physical actions, observable postconditions, source evidence, gates and recovery. Device-autonomous print and test cycles are separated from robot loading, control use and unloading. A program request, printed label or spoken completion cannot substitute for an inspection or device receipt.

Macro fabrication separates the TPU FDM beam from SLA resin sleeves/supports. A completed print process is not a qualified component. Inspection is conditional; rejected and unknown parts are retained and quarantined. The signal assembly retains a component graph of beam, two sleeves, support and bond process. Petroleum jelly belongs to the sleeve interiors under a qualified application card. Adhesive chemistry, cure, dose and solvent cleanup are not invented.

The compression station retains the source-reported Zwick Z005, 50 N load cell and simply supported fixture as apparatus references. Midpoint alignment, calibration validity, travel, force bounds and rate come from qualified instance cards. Signal release/monostability and memory bistability use role-specific acceptance. Nothing in this package establishes that the test is harmless enough to reuse every specimen; a post-test integrity decision governs reuse.

The electromagnetic station distinguishes component placement, sleeve-neighbor contact, actuator mounting, wiring, contact mapping, force-window calibration and vision calibration. Each signal and its corresponding memory are a series pair; row branches are switched sequentially. The reported switch excites at most three rows during a sweep and holds the declared last two for storage. Hardware excitation must be calibrated against constrained/unconstrained response with uncertainty and thermal limits. SI numerical 3 N and 5 N loads are not voltage settings or hardware calibration receipts.

Mechanical NOR uses MECH_CAL and MECH_READ. It does not import electrical row-history preconditions or electromagnetic calibration. Its loading-bar travel, obstruction geometry, load bounds, release and readout require proof-specific cards. The draft's input-before-output ordering is an authored realization of the reported NOR mechanism, not a timing trace recovered from the unread movie.

## Topology and specimen custody

The reported AU has twelve normal and two small signal elements. Fourteen measured instruction-memory elements are separate specimens. The twelve normal responses and two small responses are not independent newly fabricated AUs; truth-table cases and trace samples do not increase specimen count. The source says experiments reuse the same ReMM, but does not establish a complete serial-number or test-order history. New episodes explicitly allocate identities and finite repeats.

A parity bridge replaces one normal element by two small elements. The reported fourteen-signal AU can already contain that bridge. DEFECT_ROUTING therefore first checks whether the qualified bridge already exists. It either verifies the existing graph, or performs an explicitly requested one-for-two transaction and increments the topology/assembly revision. It cannot silently install an extra bridge or apply an old calibration to altered contacts.

Carriers support qualified regions rather than arbitrary thin beam centers. Transport records bind payload IDs, origin custody, destination, isolation, detached tethers, retained supports, qualified path and post-move integrity. A dropped, damaged or ambiguous item is quarantined with its existing identity. A replacement receives a new identity and links to the rejected predecessor. Reconfiguration invalidates affected contact, wiring, calibration and readout scopes. Custody cannot change merely because a record declares a new station.

## Conditions, controls and completion

Symbolic loops represent fabrication jobs, specimen/cycle tests, independent truth cases, routing cases, storage epochs and mechanical proof cases. Repeat counts remain null until a qualified bounded schedule is supplied; null is not zero, one, or successful empty work. Boolean truth tables define distinct input combinations but do not establish experimental replicate counts.

Control packages require calibrated no-load references, fresh role-specific reset, verified instruction masks, actual input observations, measured row/contact histories, state-readout calibration and post-use release. Storage adds before/after state and continuous two-row hold. Mechanical proof adds its own loading and readout chain. Mesoscale output is inspection evidence only.

A route has procedural coverage only when every required condition has classified, immutable observations plus prerequisite, control, reset, custody and cleanup receipts. Scientific disagreement is preserved: an accurately acquired wrong output can be procedure-valid and scientifically unsuccessful. Rejected acquisition, missing raw data, unknown bits and failed safety conditions do not complete a case. An episode selecting a subset cannot claim the complete truth-table route or whole-paper execution.

Whole-paper physical execution would require every physical route, the complete dependency/control closure and trusted runtime evidence in a named environment with all required execution gates resolved. No such runtime, apparatus run, physical simulation, robot driver, deformation model, electrical solver or science replication is provided. The draft instead makes the missing implementation work reviewable.

## Evaluation and release boundary

agent_visible.json is the sole actor-public static file. A future loader supplies only the goal, qualified cards, inventory, existing observations and public device status. The actor must not receive evaluator outcomes, hidden faults, future frames, source expected outputs or complete reference routes. All other package documents are authoring/review material.

The original Python checks cover JSON identity/reference integrity, physical/numerical separation, unknown-gate closure, source-readiness boundaries, symbolic loops, actor visibility, revision and reset lineage, truth-case coverage, actual-input ordering, row limits, volatile hold continuity, transport custody and exact export hashes. Fixtures are explicitly synthetic. The checker deliberately refuses to certify real-device records; caller-supplied dictionaries are not authentication. Passing tests means static and synthetic-bookkeeping consistency only.

Use `python3 -B tests/verify_package.py` and `python3 -B -m unittest discover -s tests -p 'test_*.py' -v` from this package. No third-party Python dependency is required. The exact authored export boundary is EXPORT_ALLOWLIST.json. Publication remains the parent project's decision; this worker made no public write.
