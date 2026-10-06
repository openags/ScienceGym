# Whole-paper task-design contract

## Scope and actual implementation

This package translates the complete accepted source inventory into an original, finite, offline evidence ledger. It contains a digital contract implementation, synthetic bookkeeping tests, original design prose and an exact semantic interface to a separately created Blender/GLB scene. It is one paper-level design. Physical services, robot control, pressure actuation, fluid simulation, source-code execution, raw acquisition and scientific reproduction are not implemented.

The evaluator admits a frozen plan and independently supplied receipt map. An actor can submit only operation_id and evidence_id. The implementation copies evaluator input on admission, checks exact field sets, rejects stale epochs/plan digests, links dependencies by canonical hashes, retains failed proposals and bounds digital attempts. These hashes are integrity links, not cryptographic service authentication. A receipt ID by itself does not establish that a real laboratory performed work. The evaluator must separately verify any external evidence, authority, files and qualifications.

Evidence-disposition order is not a pressure-cell operating sequence. The ledger can collect historical receipts in dependency order, but cannot verify real-world custody chronology, cell occupancy, a physical repeat schedule or safe timing. U18/U19 and the qualified service's custody/reuse records remain mandatory unresolved gates. In particular, loading the same cell again requires independent inspection, a new aliquot and a new loaded/settled state; a reused cell never preserves the earlier granular microstate by identity alone.

## Complete branch coverage

B01 covers materials, host identity, cell variants, contained preparation, settled initial state and measurement interfaces. B02 retains the paired low-rate, different-filling examples with separate condition/run identities. B03 retains the filling/reservoir sweep as sparse evidence; 22 displayed examples do not become 30 measured factorial combinations. B04 retains area/perimeter morphometry, width ratios, event distributions and their uncertainties. B05 covers the entire rate progression: low-rate frictional events, intermittent crossover, fluidized-front/coral states and resuspended viscous fingers. B06 requires a distinct baseline and altered-viscosity control identity; its reported 100-fold scaling does not supply a recipe or absolute condition pair. B07 retains high-filling granular fracture as a separate qualified service branch. B08 records borrowed porous-medium comparisons as externally attributed context. B09 records analytical fitting, sensitivity and model limitations, without executing the model.

No route count is presented as independent scientific experiments. B08 does not increase experiment counts. B06 and B07 cannot disappear from full-program coverage because their source details are incomplete. Their source observations stay in evaluator reference files and never become fixtures, raw observations or reward targets.

## Route semantics

1. R01 admits final source identity, complete reading inventory, rights, deduplication and unresolved conflict records
2. R02 admits contained grain/host/altered-host lots and distinct inspected 10 mm/19 mm cell variants through certificate references
3. R03 links lots, condition plan, formulation, batch, aliquot, accepted cell, loaded state and settled child state through closed preparation jobs
4. R04 records run-specific calibration, pressure/gas reference conventions, effective compliance, image geometry, clock alignment and qualified safety/service interfaces
5. R05 collects low-rate comparison and sparse-sweep run documentation after common gates
6. R06 independently collects rate-branch documentation, with the coral discrepancy disposition explicitly retained
7. R07 independently collects paired viscosity-control and high-filling extension documentation
8. R08 requires all three measured-branch dispositions for aggregate metrology review; accepted derived-record references bind exact pressure/image hashes, clocks, algorithm versions, geometry and uncertainty
9. R09 reviews preregistered controls/repeats, exclusions, randomization, unresolved branch assessments and evidence classes
10. R10 records external porous-medium attribution and model/source limitations; neither becomes a measured outcome
11. R11 closes each registered preparation, instrument-qualification or measurement job independently, including failed jobs, as soon as its receipt exists. It is not delayed until R08-R10 and is not a single global completion token
12. R12 archives all R01-R10 dispositions, every R11 job closeout, rejected-event history, all branch states and all twenty physical-qualification holds

An accepted digital receipt means the fields and associations satisfy this contract. It does not mean a source result was reproduced or any physical gate was cleared. Final scientific branches remain UNRUN; B08/B09 are SOURCE_CONTEXT_ONLY. Contract tests may include synthetic qualification-reference tokens, but those tokens never remove the deliverable's real physical holds.

## Preparation, identity and dependencies

Source materials are glass granules, water/glycerol host and air in a narrow glass channel. The baseline host percentage convention is unreported; mass or volume basis cannot be silently chosen. Receiving requires separate grain/host lot identity, contained material records, composition convention and property certificates. Altered-viscosity material has a distinct identity. Glass-grain sourcing/distribution/history, settling criteria and normalized filling measurement remain qualification inputs.

Finished cells are supplied by qualified services; there is no cell fabrication, cutting, sealing, loose-particle or pressurization recipe. Source nominal dimensions and historical instrument names are factual context, not pressure ratings, gripper tolerances or operating limits. The 10/19 mm plate variants remain distinct, and reservoir volume alone cannot stand in for the total cell/tubing/gas compliance.

Every condition is independently linked to grain lot, host lot, batch, aliquot, cell and loaded/settled state. The frozen plan names preparation units, statistical repeat groups and matched-pair IDs separately. Matched-pair IDs bind the low/high-filling comparison and baseline/altered-viscosity comparison to distinct conditions using one cell variant; they do not equate statistical repeat groups or require one invented experimental n. A batch ID must retain consistent grain/host parents across aliquots. Distinct preparation IDs do not by themselves prove independent batches or independent statistical replicates. Actual statistical n, randomization and between-run reuse are never inferred from displayed source images. Source values do not auto-fill a service command.

## Geometry and cross-device metrology

The scene uses metres, right-handed coordinates and Z-up. Six station origins, all 32 anchor IDs, branch/route/material IDs and source-reference geometry are shared byte-for-byte between packages. Evidence anchors are logical selectors, not grasp or motion targets. A separate illustrative carrier rule concerns only explicitly named A03/A08 proxy carriers; contact visualization is not a tolerance qualification.

Pressure/DAQ records and camera frames bind one run, instrument configuration, calibration and common experimental clock map. The pump's requested condition and independently confirmed observed condition are separate references. Pump rate is not burst invaded-volume rate. Movie playback seconds and encoded frame rate are not acquisition time or camera cadence. Source plots and presentation movies cannot replace raw streams.

Any future area A, interface length S, 2A/S, S/A, adjacent width ratio, area-to-volume conversion, event statistic or derivative requires a declared segmentation definition, geometric estimator, version, quality record and uncertainty. This software does not compute those quantities. Synthetic raw fields contain identity hashes only, claim no acquisition and carry no morphology values. External raw-reference admission does not verify file contents or prove an outcome.

## Controls, repeats and scientific limits

Matched filling comparisons, reservoir/filling sweep, rate sweep, viscosity-rate control and thicker-cell compliance control all remain explicit. Local width samples, bubble events and separately prepared experiments are distinct observational units. Twenty random widths are not twenty preparations. Replicate SD bars with unknown n do not establish a repeat count. Blank sweep positions are unobserved, not negative results. The parameter sensitivity band is not a confidence interval. The theoretical lower bound for possible continuous motion is not a universal measured transition criterion.

The coral example has unresolved conflicting labels: the written Movie 2 description says 0.1 ml/min, whereas final main text and displayed movie labels support 1.0 ml/min. Both are retained with provenance, without assigning an executable default. The p.7 Boyle-law intermediate has an apparent volume-sign inconsistency with expansion and the negative pressure-change approximation. This is a reviewer-identified issue, not a published correction. No formula is repaired or evaluated here.

B06's scaling is qualitative source evidence, not an approved 100-fold operating instruction. B07 refers to deformation/fracture in the granular pattern, never deliberately breaking glass or industrial hydraulic fracturing. B08 photographs came from external authors/setups; the combined phase picture is tentative, with inverse normalized phi, and cannot be treated as a calibrated dense phase surface.

## Failure and safe closeout

Unknown identity, composition basis, pressure qualification, cell geometry/compliance, preparation state, calibration or synchronization holds the affected route. Failed service jobs remain registered and require their own quarantine closeout. Damage, leak, changed gap, escaped material or unsafe state is referred to the qualified service; there is no escalation, emergency-release or improvised-repair algorithm.

Every job closeout binds its exact receipt hash and subject, safe-release reference, contained disposition, inspection and reuse policy. Failed jobs must remain quarantined. Physical uncoupling is never performed by this program. R12 rejects open jobs and omitted rejection history. An observation unlike a published figure remains an observation; the contract never tunes a process or edits a label until it matches.

## Publication and verification boundary

Only original authored contracts, factual annotations and synthetic identifier fixtures are exportable. Source PDFs, copied prose/figures, movies/frames, third-party photographs, source CAD/code, caches, local paths and temporary reviews are excluded. The cited paper is CC BY-NC-SA 3.0; the authored Apache license grants no source-media or commercial-source reuse rights.

Authored tests exercise finite positive and adversarial cases. Independent review and additional negative/export tests are required before sealing reciprocal core manifests. Deterministic export fixes file order, timestamps, mode and compression settings, and verifies manifest/allowlist coverage. This does not prove absence of every possible defect or provide hardware/scientific certification.
