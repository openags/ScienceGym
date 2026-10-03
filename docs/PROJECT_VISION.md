# ScienceGym Project Vision and Collaboration

3 October 2026

ScienceGym aims to turn the reported experimental programs of scientific papers into source-grounded tasks for embodied research agents. The central question is whether a robot can preserve experimental intent across preparation, fabrication, transport, instrument use, controls, repeated measurements and recovery. A successful agent must maintain both the physical state of the laboratory and the evidential integrity of its work.

This document explains the research goal and contribution model. Start with [CONTRIBUTING.md](../CONTRIBUTING.md) to choose work, claim an issue and prepare a pull request. Use the [paper task guide](contributing/PAPER_TASK_GUIDE.md) for source-to-task conversion and the [asset guide](contributing/ASSET_GUIDE.md) for objects, equipment and scene bindings. Contributors can advance these tracks in parallel without waiting for perfect CAD or a working simulator.

## Why experimental papers are useful task sources

A reported experiment has a reason for each major stage. Materials are prepared to enable fabrication; fabrication produces specimens for characterization; controls make measurements interpretable; repeated observations test consistency. These dependencies create tasks whose difficulty extends beyond an isolated manipulation. The significance of an action may become apparent much later, when the agent needs the correct calibration, specimen history or comparison condition.

Papers also provide a shared reference for reviewing task requirements. Methods, figures and supplementary information identify objectives, equipment, conditions and outcomes. They remain imperfect sources: handling details may be omitted, historical ordering may be unclear, and one figure may combine several sessions. ScienceGym therefore attaches evidence and uncertainty to the translation rather than pretending a paper is an executable protocol.

Long-horizon robotics and laboratory automation have substantial precedents. BEHAVIOR-1K studies extended everyday manipulation and state management; Burger and colleagues demonstrated autonomous experimental searches by a mobile robotic chemist. ScienceGym's proposed contribution is a reusable methodology for translating diverse published experimental programs into auditable robot task families and evaluating their operational demands. [1, 2]

The research opportunity is to study how scientific validity changes embodied tasks. A final-looking arrangement is insufficient if the wrong sample was measured, a control was omitted or an invalid observation was replaced. These obligations belong in the task definition and evaluator.

## The goal and unit of completion

The ultimate goal is an embodied agent completing the full represented physical experimental program of a paper. That includes all hands-on preparation, fabrication handling, assembly, sample handling, transfers, device setup, acquisition, recovery and cleanup within the declared scope. Automated devices may perform their own processes after valid robot setup. A process name, API call or completed specimen inserted into the initial state cannot stand in for missing physical work.

A paper usually yields a branching partial order. Shared preparation supports downstream measurements; alternative materials create distinct routes; destructive tests need allocated specimens; independent experiments may occur in either order. Preserve these relationships without inventing a single chronological chain or recovering an unreported history of trial and error.

A paper-level task family describes the represented program. An episode covers a declared route or control package. A campaign combines the required episodes and shared prerequisites. One successful episode does not establish whole-paper completion. Each family must state what was represented, what was excluded and why, and which unresolved inputs prevent execution.

Every operation must identify an actor, manipulated object, tool, station, interaction interface, preconditions, postconditions and observable completion evidence. The robot retrieves and prepares resources, loads and unloads fixtures, mounts and connects devices, reads controls, transports supported objects and restores stations. Device processing and waiting remain distinct from robot manipulation.

Closed-service abstractions can make an early design inspectable, but their boundary must be visible. If fabrication hides manual work inside a service, the package remains incomplete against the ultimate all-hands-on goal until that work is decomposed or the release explicitly limits its scope. A qualified automatic device process is different from an unnamed human doing the difficult step.

## Source scope and evidence discipline

The collection scope is Nature, journals whose formal titles begin with Nature, and Science. npj titles and other Science-branded journals are outside this initial rule. The intended scientific range is broad, subject to safety screening, lawful access and meaningful embodiment. Reviewing roughly 20–30 suitable papers per relevant journal is a collection objective, not a promise that every journal will yield that many eligible tasks.

For this contribution track, use legally accessible open-access full main articles and all supplementary materials necessary to recover the represented program. An abstract, DOI or figure caption supports indexing, not a claim of full reading. Record missing or inaccessible dependencies. Do not bypass restrictions, redistribute materials without permission or fill missing details with plausible facts.

Keep three categories explicit throughout a package: source-reported facts with locators; authored robot translations with rationale; and unknowns with affected operations and resolution requirements. Conflicting source statements stay visible. An authored replacement input can enable a declared benchmark variant after qualification, but cannot become a newly discovered fact about the original experiment.

Safety screening precedes operationalization. Actionable pathogen, toxin, viral and genetic-engineering procedures with bioweaponization potential are excluded. Use safe, inert examples for new contributor exercises. Designs are research specifications, not approved laboratory SOPs or authorization to operate equipment. Domain and equipment safeguards are additional requirements for any future physical work.

## What a contribution should produce

A useful task package connects six inspectable layers:

1. **Evidence and coverage:** bibliographic identity, lawful access records, exact source locators, experimental branch inventory, nonmanual dispositions and a gap ledger
2. **Resources and operations:** starting materials, specimen and component identities, tools, stations, robot actions, device processes and observable state transitions
3. **Experimental structure:** dependencies, controls, conditional routes, independent specimens, technical repeats, cycles, destructive allocations and lineage
4. **Agent inputs and evaluation:** selected goals, available observations and action interfaces, separated from reference routes, hidden states, future observations and evaluator predicates
5. **Assets and bindings:** geometry, appearance, interaction states, ports, supported grasps, mounts, collision approximations and mappings to task objects and operations
6. **Verification:** source review, static tests, display evidence, known limitations and versioned receipts, with functional and physical validation claimed only when separately demonstrated

Current packages are heterogeneous. These layers describe the required review baseline and a proposed common contract, not an installed universal schema or runtime API. Adapt an existing package thoughtfully, document field mappings and preserve stable identifiers. A task-only contribution can be valuable before its assets exist; an asset-only contribution can be valuable before a controller exists. Each must say exactly what is usable and what is missing.

## A worked direction in radiative cooling

The directional cooling package translates Bhatia and colleagues' *Passive directional sub-ambient daytime radiative cooling*. It contains 11 physical route leaves, including device preparation, sensor calibration, optical characterization, paired white/black outdoor comparisons, a heater-bearing route, an alternative reflector/cover assembly and three environmental thermal-map conditions. These are design branches, not eleven executed experiments. [3, 4]

The authored robot campaign starts with identified stock and fabrication inputs. The robot carries supported parts to service fixtures, verifies setup and safe-release feedback, inspects returned parts, builds identified devices, calibrates probes and preserves component membership. It loads optical references and samples, checks configurations, records acquisitions, unloads locally and retains identity across transfers.

Outdoor sessions require supported docking, sensor connections, synchronized records and verified shading geometry. Replacing films, attaching heaters or changing the reflector creates an assembly revision with renewed inspection obligations. Different weather-dependent branches require eligible sessions; weather cannot be commanded by editing a label. Damaged films are replaced and recorded, not repaired by relabeling them.

The package still lacks qualified fabrication details, geometry, calibration criteria, instrument settings, robot bindings and scientific backends. The source's reflector-height descriptions include an unresolved datum ambiguity. A contributor should preserve it, rather than choose a convenient CAD height and claim source fidelity. The paper guide shows a concrete operation-level improvement using this package; the asset guide shows how to turn its assembly needs into a reviewable asset contribution. Neither example establishes feasible motion or reproduced cooling performance.

## Research hypotheses and evaluation

The main hypothesis is that paper-grounded experimental structure creates consequential demands on persistent state and causal planning beyond the difficulty of component actions. An agent may load or measure successfully in isolation yet fail to preserve identity, calibration or controls across a route.

A second hypothesis is that explicit memory and dependency-aware planning improve cross-device coordination and branch management. Compare agents with matched perception, action capability and resource budgets, changing persistent records, structured plans or lineage representations separately. Improvements must appear in verified outcomes, not more persuasive explanations.

A third hypothesis concerns recovery under partial observability. Interrupted acquisitions, perturbed layouts, damaged components and similar specimen labels can test inspection, diagnosis and valid resumption. Hidden faults must have discoverable consequences through legitimate observations. Impossible-to-observe requirements are benchmark defects; safe partial completion should remain distinguishable from claimed success.

A fourth hypothesis is transfer across held-out papers, experimental families and laboratory layouts. Another parameterization of a familiar route is weaker evidence than a held-out paper or device combination. Split design must address near duplicates and public-paper exposure; evaluator-only material must never enter agent observations.

Source traceability is also testable. Independent reviewers should recover which requirements follow from a source, which are authored and which remain unresolved. Agreement, corrections, omission rates and curation effort can evaluate the construction methodology. These are prospective hypotheses, not reported performance findings.

Evaluation needs both stage and end-to-end metrics. Stage metrics localize manipulation, setup, acquisition, identity and recovery failures. Episode success requires its mandatory conditions; campaign success requires its declared coverage and comparisons. Report partial credit alongside strict completion so high average stage scores cannot hide failure to complete any valid program.

A matching literature number cannot compensate for missing actions or fabricated acquisition. A correctly obtained weak or negative observation can be an operational success. Literature outcomes, authored mock observations and measured outputs must remain different data classes. Scientific-result fidelity becomes meaningful only with a validated scientific backend.

Characterize horizon using dependency depth, device transitions, persistent objects, branches, loops, delayed checks and irreversible decisions, alongside action counts and time. Repeating one simple action is not sufficient evidence of long-horizon reasoning. Useful baselines include reference controllers, reactive agents, plan-then-execute agents and memory-equipped agents. Use matched short-versus-long comparisons, ablations, repeated runs, uncertainty estimates and failure analysis. A valid reference route establishes solvability only within its tested conditions.

## Current maturity and priorities

The fixed baseline at revision `3a200acfb22dfe6db3ec9864800bc26acb8e1fca` contains 563 files and 16 reviewed paper-level task-design drafts. Nine families appear in the logical explorer, and two selected routes have authored embodied storyboards. There are zero validated whole-paper robot runs. These counts describe different artifacts and must never be combined into a completed-task total. New documentation will change the file count. [5]

The current setting is CPU-only and physical simulation is paused. Continue source-grounded task conversion, asset specifications, inspectable scenes and evaluator design in parallel. Static or visual acceptance does not require new physics work. Displayed robot poses do not prove contact mechanics, reachability, valid control or experimental physics.

Near-term work should deepen representative families while broadening eligible source coverage. Resolve important gaps, make preparation explicit, improve asset affordances, test bookkeeping and quantify reviewer corrections. Then implement selected end-to-end episodes with trusted state transitions, meaningful interfaces and independently tested evaluators. Expand to campaigns when branch accounting, shared resources and specimen histories function together.

A strong eventual research contribution would combine an audited construction method, diverse executable tasks, reproducible agent comparisons and findings about long-horizon scientific work. The current prototype provides an initial design substrate. Dataset size alone does not establish performance, generalization, scientific replication or publication readiness.

## Sources and project references

[1] Li et al. *BEHAVIOR-1K*. [Research paper](https://arxiv.org/abs/2403.09227)

[2] Burger et al. *A mobile robotic chemist*. Nature 583, 237–241, 2020. [Publisher article](https://www.nature.com/articles/s41586-020-2442-2)

[3] Bhatia et al. *Passive directional sub-ambient daytime radiative cooling*. Nature Communications 9, 5001, 2018. [Open-access article](https://www.nature.com/articles/s41467-018-07293-9)

[4] [Directional cooling task package at the baseline revision](https://github.com/openags/ScienceGym/tree/3a200acfb22dfe6db3ec9864800bc26acb8e1fca/tasks/directional_cooling_operations_v2)

[5] [ScienceGym baseline](https://github.com/openags/ScienceGym/tree/3a200acfb22dfe6db3ec9864800bc26acb8e1fca) and [current repository](https://github.com/openags/ScienceGym)
