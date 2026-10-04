# Preserve a quantum-paraelectric readout experiment

## Purpose and scope

This is an original whole-available-paper DESIGN conversion of Apostolidis et al., Nature Electronics 7, 760-767 (2024), DOI 10.1038/s41928-024-01214-z. It describes what identified objects, service records, calibrations, analysis conventions and safe closure would have to exist to account for the reported work. It does not perform that work.

The task is not reduced to a readout benchmark. Purchased crystal identity, full reported varactor patterning, carbon-nanotube device preparation, attachment, bonding, board assembly, cryogenic service, calibration, all physical measurements, model studies, lineage, storage and cleanup are represented. Missing manufacturing detail remains a qualification gate. Published examples cannot establish a safe operating envelope for a new laboratory.

## Evidence and source limits

The source auditor read complete official-repository JATS, all three Methods subsections, all five main figures, all six pages of the attached supplement and all five supplementary figures. Main PDF access is not claimed. The supplement actually supplies four numbered sections, I-IV, despite metadata advertising I-V. Coverage is of all available supplied material, not proof that an unprovided Section V never existed. There are no main/SI tables or attached videos in the inspected package.

The design uses paragraph IDs, section and figure locators. It does not redistribute source prose, figures, CAD, data, solver code or layouts. The source's Zenodo link is retained, but that archive has not been ingested or executed. Cited CVD and JPA fabrication literature does not become a complete process by citation. CC BY 4.0 governs the source article, with credit-line exceptions; patent rights are a separate issue.

## Objects and specimen identity

STO and KTO are different material lineages. STO is the main article's TiO2-terminated SrTiO3 (001); KTO is KTaO3 (100), with no inherited STO termination. The nominal crystal envelope is 3 by 3 by 0.5 mm. Fixed-load characterization uses two separate crystals with nominal circular pads of 100 micrometers diameter. Quantum-device experiments use two nominal 120 by 120 micrometer pads on one STO crystal, separated by approximately 2 mm. Those dimensions are source metadata, not a fabrication qualification.

The same physical STO varactor pair is reused between SQD and DQD measurements. Its stable IDs and prior sweep history survive reassembly. The nanotube device, board/module, circuit and calibration revisions change. A new board is not a new varactor, and a changed board does not erase hysteresis. shared_specimen_contract.json and the reconfiguration helper make this explicit.

SQD and DQD substrate identities are branch-specific. The source's substrate wording is retained as a conflict, rather than making DQD inherit the SQD's degenerate doping. No exact CNT electrode geometry, nanotube placement, yield or disorder is invented. Rear varactor metallization is an RF-line conductor; a generic scene ground-record anchor does not turn it into a global ground.

## Full preparation route

A full-route instance needs independent crystal certificates, original released geometry and qualified process cards. The closed cleanroom service returns separate receipts for backside metal, photo-patterning, top-pad metal and lift-off. The patterning receipt must account for coating, exposure and development under an externally owned procedure. Paper process details are not executable settings in this package.

The nanotube route preserves a growth-service receipt, first lithography/metal stage for alignment and bond pads, AFM localization tied to those marks, and second electrode-definition/metal stage. SQD and DQD children have different device IDs and branch-appropriate substrate records. Chemical, gas, vacuum, thermal and electron-beam settings are deliberately absent.

The assembly route checks attachment of rear metal to the board, top-pad/device wire bonds, holder and connector assembly, and actual port correspondence. It consumes independent as-built evidence. The task never performs a bond, heat cycle, live wiring change or insertion. A prepared route requires independent ancestry and receives zero fabrication credit. A damaged part is quarantined rather than relabelled as virgin.

## Circuit families and calibration

circuit_family_cards.json retains three distinct source families: fixed load, SQD and DQD. Source model inductance, part code and unverified manufacturer nominal value are separate fields. The SQD model's 320 nH is never silently changed to 330 nH. Bias-tee components remain branch-specific: the SQD and DQD cards do not share a universal coupling-capacitor/resistor combination. The DQD-only series capacitor and incorporated JPA are explicit. Cards are source topology metadata, not a wiring API.

Every measurement requires current module, mount, circuit, reference-plane, gain/noise, filter, thermal and history revisions. The source's lattice and electron temperatures are distinct observations; neither is a robot setpoint. A request to the cryogenic service provides no thermal observation or access permission. Interlock and safe-state records are independent.

The RF chain has separate line reference-plane, attenuation/gain, amplifier-noise and equivalent-bandwidth evidence. Device baselines include conductance peaks, gate conversion, blocked regions and transition identities as appropriate. The Methods' kHz/time-constant wording does not license a time-domain filter conversion without its transfer function. A filter or amplifier-state change invalidates dependent comparisons.

## Characterization and models

Fixed-load STO and KTO characterization preserves complex reflection versus the declared sweep history. Magnitude and phase are separate evidence; near matching, magnitude alone can support ambiguous under/over-coupled fits. Fits therefore need independently measured phase-regime evidence. They also need residuals, parameter constraints and uncertainty. The equivalent-circuit solve and fitting routine are external and unimplemented.

Effective fitted series resistance includes other circuit losses. The loss-tangent reduction is a circuit-inclusive upper-bound interpretation, not a direct measurement of intrinsic dielectric loss. A room-temperature component loss model cannot automatically be promoted to a millikelvin calibration. The reported KTO experiment does not establish the predicted lower loss; geometry, history, calibration and topology must be matched before material attribution.

The permittivity inference, SQD/DQD SNR maps and loss-dependent SNR studies are separate external model routes. The fixed-resistance model approximation remains distinct from measured voltage-dependent capacitance and resistance. Generic arithmetic tests do not reproduce the circuit model, finite-element inversion or source fits.

## SQD readout

The SQD baseline records device-specific conductance peaks and the selected slope before readout. Gate charge conversion uses the independently observed peak spacing and modulation metadata, with uncertainty. The sideband route records carrier, sideband and noise windows and the measurement bandwidth; it must distinguish amplitude and power conventions.

Carrier-power dependence is a bounded externally qualified scan. More power is not automatically better: nonlinear response and power broadening must be retained as exclusions. Matching comparisons preserve under/matched/over-coupled phase evidence and the fact that losses can covary with capacitance. The historical charge sensitivity is not a target that can make a synthetic trace pass.

Dual-varactor tuning records the observed resonant frequency and matching state together, including cross-coupling and prior history. No task action directly changes a bias. The dual-tuning and magnetic routes retain the SQD-circuit context of main Figure 4. Their complex-reflection/phase scans earn no sideband or charge-sensitivity credit. The magnetic route consumes closed-service field records paired with thermal/time and RF evidence; no magnet target, current or ramp is exposed. Source insensitivity is limited to its observed configuration and range.

## DQD readout

The DQD route records the two-gate map, source-to-left-dot transition A and interdot transition B, and the condition under which a charge transition may be interpreted as effective capacitance. The single-source/two-gate device and low-parasitic circuit are not an SQD circuit with renamed labels.

The JPA comparison needs matched device, varactor IDs, circuit, carrier/acquisition plan, reference plane, filter, thermal/history, baseline, region and transition. Pump-off and pump-on records require their own gain/noise revisions. Saturated or power-broadened records are excluded. The synthetic helper validates these declared metadata fields; it does not authenticate instrument states.

Capacitance sensitivity depends on the independently inferred lever arm and electron temperature, the transition model, measured signal/background contrast and equivalent noise-power bandwidth. The simple arithmetic helper accepts an already declared contrast and bandwidth, and does not implement the electron thermometer or full uncertainty propagation. The source's spin-readout timescale is a projection from an assumed contrast, not a demonstrated spin experiment. Future GHz operation, geometry changes and improved losses remain discussion/model-only claims.

## Hysteresis and stability

Forward/reverse histories preserve fast-axis direction, slow-axis stepping, initialization and ordered coordinates. The same coordinate may have a different state after a different path. A comparison aligns coordinates without averaging the histories away. Carrier transfer and module reassembly do not reset this history.

Stability uses independent timestamps and quadratures over a declared observation window. Centered quadrature scatter is computed around the run mean; it cannot by itself establish no drift. The original helper also reports the simple linear drift slope, but makes no absence-of-noise or stationarity claim. A missing time point is not silently filled, and source sampling language does not establish an exact endpoint count. Repeated time points and sweeps are not independent device replicates.

## Actor and evidence separation

Only agent_visible.json enters actor context. An actor event has exactly event_id, operation_id and evidence_id. It cannot submit measurements, qualification, safety, success or control settings. Every event is bound to a unique occurrence and an evaluator-selected immutable finite registry. Changing sample, material, module, mount, calibration, history, amplifier, filter or any other required revision invalidates the selected fixture.

A request acknowledgment is never a physical observation. Verification records are independently supplied. The offline evaluator accepts only its declared finite synthetic fixtures, rejects actor-created evidence and supports dependency-equivalent ordering. Public fixtures do not establish production authentication. Passing one fixture is not completion of all branch instances or controls.

The full-preparation synthetic route includes crystal fabrication, branch-appropriate CNT stages and assembly ancestry. Material comparison includes separate STO and KTO preparation receipts with distinct constituent sample and material IDs, linked by a comparison-bundle ID. Its top-level sample_id denotes that bundle, not one physical crystal; the raw comparison metadata retains both constituent IDs. Prepared fixtures carry ancestry only. The JSON operation list is membership, not a trajectory or a chronological list; unique event occurrences and dependency edges determine actual bookkeeping order.

## Failure, safe closure and disposition

Absent qualification, source-conflict disposition, calibration, data or isolation evidence produces a scoped hold. Failed attempts remain archived. A safe-off request can run independently of post-acquisition analysis, but undocking requires current independent safe-release evidence. Unknown isolation remains contained and is not stored as released inventory.

Post-service condition is inspected. Damage leads to quarantine. Replacement specimens receive new identities and preserve their relation to the failed attempt. The archive joins analysis/hold and closure/containment evidence before final station closure. Cleanup, waste handling and physical storage are external service receipts; none is implemented here.

## Static assets and release boundary

The 12 original asset groups bind all 80 operations once and expose 65 semantic anchors. Device dimensions are nominal source references; room-scale service shells, carriers, supports, coordinates and enlarged device insets are original display geometry. A visible disabled instrument is not a qualified control interface. Exact pad-edge contact, robot grasp, collision, kinematics, thermalization, electromagnetic response and safety are unvalidated.

The exact text-only export is hash-pinned and independently checked against a hard-coded member list. Source files and private acquisition paths are excluded. The separately reviewed asset archive is pinned when available; its static nature never changes this package's physical/scientific execution flags. Validated runnable whole-paper tasks contributed by this release: zero.
