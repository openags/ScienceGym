# Arc-Morph task design

## Evidence and scope

The accepted source review read all 12 pages of the final paper and all 22 written supplement pages. Six main and eight supplementary figures were inspected. The 728.4 MB Zenodo archive was not downloaded or read. Its earlier preprint figure numbering remains C07/U14, so final-figure correspondence is not presumed. Source facts, newly authored robot interfaces, nominal art, synthetic test data, new observations and model predictions are different provenance classes.

The whole-paper design has four separately identified cardstock families (CS1–CS4), polymer stock-to-specimen preparation (PP_PREP), polymer rigid metrology (PP_RIGID), and qualitative polymer shear (PP_SHEAR). PHOTO_ANALYSIS and CLOSEOUT are auxiliary dispositions. Six nonmanual mathematical dispositions retain analytical coverage without manufacturing robot episodes from algebra or rendered theory. Exactly eight source-aligned rigid configuration slots belong to one specimen and one measurement set; they are not eight independent specimens, technical repeats or a fatigue test.

## Preparation must be represented

Campaign allocation precedes stock handling. An accepted material lot and drawing revision are tied to a persistent stock, carrier, prepared-sheet and specimen chain. The robot seats supported stock, transfers it to a qualified closed fabrication dock, binds a job, waits for independently evidenced completion and safe release, and inspects the output there before transferring it to folding. The service has no operating settings or control endpoint in this artifact. Cardstock cutting/creasing is a candidate authored implementation because the historical cardstock fabrication procedure is not supplied by the reviewed source.

Folding is an explicit per-edge loop, not a service-receipt shortcut. Each externally qualified edge plan names dependency order, panels, support, contact patches, allowed motion and inspection. The action sequence is support, engage, bounded fold, release, inspect and append evidence. The complete expected edge set must be accounted for once before baseline qualification. A generic status update cannot transform a flat sheet into a folded specimen. The synthetic three-edge fixture exercises these rules only and has no source-matched geometric meaning.

## Custody, leases and state

Every R03 occurrence binds a real source station, destination, object and retained carrier. Preparation and measurement transfers have separate entries in transport_routes.json. Final storage movement is represented by R23. Co-location may shorten a path but cannot erase custody checks. Mounted or loaded specimens cannot be transported. Device membership and leases are exclusive: preparation dock, folding station, fixture and cameras cannot silently serve two incompatible jobs.

The rigid fixture retains three sample sliders, two independent plate sliders, its approved spacers, mount interfaces and all required lock identities. The qualitative corner fixture and the benign rigid demonstration support are separate modes and interfaces even if a nominal asset group contains both. R22 closes a corner-load mount; R30 closes a rigid fixture mount. Releasing the wrong type is an error. Neither operation is required when a specimen never acquired that mount.

State revisions and conditioning history are append-only. Load release cannot erase folding, damage or previous failures. A replacement gets a new specimen and series identity. Recovery checks compare against the preserved baseline; a changed rest state gates comparisons that assume the old state.

## Paired-camera metrology

The two camera/lens assemblies are independently identified and have different view roles. Calibration records bind both camera revisions, both reference identities, the fixture revision and time coverage. Camera, lens, mount, fixture or reference changes invalidate dependent calibration and capture tokens. A visible ruler or attractive rendering is not a traceable calibration.

For each requested height, supported configuration change precedes all-lock readback, multiple-location height readings and stable-state evidence. An externally qualified policy defines limits and token lifetime; all numerical defaults remain null here. Frontal and lateral captures each have an immutable file identity and independent quality result. Pairing requires one specimen, one configuration, one token, the same locked interval and current calibration. An interruption, slip or changed setting rejects an incomplete pair. Both views are reacquired with a new attempt and token, while failed files remain retained.

Analysis separates height, interior radius and exterior radius with method, uncertainty and raw parents. A coarse-grained model prediction is a different field. Near-flattening discrepancy is preserved rather than edited to match a curve. Source radii are evaluator-only references and never acquisition targets or operational success conditions.

## Controls and repetition

Reported controls are distinguished from authored benchmark controls. The source supplies orthogonal view roles, length references, locked capture state and height-uniformity checks. Added immutable receipts, calibration expiry, baseline/rest inspection, failure histories and token rules are authored validity requirements. A new study may add repeats only through an explicit frozen allocation: fresh capture identities for technical repeats and fresh physical specimen identities for independent specimens. Repeated images and configuration changes do not increase specimen count. Statistical independence and uncertainty estimates require their own evidence.

## Holds and failure closeout

Every physical branch can reach a supported hold without analysis success. A missing load-removal, support or safe-release record cannot be replaced by a software request. If qualified recovery can be performed, acquisition stops, load is removed under support, the actual fixture mount is released, the retained carrier is checked, the rest state is inspected and storage/quarantine is reconciled. If any of those observations is uncertain, the terminal disposition is a supported unresolved hold. It is partial accounting, never a completed unload or permission to transport.

Closeout reconciles every selected route, tool, specimen, carrier, lease, reference and failed/accepted evidence item. Unselected and unattempted branches remain explicit. No phantom duplicate, deleted rejection or unresolved loaded station can produce a whole-campaign completion claim.

## Source-model gates

C01 preserves 383.63 mm in Methods and 383.65 mm in the figure without averaging them into a fabrication size. C02–C06 and C08–C10 preserve printed averaging, sign, angle, normalization, notation, legend and strain-expression inconsistencies. These are reuse cautions, not an independently proved erratum. No corrected formula is implemented. Source-matched geometry and model comparison require independent scoped qualification. Legitimate image custody can remain valid when only a model oracle is held. C07/U14 separately blocks raw-data attribution.

## Verification boundary

The Python module implements strict symbolic guards and finite evaluator-pinned synthetic replay, not physical automation. Actor messages carry only identifiers and cannot inject sensor values, success, qualification or source outcomes. Mutated registries, repeated occurrences, dependency reordering, wrong lineage and forged roles are rejected. A production sensor authority, actual actor/evaluator filesystem separation, real hardware interlocks, motion feasibility, compliant mechanics, image extraction and scientific-model validation remain unimplemented.

The asset binding plan coordinates A01–A12, ASSET.Axx roots and ANCHOR.Rxx.primary/control with the original scene package. The revised binding also pins concrete primary/control object selectors. R06 stays at the dual-purpose fabrication input/safe-output inspection dock, while R26/R27 select the separate rigid demonstration support. Fixture-specific release selectors are explicit. These names provide nominal correspondence only. Dimensions, collision proxies, grips and visualization cannot discharge U01, U04, U05 or U12. Neither static review nor a sanitized ZIP establishes hardware or safety qualification.
