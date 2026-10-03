# Mechanical-network backpropagation: whole-paper mobile-robot task design

Li and Mao, *Training all-mechanical neural networks for task learning through in situ backpropagation*, Nature Communications 15, 10528 (2024). [Article and Methods](https://www.nature.com/articles/s41467-024-54849-z), DOI 10.1038/s41467-024-54849-z.

## Status and scientific boundary

This is an independently authored ScienceGym task-design draft. It specifies a future mobile robot's physical preparation, tool use, transport, station loading, parameter binding, start requests, observation, unloading and cleanup. No robot task, physical simulator, fabrication job or experiment has been executed or validated. Missing qualified inputs remain gates, not guessed defaults.

The physical work is organized into nine selectable test routes plus a whole-paper campaign: two forward/adjoint gradient cases, three initial/trained behavior configurations, one regression sweep and three Iris feature inputs. Shared fabrication and calibration are real task stages. The computational work has its own explicit coverage inventory; it cannot substitute for the physical routes. A complete source-matched physical campaign requires all nine configurations, all seven regression load points and three valid independent trials per case. A subset or changed repeat count is a bounded partial episode or authored departure, not that complete campaign.

The central distinction is essential: the study physically obtained forward and adjoint responses and tested fabricated networks. Updating the bond spring constants during training was numerical. A geometry file becoming a new version does not change an already printed lattice. A trained geometry must produce a separately identified fabricated specimen before its physical response is tested. Physically self-updating hardware, physical task-switch retraining and physical damage recovery are not reported demonstrations and are not executable branches here.

The full main article text, all 16 SI pages as text, selected SI figures, the supplementary-video description sheet and the three-page reporting summary were read. The official Source Data workbook was inspected for its five-sheet structure and relevant figure-level experimental columns. Its full numerical lineage was not independently reproduced. The author repository README and top-level inventory were read, but implementation files and exact archived commit were not audited. Five video descriptions were read; no movie frames were viewed. Each inspection boundary and requiredness decision appears in `source_access_audit.json`.

## What a future actor receives

The actor receives one selected public goal, actual initial inventory, identifiers and qualified cards for geometry, materials, instruments, loading, acquisition, analysis and safety. It sees observations acquired during its own work. It does not receive the expected response, source-result arrays, hidden faults, evaluator assertions or a mandatory reference action sequence. A classification trial's true species may remain with the evaluator until the prediction is committed; the actor can still receive the anonymous feature-to-weight card.

The package itself is a design/reference artifact, not an actor prompt. Release separation is specified, not implemented as a runtime security mechanism. `agent_visible.json` defines the permissible projection; `evaluator_reference.json` and `source_outcomes.json` remain reference-only.

All grasp locations, carriers, tools, docking, interlocks, timing criteria, calibration acceptance limits, record formats, recovery and cleanup below are authored robot translations. They are not claims about the authors' precise hand motions. Source evidence supports the apparatus and scientific conditions, not robot reachability or dexterity.

## 1. Preparation, numerical design and fabrication

A robot starts at records, binds the work order and allocates specimens, fixture IDs and trial IDs. It retrieves qualified packaged stock, clean indexed trays, supported carriers, strings, certified weights and appropriate handling tools from storage. Hands retract and loads are retained before base movement; a station transfer requires verified source release and destination docking. Records alone cannot move an object.

The geometry route distinguishes an initial uniform network, a numerically trained final network and an explicitly supplied prequalified geometry. The computation service may generate widths from a bound model, dataset, seed/split, optimizer and convergence card. It returns a versioned digital result, with model and training provenance. It neither edits physical spring constants nor reports physical success. Exact historical widths, topology, node indexing and training checkpoints are unresolved without a verified source mapping. A future supplied geometry must state whether it is an authored reconstruction or a verified author file.

The source material is black flexible Agilus30, printed with a PolyJet J850 Digital Anatomy system. SI Note 6 gives 16 mm bar length and 2 mm thickness. Main Methods specify thinner attachment regions at half the bond width; SI gives an 8:1 bar-to-thinner-end length ratio. Numerical middle-width bounds are 1.5 to 2.5 mm with an initial width of 2 mm. These are source constraints, not complete CAD. The exact interpretation of the end-length ratio, junction geometry, boundary pads, print orientation, tolerances and machine settings must be resolved in a qualified manufacturing card. Do not derive two end lengths by assumption or turn the network illustration into a manufacturing file.

Fabrication is an enclosed, qualified station service. The robot stages identified consumables and the build carrier, binds the geometry checksum to the job, verifies material and recipe readback, closes guards and requests start. The device executes only the approved job. The robot observes completion and a safe-unload indication, then receives the part on its carrier. Support removal, cleaning, conditioning and any post-curing are separately card-defined postprocessing steps. They are not automatically omitted because the paper does not list them. No uncured resin handling or invented chemical recipe is permitted by this draft; require a qualified enclosed service or stop that fabrication path.

Dimensional inspection records actual bond/junction dimensions, defects and geometry-to-part correspondence. Qualified acceptance limits, measurement uncertainty and handling regions are supplied inputs. An out-of-tolerance part is quarantined or reworked under a new attempt/version; it is not made acceptable by changing the label. A supplied already-fabricated specimen is allowed only in an explicitly preparation-excluded episode. It cannot complete a fabrication-required goal.

## 2. Truss assembly, attachment and safe transport

At assembly, the robot stages an identified support truss in an alignment jig. It assembles or checks its connectors with the supplied fastener/tool card and installs a load-catch tray. It supports the soft lattice at approved regions and attaches only the specified two fixed nodes to the truss. The original method uses glue; adhesive identity, quantity, surface preparation, cure schedule, attachment area and qualification load are not recovered. All are release gates. Do not improvise an adhesive or infer a cure duration from a photograph.

Cure/release and fixture inspection must precede loading. Record the actual node map, fixed-node positions, specimen orientation, mounting version and any preload or slack. A loaded-network station is not a place to change glue bonds. Move the unloaded, supported mounted specimen to the measurement station in a carrier, dock the truss and verify stability. Transporting a suspended weight together with the sample is prohibited by the authored handling contract.

The source states the two top fixed nodes for its illustrated network; SI's broader phrase about fixing two sides does not license arbitrary side clamping. The qualified geometry card identifies the fixed nodes precisely. Reconfiguration changes a real fixture/attachment record and invalidates the prior image baseline.

## 3. Camera, coordinates and baseline

The robot installs/checks the tripod-mounted DSLR, remote trigger and illumination. Source camera settings are f/5.0 and ISO 800; exposure time, lens, distance, image scale, focus procedure, illumination and camera model are missing. The original viewing direction is perpendicular to the sample plane and at its height. These details must be supplied and checked rather than inferred from a default camera.

The robot brings a qualified checkerboard to the calibration plane, records its identity and dimensions, acquires the required poses through the camera interface, and has the analysis service solve camera parameters. Reprojection/scale acceptance thresholds and pose coverage are authored inputs. Remove the checkerboard from the loading region, verify no view obstruction, and retain both raw and corrected images. Calibration must remain associated with the actual camera configuration; moving the camera, changing focus/zoom or remounting the truss triggers the qualified recalibration/rebaseline policy.

Before every independently reset condition, capture a load-free image. Define the object-plane metric transform, pixel-to-metre scale, positive x/right and y/up signs, node labels and reference bond endpoints. A zero-mass condition is a real observation, not a fabricated all-zero row. A baseline is not reused after unresolved drift, damage or fixture movement.

Node centers are tracked by image correlation. The processing card supplies subset/search sizes, confidence and outlier rules, uncertainty, missing-node policy and image correction. Preserve raw images and measured coordinates before deriving displacement. Missing or ambiguous nodes block the affected result; model predictions cannot fill them.

## 4. Strings, weights and a complete acquisition cycle

The robot prepares the card-specified strings with qualified scissors/tweezers or other tools and attaches them at the designated input-node joints. The paper uses thin strings wound around the joints. String material, length, winding/retention method, routing, tare and approved contact forces remain input gates. Strings must not bridge unintended nodes, restrain horizontal motion or obscure tracked joints.

Read each weight's ID, nominal/verified mass and uncertainty. Bind the case's node-to-load vector and the order of load placement. Include all active weights and account for string/hanger tare in the supplied calibration and load envelope. SI bounds the hanging weights at 20 g total. This is a source envelope, not an independently validated safety limit: use the stricter qualified station/specimen limit. The 20 g same-node case cannot silently gain extra hanging mass from an unaccounted holder.

The robot supports each weight until its attachment is seated, then transfers the force slowly under the qualified loading card. It clears hands and verifies the exact active node/load vector, free hanging clearance and catcher position. No transient intermediate load may violate the bound. The station/camera observes until the supplied equilibrium/drift criterion is met, or records a timeout. The paper does not provide a settling time. Capture remote images only with verified case/trial/phase labels and camera-state readback.

After acquisition, support and remove every active weight, return each to its indexed tray, inspect strings and attachment points, and observe return to the qualified unloaded state. The record retains load order, duration, drift, failed attempts and residual displacement. A fixed-length wait or automatic reset is not a substitute for observing recovery. Damage, adhesion slip, nonlinear motion, occlusion or a dropped weight creates a failed or incomplete condition, followed by supported safe recovery. Do not continue to meet a expected graph.

## 5. Physical forward/adjoint gradient routes

Two routes preserve the input/output distinction:

- `GRADIENT_SEPARATE`: the forward weight is 10 g at the bottom-right node; the loss uses the bottom-left vertical displacement and a target offset of 0.025 m
- `GRADIENT_SAME`: the forward weight is 20 g at the bottom-right node; the loss uses that same node's vertical displacement and an offset of 0.028 m

Each trial has two independent load phases on the same identified mounted specimen, with no geometry update in between. Measure the forward field first. Compute the adjoint target from that trial's measured output, the explicit loss definition and a qualified unit/sign-to-force convention. The source applies downward adjoint forces equivalent to approximately 5 g in both reported demonstrations, using g = 9.8 m/s². The reported response and 5 g result are evaluator context, not values to inject into a new measurement.

The dimensional conversion deserves an explicit card: the derivative of a dimensional squared-displacement loss is not a self-documenting force calibration. Preserve the source's operational convention and require the normalization/force scale before issuing weights. Record calculated continuous force, chosen available masses, actual applied force, rounding rule and residual. If the sign requires an unsupported upward force, the required mass exceeds the envelope or the error exceeds the declared tolerance, stop the adjoint phase instead of taking an absolute value or clipping silently.

Completely unload the forward force and verify recovery before applying the adjoint force. This is not the equilibrium-propagation nudged state: input force must be absent in the adjoint phase, even when input and output refer to the same node. A 10 g plus 5 g or 20 g plus 5 g combined loading is the wrong experiment.

Process both fields using the same bond map, sign convention, geometry version and calibration policy. Measured elongation uses the difference between loaded and original endpoint distances, while the linear bar model uses a projection onto the reference bond direction. Preserve those method labels; do not silently treat finite-deformation measurements as exact linear derivatives. Multiply matching forward and adjoint elongations bond by bond on a computer. Record the effect of any qualified force scaling/quantization; do not claim exact loss gradient if the applied adjoint differs from its ideal value without an appropriate correction/uncertainty treatment.

Repeat the full unloaded-forward-unloaded-adjoint-unloaded sequence under the declared plan. The source reports three independent experiments. It does not establish three independent printed specimens or their historical reuse, so trial and specimen identities remain distinct. Report pairwise products, aggregate means/uncertainty and optional comparison with an independently supplied model. The published gradient-error value is context, not a pass threshold.

## 6. Initial and numerically trained behavior comparison

Prepare three geometry conditions: uniform initial widths, a trained left-dominant response, and the alternative trained right-dominant response. The right-dominant physical comparison is explicitly supported by SI Figure 4. Each geometry corresponds to a real accepted specimen; changing a condition name cannot transform one lattice into another. Historical specimen reuse is unknown.

Apply the 5 g input at the node identified by the condition's verified node map. Capture baseline and loaded images, measure both bottom-node vertical displacements, unload and verify recovery. Derive absolute-displacement difference and, when the normalization denominator is valid, the two response fractions. Report actual response even if ordering disagrees with the numerical design. Comparison across geometries requires matched loading, measurement and condition-history cards; it is not a physical gradient-descent loop.

SI Note 4's four prescribed MSE target pairs are retained as a numerical branch. Its word “actual” is not sufficient evidence that four extra physical specimens were tested: the figure does not label experimental data, unlike SI Figure 4. Fabricating those variants would be a separately authorized, clearly authored extension, not a completed or recovered paper experiment.

## 7. Physical regression sweep

Bind the final regression geometry and the verified input/output node map. The physical sweep uses nominal masses 0, 2, 4, 6, 8, 10 and 12 g. Measure horizontal and vertical displacement of both output nodes at every mass. The planned task resets to an unloaded verified reference between loads; this conservative handling choice is authored, because the original exact loading sequence and dwell are absent. Every condition retains its own baseline/recovery record and trial identity.

The regression reference uses a signed input force consistently with image y direction. The published target coefficients are 0, 0.016, 0.004 and 0.016 for uRx, uRy, uLx and uLy respectively; a load magnitude must not be inserted into a signed equation without defining its sign. The task's analysis card specifies units, target construction, intercept treatment and norm/loss aggregation.

Fit/report response from measurements rather than the printed training curve. Keep zero-force measurements, confidence and residuals, including an unavailable normalized metric when the target norm is zero. Do not divide by zero or silently discard a missing load. The source's noisy/noise-free training datasets and training trajectories are computational comparisons; the measured sweep at a final network is not a claim that all training epochs or both models were separately fabricated.

## 8. Three physical Iris classification cases

The network consumes numeric feature cards only; no plants, organisms or biological material are involved. Each of three selected cases requires a traceable original record ID, four original feature values, scaling, rounding convention, integer weight vector, node mapping and actual applied masses. The text describes scaling/rounding but does not give a complete recoverable mapping or identify the three original rows. The source workbook's normalized output columns do not close those gaps.

The robot retrieves four specified weights/weight combinations and stages them fully supported in the tray. With prepared strings but no hanging weights, it records a fresh unloaded baseline. It then attaches/transfers the four weights to the input nodes and verifies the complete simultaneous load vector within the 20 g/source and qualified limits. It obtains a settled loaded image, measures horizontal displacement at the three output nodes, commits the result and only then evaluates against the withheld label if applicable. It unloads all four inputs before the next case and confirms recovery.

A qualified processing card defines normalization, signed displacement convention, nonpositive/zero denominators, uncertainty and tie/near-tie handling. Do not silently replace the source's largest-horizontal-displacement rule with largest magnitude. Report ambiguous classifications instead of forcing the expected species. Physical success for three selected cases does not establish the numerical test-set accuracy or accuracy on every Iris sample. Three independent repetitions per case are not the ten randomized numerical training runs.

## 9. Computational and proposed branches

`nonmanual_scope.json` retains the linear adjoint derivation; finite-difference/nonlinear error analysis; bar-versus-3D FEM comparison; equilibrium-propagation comparison; behavior training and MSE feasibility; noisy/noise-free regression; Iris training/confusion matrices and alternative node choices; penguin classification; task switching; damage retraining; and bond-importance/zero-mode analysis. Any future computation must preserve model/dataset/version/split provenance and numerical-only result labels. No unreviewed author code was run for this package.

The five supplementary videos are described as training/retraining evolutions. Their descriptions and the main text establish relevance to the computational inventory, but the movies remain unviewed. They are not needed to invent physical manipulation choreography and cannot establish fabrication details. Exact animation/timing reproduction remains gated on content inspection.

The paper's tunable-material and microcontroller-based all-physical update loop is future work. This package neither builds it nor equates it with the printed Agilus30 tests. Physical cutting/pruning, self-updating spring control, magnetoactive or phase-changing hardware are not part of these physical branches.

## 10. Controls, lineage and closure

Necessary controls include fixture/camera stability, metric calibration, load-free baseline and recovery, signed load verification, full-load-vector mass cap, correlation confidence, matched before/after geometry conditions, and same-specimen paired gradient phases. Calibration and trial success thresholds are episode inputs, not inferred from the publication's graphs. A reference model is separate from measured data and cannot overwrite it.

Lineage links material lot -> geometry/training version -> print job -> postprocessing -> accepted specimen -> mounted fixture version -> calibration -> baseline -> phase/load case -> raw images -> node coordinates -> displacement/elongation -> gradient or task result. Weight and string inventories are separately tracked. Reprinting creates a new specimen; reanalysis creates a new result version while preserving the original images; a failed trial is retained. Historical records are marked unknown instead of fabricated.

To finish, remove and inventory all weights, verify an unloaded stable specimen, remove only releasable strings under the supplied card, undock the truss using robust handles and transfer the supported mounted specimen to labeled archive. Adhesive removal is not assumed safe; storage on the fixture is allowed. Clean the catcher, tools and work surfaces through material-approved methods, close the fabrication/postprocessing station and log waste disposition through its qualified service. Verify no dropped weights, loose tools, obstructed walkways or dangling loaded strings remain.

The final report distinguishes completed, failed, blocked and unattempted conditions; reports actual observation coverage and uncertainty; links the identities above; and states source, authored and simulation-derived roles. Missing acquisition or unresolved input cards prevent a fabricated “complete” result but do not erase covered portions.

## Validation and release

`reference_routes.json` binds the reusable operations to concrete carrier transfers, source/target custody receipts and typed repeat bodies. The regression loop encloses all seven acquisition/reset cycles before sweep analysis; each gradient repeat encloses both complete reset-separated fields and pairing. Digital record processing does not move the specimen. Finite tests check referential integrity, branch/operation coverage, actor/device separation, scoped phase dependencies, acquisition/reset ordering, source-versus-authored labels, source access honesty, mass/identity controls and rejection of selected shortcut traces. These are static and symbolic contract tests, not a robot controller, physics solver or validation of physical feasibility.

The project LICENSE is preserved without changing it. The article is CC BY-NC-ND 4.0; source files, publisher pixels, video frames, full text, copied code and raw workbook data are excluded from the public export. The artifact consists of original task contracts, brief factual identifiers, scientific conditions and source pointers. Its license does not relicense third-party material. Publication is the parent's responsibility after independent review; this worker performs no remote writes.
