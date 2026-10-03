# Export scope

Export only paths explicitly named in `EXPORT_ALLOWLIST.json`. The package contains authored task descriptions, factual paraphrases, citations, requirement contracts and static tests.

Do not export `.private/`, publisher PDF/text, page renders, screenshots, movie bytes, the source workbook or local build/intermediate files. Original source URLs are citations, not redistribution of the underlying files. Do not infer that source access is complete.

No repository LICENSE is added, replaced or modified here. Existing repository licensing remains unchanged. `agent_visible.json` defines the intended future actor boundary; evaluator-reference documents remain design files and are not runtime access controls.

The five allowlisted `independent_review/` files are authored review/report/checking artifacts. They use relative package paths and source citations only; no source payloads are included.
