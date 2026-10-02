# ScienceGym Task Explorer

**See the task before reading its JSON.** Seven public paper-level task families, with complete reference-route occurrences, nested repetition, objects, state transitions and evidence.

This is a **read-only public reference inspector**, including evaluator material. It is not a simulator, a task runner, an actor-facing prompt or evidence that a robot performed any operation. The source release has **zero validated runnable whole-paper tasks**.

## Start here

1. Download or clone this folder and open **[index.html](index.html)** in a browser. It uses local JavaScript data, no fetch, server, installation or external library
2. Choose a task family and a route. Click any operation to inspect robot actions, target objects, pre/post state, evidence, acceptance, recovery and unknowns
3. Use **Dependencies & choices** to inspect declared partial orders, joins and shared-resource constraints. Use **Acceptance & unknowns** for complete family-level reference contracts
4. Search highlights matching operation occurrences without hiding the rest of the route. Previous/Next and browser Back/Forward retain occurrence identity, including repeated operation IDs

GitHub displays HTML source rather than running it. The diagrams and Markdown routes below are readable directly on GitHub.

## Seven visual route maps

Each SVG shows every listed step in its designated reference route: Chiral R01, Deconwolf tubulin, fibre OPTO_SI, thermoelectric PAIRED_TWO, diSPIM D-R01 and Acoustic WHOLE_PAPER_PRACTICAL. The right-hand index lists every route choice. SVGs are deliberately long: no operation is silently removed. Each Markdown page includes **all** family routes, not just the pictured route.

| Family | Diagram | Every branch and route |
| --- | --- | --- |
| Chiral metamaterials | [Full SVG](diagrams/chiral.svg) | [28 route records](docs/chiral.md) |
| Deconwolf microscopy | [Full SVG](diagrams/microscopy.svg) | [6 preparation/imaging + 7 data branches](docs/microscopy.md) |
| Semiconductor fibres | [Full SVG](diagrams/fibre.svg) | [49 route records](docs/fibre.md) |
| Thermoelectric devices | [Full SVG](diagrams/thermoelectric.svg) | [15 route records](docs/thermoelectric.md) |
| diSPIM microscopy | [Full SVG](diagrams/dispim.svg) | [7 route templates, plus original branch contracts](docs/dispim.md) |
| Helical acoustics | [Full SVG](diagrams/acoustic.svg) | [8 route records, with nested loops](docs/acoustic.md) |

![Chiral first reference route and all branch choices](diagrams/chiral.svg)

## What the graph means

- Scientific stages may be source-reported; robot interfaces, transport, fixture handling and recovery are separately authored task designs
- Dashed connectors and downward UI arrows indicate the package's **reference list order**, not recovered author chronology or the only valid robot trajectory
- Acquisition/data obligation groups have **no inferred order between children**. Explicit source order annotations remain in each operation's provenance
- Acoustic loops retain the original loop variable, values, body and completion rule. The viewer shows one body template; it does not treat that as one completed repeated experiment
- Repeated scalar IDs in a route remain distinct occurrences. diSPIM's P001/P004 and the fibre P/N prefixes are not deduplicated
- Required transport insertions, sample cardinality, resource exclusions and incomplete inputs remain explicit obligations. The explorer does not silently satisfy them
- Counts describe the representation, not independent experiments, samples or successful executions
- Unknown real parameters and authored placeholders are never reclassified as measured facts

## Files and source fidelity

- `index.html`, `styles.css`, `app.js`: static, accessible, no-network viewer
- `data/<family>.json`: compact, inspectable normalized records
- `data/<family>.js`: the same JSON as a local-script assignment so `file://` does not require fetch
- `diagrams/*.svg`, `docs/<family>.md`: GitHub-native alternatives
- `build.py`: seven explicit source-schema adapters, standard library only
- `tests/test_semantics.py`, `tests/test_app.js`: source-level fidelity and mocked-DOM UI state checks
- [Adapter notes](docs/ADAPTERS.md), [verification report](VERIFICATION.md), [README integration snippet](README_INTEGRATION.md)

The immutable source snapshot is [openags/ScienceGym at 2f926a9d2c2b](https://github.com/openags/ScienceGym/tree/ebf366bde7d8b8fd0899165d168a9f8f7c43c8ca). Every source JSON link is pinned to that commit. Per-file SHA-256 values are retained in each data file. The original task JSON remains authoritative. No source PDFs, paper images or third-party assets are redistributed.

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
