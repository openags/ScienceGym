# Verification report

Verified against the English task snapshot at `2f926a9d2c2b8a0c71e8939feaa6ca5696e14c27` on 2026-10-02.

## Passed

- **15 Python tests**, all run with the source directory supplied; no skipped source checks
- Source SHA-256 checks for every referenced JSON file
- Exact reference sequence equality for all Chiral, Fibre, Thermoelectric and diSPIM routes
- Exact actions, object roles, preconditions, postconditions and recovery lists for the four common-operation families
- Exact microscopy preparation order, state transitions, parameters and interaction macros
- Acoustic nested loop body/value/completion-rule preservation
- All operation references resolve; IDs are unique within each family
- diSPIM P001/P004 repeated occurrences remain separate
- Microscopy acquisition/data obligation groups do not acquire invented chronological edges
- Six JSON files and matching JavaScript assignment payloads; each below 200,000 bytes
- Six SVGs parse as XML; all text has inline fill and font family
- Local bundle asset links resolve; runtime code uses no fetch, WebSocket, eval or HTML-string injection
- JavaScript syntax check
- **Mocked-DOM UI tests:** all **120 route/branch records** render; **3,325 displayed operation occurrences** inspected across those route templates. Counts do not expand acoustic loops and do not count experiments
- Mocked-DOM selection, final occurrence, duplicate-ID distinction, search highlights, view tabs and malformed-hash fallback
- The same mocked-DOM tests pass for the **single-file HTML export**, including its embedded data scripts and SVG-download path
- Portable raster rendering of all six SVGs using preinstalled PyMuPDF. The six top regions were visually inspected; the final Fibre and Thermoelectric complete-route previews were re-rendered after changing defaults. Full SVGs were rendered successfully; displayed operation titles fit their two-line slots
- Standalone export has no remaining local file links. Its CSS, JavaScript, data and six SVG downloads are embedded. Script closing sequences are escaped

## Counts

| Family | Operation definitions | Route / branch records | Default diagram |
| --- | ---: | ---: | --- |
| Chiral | 31 | 28 | R01 |
| Deconwolf microscopy | 132 | 13 | tubulin |
| Fibre | 68 | 49 | OPTO_SI |
| Thermoelectric | 57 | 15 | PAIRED_TWO |
| diSPIM | 92 | 7 | D-R01 |
| Acoustic | 86 | 8 | WHOLE_PAPER_PRACTICAL |
| Total | 466 | 120 | |

Microscopy includes clearly labeled inspector navigation definitions for unload, analysis and each data-workstation action. These are not newly inferred paper experiments.

## Not verified / not claimed

- **Actual browser rendering and interactions.** The supported cloud browser rejects file URLs; parent context also records a denied localhost route. No alternate protocol, port, data URL, browser engine or external hosting was used to bypass the restriction
- Therefore browser layout, mobile responsiveness, keyboard focus and real browser Back/Forward remain unverified visually. Mocked-DOM checks establish application state behavior only
- Scientific source correctness beyond faithful mapping of the supplied reviewed task JSON
- Scientific response prediction, experiments, robot trajectories, physics, actual instruments, task-loader implementation or evaluator execution
- GitHub or Library publication; the parent owns those writes and remote verification

## Reproduction

```sh
SCIENCEGYM_TASKS=/path/to/ScienceGym/tasks python3 -m unittest discover -s tests -v
node --check app.js
node tests/test_app.js
python3 export_standalone.py
node tests/test_app.js ../ScienceGym-Task-Explorer.html
```

All runtime and build dependencies are either browser built-ins, Node built-ins or Python standard library. PyMuPDF/Pillow were preinstalled and used only for optional image QA; they are not required for the deliverable or its tests. No software was installed and no account, security or repository LICENSE setting was changed.
