# Horn-like metasurface: whole-paper robot-task design

## Scope and source boundary

This local schema, horn_acoustics_paper_task.v1, describes the physical experimental program of Ghaffarivardavagh et al., Nature Communications 9, 1349 (2018), DOI 10.1038/s41467-018-03839-z. Full main text, Methods, seven main figures, the twenty-page SI, four notes, nine SI figures and both tables were inspected. The OpenBU PDF has a repository cover followed by eight published pages. Peer review is listed but unread; no movies are listed in the retrieved article.

The only measured wavefront demonstration is cylindrical-to-plane conversion, the reverse of the focusing design. A fabricated ABS panel is compared with its absence under a localized source. Forward focusing, splitting, analytical bounds, transfer matrices, loss calculations and all SI parameter comparisons remain theoretical or numerical. There is no physical impedance-tube branch, beam-splitter specimen or phase-only control hidden in this design.

## Experimental intent and count semantics

The focusing design has thirty positions of width lambda/6 and length lambda/2. Table 1 specifies fifteen rows and maps row i to positions i and 31-i. This does not establish how many separately printed parts or batches were used. A qualified segmentation manifest supplies that missing manufacturing choice. The analogous splitter table is reference-only numerical geometry.

The source reports two initially calibrated Audix TM1 microphones: a fixed reference and a moving probe. Each condition has 190 equally spaced positions at 9 cm centers, with ten complex transfer-function readouts averaged per position. Table 2 is indexed X1-X10 and Y1-Y19. These are spatial samples and technical readouts, not independent specimens or repeated campaigns. One complete authored paired campaign needs 3,800 valid readouts arithmetically; the source does not provide those underlying raw records or independent replication statistics. Its two complex arrays are averaged literature data and are not included here.

## Preparation, fabrication and embodied work

The initial state contains identified stock and unassembled resources, qualified cards when eventually available, and unbound assets. It does not contain an accepted final panel. The robot issues ABS, tools and supported carriers; loads and starts an identified print job; waits for device completion and safe release; unloads, finishes and measures parts; and assembles and inspects a versioned focusing panel. Fabrication repeats over a finite qualified job/segment manifest. Support removal is a robot-facing qualified procedure, not an unnamed outside service.

Thirty design positions are covered exactly once by inspected physical part membership. A monolithic or segmented build can satisfy this contract if qualified. A replacement or rework changes the part or panel revision and invalidates downstream inspection. Printer resolution of 0.2 mm is source-reported; it is not a manufacturing tolerance, layer prescription or guarantee that the CAD is printable.

The robot retrieves two plywood sheets measuring 250 by 250 by 2.5 cm using a payload-rated lift/fixture, seats the base, fits supports and 5 cm absorbing foam, mounts the speaker/tube source, places the upper sheet and checks the 2 cm parallel-sheet gap. Rated handling, port access, joining, seals, acoustic boundary layout and tolerances are missing input cards. No untested single-arm lift is assumed. All carried resources retain identity through MOVE occurrences with departure, retention, docking and arrival evidence.

## Calibration, source and scan

Both microphone/channel pairs undergo separately identified calibration mount, acquisition, acceptance and unload occurrences. The calibrated reference is locked at a qualified pose; the scanning probe is mounted with safe cable travel. A registered grid resolves source and panel frames, all 190 actual coordinates, reference position and the approximate 40 cm boundary-offset statement. Photographs are not metric robot poses. The two-channel DAQ receives a declared channel map, transfer direction, clock, capture settings, phase convention and quality rules.

The reported experimental frequency is 1 kHz. Physical source level, voltage and tube dimensions are unspecified. The simulated incident amplitude of 1 kPa must never become a physical drive setting. Absolute wavelength conversion also remains gated; no sound speed is silently assumed.

For either condition, isolate the source before changing the panel, park the probe clear, establish the panel-presence state, restore domain closure and verify the matched configuration. Either condition order is allowed; the paper's historical order is not reconstructed. Each point requires observed probe placement and settling, then ten distinct valid two-channel readouts under stable epochs. Failed attempts remain in the record and explicit replacement attempts fill the same slot. Averaging requires all ten selected readouts and a declared complex aggregation rule. Completing a map requires every grid point, a source-off receipt, immutable export and a post-map reference stability assessment.

A reference move, expired calibration, panel rework, grid change or altered acquisition/source configuration invalidates the affected downstream evidence. A command or an actor-written success flag is not an authoritative receipt. Interrupted partial scans retain their acquired prefix, but no incomplete point or map qualifies as finished.

## Comparison, data and cleanup

The paired-control contract permits panel presence to vary and otherwise checks rig, source, microphones, reference pose, calibrations, channel map, grid and processing cards. Comparing unrelated successful maps is not a completed control package. Qualified normalization precedes spline visualization; both retain hashes and lineage to the original complex grid. Interpolated pixels never increase physical sample count. Table 2 values and numerical fields never satisfy acquisition predicates.

Archive preparation, manufacturing, custody, calibration, both conditions, failed attempts and processing records. A valid weak or negative measured result may pass operational criteria; matching a paper number is not an acceptance rule. End by verifying source isolation, parked probe, supported panel removal/storage, both protected microphones, returned tools, waste disposition and safely restrained apparatus. Historical cleanup details were not reported; these are authored workflow closure.

## Readiness and evaluation

The design contains 44 operation templates, five physical/prerequisite/closure branches and nine explicitly nonphysical reference branches. Seventeen unknown-input groups block execution. The source coverage matrix covers the whole reported program without converting numerical work into physical tasks.

Every operation specifies actor, object roles, station, interface, concrete actions, preconditions, changed state, observable evidence, source IDs, missing gates and failure handling. Templates are a partial-order vocabulary, not an installed runtime API or verified action sequence. Occurrence IDs distinguish calibration by microphone, fabrication by job and acquisition by condition/point/slot/attempt.

The package has no CAD, robot binding, acoustic solver, trusted event infrastructure, qualified operating cards or experimental raw readouts. Structural tests use explicitly synthetic bookkeeping records. They establish contract behavior only, not acoustic performance, robot reachability, safety qualification or scientific replication. An independent source/contract review and exact export manifest accompany the completed candidate.

## Synthetic occurrence checks

The test occurrence graph expands fabrication by job and component, calibration by microphone, setup and closure by condition, and acquisition by point and readout attempt. Prerequisite event IDs and logical ordering must match; probe-pose and raw-readout receipts bind to their events. Reversing condition order selects the corresponding final panel-return path. Phase-convention cards remain part of the matched control state and readout epochs. These checks reject a dictionary of generic completed operation labels as a substitute for occurrence evidence. They do not authenticate hardware, establish physical timing or qualify placeholder cards.
