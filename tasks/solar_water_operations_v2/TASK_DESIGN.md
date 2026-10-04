# Bounded clean-water physical task design

## Scope and source

This original design adapts physical portions of Singh et al., Nature Sustainability 3, 938–946 (2020), DOI [10.1038/s41893-020-0566-x](https://doi.org/10.1038/s41893-020-0566-x). The upstream audit read the complete 19-page main PDF including ten Extended Data pages and complete 36-page written SI, and sampled all four supplementary videos. This conversion re-inspected the audit and actual physical source sections and selected physical image/video sheets. It does not claim a fresh independent full-page source audit.

Complete source accounting is different from conversion coverage. This package is a bounded nonbiological design. It must not enter a full-paper-complete count. The biological sample and assay work is excluded, as are unknown environmental water, field dirt and contaminated-coupon handling. No organism-related operational procedure is included. Fabrication and hazardous chemistry are qualified-service boundaries; this package cannot operate a laser fabrication line or a pollutant preparation/analysis workflow. All collected water remains outside any potable, sterile or disinfection claim.

## Physical branches

Fifteen branches cover qualified coupon receipt; clean-water assembly registration; spectral/angular optics; qualified surface metrology; wet-front motion; reservoir transfer transients; dark loss; horizontal light-driven loss; dry thermal response; vertical operation; orientation comparison; bifacial comparison; fixed outdoor observations; clean-water condensate bookkeeping; and benign-only closed cleaning/reuse inspection. There are 34 original action templates. Preparation/service branches do not purport to reproduce the omitted source fabrication and chemical methods.

Scientific source facts, authored interfaces and missing qualifications are separate. Each control field has an explicit provenance category; task guards housed alongside source constraints are not source-reported instructions. The paper describes physical geometry and measured observables, but supplies neither robot CAD/trajectories nor authenticated station adapters. Source dimensions remain historical context. Actual grip points, bend tolerances, fixture forces, sensor placements, acceptable calibration error, water volumes, optical/thermal trip limits and replicate design are unresolved. A source measurement is not a robot target or an authorization to increase illumination.

## Three distinct mass experiments

1. Wet-front imaging measures position over acquisition time. The source camera acquisition rate and slowed publication playback are distinct. Pixel calibration, front segmentation, initial wetness and contact geometry must remain explicit.
2. Reservoir transfer observes a coupon supported separately from the reservoir balance. Contact, buoyancy, meniscus force, uptake, withdrawal, retained-water release and ordinary evaporation are distinct phases. A balance jump alone is not water transfer.
3. Evaporation weighs the floating assembly and reservoir together. Matched aperture, active area, temperature and ambient metadata matter. Open mass loss is not recovered condensate yield. The condensate branch is explicitly a clean-water adaptation with its own collector and mass-balance uncertainty.

## Material and apparatus lineage

The receipt service publishes the qualified inventory for selected cases. For assembled routes, these coupons enter the ASSEMBLE batch intake before they can appear in a downstream device release. The assembly branch mount refers to an independent batch carrier, not a downstream device; receiving the service output invalidates its prior calibration and is followed by registration and recalibration. The assembly service names each downstream coupon and assembly in its output inventory, grouped by the qualified horizontal/vertical assembly form. Child jobs bind the exact released target records and inventory hashes. Distinct processed/unprocessed, single/double and bulk-water controls have distinct material identities. Bulk-water controls have no coupon, rather than borrowing a processed coupon identifier.

Each case keeps coupon/version, fabrication lot, surface revision, assembly/support/aperture/reservoir identifiers, fluid lot, collector where applicable, mount/setup revision and calibration. Fresh water creates a new lot and records the previous disposition. Service cleaning changes the coupon version and surface revision; previous wetting/optical baselines cannot be presumed current. The proposal supplies service handoff semantics, not measured proof that any particular assembly exists.

## Causal safety boundaries

Transfer and mount require independent safe-state evidence. Mount and orientation changes invalidate calibration. Geometry registration precedes current calibration. Each wet illumination case obtains its own dark baseline and clean-water thermal reset before requesting only the station-approved exposure. Bifacial cases include front and rear flux records. Outdoors, current weather, shading and sensor plane are additional conditions; the paper does not demonstrate closed-loop solar tracking.

Shutdown requests do not prove a safe state. The release sequence is deenergize, qualified cooldown, independent clearance, readout, disconnect, retain/retrieve, inspect, archive and disposition. Missing or unsafe evidence stops dependent work. Numeric cooldown duration and safety thresholds are not fabricated. Dry-out, spill, optical and thermal protection require a real station qualification absent here. Failure does not erase exposure, damage or surface history.

## Conflicts and interpretation

All 14 audited conflicts remain in source_conflicts.json. In particular, the SI seconds-based rate units and main hours-based units stay source-specific; the outdoor angular conventions are not silently reconciled; dark fitting windows differ; raw and area-corrected slopes differ; and spectral versus solar-weighted absorption is not one acceptance bound.

The reduced effective vaporization enthalpy is a model-dependent source hypothesis that relies on heat-input and area assumptions. It is not direct calorimetry, a validated universal constant or a scientific success criterion. Ambient temperature equality does not independently prove equal heat input. Raman/cluster interpretations, FDTD, annual flux calculations and analytic models remain unimplemented dependencies. Rear illumination changes bifacial energy input. Neither an evaporation-rate gain nor a comparison to an ideal reference model establishes measured over-unity conversion.

Chemical identity/value conflicts and the laboratory disclaimer remain visible in coverage accounting without enabling chemical or biological operational branches. Historical threshold tables do not certify regulatory compliance. The qualitative cleaning clip supplies no standardized cleaning pressure, lifetime or quantitative decontamination endpoint.

## Offline contract checks

Only agent_visible.json is actor-facing. The actor supplies event_id, job_id and phase. Environment-side fixture cards, observations and immutable raw-record hashes are separate. The offline checker requires the exact canonical plan and rejects actor-supplied outcomes, missing/reordered/replayed phases, false source resolutions, stale calibration/lineage and missing controls or cleanup.

The fixture contains synthetic bookkeeping records only, with scientific_measurement_values=null. Its time is ordinal, not elapsed exposure. The context is caller-owned; this is not an authenticated security boundary or a production evaluator. Recomputing a deterministic fixture proves consistency of a proposed contract, not actual robot safety, experimental success, scientific replication, numerical reproduction or physics simulation.

## Release

The exact allowlist contains only original package JSON, documentation and Python validators/tests. Source PDFs, text, figures, videos, third-party reports, acquisition records and raw source assets are excluded. Publication is handled separately by the parent workflow. The package author has made no public writes.
