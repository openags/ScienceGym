# Independent review: thermal-jamming task design

## Decision

Pass as a source-bounded whole-paper mobile-robot **task design**, with explicit unresolved episode inputs. No blocking design findings remain in the reviewed packet. This is not acceptance for physical execution, feasibility, equipment safety, experimental reproduction, solver validity or a runtime evaluator.

The independent finite suite passes **34/34** checks. The author's suite was inspected and independently rerun: **25/25** passes. Both suites check authored contracts and synthetic evidence rules; neither authenticates device receipts or demonstrates material behavior.

## Resolved finding

The initial XCT cycle branch inherited a mechanical-cycle control requiring reinsertion. That silently selected an intervening pull-out even though the branch correctly left the joint scan/pull sequence unresolved. The author replaced it with a distinct `C_XCT_CYCLE` control. Reinsertion is now required only if the finite, qualified manifest includes a mechanical extraction. The mechanical pull/cool/reinsert route retains its separate control. This repair was reread and tested.

## Review findings

- The packet gives physical preparation, cutting, shape-history verification, fixture/stick fabrication, charge allocation, packing, fastening, transport, mounting, instrument interfaces, recovery and cleanup to the robot. Device-owned regulated processes remain separate. It does not use a finished clamp to bypass fabrication.
- The thirteen configurations preserve the different physical investigation families. Figure-level coverage also retains numerical and conceptual work without relabeling it as a physical experiment. Fixed-rod filler addition and fixed-total composition change remain different comparisons.
- Causal state and lineage are explicit: insertion precedes thermal conditioning; actual thermal qualification precedes pulling; extraction changes packing/insertion state; cooling precedes reinsertion; repacking breaks same-packing continuity; tomography acquisition precedes segmentation; long-duration holding is separate from repeated pulls.
- The source reports distinct baseline and aspect-ratio fixtures. Its outside/inside dimensional incompatibility remains visible and gated. The scanner designation is not promoted to a run setting. Unspecified initial shape programming is not fabricated. The simulation-only packing count is not assigned to physical repeats. These checks are grounded in the [main article's Results and Methods](https://www.nature.com/articles/s41467-025-57475-5).
- The friction fixture's fixed contact array and separate sliding object are preserved. Cantilever loading, unloading and subsequent thermal recovery are ordered. Missing preparation and acquisition details remain qualified input gates rather than guessed values, consistent with [SI S1 and S2](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-025-57475-5/MediaObjects/41467_2025_57475_MOESM1_ESM.pdf).
- Controls distinguish independent packings, repeat measurements, cycles and tracked rods. Source outcomes cannot become raw parents. Failed, interrupted and thermally invalid attempts remain visible. Actor projection excludes answer routes and published outcomes; no executable loader is claimed.
- The allowlist inspected during review contains authored files only. Publisher assets and the construction generator are excluded. Final status/verification and newly added review files may be added by the author without changing the substantive design. This is an asset-boundary check, not legal clearance.

## Evidence and limits

Independent source work used the lawful publisher article and the already available SI. The review read the main physical Results/Methods, SI experimental setup, single-rod validation, parameter provenance and numerical/physical classifications. SI PDF pages 4–6 (Figs. S2–S4) were also visually inspected. This is a bounded source audit, not an exhaustive reinspection of every source figure or historical dataset.

Movies, source workbook, complete code/solver and exact historical allocations remain uninspected or unresolved as stated in the packet. No source-access bypass, new source-asset publication, remote write, equipment action, CAD work or viewer work was performed. An honest blocked episode remains an allowed result; resolving a qualified input does not turn an authored implementation choice into a source fact.

`contract_check_results.json` records the checked JSON hashes. `author_suite_rerun.txt` records the independent rerun of the inspected author suite.

Final narrow recheck: the phase-map multiplier and the eight explicit derived-record contracts were inspected after the initial pass. The multiplier is correctly labeled a source-specific convention with measured-parent requirements, not a universal criterion or load rating. No route or actor contract changed. Both suites were rerun with the same passing totals and the JSON hashes were refreshed.
