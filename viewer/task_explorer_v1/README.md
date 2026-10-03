# ScienceGym Task Explorer

**See the task before reading its JSON.** Nine public paper-level task families, with reference-route occurrences, partial-order memberships, nested repetition, objects, state transitions and evidence.

The explorer contains **191 route/configuration records and 1,320 operation definitions**: the existing eight families retain 172 records and 1,267 definitions; EmVP adds 19 configurations and 53 definitions across five practical families. These are representation counts, not completed experiments or independent specimens.

This is a **read-only author/evaluator logical inspector**, including public reference and evaluator material. It is not a simulator, a task runner, an actor-facing prompt or evidence that a robot performed any operation. This integration adds no new 3D storyboard. The source release has **zero validated runnable whole-paper tasks**.

## Start here

1. Download or clone this folder and open **[index.html](index.html)** in a browser. It uses local JavaScript data, no fetch, server, installation or external library
2. Choose a task family and a route. Click any operation to inspect robot actions, target objects, pre/post state, evidence, acceptance, recovery and unknowns
3. Use **Dependencies & choices** to inspect declared partial orders, joins and shared-resource constraints. Use **Acceptance & unknowns** for complete family-level reference contracts
4. Search highlights matching operation occurrences without hiding the rest of the route. Previous/Next and browser Back/Forward retain occurrence identity, including repeated operation IDs

GitHub displays HTML source rather than running it. The diagrams and Markdown routes below are readable directly on GitHub.

## Nine visual route maps

Each SVG shows the designated reference view: Chiral R01, Deconwolf tubulin, fibre OPTO_SI, thermoelectric PAIRED_TWO, diSPIM D-R01, Acoustic WHOLE_PAPER_PRACTICAL, perovskite SPIN_MODULES, prismatic CUBE_HINGE_COMPARISON and EmVP POSITIVE_HELIX. Prismatic views distinguish operation membership, independent subcampaigns, conditional recovery and symbolic loops; they do not turn the membership list into a chronological route. The right-hand index lists every route/configuration choice. SVGs are deliberately long: no operation is silently removed. Each Markdown page includes **all** family routes/configurations, not just the pictured view.

| Family | Diagram | Every branch and route |
| --- | --- | --- |
| Chiral metamaterials | [Full SVG](diagrams/chiral.svg) | [28 route records](docs/chiral.md) |
| Deconwolf microscopy | [Full SVG](diagrams/microscopy.svg) | [6 preparation/imaging + 7 data branches](docs/microscopy.md) |
| Semiconductor fibres | [Full SVG](diagrams/fibre.svg) | [49 route records](docs/fibre.md) |
| Thermoelectric devices | [Full SVG](diagrams/thermoelectric.svg) | [15 route records](docs/thermoelectric.md) |
| diSPIM microscopy | [Full SVG](diagrams/dispim.svg) | [7 route templates, plus original branch contracts](docs/dispim.md) |
| Helical acoustics | [Full SVG](diagrams/acoustic.svg) | [8 route records, with nested loops](docs/acoustic.md) |
| Perovskite solar modules | [Full SVG](diagrams/perovskite.svg) | [40 route templates](docs/perovskite.md) |
| Prismatic metamaterials | [Full SVG](diagrams/prismatic.svg) | [12 route/configuration records across seven practical families](docs/prismatic.md) |
| Embedded extrusion-volumetric printing | [Full SVG](diagrams/emvp.svg) | [19 configurations across five practical families](docs/emvp.md) |

![Chiral first reference route and all branch choices](diagrams/chiral.svg)

## What the graph means

- Scientific stages may be source-reported; robot interfaces, transport, fixture handling and recovery are separately authored task designs
- For ordered reference sequences, dashed connectors and downward UI arrows indicate the package's **reference list order**, not recovered author chronology or the only valid robot trajectory
- Prismatic `operation_ids` declare **membership governed by partial-order constraints**, not chronology. Whole-paper campaign dispatch keeps the eleven component branches independent; it does not impose an order between them
- Prismatic material × target × attempt and thickness × target × attempt coverage remains nested. Unknown loop values/counts are not expanded, replaced with zero or treated as successful empty loops
- EmVP operation membership retains authored viewing order without adjacency arrows. The mixed cage comparison dispatches three separate condition routes; direct and embedded paths are never combined into one vial history
- EmVP comparison packages preserve outer allocation and inner observation dimensions without inventing operation-loop bodies. Known physical states, analysis regions and four hardness sites do not supply unknown independent specimen counts
- EmVP completion evidence is shown separately from the explicitly absent postconditions field; all 30 unresolved gates and source conflicts remain visible
- Prismatic `QUARANTINE` is conditional recovery, not a mandatory step in every route
- Acquisition/data obligation groups have **no inferred order between children**. Explicit source order annotations remain in each operation's provenance
- Acoustic loops retain the original loop variable, values, body and completion rule. The viewer shows one body template; it does not treat that as one completed repeated experiment
- Repeated scalar IDs in a route remain distinct occurrences. diSPIM's P001/P004 and the fibre P/N prefixes are not deduplicated
- Required transport insertions, sample cardinality, resource exclusions and incomplete inputs remain explicit obligations. The explorer does not silently satisfy them
- Counts describe the representation, not independent experiments, samples or successful executions
- Where the source provides no per-operation object-role list, the inspector labels that absence explicitly rather than inventing target roles
- Unknown real parameters and authored placeholders are never reclassified as measured facts

## Files and source fidelity

- `index.html`, `styles.css`, `app.js`: static, accessible, no-network viewer
- `data/<family>.json`: compact, inspectable normalized records
- `data/<family>.js`: the same JSON as a local-script assignment so `file://` does not require fetch
- `diagrams/*.svg`, `docs/<family>.md`: GitHub-native alternatives
- `build.py`: nine explicit source-schema adapters, standard library only; rebuilds counts and release-file checksums
- `tests/test_semantics.py`, `tests/test_prismatic.py`, `tests/test_emvp.py`, `tests/test_app.js`: source-level fidelity and mocked-DOM UI state checks
- [Adapter notes](docs/ADAPTERS.md), [verification report](VERIFICATION.md), [README integration snippet](README_INTEGRATION.md)

The immutable source snapshot is [openags/ScienceGym at 293e32da790303c1a17131e036235f69a5f342e0](https://github.com/openags/ScienceGym/tree/293e32da790303c1a17131e036235f69a5f342e0). Every source JSON link is pinned to that historical commit. Per-file SHA-256 values describe the local task files used to build this viewer. The 2026-10-03 standalone-presentation update changes scene-binding wording in three local perovskite metadata files; those local hashes therefore differ from the linked historical bytes, while scientific task contracts remain unchanged. See [verification](VERIFICATION.md). The original task JSON remains authoritative. No source PDFs, paper images or third-party assets are redistributed.

## Rebuild and test

From this folder, with the source repository available:

```sh
python3 build.py --tasks /path/to/ScienceGym/tasks
python3 -m unittest discover -s tests -v
node --check app.js
node tests/test_app.js
```

Set `SCIENCEGYM_TASKS=/path/to/ScienceGym/tasks` to run source-equality tests. Without it, source-equality tests skip explicitly; the bundled structural checks still run.

No remote publishing, external software installation, browser security changes, account changes or physics execution are part of this bundle. Repository-root LICENSE is unchanged.
