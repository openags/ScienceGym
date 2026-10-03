# Independent prismatic-metamaterials source audit

Paper: [Exploring multistability in prismatic metamaterials through local actuation](https://www.nature.com/articles/s41467-019-13319-7)
DOI: 10.1038/s41467-019-13319-7

## Bottom line

All requested physical branches are present in the supplied primary sources, with major limitations on executable detail. The most important correction is a text/figure disagreement in truncated-tetrahedron relaxation destinations: the text says vii/xi, while Figure 4b shows vii/xiii. The compression instability counts also differ between the main and SI captions.

## Scope

Full main scientific text, Methods, data/code statements and primary SI captions/text; visual inspection of all scientific main figures and SI Figures 1–9 (SI text-only title/references pages read).

No main-PDF retry, movie inspection, physical simulation, hardware work, or remote publishing was performed. Source files remain unchanged except a separate convenience text extraction. The audit is source verification, not independent replication.

## Branch findings

### cardboard_dimensions
Figure 1 demonstrates cardboard prototypes with 24 mm square faces, 0.4 mm cardboard thickness and double-sided-tape hinges; panels a/b/c represent truncated tetrahedron / truncated cube / cuboctahedron.
Evidence: cardboard, figure_1_pixels. Status: source_reported.

- These dimensions do not establish L or face dimensions for the separate PLA/Mylar prototypes.
- Tape brand, layup, hinge-gap geometry, net/CAD and assembly tolerances are not supplied in the inspected main article or primary SI.

### elastic_vs_rigid
Additional states can be spatially admissible yet unreachable under rigid-face folding; temporary face deformation lowers the transition barriers. The numerical surrogate uses in-plane stretching and suppresses face bending.
Evidence: design, model_overview. Status: source_reported.

- Experimental deformation must not be equated with measured intrinsic PLA face stretching alone; source describes effective compliance arising from hinge stretchability/flexibility.

### pla_mylar_fabrication
Each compression-prototype face is built from two Ultimaker 3-printed PLA pieces, each 0.5 mm thick; a laser-cut 50 micrometre Mylar sheet is manually clamped between the pair to connect faces and form hinges.
Evidence: compression_fabrication, compression_caption. Status: source_reported.

- 2 × 0.5 mm describes paired pieces, not a single 0.5 mm total face.
- Printer settings, Mylar grade, cut geometry, hinge gaps and face dimensions are unreported in inspected sources.

### compression_apparatus
The source names a cuboctahedron-based prototype and an Instron 5965L9510 material test machine, with cyclic displacement magnitude u_max = sqrt(2) L.
Evidence: compression_fabrication. Status: source_reported.

- Preserve instrument designation as printed; no independent model/serial interpretation.
- L in physical length units, loading speed, grip dimensions, load cell specification and data acquisition rate are unresolved.

### compression_cycles
The main text averages the last five compression cycles and uses line thickness for standard deviation. The Figure 2 caption describes cyclic loading five times.
Evidence: compression_fabrication, compression_caption. Status: source_reported.

- Five contributing cycles are supported; total specimen history, excluded cycles and independent specimen count are not established.

### compression_response
The reported response has a plateau near u/u_max ≈ 0.6, negative force after an instability near 0.75 and different unloading path (hysteresis). Simulation is claimed to agree qualitatively, with a small simulated end-of-compression hysteresis loop absent experimentally.
Evidence: compression_response, compression_caption, figure_2_pixels. Status: source_reported.

- No calibrated numerical error bound, repeatability across specimens or raw traces are provided.
- Exact event-count ground truth is disputed between Figure 2 and SI Figure 1; see conflict C2.

### compression_simulation_parameters
The comparison simulation uses κ = 10^-4; opposite-face boundary constraints permit vertices to move only along the compression axis. Two added axial edges apply a displacement-control penalty. Loading has 1000 increments and unloading another 1000, relaxing at each increment with Active-set.
Evidence: compression_simulation, compression_penalty, compression_steps, equation_28. Status: source_reported.

- 1000 is a numerical increment count, not a physical sampling rate or physical cycle count.
- Penalty stiffness is specified comparatively as much larger than hinge and edge stiffness, without a numerical value.

### stiffness_sweep
SI Figure 1 compares κ = 10^-4, 10^-3 and 10^-2; the first two are qualitatively similar, while 10^-2 changes unloading behavior and raises minimum force. The caption also says κ below 10^-4 gives similar results, not shown.
Evidence: compression_response, si_figure_1. Status: source_reported.

- This is numerical evidence, not additional physical testing or a material calibration.

### pair_actuation
The hinge-pair scans load one hinge and then another while holding the first target, record the loaded energy, then release both torques and relax. Altering order can alter outcomes.
Evidence: pair_loading, pair_caption, pair_relaxation, truncated_tetrahedron_pair_states, si_figure_2, si_figure_3. Status: source_reported.

- The maps are two-dimensional projections of a higher-dimensional, path-dependent system, not globally exhaustive energy landscapes.

### triangular_prism_pair_count
For the shown triangular-prism hinge pair, released configurations converge to two states at angle pairs (2π/3, 2π/3) and (π, 0); other hinge-pair scans show at least three stable configurations.
Evidence: pair_relaxation, si_figure_2. Status: source_reported.

- Do not confuse triangular prism with tetrahedron or truncated tetrahedron.

### tetrahedron_search_counts
A truncated-tetrahedron hinge pair yields 16 raw states, reduced to eight by symmetry-related clustering; scanning all other hinge pairs yields 12 unique states. Discrete unique hinge-combination search reports 213 stable states after duplicate/symmetric-state removal.
Evidence: truncated_tetrahedron_pair_states, tetrahedron_reachability. Status: source_reported.

- These counts have different search scopes and must not be substituted for one another.
- They are search results, not a mathematical proof of complete physical state enumeration.

### tetrahedron_attempt_partition
For 17 states accessible numerically using up to three simultaneous actuated hinges, seven are directly retained experimentally; i–v do not persist after release, and viii plus xiv–xvii cannot be reached because of maximum prototype hinge stretch.
Evidence: tetrahedron_reachability, states_caption, figure_4_pixels. Status: source_reported.

- Tetrahedron here means truncated tetrahedron; regular tetrahedron appears separately in SI Figure 5a.
- 17 = 7 directly retained + 5 relax-after-release + 5 stretch-limited. This partition is source-supported; destination identities have conflict C1.

### tetrahedron_direct_ids
Figure 4b shows physical retained matches for vi, vii, ix, x, xi, xii and xiii.
Evidence: figure_4_pixels. Status: visually_verified.

- These seven identities are read from panel labels/photographs, not explicitly enumerated together in body text.

### tetrahedron_kappa
Failure of states i–v with κ_max < 10^-3 motivates the authors’ approximate experimental κ ≈ 10^-3. κ_max is the last stiffness ratio retaining a found state while hinge stiffness is increased stepwise.
Evidence: tetrahedron_reachability, stiffness_stability. Status: source_reported.

- The approximate κ is inferred from state retention, not a reported direct measurement of hinge/face moduli or a universal threshold.
- No κ sweep step size is given.

### cube_hinge_swap
Eight cube states are reported numerically. None can be reached with the Mylar implementation; replacement with 0.5 mm elastomeric rubber hinges allows six states. State ii remains stretch-limited; state iii requires non-adjacent face crossing omitted by the model.
Evidence: cube_hinge_change, states_caption, figure_4_pixels. Status: source_reported.

- Source calls the material silicon rubber/silicon hinges; use an explicit source-spelling note if normalizing to silicone.
- No elastomer product, Shore hardness, modulus, curing recipe or replacement joint design is recovered.

### cube_retained_ids
Figure 4d depicts retained elastomer-hinge physical states i, iv, v, vi, vii and viii, with single-asterisk failure at ii and double-asterisk failure at iii.
Evidence: figure_4_pixels, states_caption. Status: visually_verified.

### broader_search_limits
The 16 additional structures are investigated with all unique hinge combinations only through 18 internal hinges; larger structures use at most three hinges. The article reports found-state counts ranging from 2 to 418.
Evidence: broader_search, si_figure_5. Status: source_reported.

- Do not infer exact per-structure totals by counting plotted, potentially overlapping dots.
- SI Figure 5 panels a–e cover all unique combinations; f–p use at most three hinges.

### si6_displayed_pairs
SI Figure 6 page 11 shows 11 numbered selected experiment/numerical pairs for truncated cube (a, 1–11) and 15 for rhombicuboctahedron (b, 1–15).
Evidence: si_figure_6. Status: visually_verified.

- These are displayed selected configuration comparisons, not exhaustive unique-state totals or 11/15 additional-state claims.
- Exact actuation patterns, transition paths, successful-trial counts and durations cannot be read from static configurations.
- The caption itself does not specify the fabrication material or dimensions.

### periodic_search_scope
The periodic search uses cubic tessellations of 11 polyhedra yielding 15 materials; it reuses actuation patterns that produced isolated-unit states. Eleven materials show additional states. Periodic constraints exclude many asymmetric unit states and can shift state energies.
Evidence: periodic_search, periodic_results. Status: source_reported.

- Unit-cell state identity/energy does not automatically transfer to an assembly.
- This is an initial, restricted search, not exhaustive enumeration.

### main_periodic_counts
Figure 5 labels three additional states for the cuboctahedron material, three for its rhombicuboctahedron material and 16 for its truncated-cuboctahedron material.
Evidence: figure_5_pixels. Status: visually_verified.

- Counts attach to the specific displayed tessellations. Other tessellations using the same polyhedron can have different counts.

### finite_array
The experimental cuboctahedron assembly contains 2 × 2 × 2 building blocks. With 50 micrometre Mylar hinges, one targeted bulk stable state is achieved; target states ii and iii fall below the approximate κ ≈ 10^-3 stability threshold.
Evidence: array_thickness, array_caption, figure_5_pixels. Status: source_reported.

- The array has eight building blocks by arithmetic, not eight measured independent replicates.
- The one-state claim concerns the targeted periodic bulk states and must be kept separate from observed boundary/long-period states.

### array_thickness_control
A second assembly uses 125 micrometre Mylar sheets and is reported not to exhibit stable states in the discussed multistable-state test.
Evidence: array_thickness. Status: source_reported.

- Interpret as no additional retained states in the tested context; do not claim the object lacks an initial equilibrium.
- The paper does not provide a measured new κ, replicate count, thickness-dependent quantitative law or all specimen equivalence controls.

### finite_array_model_mismatch
Figure 5f and text identify boundary-localized stable states; Figure 5g/text identify states with periodicity or wavelength larger than one unit cell, outside the single-cell periodic simulations. Larger unit cells would be required to capture the latter.
Evidence: array_boundary, array_caption, figure_5_pixels. Status: source_reported.

- Do not count these as failed predictions of the exact same modeled boundary-value problem.
- No exhaustive boundary-state or long-period state total is provided.

### pneumatic_demo
Discussion reports discrete local actuation of two pneumatic pouches on a truncated-tetrahedron structure attaining four stable states and cites Supplementary Movie 6.
Evidence: pneumatic. Status: source_reported.

- Text-only branch in this audit; Movie 6 was neither acquired nor inspected.
- Pressure, flow, pneumatic circuit, pouch dimensions/materials, hinge attachment IDs, timing/order and state labels are not recovered.
- Do not infer a complete 2-bit truth table solely from two pouches and four states.

### scale_scope
Experiments are validated only at centimetre scale. Scale independence is a theoretical mechanical statement, and microscale fabrication, capillarity and individually addressable actuation are named open issues.
Evidence: pneumatic. Status: source_reported.

- No experimental microscale validation or deployed acoustic/MEMS/energy-storage application is established.

### contact_and_strain_constraints
The numerical model constrains hinge angles within ±0.985π, edge/diagonal strain within ±0.30, suppresses face bending, and uses hinge plus stretch energy.
Evidence: model_overview, equation_1, equation_18, equation_19. Status: source_reported.

- Adjacent-face angle constraints do not establish global non-adjacent self-contact protection.
- ±0.30 is a numerical convergence/search bound, not a measured maximum elastic strain or rupture limit for PLA, Mylar or elastomer.
- Numerical target angles at 0 or π should be distinguished from exactly achieved values under tighter contact constraints and a finite penalty.

### solver_and_state_matching
The source uses MATLAB fmincon: Active-set for pair landscapes/compression and SQP for other searches (three folding optimization steps). It groups states by sorted internal/external hinge-angle arrays with centroid-linkage Euclidean hierarchical clustering.
Evidence: solver, clustering. Status: source_reported.

- The source algorithm/clustering should be represented as reported; sorted angle multisets need not uniquely determine spatial shape in every possible case.
- Solver tolerances, randomization/initialization details and complete source code are not included; article says data and code are available from corresponding author upon reasonable request.

## Conflicts and implementation cautions

### C1: Truncated-tetrahedron release destinations
Body text: States i–v relax to states vii and xi.
Figure pixels: Fig. 4b arrows show i→xiii, ii→xiii, iii→xiii, iv→vii, v→xiii.
Handling: Retain both with modality-specific provenance. No single resolved xi/xiii label without further authoritative evidence. A task may score recognition of conflict rather than one destination.
Evidence: tetrahedron_reachability, figure_4_pixels.

### C2: Compression instability enumeration
Main caption: Fig. 2 says one instability during compression and two during return, in experiment and simulation.
Si caption: SI Fig. 1 says two during compression and three during return for κ=10^-4 and 10^-3.
Handling: Store separate count assertions. A small additional numerical loop is also discussed in main caption, but do not assert that it fully resolves the discrepancy or overwrite either count.
Evidence: compression_caption, si_figure_1.

### C3: Internal-only actuation combination formula
Main printed formula: eta_int = 2^(2 n_int)
Si plot label: 2^n_int
Check: Binary selection of n_int hinges gives 2^n_int. With cuboctahedron n_int=24, full 2^72 to internal-only 2^24 gives 2^48 ≈ 2.8×10^14 reduction, consistent with stated 14 orders; 2^48 remaining would give only ≈7.2 orders reduction.
Handling: Preserve printed formula and mark likely typographical inconsistency; corrected combinatorics is a separately labeled derivation.
Evidence: combinations_internal, combinations_full, si_figure_4.

### C4: Compression prototype figure cross-reference
Body reference: Compression paragraph names cuboctahedron but cites Fig. 1b.
Actual panel: Figure 1 caption/pixels identify b as truncated cube and c as cuboctahedron.
Handling: Use named cuboctahedron confirmed by Fig. 2/Methods; mark Fig. 1b cross-reference as inconsistent.
Evidence: compression_fabrication, cardboard, figure_1_pixels.

### C5: Solver paragraph figure cross-references
Body reference: Methods links energy landscapes to Fig. 2 and compression simulation to Fig. 3.
Actual figures: Fig. 2 is compression; Fig. 3 is hinge-pair energy landscapes/state diagrams.
Handling: Keep method choices tied to described experiment types, not mistaken figure numbers.
Evidence: solver, compression_caption, pair_caption.

### C6: Polyhedron example in graph typing
Body example: The main reducing-search-space paragraph calls a prism with triangle-square and square-square edge types a hexagonal prism.
Other evidence: Methods and SI Fig. 9 explicitly demonstrate triangular prism with those edge types.
Handling: Do not copy the hexagonal example as verified topology. Triangular-prism example is consistently supported by Methods and SI.
Evidence: combinations_internal, si_figure_9.

### C7: Printed numerical equations and tolerance arithmetic
- Eq. 8 prints length change as the norm of endpoint displacement difference, rather than an explicit deformed-edge norm minus initial length; this should not be silently treated as a verified implementable geometric identity.
- Eq. 29 prints a sum over per-step energy/displacement slopes while describing a numerical gradient along the loading path; implementation details need clarification.
- Clustering text gives maximum cluster distance 1.5 rad but then per-angle error 1/sqrt(n_tot) rad, which is not an exact restatement of a 1.5-rad Euclidean cutoff.
Handling: Treat as source-as-printed implementation caveats. This audit does not repair, execute or validate the numerical model.
Evidence: equation_8, equation_29, clustering.

## SI Figure 7 labels

- Panel a: triangular prism, 2 additional states
- Panel b: triangular prism, 4 additional states
- Panel c: cube, 0 additional states
- Panel d: hexagonal prism, 14 additional states
- Panel e: truncated tetrahedron, 131 additional states
- Panel f: octagonal prism, 0 additional states
- Panel g: dodecagonal prism, 0 additional states
- Panel h: truncated cube, 0 additional states
- Panel i: truncated octahedron, 6 additional states
- Panel j: rhombicuboctahedron, 5 additional states
- Panel k: truncated cuboctahedron, 56 additional states
- Panel l: truncated cuboctahedron, 16 additional states

These counts belong to the depicted periodic material designs. In the main Figure 5, cuboctahedron, rhombicuboctahedron and truncated-cuboctahedron designs carry 3, 3 and 16 additional-state labels, respectively.

## Use in task construction

- Separate reported source facts, pixel-read facts, arithmetic derivations, source conflicts and benchmark-designer assumptions in schema.
- Use source-backed qualitative event outcomes (retained, relaxes, stretch-limited, non-adjacent crossing, outside periodic model) rather than invented success thresholds or physical procedures.
- Do not fill missing laboratory settings with defaults or borrow cardboard dimensions into PLA/Mylar geometry.
- Score stiffness/maximum stretch/non-adjacent contact as different mechanisms rather than treating every simulation–experiment mismatch as solver failure.
- For C1 and C2, accept explicitly provenance-qualified conflicting answers or make conflict detection the target; do not encode one unqualified ground truth.
- Keep numerical plans descriptive until source code, dimensions, material calibration and physical controls have been independently supplied and validated.

## Evidence lookup

audit.json includes exact current-source SHA-256 hashes, stable publisher section links, deterministic DOM locators, normalized evidence-text hashes, SI page/panel locators and the prior-record comparison. Figure counts and arrows are marked as visual readings. The stored audit deliberately omits publisher figure files and long excerpts.
