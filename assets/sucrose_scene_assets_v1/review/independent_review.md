# Independent sucrose scene review

**PASS for original static-asset scope. Approved: true. No open blocking findings.**

Reviewed on 2026-10-04 by a reviewer separate from the implementer. Revision 2 reopens and closes the clamp/switch lifecycle review. Approval covers the editable generic scene, factual metadata, static bindings and local fixture guards. It does not certify scientific accuracy, physical execution, device safety, or public-publishing rights.

## Evidence examined

- Opened the final native Blend in Blender 4.3.2 with script auto-execution disabled. It contains two separate editable scenes, six apparatus roots, 31 anchors with existing targets, 48 editable text objects, and identity root transforms
- Independently reran the package tests: **38 passed, zero failed**. Independently reran native validation: **65 checks passed**
- Independently decoded both final GLBs, checked scene graphs, buffer/accessor bounds, finite float attributes and all 31 anchor coordinate conversions. Apparatus: **176 nodes, 139 meshes, six roots**. Display: **17 nodes, 16 meshes, one display root**. Each contains exactly one scene, no studio floor, no orphan nodes and no external resources, textures, animation or skins. Blender re-import receipts also pass
- Read the generator, static guards, contracts, tests, exporter, licenses, source-fact packet and task binding authority. The snapshot exactly matches the current authority: **37 operation IDs, 31 anchors, six groups**
- Inspected all three actual 1600 × 1100 PNGs: overview, cartridge close-up and volume lineage. Pump-blocked, unresolved 40x conflict and no-live-data notices are legible. The three volume meanings are visibly distinct; equal-size cards explicitly do not encode relative volume
- Verified the original AFM source Blend hash and all 15 reused parts against the reuse snapshot, including vertices, faces, transforms and modifiers. Final meshes match the snapshot. Two reused families receive **zero new unique-asset credit**
- Read all 35 allowlist entries and the exporter. All referenced files exist; paths are bounded and contain no source PDFs, private extractions, source art, logs, backups or external texture files. Attribution and the Blender font notice are present

The native file has one inert Render Result viewer entry, with no filepath or packed pixels. It has no external images, linked libraries, embedded scripts, animation drivers, fluid/particle/rigid-body implementation or image/script material nodes. Text uses Blender's built-in font.

## Blockers found and resolved

1. **Cross-scene GLB leakage.** Initial exports included unintended scenes and a studio floor. Final active-scene-only exports pass independent structural and import checks
2. **Missing lineage validation.** Initial receipts accepted empty setup, plate and wavelength IDs. All receipt identity fields now require nonempty non-whitespace strings, including direct-state invalid inputs
3. **Partial configuration mutation.** Mixed valid/invalid updates could retain old calibration after mutating a plate. Updates now prevalidate atomically; valid configuration changes invalidate calibration, and saved calibration context rejects stale direct mutation. Regression tests pass

4. **Reusable clamp observation.** A successful switch previously left the old clamp observation available for a second switch. Each successful switch now consumes its current cycle. A fresh CLAMP and separate positive VERIFY_CLAMP are required before the next switch; direct re-verification cannot revive a consumed cycle
5. **Undocked clamp/switch path.** The old metadata fixture allowed these operations without docking. CLAMP, VERIFY_CLAMP and SWITCH_SAMPLE now require a docked cartridge. Undock discards pending observation, and redocking requires a fresh cycle

## Reopened lifecycle verification

Independently reran all **38 package tests** and **21 additional direct lifecycle checks**. These exercise undocked operations, initial verification without a command, command-only and negative-observation rejection, one-use observation consumption, second-switch rejection without changing identities/reference, rejection of re-verifying a consumed cycle, fresh-cycle recovery with reference clearing, new-command invalidation, undock/redock invalidation, and continued physical pump/acquisition blocking after acknowledgement. All passed.

The Blend, both GLBs and all three PNG hashes are unchanged from their prior direct inspections. Contracts, implementation, tests and documentation were reread, and the stable-file hash set was refreshed only after the lifecycle corrections passed. The review JSON embeds all lifecycle results, so no extra inspection file is required.

This is parity for the **implemented clamp/switch metadata subset**. The task evaluator is an exact canonical-trace checker; the scene guard is smaller. Full evaluator parity, authenticated observations and persistent replay protection are not claimed.

## Nonblocking visual notes

Some small labels and the qualification indicator are partly occluded in the overview. Fine base text on the volume display is smaller and lower-contrast than the main cards. The editable scene, close-up and metadata support closer inspection; core scientific boundaries remain clear. The final metadata/export changes did not alter the rendered geometry, materials, cameras or lighting.

## Preserved boundaries

All apparatus dimensions and anchors are authored and unqualified. No source-shaped SPP, internal microchannel, open-beam assembly or vendor CAD is supplied. The nominal **22 µL chamber**, approximately **300 pL optical region**, and **unknown required handling volume** remain separate facts, never transfer requirements inferred from the model.

The flow conflict is unresolved. Pump and physical acquisition requests remain blocked even after a fixture acknowledgement. Fixtures emit metadata only, never measurements, images or device authorization. Precision is not represented as absolute accuracy. There is no fluid physics, optical simulation, robot backend, validated collision/grasp behavior or qualified calibration.

The source paper's CC BY-NC-ND license is recorded, and observed outputs contain independently authored generic geometry rather than source figures or copied CAD. This review is not a global plagiarism search or legal determination. Six groups, repeated parts and multiple exports must not inflate unique-asset counts.

## Freeze requirement

The archive was not yet frozen at review time. After incorporating this report, the builder must run the reviewed exporter and verify final ZIP membership and manifest hashes. The JSON companion is self-contained and records the reviewed stable-file SHA-256 values and inspection details; no unbundled inspection file is needed to interpret the approval.
