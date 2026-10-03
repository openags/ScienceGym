# Contributing to ScienceGym

Help turn full papers into inspectable robot task families, or build the assets and interfaces those tasks require. The current release supports static design and display review. It has no supported whole-paper execution command. Physical simulation is paused; task and asset work can proceed independently.

## Start with one bounded contribution

1. Read the [project vision](docs/PROJECT_VISION.md), repository README and one relevant task's TASK_DESIGN.md. For a safe mechanical example, use [directional cooling](tasks/directional_cooling_operations_v2/TASK_DESIGN.md).
2. Search open and closed issues, pull requests and `tasks/` for the DOI, title and device name. A preprint, journal version and correction usually belong to one source family, not three independent tasks.
3. Open or join an issue. State the DOI or asset ID, exact deliverable, affected branches, access status, likely gaps and what another contributor can do in parallel. Use the paper or asset issue template. Claim ownership by agreement in that issue; an assignment or comment does not grant repository permissions.
4. Choose the smallest reviewable unit: a source audit, one preparation branch with coverage dispositions, an asset with affordances, a task binding, or evaluator tests. Identify interfaces before collaborators edit overlapping files.
5. Submit a focused pull request with evidence and limitations. A complete task-design submission needs a whole-paper coverage map even when some branches remain gated or deferred. A branch-only PR must say so.

## Contribution tracks

- **Task only:** evidence, complete coverage inventory, robot operations, dependencies, controls, lineage and explicit unknowns. List unbuilt assets; do not wait for CAD
- **Assets only:** licensed or original geometry plus scale, states, interaction metadata, screenshots and limitations. Identify the task need or reusable interface it serves
- **Task binding:** map stable task IDs to concrete asset instances, stations, controls and observations; demonstrate representative interactions at the claimed level
- **Evaluator and tests:** add trusted completion contracts and positive/negative tests, keeping agent and evaluator visibility separate
- **Documentation and review:** improve onboarding, audit source claims, test instructions or record reproducible defects

## Roles and handoffs

Roles describe responsibilities, not assigned people or promised permissions. One contributor may hold several roles, but an independent review should examine consequential source and evaluation claims.

| Role | Owns | Handoff evidence |
| --- | --- | --- |
| Source reviewer | Access, version, rights, source locators | Source audit and coverage dispositions |
| Task author | Robot actions, branches, lineage and gaps | Task package and operation walkthrough |
| Asset author | Geometry, states, affordances and provenance | Asset record and screenshots |
| Integrator | Task-to-scene mappings and interface compatibility | Binding map and exercised cases |
| Evaluator reviewer | Completion predicates and leakage checks | Positive and negative tests |
| Maintainer | Scope, review resolution and release decision | Recorded acceptance at a stated readiness level |

Agree on IDs, coordinate conventions and ownership in the issue before parallel work. Use small linked PRs when assets, task design and bindings have different readiness. Unresolved decisions should name the affected files, a proposed next step and the person who has agreed to resolve them. If work is paused, leave a handoff with current status; do not silently duplicate someone else's draft.

## Branches and pull requests

Use a fork if you lack write access, or an authorized feature branch such as `task/cooling-cover-handling` or `asset/film-holder`. Keep generated renders, source downloads, secrets and local paths out of unrelated diffs. Do not rewrite historical review receipts to make them describe a new revision; add a dated receipt and reference the tested revision.

A PR should link its issue, summarize the exact scope, distinguish source facts from authored choices, list gaps and readiness claims, and include commands with actual results. Explain changes to stable IDs, visibility or acceptance rules. If an interface breaks compatibility, record the migration and affected consumers. A merged draft remains a draft until the stronger gate is independently evidenced. Merge authority belongs to the repository's maintainers.

## Run the checks that exist

From the repository root, with Python 3.9+ and Node.js on PATH:

```sh
python3 -B scripts/verify_release.py
```

This checks JSON syntax, English hygiene, verifier regressions, explorer semantics, JavaScript/mock-DOM display contracts and frozen image hashes. It does not discover every task package's tests, enforce a universal task/asset schema, use a real browser or execute a robot. Run relevant package tests separately; the paper guide gives a verified example. Record failed or unavailable checks honestly. Do not claim CI ran unless an actual CI result exists.

## Acceptance and reviewer decisions

Use the [readiness rubric and PR checklist](docs/contributing/REVIEW_CHECKLIST.md). Reviewers should request changes for generic “prepare sample” steps with hidden manipulation; omitted controls or destructive allocation; invented source procedures; unknowns converted into defaults; evaluator answers exposed to the actor; unlicensed source/CAD/texture redistribution; or attractive assets with no task-relevant affordances.

A draft with visible execution gaps can be accepted as a design contribution. A missing source dependency that prevents defensible extraction blocks a stronger source-complete claim. A missing grasp or calibration input blocks affected execution, not unrelated evidence review. Every acceptance should name its scope and readiness level rather than calling the task simply “done.”
