# Beaded metamaterials: independent source-claim audit

DOI: 10.1038/s41467-025-61809-8
Date: 2026-10-03 UTC

## Scope and source integrity

The main Results, captions, and Methods were independently inspected in an already-retrieved publisher-text view. The seven-page SI was reviewed through the parent and triage agents’ previously retrieved caption paraphrases. This auditor did not inspect SI figure pixels. Tables 1 and 2 were not independently available. No additional source routes were attempted after the access warning. No source full text or source figure images are reproduced here. This is a static audit, not a validated experiment or safety certification.

## Priority conflicts

### Nylon diameter

Status: unresolved_source_conflict
- Results, paragraph introducing Fig. 2b-c: 1 mm
- Fig. 2 caption, b-c: 0.5 mm

Do not select a diameter. The discrepancy affects cross-sectional area, elastic comparison, fit provenance and material identity. A library asset must preserve both claims with their locators.

### Catenary thread polymer

Status: unresolved_source_conflict
- Results, catenary-shell paragraph; Methods, Catenary shell: "nylon"
- Fig. 4d caption: "polyester"

Do not merge these polymer identities or infer a product from appearance. Preserve the waxed-filament/cord description separately from unresolved polymer identity.

### Cone state colour

Status: unresolved_source_conflict
- Fig. 4e caption: {"up": "white", "down": "gray"}
- Results, paragraph describing Fig. 4e: {"up": "gray", "down": "white"}

Use independently defined geometric orientation as a state label; keep the color legend unresolved.

### Chain decay comparison

Status: apparent_source_typographical_error_unresolved
- Results, paragraph describing Fig. 3d: The same polymer is named on both sides of a shorter-decay-length comparison.

Do not silently replace either occurrence with another material. This sentence cannot support an ordered material comparison on its own.

### Tomography panel pointer

Status: cross_reference_inconsistency
- Methods, Tomography: "Fig. 1b ii"
- Fig. 1 caption: "Fig. 1b iv"

Keep the caption-identified CT panel separate from the Methods pointer; avoid interpreting a photograph as a CT measurement.

### Shell projection alpha

Status: internal_equation_parameter_inconsistency
- Results, shell-load estimate following Fig. 3c: "alpha=0"
- Methods, Tracking bead motion, Eq. (3) and following sentence: "F_parallel=F/(m tan(theta_2) sin(alpha)); sin(alpha) approximately 0.9-1.0"

Substitution of the stated zero angle makes the denominator zero. No repaired angle convention is independently verified, so block automatic numerical evaluation for that stated special case.

### Friction tension convention

Status: analysis_convention_ambiguity
- Results, introduction to Fig. 3a-b: "Description refers to a difference between end tensions."
- Results, Eq. (1); Methods, Effective sliding friction: "The exponential relation has a tension-ratio form; the Methods measures sensor-end tension."

Store raw sensor-end tension, pretension and any derived difference separately. The capstan ratio applies to absolute tensions; do not treat a subtracted signal as interchangeable without resolving the authors’ convention.

## Tables 1 and 2

Both material tables remain unverified. Do not import supplier, SKU, bead-bore or thread-variant detail from an inherited record as if it were newly checked. An unread table cannot settle a diameter or polymer conflict.

## SI page and figure audit

### SI Figure 1 (PDF page 2)

Use separate fixture and specimen lineages. End fixation and platform bonding are distinct operations; a generic knot-only CT route loses a source-specific nitinol boundary. Do not reuse the testing-chain identity for the shorter CT chain. Dimensions, glue product, applied pretension and scan settings remain unresolved.

### SI Figure 2 (PDF page 3)

These are separate panels, not evidence of a full factorial experiment. Column-tip diameter must not become bead diameter. Pretension ranges do not enumerate all cases. Manual fixed-length clamping is not an independently calibrated constant-force condition. Numerical bead-size series, bore dimensions, frosted-surface preparation, repeat counts, slope fit range and failure definition remain unresolved. Printed Fig?? references in the SI are unresolved source placeholders.

### SI Figure 3 (PDF page 4)

The two illustrated materials also differ in pretension. Do not describe this pair as a pretension-matched material comparison. A reconstructed force path is a source interpretation, not an independently measured contact-force vector. Preserve 7.9 N as reported here rather than silently replacing it with the nearby 7.8 N bound used elsewhere.

### SI Figure 4 (PDF page 5)

CT ring sizes do not establish CT imaging for n=6. Preserve the normalization definition as an unresolved analysis detail until directly extracted. CT appearance alone does not validate a force model or a unique slack-distribution mechanism.

### SI Figure 5 (PDF page 6)

Keep the projected quantity separate from directly measured vertical indenter force. The three positions in an inset are not three independent replicates. This 2 N illustration does not enumerate every pretension in the main chain experiment. Sequential deformation history must remain attached to chain and position identity.

### SI Figure 6 (PDF page 7)

The four cycles do not establish four independent cones. The measured n=4 example is narrower than the n=3,4,5 design family discussed in the main Results. Point-contact geometry, loader speed, quantitative initial tension, force limit, full defect-family test matrix and moving-average window remain unresolved. Do not invent a universal snap-through threshold.

## Condition and count rules

- Distinguish architecture, condition, specimen, position, loading cycle, observation cycle, and derived display curve
- Never convert repeated cycles or architecture layers into independently fabricated specimen counts
- Keep ring n, total chain m, positional i and the shell’s local definitions scoped to their routes
- Keep ranges as ranges unless the discrete schedule is reported; do not generate unreported full-factorial condition grids
- Keep mechanical testing, tomography and photograph demonstrations as separate specimen lineages unless continuity is explicitly documented
- Do not harmonize mm/s with mm/min: the source assigns different units to different routes
- Reported fitted clamp extensions are analysis parameters, not the free gauge length set by an operator

The JSON companion contains the route-specific values and precise locators.

## Outstanding gaps

- No audited specimen-level ledger, independent fabrication count, randomization rule or explicit definition of statistical uncertainty is established here.
- Source-reported demonstration load capacity is not a validated safe working load. No human-support test should be inferred as part of the conversion.
- No byte-complete source archive was available; old hashes inside the inherited entry are unverified provenance claims, not hashes calculated from currently held sources.
- Do not use inventory membership to imply that every material, bead size, boundary condition and loading route formed a full factorial experiment.
- No primary data were rerun, and no data points were digitized from figures in this audit.
- Nitinol and nylon comparisons do not establish a thread-diameter-matched material-only control. Diameter identity is different or conflicting; preserve geometric and material covariates separately.
- Source text is adequate for a bounded static claim audit, not execution readiness. Source drawings were not visually inspected here; exact geometric dimensions and data-series counts require direct source verification when lawfully available.

## Sources

- Main article: https://www.nature.com/articles/s41467-025-61809-8
- Seven-page SI: https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-025-61809-8/MediaObjects/41467_2025_61809_MOESM1_ESM.pdf
