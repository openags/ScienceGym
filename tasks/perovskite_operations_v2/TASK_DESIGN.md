# Perovskite whole-paper mobile-robot task design

Ding et al., *Dopant-additive synergism enhances perovskite solar modules*, Nature (2024). DOI: [10.1038/s41586-024-07228-z](https://doi.org/10.1038/s41586-024-07228-z).

## 1. What this package is

This is a whole-paper experimental task design for long-horizon mobile manipulation. It covers the paper's reported preparation, fabrication, manipulation and measurement families, including independent controls, formulation panels, assay substrates, destructive characterization and long-duration histories. It is not an executable chemistry protocol, physical reproduction, scene/asset package, installed framework or new process-optimization campaign. Hooke provides scenes separately. Every hazard-bearing activity is an inert closed-service proxy, and physical simulation is paused.

The package contains 40 task templates, 96 named service-stage definitions and 752 expanded action specifications. These counts describe specification organization, not independent experiments, source replicates, scientific validation or paper quota credit. Conditional variants and event loops must be expanded according to their recorded contracts.

Whole-paper completeness means that each of the 22 source inventory families, five main figures, 33 supplementary figures, five tables and two notes has an explicit task or analytical disposition. Missing source protocols and contradictions remain explicit. The article does not supply one chronological end-to-end experiment or a complete sample ledger.

## 2. File and visibility contract

- agent_visible.json supplies only the selected actor goal, initial state, known source issues, condition references and deliverables
- material_cards.json supplies reported condition facts and explicit missing/contradictory fields. It is metadata for inert services, not permission for real processing
- branches.json and operations.json contain evaluator-only reference routes, source links, state constraints, variant selection and expanded manipulation actions
- evaluator_reference.json defines acceptance, valid recovery and rejection cases; it must not be included in the actor prompt
- lineage_contract.json, mock_contract.json, control_packages.json and station_contracts.json define identity, observations, independent groups and scene-interface requirements
- coverage_matrix.json, provenance.json, unknown_parameters.json and granularity_gaps.json distinguish sourced facts from authored connections and unknowns
- Release receipts and static-check reports are maintained outside this task-only export. They do not establish simulator or robot-rollout validity

The actor receives an outcome, raw initial objects and applicable condition cards. It does not receive the complete route, expected scientific results, hidden failure seed, success flags or evaluator acceptance chain. Merely withholding headings while placing the whole route inside the goal would violate this boundary.

## 3. Actor task and whole-paper allocation

A representative actor goal is: “Prepare independently traceable control and target module proxies, obtain condition-linked electrical and stability records, preserve all irreversible histories and missing observations, and finish with archived objects and reset stations.” The starting inventory contains unused FTO or assay-specific substrate proxies, sealed symbolic material components, empty carriers, masks, reference objects and empty stopped stations. There are no finished films, crystals, cells, modules or future observations. Externally synthesized named additives are explicitly traceable incoming lots; their cited chemical syntheses are not recreated.

Issue one selected episode at a time, or a campaign consisting of explicitly selected independent episodes. Source group identity, assay substrate and comparison condition are mandatory. The default one symbolic independent specimen per condition is an authored minimum for task coverage, not an adequate scientific sample size or a claim about the paper. More independent task replicates may be issued, but each consumes inventory and gets a new lineage. Three consecutive forward/reverse certification tests are repeats on a module, not three independent modules.

When a source assay does not repeat all preparation details, reuse of a compatible fabrication prefix is an authored connection. Named source exceptions override it: the S24 stack, quartz/mesoporous-FTO/sapphire optical substrates, the 120 s initial HIM drying route, wet-film microscopy and the 1.0 M PbI2 basis for the growth series remain distinct.

The CRYSTAL_GROWTH coating service is explicitly unresolved-source: GROWTH.growth_spin_program remains unknown and overrides the shared device COATING.PPS_spin values. Reusing the service interface does not supply missing growth-film spin settings.

## 4. Manipulation granularity and closed services

A normal stage expands into eight observable actions: carry the released carrier; load and seat; verify object/state/condition; guard; start an inert work order; observe completion and acquire the required events; wait for safe release; retrieve and record the handoff. Every changed station requires transport. Every input token is selected and identity-bound. A receipt is earned through these actions; writing a new label cannot create a fabricated sample.

Photovoltaic measurement is intentionally different: mounting/calibration retains the object in the station, forward/reverse/MPP operations acquire data while it remains clamped and connected, and a separate stop/support/disconnect/unload operation releases it. No generic unload is inserted between retained scans.

All processing inside chemical, heated, vacuum, gas, laser, beam, sputter, evaporation, magnetic, electrical and UV services is nonphysical. The robot handles inert exteriors, carriers, masks, covers and reversible connectors. Submillimetre crystal picking and destructive cross-section preparation are closed-service transitions, not claims that this task validates those real dexterous skills. Services expose public readiness, occupied/empty, progress, observation-validity and trusted safe-release states. Elapsed time alone never proves a safe state.

Point and time series require explicit loop events. A PV bias point contains a command, settling state, acquisition and saved row. NMR temperature steps contain equilibration and nucleus-specific acquisitions. Depth profiles alternate sputter and acquisition events. Three rinse cycles remain three recorded cycles. A whole trace cannot be supplied as one unexplained final row.

## 5. Complete module route and independent alternatives

The first complete route is in FIRST_ROUTE_MODULE.md. The authoritative structured spin-module route begins with raw module FTO and P1 patterning, followed by three-solvent cleaning, Ti stock/bath/rinse/anneal, separate Sn stock/modification/rinse/anneal, PMMA:PCBM preparation/coating/anneal, formulation-specific precursor preparation/stirring, wet-film coating, device rapid drying and two anneals. PEAI and hole-transport layers precede P2; MoO3, ITO and Au are separate ordered deposition handoffs; P3 completes the series-connected module. Electrical mounting, reference checking, forward/reverse scans and separate MPP tracking precede safe release. Packaging records edge cleaning, indium contacts, separate cover-glass placement, edge sealing and guarded curing. Operational ageing uses independently allocated encapsulated module pairs for room temperature and 65 C. [CELL: Small-area device fabrication; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf); [SPIN_MODULE: Spin-coated eight-subcell module fabrication; PDF 8, 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [PACKAGE: Module encapsulation; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [PV: Device characterization and masking; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [AGE: Film thermal stability and operational module stability; PDF 6, 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [F1: Main Figure 1; PDF 2](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S33: Supplementary Figure S33; PDF 43](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

The blade branch uses the independently reported lower-concentration precursor, blade application of PMMA:PCBM, perovskite, PEAI and HTL, gas-pump perovskite drying and N2-knife assistance for PEAI/HTL. It retains the same explicit module interconnection/deposition dependencies. Knife-service entries are a segmented interface for the reported coupled coating/drying operation; no arbitrary real waiting interval is invented. The small-cell branch uses source-supplied patterned FTO and omits module P1/P2/P3 fabrication. [BLADE_MODULE: Blade-coated module fabrication; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S7: Supplementary Figure S7; PDF 14](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [CELL: Small-area device fabrication; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf)

## 6. Full task catalogue

The routes below are private evaluator references. Each starts with inventory inspection, fresh lineage allocation and the listed raw-input preparation; each ends with archive and cleanup. Arrows describe dependencies, not recovered author chronology. Where variants exist, select the explicit variant instead of executing the illustrative base list. All stage names expand into their manipulation actions in operations.json.

### 6.1. Receive externally prepared additive families (ADDITIVE_INTAKE)

Source families: B01, B07.

Condition package: {"families": ["[Bcmim]Cl", "[Bcmim]TFSI", "[Bcmim]BF4", "[Bcmim]I", "[Bcmim]PF6", "[Bcmim]SCN", "[C1SCNmim]Cl"]}.

Reference route: Register externally prepared additive lots.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary: The cited syntheses are explicit preparation dependencies. The task exercises incoming identity/provenance handling; it does not invent or credit their unavailable chemical synthesis.

Relevant unresolved issues: U01.

Evidence: [MATERIALS: Methods / Materials; cited syntheses are external dependencies; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### 6.2. Compare three model-crystal parent routes (CRYSTAL_MODELS)

Source families: B01.

Condition package: {"reaction_groups": ["[Bcmim]Cl+PbI2", "[Bcmim]Cl+PbI2+MAI", "[Bcmim]Cl+PbI2+FAI"]}.

Reference route: Allocate sealed material portions → Prepare model-adduct solution proxy → Heat model-adduct mixture proxy → Grow model crystal proxy → Select and mount crystal proxy → Acquire single-crystal diffraction.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary: MAI and FAI parent routes remain independent even where reported crystal product is the same.

Relevant unresolved issues: Q02, Q07, U16.

Evidence: [CRYSTAL: Model-adduct preparation and single-crystal characterization; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S28: Supplementary Figure S28; PDF 37](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [T5: Supplementary Table S5; PDF 49](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.3. Prepare compact transport-layer substrates (ETL_PREPARATION)

Source families: B02.

Condition package: {"substrate": "FTO"}.

Reference route: Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary: Ti preparation, rinsing and annealing precede separately identified Sn modification; mock unresolved-card treatment required.

Relevant unresolved issues: Q01, U03.

Evidence: [ETL: Compact TiO2 and SnO2-modified TiO2 preparation; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### 6.4. Fabricate and test control and target cells (CELL_CONTROL_TARGET)

Source families: B03, B07.

Condition package: {"groups": ["control", "target"], "architecture": "small-area n-i-p"}.

Reference route: Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Prepare PEAI solution proxy → Spin PEAI layer proxy → Prepare doped Spiro-OMeTAD solution proxy → Spin hole-transport layer proxy → Deposit MoO3 layer proxy → Deposit ITO layer proxy → Deposit Au layer proxy → Mount and calibrate photovoltaic station → Acquire forward electrical scan → Acquire reverse electrical scan → Stop and unload photovoltaic fixture → Acquire spectral response.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary: Small-area route has no module P1/P2/P3 steps.

Relevant unresolved issues: U03, Q01, U06, U04, Q03, U10.

Evidence: [CELL: Small-area device fabrication; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf); [PV: Device characterization and masking; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S4: Supplementary Figure S4; PDF 11](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.5. Compare reported additive cation identities (CATION_SCREEN)

Source families: B03, B07.

Condition package: {"MACl_mol_percent": 20, "ionic_liquid_mol_percent": 0.6, "ionic_liquids": ["none (control)", "[Im]Cl", "[Dmim]Cl", "[C1SCNmim]Cl", "[Bmim]Cl", "[Cmmim]Cl", "[Bcmim]Cl"]}.

Reference route: Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Prepare PEAI solution proxy → Spin PEAI layer proxy → Prepare doped Spiro-OMeTAD solution proxy → Spin hole-transport layer proxy → Deposit MoO3 layer proxy → Deposit ITO layer proxy → Deposit Au layer proxy → Mount and calibrate photovoltaic station → Acquire forward electrical scan → Acquire reverse electrical scan → Stop and unload photovoltaic fixture.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary: Reported panel replay, not new optimization. Distinct stocks must not be chemically transformed into other additives by renaming.

Relevant unresolved issues: U03, Q01, U06, U04, Q03, U10.

Evidence: [CELL: Small-area device fabrication; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf); [PV: Device characterization and masking; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S1: Supplementary Figure S1; PDF 8](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.6. Compare reported additive counterions (ANION_SCREEN)

Source families: B03, B07.

Condition package: {"MACl_mol_percent": 20, "ionic_liquid_mol_percent": 0.6, "ionic_liquids": ["none (control)", "[Bcmim]BF4", "[Bcmim]PF6", "[Bcmim]I", "[Bcmim]SCN"]}.

Reference route: Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Prepare PEAI solution proxy → Spin PEAI layer proxy → Prepare doped Spiro-OMeTAD solution proxy → Spin hole-transport layer proxy → Deposit MoO3 layer proxy → Deposit ITO layer proxy → Deposit Au layer proxy → Mount and calibrate photovoltaic station → Acquire forward electrical scan → Acquire reverse electrical scan → Stop and unload photovoltaic fixture.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary: Cross-panel Cl comparison may use independently fabricated [Bcmim]Cl condition; S2 is not an arbitrary search domain.

Relevant unresolved issues: U03, Q01, U06, U04, Q03, U10.

Evidence: [CELL: Small-area device fabrication; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf); [PV: Device characterization and masking; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S2: Supplementary Figure S2; PDF 9](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.7. Compare the reported MACl concentration panel (MACL_SCREEN)

Source families: B03, B07.

Condition package: {"MACl_mol_percent": [0, 10, 20, 30, 40, 50, 60], "Bcmim": "absent"}.

Reference route: Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Prepare PEAI solution proxy → Spin PEAI layer proxy → Prepare doped Spiro-OMeTAD solution proxy → Spin hole-transport layer proxy → Deposit MoO3 layer proxy → Deposit ITO layer proxy → Deposit Au layer proxy → Mount and calibrate photovoltaic station → Acquire forward electrical scan → Acquire reverse electrical scan → Stop and unload photovoltaic fixture.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary: The source grid is fixed; no new adaptive optimization.

Relevant unresolved issues: U03, Q01, U06, U04, Q03, U10.

Evidence: [CELL: Small-area device fabrication; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf); [PV: Device characterization and masking; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S3: Supplementary Figure S3; PDF 10](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.8. Compare the reported additive concentration panel (BCMIM_SCREEN)

Source families: B03, B07.

Condition package: {"MACl_mol_percent": 20, "Bcmim_mol_percent": [0, 0.2, 0.6, 1.0, 1.4]}.

Reference route: Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Prepare PEAI solution proxy → Spin PEAI layer proxy → Prepare doped Spiro-OMeTAD solution proxy → Spin hole-transport layer proxy → Deposit MoO3 layer proxy → Deposit ITO layer proxy → Deposit Au layer proxy → Mount and calibrate photovoltaic station → Acquire forward electrical scan → Acquire reverse electrical scan → Stop and unload photovoltaic fixture → Acquire spectral response.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary: EQE integral is derived with an explicitly specified spectrum or remains unknown.

Relevant unresolved issues: U03, Q01, U06, U04, Q03, U10.

Evidence: [CELL: Small-area device fabrication; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf); [PV: Device characterization and masking; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S4: Supplementary Figure S4; PDF 11](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.9. Fabricate and test spin-coated modules (SPIN_MODULES)

Source families: B02, B04, B08.

Condition package: {"groups": ["control", "target"], "series_subcells": 8}.

Reference route: Allocate sealed material portions → Pattern P1 module lines → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Prepare PEAI solution proxy → Spin PEAI layer proxy → Prepare doped Spiro-OMeTAD solution proxy → Spin hole-transport layer proxy → Pattern P2 module lines → Deposit MoO3 layer proxy → Deposit ITO layer proxy → Deposit Au layer proxy → Pattern P3 module lines → Mount and calibrate photovoltaic station → Acquire forward electrical scan → Acquire reverse electrical scan → Stop and unload photovoltaic fixture.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary: P1 precedes stack, P2 precedes electrode deposition, P3 follows Au. No eight cells are inferred from a single photograph.

Relevant unresolved issues: U03, Q01, U06, U04, Q03, U10.

Evidence: [SPIN_MODULE: Spin-coated eight-subcell module fabrication; PDF 8, 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [F1: Main Figure 1; PDF 2](https://www.nature.com/articles/s41586-024-07228-z.pdf); [PV: Device characterization and masking; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### 6.10. Fabricate and test blade-coated modules (BLADE_MODULES)

Source families: B02, B05, B08.

Condition package: {"groups": ["control", "target"]}.

Reference route: Allocate sealed material portions → Pattern P1 module lines → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Blade PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare blade precursor proxy → Blade perovskite wet-film proxy → Gas-pump drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Prepare PEAI solution proxy → Blade PEAI layer proxy → Dry blade PEAI with N2-knife proxy → Prepare doped Spiro-OMeTAD solution proxy → Blade hole-transport layer proxy → Dry blade HTL with N2-knife proxy → Pattern P2 module lines → Deposit MoO3 layer proxy → Deposit ITO layer proxy → Deposit Au layer proxy → Pattern P3 module lines → Mount and calibrate photovoltaic station → Acquire forward electrical scan → Acquire reverse electrical scan → Stop and unload photovoltaic fixture.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary: Blade concentrations differ from spin. N2-knife drying is coupled with layer coating; consecutive service entries are interface segmentation, not claimed real timing.

Relevant unresolved issues: U03, Q01, U04, U06, Q03, U10.

Evidence: [BLADE_MODULE: Blade-coated module fabrication; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S7: Supplementary Figure S7; PDF 14](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [PV: Device characterization and masking; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### 6.11. Fabricate and encapsulate matched modules (ENCAPSULATION)

Source families: B04, B06.

Condition package: {"groups": ["control", "target"]}.

Reference route: Allocate sealed material portions → Pattern P1 module lines → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Prepare PEAI solution proxy → Spin PEAI layer proxy → Prepare doped Spiro-OMeTAD solution proxy → Spin hole-transport layer proxy → Pattern P2 module lines → Deposit MoO3 layer proxy → Deposit ITO layer proxy → Deposit Au layer proxy → Pattern P3 module lines → Clean module edge proxy → Lay module edge contact proxies → Place cover-glass proxy → Apply edge-seal proxy → Cure package proxy.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary: No finished modules initially; dedicated standalone packaging stress tests may start from traced route output only and must say so.

Relevant unresolved issues: U03, Q01, U06, U04.

Evidence: [SPIN_MODULE: Spin-coated eight-subcell module fabrication; PDF 8, 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [PACKAGE: Module encapsulation; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### 6.12. Track a mock external performance handoff (CERTIFICATION_HANDOFF)

Source families: B04, B08.

Condition package: {"group": "target", "certificate_scan_pairs": 3, "stabilized_output_seconds": 300}.

Reference route: Allocate sealed material portions → Pattern P1 module lines → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Prepare PEAI solution proxy → Spin PEAI layer proxy → Prepare doped Spiro-OMeTAD solution proxy → Spin hole-transport layer proxy → Pattern P2 module lines → Deposit MoO3 layer proxy → Deposit ITO layer proxy → Deposit Au layer proxy → Pattern P3 module lines → Mount and calibrate photovoltaic station → Acquire forward electrical scan → Acquire reverse electrical scan → Stop and unload photovoltaic fixture → Dispatch mock external-test carrier → Receive mock external-test report.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary: No real external communication or fresh certification. Published report is evidence; mock receipt must be marked mock.

Relevant unresolved issues: U12, U03, Q01, U06, U04, Q03, U10.

Evidence: [SPIN_MODULE: Spin-coated eight-subcell module fabrication; PDF 8, 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S5: Supplementary Figure S5; PDF 12](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S6: Supplementary Figure S6; PDF 13](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.13. Measure precursor variable-temperature stability (NMR_TEMPERATURE)

Source families: B09.

Condition package: {"groups": ["control", "target"], "temperature_C": [25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]}.

Reference route: Allocate sealed material portions → Prepare deuterated operando precursor proxy → Dissolve NMR solution proxy → Load NMR tube proxy → Acquire variable-temperature NMR series.

Control/repetition: Independent control and target tubes. Within each tube, register ordered temperature steps and individual acquisitions; cannot reset degradation between temperatures.

Relevant unresolved issues: Q08.

Evidence: [NMR: NMR spectroscopy, model interactions, HBA, operando VT/time-dependent and EXSY measurements; PDF 10, 11](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S10: Supplementary Figure S10; PDF 17](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.14. Measure precursor time-dependent stability (NMR_TIMECOURSE)

Source families: B09.

Condition package: {"groups": ["control", "target"], "temperature_C": [25, 60], "duration_h": 24, "reported_timepoints": 96}.

Reference route: Allocate sealed material portions → Prepare deuterated operando precursor proxy → Dissolve NMR solution proxy → Load NMR tube proxy → Acquire time-dependent NMR series.

Control/repetition: Four separate group-temperature tubes by authored allocation. Acquire 1H time grid plus linked baseline/end 207Pb records. Preserve all missing intervals.

Relevant unresolved issues: Q05, Q08, Q10, U15.

Evidence: [NMR: NMR spectroscopy, model interactions, HBA, operando VT/time-dependent and EXSY measurements; PDF 10, 11](https://www.nature.com/articles/s41586-024-07228-z.pdf); [F2: Main Figure 2; PDF 3](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S11: Supplementary Figure S11; PDF 18](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S12: Supplementary Figure S12; PDF 19](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.15. Compare fresh and stored precursor-derived films (PPS_STORAGE_FILMS)

Source families: B09, B13.

Condition package: {"age_days": [0, 10], "Bcmim_mol_percent": [0, 0.2, 0.6, 1.0, 1.4], "MACl_mol_percent": 20}.

Reference route: Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Age precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → Record film appearance → First perovskite anneal proxy → Second perovskite anneal proxy → Record film appearance.

Control/repetition: For each formulation allocate fresh/aged aliquots from a registered parent batch. Fresh condition bypasses STORE_PPS rather than performing ten-day storage. Each film is photographed unannealed then annealed.

Conditional routes:

- PPS_STORAGE_FILMS__0D: {"age_days": 0}; Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → Record film appearance → First perovskite anneal proxy → Second perovskite anneal proxy → Record film appearance. Repeat separately for each of five additive labels; fresh and aged aliquots retain their parent batch relation.
- PPS_STORAGE_FILMS__10D: {"age_days": 10}; Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Age precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → Record film appearance → First perovskite anneal proxy → Second perovskite anneal proxy → Record film appearance. Repeat separately for each of five additive labels; fresh and aged aliquots retain their parent batch relation.

Source/authored boundary: Zero-day branch explicitly omits storage. Source substrate/handling allocation not fully specified; device-underlayer choice is authored. A shared preparation prefix is an authored connection where this assay does not report a complete standalone method; relevant source-specific cards override it.

Relevant unresolved issues: U11, U03, Q01, U06, U04, U18.

Evidence: [S13: Supplementary Figure S13; PDF 20](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [CELL: Small-area device fabrication; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### 6.16. Compare model ionic-liquid interaction series (NMR_INTERACTIONS)

Source families: B10.

Condition package: {"MA_salt": ["MACl"], "ionic_liquids": ["[Bcmim]Cl", "[Cmmim]Cl", "[Dmim]Cl", "[Bmim]Cl"], "ratio_percent": [0, 1, 2, 3, 4, 5, 10, 20, 40, 60, 80, 100]}.

Reference route: Allocate sealed material portions → Prepare model-solution comparison proxy → Load NMR tube proxy → Acquire one-dimensional model NMR.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary: Separate labelled tube per ratio is authored to avoid unreported sequential-addition history. Ratio 0 can be a shared matched baseline within a stock batch; never counted as extra independent replicates.

Relevant unresolved issues: Q11, U13.

Evidence: [NMR: NMR spectroscopy, model interactions, HBA, operando VT/time-dependent and EXSY measurements; PDF 10, 11](https://www.nature.com/articles/s41586-024-07228-z.pdf); [F3: Main Figure 3; PDF 3](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S14: Supplementary Figure S14; PDF 21](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.17. Compare iodide substitution controls (NMR_MAI_CONTROLS)

Source families: B10, B11.

Condition package: {"MA_salt": "MAI", "ionic_liquids": ["[Dmim]Cl", "[Bcmim]Cl"], "ratio_domain": "0–100% reported; exact SI S14 grid retained as unresolved unless explicitly issued"}.

Reference route: Allocate sealed material portions → Prepare model-solution comparison proxy → Load NMR tube proxy → Acquire one-dimensional model NMR.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Relevant unresolved issues: U06, Q11, U13.

Evidence: [NMR: NMR spectroscopy, model interactions, HBA, operando VT/time-dependent and EXSY measurements; PDF 10, 11](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S14: Supplementary Figure S14; PDF 21](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [T2: Supplementary Table S2; PDF 46](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.18. Measure additive self-concentration shifts (NMR_SELF_DILUTION)

Source families: B10.

Condition package: {"solute": "[Bcmim]Cl", "concentration_M": [0.0015, 0.003, 0.0045, 0.006, 0.0075]}.

Reference route: Allocate sealed material portions → Prepare model-solution comparison proxy → Load NMR tube proxy → Acquire one-dimensional model NMR.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary: No MACl added in this self-concentration control; NMR_MODEL self-dilution card overrides interaction-mixture fields.

Relevant unresolved issues: Q11, U13.

Evidence: [NMR: NMR spectroscopy, model interactions, HBA, operando VT/time-dependent and EXSY measurements; PDF 10, 11](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### 6.19. Measure alternative-explanation controls (NMR_ALTERNATIVES)

Source families: B11.

Condition package: {"groups": ["MACl+LiCl", "MACl+HCl", "MACl+TFA", "MACl+LiCl+[Bcmim]Cl", "MACl+HCl+[Bcmim]Cl", "MACl+[Bcmim]BF4", "MAI+[Bcmim]Cl", "MACl+TFA+[Bcmim]Cl (prose-only preparation gap)"]}.

Reference route: Allocate sealed material portions → Prepare model-solution comparison proxy → Load NMR tube proxy → Acquire one-dimensional model NMR.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary: Seven table rows plus the TFA/Bcmim pair mentioned by Note1 are represented. Last route is protocol-underdetermined, not falsely inferred complete.

Relevant unresolved issues: Q11, U13.

Evidence: [N1: Supplementary Note 1: alternative NMR explanations and control preparations; PDF 6](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [T2: Supplementary Table S2; PDF 46](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S14: Supplementary Figure S14; PDF 21](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.20. Measure relative hydrogen-bond accepting comparison (HBA_COMPARISON)

Source families: B10.

Condition package: {"groups": ["[Bcmim]Cl+PPA", "[Bcmim]TFSI+PPA", "PPA external reference"], "nucleus": "31P"}.

Reference route: Allocate sealed material portions → Prepare hydrogen-bond comparison proxy → Acquire one-dimensional model NMR.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary: PPA shifts support a relative comparison only.

Evidence: [NMR: NMR spectroscopy, model interactions, HBA, operando VT/time-dependent and EXSY measurements; PDF 10, 11](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S15: Supplementary Figure S15; PDF 22](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.21. Compare model and precursor proton exchange (EXSY_COMPARISON)

Source families: B10, B11.

Condition package: {"model_additives_at_1_mol_percent": ["[Bcmim]Cl", "[Bcmim]BF4", "[Bcmim]PF6", "[Bcmim]I", "[Bcmim]SCN"], "additional_group": "target PPS"}.

Reference route: Allocate sealed material portions → Prepare model-solution comparison proxy → Load NMR tube proxy → Acquire exchange NMR.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Conditional routes:

- EXSY_COMPARISON__MODEL: {"solution_family": "MACl model"}; Allocate sealed material portions → Prepare model-solution comparison proxy → Load NMR tube proxy → Acquire exchange NMR. Repeat for the five reported 1 mol% additive identities.
- EXSY_COMPARISON__PPS: {"solution_family": "target PPS"}; Allocate sealed material portions → Prepare deuterated operando precursor proxy → Dissolve NMR solution proxy → Load NMR tube proxy → Acquire exchange NMR. One independent target aliquot per authored replicate; Q08 remains unresolved.

Source/authored boundary: Target PPS uses operando precursor preparation instead of MODEL_MIX; its tube type is selected from the resolved assay card, not guessed from EXSY figure.

Relevant unresolved issues: Q08, Q11, U13.

Evidence: [NMR: NMR spectroscopy, model interactions, HBA, operando VT/time-dependent and EXSY measurements; PDF 10, 11](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S16: Supplementary Figure S16; PDF 23](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S17: Supplementary Figure S17; PDF 24](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.22. Acquire supporting molecular assignment spectra (NMR_ASSIGNMENTS)

Source families: B10, B22.

Condition package: {"sequences": ["1H", "13C", "COSY", "HSQC", "HMBC"], "sample_mapping": "not fully reported"}.

Reference route: Allocate sealed material portions → Prepare model-solution comparison proxy → Load NMR tube proxy → Acquire one-dimensional model NMR → Acquire assignment-support two-dimensional NMR.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary: The source reports these acquisition families but does not give all spectra-to-mixture mappings. This is bounded assay coverage, not a fabricated assignment campaign.

Relevant unresolved issues: U13, Q11.

Evidence: [NMR: NMR spectroscopy, model interactions, HBA, operando VT/time-dependent and EXSY measurements; PDF 10, 11](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S9: Supplementary Figure S9; PDF 16](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.23. Compare lead-environment model spectra (LEAD_INTERACTIONS)

Source families: B10, B11.

Condition package: {"Pb207_groups": ["control PPS", "target PPS", "PbI2", "NaPbI3", "[Bcmim]PbI3", "equimolar PbI2+[Bcmim]PbI3", "PbI2+0.6 mol% [Bcmim]BF4", "PbI2+50 mol% [Bcmim]BF4"], "B11_groups": ["[Bcmim]BF4", "PbI2+0.6 mol% [Bcmim]BF4", "PbI2+50 mol% [Bcmim]BF4"]}.

Reference route: Allocate sealed material portions → Prepare model-solution comparison proxy → Load NMR tube proxy → Acquire one-dimensional model NMR.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Conditional routes:

- LEAD_INTERACTIONS__PPS: {"solution_family": "PPS", "nucleus": "207Pb"}; Allocate sealed material portions → Prepare deuterated operando precursor proxy → Dissolve NMR solution proxy → Load NMR tube proxy → Acquire one-dimensional model NMR. Repeat control and target; proper deuterated precursor lineage.
- LEAD_INTERACTIONS__MODEL_PB: {"solution_family": "model", "nucleus": "207Pb"}; Allocate sealed material portions → Prepare model-solution comparison proxy → Load NMR tube proxy → Acquire one-dimensional model NMR. Repeat PbI2, NaPbI3, BcmimPbI3, equimolar PbI2/BcmimPbI3 and two PbI2/BcmimBF4 conditions.
- LEAD_INTERACTIONS__MODEL_B: {"solution_family": "model", "nucleus": "11B"}; Allocate sealed material portions → Prepare model-solution comparison proxy → Load NMR tube proxy → Acquire one-dimensional model NMR. Repeat BcmimBF4 alone and both PbI2/BcmimBF4 conditions.

Source/authored boundary: Nucleus-specific records and parent solution routes are mandatory. 50 mol% equimolar wording retained, not normalized silently.

Relevant unresolved issues: U13, Q08, Q11.

Evidence: [NMR: NMR spectroscopy, model interactions, HBA, operando VT/time-dependent and EXSY measurements; PDF 10, 11](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S27: Supplementary Figure S27; PDF 36](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.24. Compare six ionic-liquid acidity labels (ACIDITY_COMPARISON)

Source families: B12.

Condition package: {"ionic_liquids": ["[Dmim]Cl", "[Bmim]Cl", "[Cmmim]Cl", "[Bcmim]Cl", "[Bcmim]BF4", "[Bcmim]TFSI"]}.

Reference route: Allocate sealed material portions → Prepare ionic-liquid acidity proxy → Acquire pH comparison.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Relevant unresolved issues: Q09.

Evidence: [PH: pH comparison; PDF 11](https://www.nature.com/articles/s41586-024-07228-z.pdf); [T3: Supplementary Table S3; PDF 47](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.25. Compare additive-dependent film structure (FILM_STRUCTURE)

Source families: B13.

Condition package: {"Bcmim_mol_percent": [0, 0.2, 0.6, 1.0, 1.4], "MACl_mol_percent": 20}.

Reference route: Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Acquire film diffraction → Acquire rocking curves → Acquire grazing-incidence scattering → Acquire top-view morphology.

Control/repetition: Allocate assay-specific sister films by authored default; apply complete preparation to each. Four assays are parallel branches, not proof of source specimen reuse.

Conditional routes:

- FILM_STRUCTURE__XRD: {"assay": "XRD"}; Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Acquire film diffraction. Repeat for all five Bcmim levels with separate sister films by default.
- FILM_STRUCTURE__ROCK: {"assay": "ROCK"}; Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Acquire rocking curves. Repeat for all five Bcmim levels with separate sister films by default.
- FILM_STRUCTURE__GIWAXS: {"assay": "GIWAXS"}; Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Acquire grazing-incidence scattering. Repeat for all five Bcmim levels with separate sister films by default.
- FILM_STRUCTURE__SEM_TOP: {"assay": "SEM_TOP"}; Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Acquire top-view morphology. Repeat for all five Bcmim levels with separate sister films by default.

Source/authored boundary:  A shared preparation prefix is an authored connection where this assay does not report a complete standalone method; relevant source-specific cards override it.

Relevant unresolved issues: U03, Q01, U06, U04, U18.

Evidence: [FILM_MEASURE: Film characterization: XRD, GIWAXS, microscopy, DLS, SEM, absorption, XPS, PL, TRPL, PLQY; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S18: Supplementary Figure S18; PDF 25, 26](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.26. Compare counterion-dependent film diffraction (FILM_ANIONS)

Source families: B13.

Condition package: {"ionic_liquids": ["none (control)", "[Bcmim]PF6", "[Bcmim]BF4", "[Bcmim]I", "[Bcmim]SCN"]}.

Reference route: Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Acquire film diffraction.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary:  A shared preparation prefix is an authored connection where this assay does not report a complete standalone method; relevant source-specific cards override it.

Relevant unresolved issues: U03, Q01, U06, U04, U18.

Evidence: [S19: Supplementary Figure S19; PDF 27](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [FILM_MEASURE: Film characterization: XRD, GIWAXS, microscopy, DLS, SEM, absorption, XPS, PL, TRPL, PLQY; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### 6.27. Compare dopant-dependent morphology and diffraction (FILM_MACL)

Source families: B13.

Condition package: {"MACl_mol_percent": [0, 10, 20, 30, 40, 50, 60], "Bcmim_mol_percent": [0, 0.6]}.

Reference route: Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Acquire film diffraction → Acquire top-view morphology.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Conditional routes:

- FILM_MACL__XRD: {"assay": "XRD"}; Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Acquire film diffraction. Repeat for seven MACl levels crossed with two Bcmim states. SEM endpoint route is explicitly authored from incomplete thermal details.
- FILM_MACL__SEM_TOP: {"assay": "SEM_TOP"}; Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Acquire top-view morphology. Repeat for seven MACl levels crossed with two Bcmim states. SEM endpoint route is explicitly authored from incomplete thermal details.

Source/authored boundary: XRD series explicitly stops at 100 C for 1 h; no extra 150 C anneal is silently added. SEM thermal endpoint is less explicit and retained as source gap. A shared preparation prefix is an authored connection where this assay does not report a complete standalone method; relevant source-specific cards override it.

Relevant unresolved issues: U08, U03, Q01, U06, U04, U18.

Evidence: [S21: Supplementary Figure S21; PDF 30](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S22: Supplementary Figure S22; PDF 31](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S23: Supplementary Figure S23; PDF 32](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.28. Capture four phase-transition time series (PHASE_EVOLUTION)

Source families: B14.

Condition package: {"formulations": ["pristine", "Bcmim_only", "control", "target"], "seconds": [2, 5, 10, 15, 20, 30], "temperature_C": 100}.

Reference route: Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Create phase-time checkpoint → Acquire film diffraction.

Control/repetition: Twenty-four independent checkpoint films per authored replicate; do not anneal a 30 s film back to 2 s. Initial drying and snapshot method remain unresolved.

Source/authored boundary:  A shared preparation prefix is an authored connection where this assay does not report a complete standalone method; relevant source-specific cards override it.

Relevant unresolved issues: U08, U03, Q01, U06, U18.

Evidence: [F4: Main Figure 4; PDF 4](https://www.nature.com/articles/s41586-024-07228-z.pdf); [CELL: Small-area device fabrication; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### 6.29. Compare four final annealed phase patterns (PHASE_ENDPOINTS)

Source families: B14.

Condition package: {"formulations": ["pristine", "Bcmim_only", "control", "target"]}.

Reference route: Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Acquire film diffraction.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary:  A shared preparation prefix is an authored connection where this assay does not report a complete standalone method; relevant source-specific cards override it.

Relevant unresolved issues: U03, Q01, U06, U04, U18.

Evidence: [F4: Main Figure 4; PDF 4](https://www.nature.com/articles/s41586-024-07228-z.pdf); [CELL: Small-area device fabrication; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### 6.30. Map initial and annealed film composition (LATERAL_MAPS)

Source families: B15.

Condition package: {"formulations": ["control", "target"], "thermal_state": ["initial", "final annealed"]}.

Reference route: Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Prepare initial HIM film proxy → Acquire helium secondary-electron image → Acquire negative-ion lateral map → Acquire positive-ion lateral map.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Conditional routes:

- LATERAL_MAPS__INITIAL_HIM_NEG: {"thermal_state": "INITIAL", "polarity_service": "HIM_NEG"}; Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Prepare initial HIM film proxy → Acquire helium secondary-electron image → Acquire negative-ion lateral map. Repeat for control and target. Separate sister specimens or registered regions for polarities; do not reset sputtered material.
- LATERAL_MAPS__INITIAL_HIM_POS: {"thermal_state": "INITIAL", "polarity_service": "HIM_POS"}; Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Prepare initial HIM film proxy → Acquire helium secondary-electron image → Acquire positive-ion lateral map. Repeat for control and target. Separate sister specimens or registered regions for polarities; do not reset sputtered material.
- LATERAL_MAPS__FINAL_HIM_NEG: {"thermal_state": "FINAL", "polarity_service": "HIM_NEG"}; Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Prepare initial HIM film proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Acquire helium secondary-electron image → Acquire negative-ion lateral map. Repeat for control and target. Separate sister specimens or registered regions for polarities; do not reset sputtered material.
- LATERAL_MAPS__FINAL_HIM_POS: {"thermal_state": "FINAL", "polarity_service": "HIM_POS"}; Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Prepare initial HIM film proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Acquire helium secondary-electron image → Acquire positive-ion lateral map. Repeat for control and target. Separate sister specimens or registered regions for polarities; do not reset sputtered material.

Source/authored boundary: Final-state branch inserts ANNEAL_100, ANNEAL_150 after DRY_HIM. Polarity measurements use separate registered regions or sister specimens by authored default; not reused pristine sputtered area.

Relevant unresolved issues: U09, U03, Q01, U06.

Evidence: [HIM: HIM-SIMS surface composition and initial/final film preparation; PDF 9, 10](https://www.nature.com/articles/s41586-024-07228-z.pdf); [F5: Main Figure 5; PDF 5](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### 6.31. Measure destructive composition depth profiles (DEPTH_PROFILES)

Source families: B16.

Condition package: {"formulations": ["control", "target"], "substrate_stack": "perovskite/SnO2@TiO2/FTO"}.

Reference route: Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Acquire alternating sputter-depth profile.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary: S24 named stack omits PMMA:PCBM; this route preserves it. Spin-preparation link/drying is authored where figure does not repeat complete fabrication details.

Relevant unresolved issues: U09, U10, U03, Q01, U06, U04.

Evidence: [TOF: ToF-SIMS depth profiling; PDF 10](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S24: Supplementary Figure S24; PDF 33](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.32. Compare film surface chemical environments (SURFACE_SPECTRA)

Source families: B17.

Condition package: {"groups": ["control", "Bcmim-modified"], "exact_Bcmim_series": "not fully enumerated by S25"}.

Reference route: Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Acquire surface photoelectron spectra.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary: Main text mentions increasing additive content, but S25 does not give an explicit full concentration grid; no new series invented. A shared preparation prefix is an authored connection where this assay does not report a complete standalone method; relevant source-specific cards override it.

Relevant unresolved issues: U03, Q01, U06, U04, U18.

Evidence: [S25: Supplementary Figure S25; PDF 34](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [FILM_MEASURE: Film characterization: XRD, GIWAXS, microscopy, DLS, SEM, absorption, XPS, PL, TRPL, PLQY; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### 6.33. Measure substrate-specific emission and lifetime (LUMINESCENCE)

Source families: B18.

Condition package: {"formulations": ["control", "target"], "quartz_assays": ["PL_MAP", "PLQY", "TRPL"], "mesoporous_FTO_assays": ["TRPL"]}.

Reference route: Allocate sealed material portions → Prepare optical substrate proxy → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Acquire photoluminescence mapping → Acquire photoluminescence yield → Acquire time-resolved photoluminescence.

Control/repetition: Separate substrate/formulation/assay specimen allocations. Mesoporous FTO skips PL_MAP and PLQY. Each raw record retains substrate; diffusion length is a separate derived record.

Conditional routes:

- LUMINESCENCE__quartz_PL_MAP: {"substrate": "quartz", "assay": "PL_MAP"}; Allocate sealed material portions → Prepare optical substrate proxy → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Acquire photoluminescence mapping. Repeat for control and target with separately allocated optical films.
- LUMINESCENCE__quartz_PLQY: {"substrate": "quartz", "assay": "PLQY"}; Allocate sealed material portions → Prepare optical substrate proxy → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Acquire photoluminescence yield. Repeat for control and target with separately allocated optical films.
- LUMINESCENCE__quartz_TRPL: {"substrate": "quartz", "assay": "TRPL"}; Allocate sealed material portions → Prepare optical substrate proxy → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Acquire time-resolved photoluminescence. Repeat for control and target with separately allocated optical films.
- LUMINESCENCE__mesoporous_FTO_TRPL: {"substrate": "mesoporous_FTO", "assay": "TRPL"}; Allocate sealed material portions → Prepare optical substrate proxy → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Acquire time-resolved photoluminescence. Repeat for control and target with separately allocated optical films.

Source/authored boundary:  A shared preparation prefix is an authored connection where this assay does not report a complete standalone method; relevant source-specific cards override it.

Relevant unresolved issues: U07, U10, U06, U04, U18.

Evidence: [FILM_MEASURE: Film characterization: XRD, GIWAXS, microscopy, DLS, SEM, absorption, XPS, PL, TRPL, PLQY; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S20: Supplementary Figure S20; PDF 28, 29](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [T4: Supplementary Table S4; PDF 48](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.34. Measure sapphire-film microwave response (MICROWAVE_CARRIERS)

Source families: B18.

Condition package: {"formulations": ["control", "target"], "substrate": "sapphire"}.

Reference route: Allocate sealed material portions → Prepare optical substrate proxy → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Acquire microwave conductivity.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary: Mobility on sapphire is not silently a direct measurement on quartz/mesoporous substrates; combining it with lifetimes is a reported modelling assumption. A shared preparation prefix is an authored connection where this assay does not report a complete standalone method; relevant source-specific cards override it.

Relevant unresolved issues: U07, U10, U06, U04, U18.

Evidence: [TRMC: TRMC measurement and derived mobility; PDF 10](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S20: Supplementary Figure S20; PDF 28, 29](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [T4: Supplementary Table S4; PDF 48](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.35. Measure precursor aggregate distributions (AGGREGATE_SIZES)

Source families: B19.

Condition package: {"Bcmim_mol_percent": [0, 0.2, 0.6, 1.0, 1.4], "concentration": "device-fabrication-equivalent"}.

Reference route: Allocate sealed material portions → Prepare spin precursor proxy → Stir spin precursor proxy → Acquire precursor aggregate distributions.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary: DLS receives aliquots, not fabricated film; no filtration/dilution invented.

Relevant unresolved issues: U06.

Evidence: [FILM_MEASURE: Film characterization: XRD, GIWAXS, microscopy, DLS, SEM, absorption, XPS, PL, TRPL, PLQY; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S29: Supplementary Figure S29; PDF 38](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.36. Observe wet-film nucleation and growth (CRYSTAL_GROWTH)

Source families: B19.

Condition package: {"Bcmim_mol_percent": [0, 0.2, 0.6, 1.0, 1.4], "substrate": "FTO", "temperature_C": 100, "video_window_s": [0, 5.4]}.

Reference route: Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare growth-observation precursor proxy → Spin perovskite wet-film proxy → Observe wet-film crystal growth.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary: Wet film goes directly to hot-stage observation. Concentration basis explicitly references 1.0 M PbI2; use a distinct card, not an automatic 1.365 M conversion. A shared preparation prefix is an authored connection where this assay does not report a complete standalone method; relevant source-specific cards override it.

Relevant unresolved issues: U06, U03, U04, U18.

Evidence: [FILM_MEASURE: Film characterization: XRD, GIWAXS, microscopy, DLS, SEM, absorption, XPS, PL, TRPL, PLQY; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S30: Supplementary Figure S30; PDF 39](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.37. Track film thermal stability (FILM_THERMAL_AGE)

Source families: B20.

Condition package: {"formulations": ["control", "target"], "cumulative_age_h": [0, 48, 96, 192, 360, 600], "environment": "N2", "temperature_C": "60 ± 5"}.

Reference route: Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Acquire absorption spectrum → Acquire film diffraction → Thermally age film to next checkpoint → Acquire absorption spectrum → Acquire film diffraction.

Control/repetition: Baseline UVVIS/XRD precede ageing. Repeat FILM_AGE→UVVIS→XRD for each subsequent cumulative checkpoint using the assigned same-film/sister-film policy; never replay fabrication on the same ID.

Source/authored boundary:  A shared preparation prefix is an authored connection where this assay does not report a complete standalone method; relevant source-specific cards override it.

Relevant unresolved issues: U11, U03, Q01, U06, U04, U18.

Evidence: [AGE: Film thermal stability and operational module stability; PDF 6, 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S31: Supplementary Figure S31; PDF 40](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S32: Supplementary Figure S32; PDF 41, 42](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### 6.38. Track two operational module ageing conditions (MODULE_OPERATIONAL_AGE)

Source families: B21, B06.

Condition package: {"formulations": ["control", "target"], "temperature": ["room temperature", "65 C"], "window_h": 1000}.

Reference route: Allocate sealed material portions → Pattern P1 module lines → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Prepare PEAI solution proxy → Spin PEAI layer proxy → Prepare doped Spiro-OMeTAD solution proxy → Spin hole-transport layer proxy → Pattern P2 module lines → Deposit MoO3 layer proxy → Deposit ITO layer proxy → Deposit Au layer proxy → Pattern P3 module lines → Mount and calibrate photovoltaic station → Acquire forward electrical scan → Acquire reverse electrical scan → Stop and unload photovoltaic fixture → Clean module edge proxy → Lay module edge contact proxies → Place cover-glass proxy → Apply edge-seal proxy → Cure package proxy → Operate encapsulated module ageing.

Control/repetition: Four independently fabricated/encapsulated module proxies by authored minimum. Each condition retains its own timeline, reference signal and missing-data intervals.

Source/authored boundary: Original source does not report one sequence linking all scans, packaging and ageing; pre-age scans are an authored baseline connection.

Relevant unresolved issues: U11, U03, Q01, U06, U04, Q03, U10.

Evidence: [AGE: Film thermal stability and operational module stability; PDF 6, 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S33: Supplementary Figure S33; PDF 43](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [PACKAGE: Module encapsulation; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### 6.39. Inspect a sacrificial device cross section (DEVICE_CROSS_SECTION)

Source families: B03, B13.

Condition package: {"group": "target"}.

Reference route: Allocate sealed material portions → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Prepare PEAI solution proxy → Spin PEAI layer proxy → Prepare doped Spiro-OMeTAD solution proxy → Spin hole-transport layer proxy → Deposit MoO3 layer proxy → Deposit ITO layer proxy → Deposit Au layer proxy → Prepare cross-section proxy → Acquire cross-section morphology.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary: Destructive sister-device route; sectioned device cannot later enter intact PV/certification/ageing routes.

Relevant unresolved issues: U09, U03, Q01, U06, U04.

Evidence: [F1: Main Figure 1; PDF 2](https://www.nature.com/articles/s41586-024-07228-z.pdf); [FILM_MEASURE: Film characterization: XRD, GIWAXS, microscopy, DLS, SEM, absorption, XPS, PL, TRPL, PLQY; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### 6.40. Acquire separate stabilized module output (STABILIZED_MODULE_OUTPUT)

Source families: B04, B08.

Condition package: {"group": "target", "MPP_window_s": 300}.

Reference route: Allocate sealed material portions → Pattern P1 module lines → Ultrasonic cleaning proxy: acetone → Ultrasonic cleaning proxy: isopropanol → Ultrasonic cleaning proxy: deionized water → Prepare and store Ti stock proxy → Form compact Ti layer proxy → Rinse Ti plate proxy → Anneal Ti layer proxy → Prepare and store Sn stock proxy → Modify Ti layer with Sn proxy → Rinse modified plate proxy → Anneal modified compact layer proxy → Prepare PMMA:PCBM solution proxy → Spin PMMA:PCBM interface proxy → Anneal PMMA:PCBM interface → Prepare spin precursor proxy → Stir spin precursor proxy → Spin perovskite wet-film proxy → Rapid vacuum drying proxy → First perovskite anneal proxy → Second perovskite anneal proxy → Prepare PEAI solution proxy → Spin PEAI layer proxy → Prepare doped Spiro-OMeTAD solution proxy → Spin hole-transport layer proxy → Pattern P2 module lines → Deposit MoO3 layer proxy → Deposit ITO layer proxy → Deposit Au layer proxy → Pattern P3 module lines → Mount and calibrate photovoltaic station → Acquire forward electrical scan → Acquire reverse electrical scan → Acquire stabilized-output trace → Stop and unload photovoltaic fixture.

Control/repetition: Repeat the complete specimen route for each condition and authored independent replicate; do not relabel an existing specimen.

Source/authored boundary: The source trace is from the certified target module. This is a source-grounded mock acquisition task, not new certification. A control MPP comparison, if issued, is labelled authored expansion.

Relevant unresolved issues: U03, Q01, U06, U04, Q03, U10.

Evidence: [SPIN_MODULE: Spin-coated eight-subcell module fabrication; PDF 8, 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [F1: Main Figure 1; PDF 2](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S6: Supplementary Figure S6; PDF 13](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

## 7. Long-horizon clocks, handoffs and repeats

Time-dependent precursor measurements preserve separate control/target tubes at 25 C and 60 C, the source's 96-point/15 min statement and its unresolved endpoint convention. The variable-temperature route retains cumulative thermal history rather than resetting the tube between temperatures. Fresh/ten-day precursor-derived films use matched but separately aged aliquots. Film thermal ageing preserves 0, 48, 96, 192, 360 and 600 h checkpoints; operational module ageing preserves distinct room-temperature/65 C conditions across the stated 1000 h window. Each timer is a recorded mock clock. No real waiting period or real measurement is claimed. [NMR: NMR spectroscopy, model interactions, HBA, operando VT/time-dependent and EXSY measurements; PDF 10, 11](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S13: Supplementary Figure S13; PDF 20](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S31: Supplementary Figure S31; PDF 40](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S32: Supplementary Figure S32; PDF 41, 42](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S33: Supplementary Figure S33; PDF 43](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

Interrupted measurements retain timestamps, missing intervals, exposure and invalid records. Reacquisition is permitted only if the state remains comparable. An aged film cannot be returned to its earlier checkpoint; a sputtered surface cannot become fresh; a sectioned device cannot return to intact-cell measurement. Remaking requires new sufficient input stock.

External beamline, diffraction or certification-like transfers are custody-preserving mock services. Every departure and return records carrier, sample and report identity. The existing NPVM certificate is source evidence only. There is no actual shipment, communication, upload or certification request. [S5: Supplementary Figure S5; PDF 12](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S6: Supplementary Figure S6; PDF 13](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [FILM_MEASURE: Film characterization: XRD, GIWAXS, microscopy, DLS, SEM, absorption, XPS, PL, TRPL, PLQY; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf)

## 8. Measurement records and honest derivation

Every acquisition records sample, parent batch, condition, instrument/service job, attempt, time, units, channel/nucleus/region, calibration status, validity and mock=true. The raw record is immutable. A fitted or derived output has separate input references and assumptions.

- PV: distinguish current from current density, aperture from substrate area, scan direction, scan-derived PCE, average MPP output and final stabilized output. Unknown irradiance prevents valid PCE even if raw I/V is usable
- EQE: preserve raw wavelength response and reference; integrated current requires a declared incident spectrum and units
- NMR: preserve nucleus, solvent, reference, tube and time/temperature history; peak shifts, linewidths and fits are not unobserved molecular reactions
- XRD/GIWAXS/rocking: keep geometry, orientation, axes and fit metadata; selected peak ratios are not automatically absolute mass fractions
- HIM/ToF-SIMS: preserve polarity, region, ion channel and exposure; elapsed sputter time is not calibrated depth without a supported conversion
- PLQY/TRPL/TRMC: reference acquisitions and instrument response/calibration remain separate. TRMC directly supports a yield-weighted mobility quantity; assuming yield near unity must be explicit. Combining sapphire mobility with quartz/mesoporous-film lifetimes is a modelling connection, not a direct same-specimen measurement
- Microscopy and DLS: grain counts, distributions and classifications require recorded analysis rules; video frames are not independent specimens, and DLS intensity distributions are not particle-number distributions

No reported efficiency, pH, lifetime, peak shift, phase fraction or retention percentage is a reward target or automatically inserted mock observation. A correctly recorded unexpected result is preferable to fabricated agreement. [PV: Device characterization and masking; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [NMR: NMR spectroscopy, model interactions, HBA, operando VT/time-dependent and EXSY measurements; PDF 10, 11](https://www.nature.com/articles/s41586-024-07228-z.pdf); [TOF: ToF-SIMS depth profiling; PDF 10](https://www.nature.com/articles/s41586-024-07228-z.pdf); [TRMC: TRMC measurement and derived mobility; PDF 10](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S20: Supplementary Figure S20; PDF 28, 29](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [T4: Supplementary Table S4; PDF 48](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S32: Supplementary Figure S32; PDF 41, 42](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

## 9. Irreversibility, recovery and cleanup

- Wrong lot identified before mixing: Return the still sealed unused token, correct the selection and log the rejected attempt.
- Wrong ingredient already consumed: Stop, quarantine mixed child and residuals; allocate new parent portions. Never remove an ingredient by changing a label.
- Carrier, mask or reversible connector is misseated: Stop output/service, wait for safe access, support and reseat, reacquire readiness/reference checks and record a new attempt.
- Interlock, safe-release or station readiness is absent: Do not start/open. Keep item supported in allowed state, log blocker, isolate station if needed. No time-based invented safe release.
- Proxy breaks, drops or produces fragments: Stop motion, contain fragments in authored collection area, quarantine parent and all fragments, allocate a new specimen if inventory allows.
- Point, spectrum or interval invalid/missing: Retain invalid record. Reacquire only if state and time remain comparable; otherwise flag missing checkpoint and continue only the permitted trajectory.
- Light, temperature or NMR condition drifts: Stop acquisition, retain gap/drift interval, restore only reversible conditions, log a new attempt with cumulative exposure. Do not restart the clock as fresh.
- Calibration/reference missing or invalid: Record raw data with calibration unknown; derived PCE, absolute depth, PLQY or mobility remain unknown until supported by a valid independent check.
- Task asks for pristine state after section/sputter/age/cure: Reject reuse; choose a preallocated sister specimen or report stock shortage.
- Mock external report ID disagrees with custody manifest: Quarantine report linkage, retain both IDs and request corrected mock receipt; never attach another sample's result.
- Source contradiction or absent parameter reached: Use only an explicitly declared unresolved-source inert service card; otherwise stop that branch and report what is unknown. Never infer real chemical settings.

Final closure includes specimen and data archive, separate failed/sectioned/sputtered/aged-object locations, closed spent-token waste, returned masks/carriers/tools and empty stopped stations. A genuinely blocked station remains isolated with a stated blocker; it is never falsely declared reset.

## 10. Source contradictions and missing information

These are retained boundaries of the design. Numeric source claims are stored as reported; authored service mechanics do not silently repair them. A mock-only episode can use a visibly unresolved-source card. A source-exact chemistry execution would stop for clarification.

### Q01. Sn modification dilution conflict

SnCl2/ethanol stock is described, while the dilution parenthesis names aqueous TiCl4 and water. Mock-only unresolved-source card; never pick a real recipe or silently fix the text.

Evidence: [ETL: Compact TiO2 and SnO2-modified TiO2 preparation; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### Q02. Model crystal formula conflict

Preparation heading uses [Bcmim]2Pb3Cl2I6·2DMF; characterization, main discussion and SI use [Bcmim]4Pb3Cl2I6·2DMF. Use reaction-parent lineage plus neutral crystal-family ID; preserve both labels without choosing a formula.

Evidence: [CRYSTAL: Model-adduct preparation and single-crystal characterization; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S28: Supplementary Figure S28; PDF 37](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [T5: Supplementary Table S5; PDF 49](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### Q03. Device illumination unit conflict

Device Methods report 100 mA cm^-2 as light intensity, whereas ageing reports 100 mW cm^-2. Keep device value as reported and mark irradiance unresolved; PCE requires separately valid mock irradiance card.

Evidence: [PV: Device characterization and masking; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [AGE: Film thermal stability and operational module stability; PDF 6, 9](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### Q04. This-work stack conflict

SI Table S1 this-work row contains Br, PDCBT and Cr labels differing from main composition and PEDOT:complex/MoO3/ITO/Au Methods. Main Methods define task fabrication route; record table disagreement, do not merge the stacks.

Evidence: [T1: Supplementary Table S1; PDF 44, 45](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [CELL: Small-area device fabrication; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf); [F1: Main Figure 1; PDF 2](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### Q05. S12 control panel temperatures

S12 caption labels both control panels c and d as 60 C, but the plotted panel c is labelled Control at 25 C and panel d Control at 60 C. Preserve caption-versus-panel disagreement. Methods independently define 25 C and 60 C routes; no hidden correction is made.

Evidence: [S12: Supplementary Figure S12; PDF 19](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [NMR: NMR spectroscopy, model interactions, HBA, operando VT/time-dependent and EXSY measurements; PDF 10, 11](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### Q06. Transport table cross-reference

S20 text points to Table S2, while transport fitting values are in Table S4. Cite actual labelled table; preserve incorrect cross-reference as a source issue.

Evidence: [S20: Supplementary Figure S20; PDF 28, 29](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [T4: Supplementary Table S4; PDF 48](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### Q07. Crystallographic table cross-reference

S28 text points to Table S3; crystallographic table is S5. Cite actual S5; do not infer unseen measurements.

Evidence: [S28: Supplementary Figure S28; PDF 37](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [T5: Supplementary Table S5; PDF 49](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### Q08. Operando additive concentration conflict

Fabrication specifies 0.0078 M [Bcmim]Cl; operando Methods state 0.6 mol%, 0.78 mM. Preserve nominal target and both numeric claims; mock operando card is unresolved, not normalized to fabrication.

Evidence: [CELL: Small-area device fabrication; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf); [NMR: NMR spectroscopy, model interactions, HBA, operando VT/time-dependent and EXSY measurements; PDF 10, 11](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### Q09. pH concentration and panel membership conflict

Methods give 0.0075 mmol in 10.0 ml, arithmetically 0.00075 M; Table S3 says 0.0075 M and includes [Bcmim]BF4 omitted from the Methods list. Use six labelled comparison groups; flag BF4 preparation and concentration unresolved. No acidity target values awarded.

Evidence: [PH: pH comparison; PDF 11](https://www.nature.com/articles/s41586-024-07228-z.pdf); [T3: Supplementary Table S3; PDF 47](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### Q10. Apparent kinetic units

S11 calls values apparent first-order rate constants but reports mM s^-1 units. Retain raw concentration/time records; do not label a fitted first-order constant in inverse-time units without a defined model.

Evidence: [S11: Supplementary Figure S11; PDF 18](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### Q11. NMR control nominal percentages

Note 1 reports final LiCl 0.0065 M against 0.15 M MACl as 5 mol%; listed additions/final volumes are not fully self-consistent; TFA with [Bcmim] is mentioned in prose but not a numbered table row. Keep stated labels and numbers separate; include paired-TFA comparison as a reported-prose, underdetermined route, not a resolved recipe.

Evidence: [N1: Supplementary Note 1: alternative NMR explanations and control preparations; PDF 6](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [T2: Supplementary Table S2; PDF 46](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### U01. External additive syntheses

[Bcmim]Cl, exchanged counterions and [C1SCNmim]Cl rely on references 33/34; no complete synthesis within retained paper/SI. Closed incoming-material provenance service with supplied symbolic raw lots. Synthesis completion is not credited; no guessed reaction route.

Evidence: [MATERIALS: Methods / Materials; cited syntheses are external dependencies; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### U02. Missing handling and apparatus interfaces

Transfer vessels, sample counts, grips, switches, carriers, cleaning details and almost all safety interlocks are not reported. Explicit authored robotic interfaces; Hooke supplies scenes. No claim of recovered human microtrajectory.

Evidence: [ETL: Compact TiO2 and SnO2-modified TiO2 preparation; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf); [CELL: Small-area device fabrication; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf); [FILM_MEASURE: Film characterization: XRD, GIWAXS, microscopy, DLS, SEM, absorption, XPS, PL, TRPL, PLQY; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [NMR: NMR spectroscopy, model interactions, HBA, operando VT/time-dependent and EXSY measurements; PDF 10, 11](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### U03. Cleaning duration allocation

Sequential acetone/isopropanol/water ultrasonic cleaning is described with 15 min; allocation per solvent is not explicit. Use ordered three-stage proxy cycle; retain reported duration as unallocated metadata.

Evidence: [ETL: Compact TiO2 and SnO2-modified TiO2 preparation; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### U04. Rapid-drying apparatus and coating details

Reference 35 supplies rapid-vacuum apparatus details; pressure, ramp, blade gap/speed and gas-pump/N2-knife settings are not provided here. Closed services expose only mock completion; unspecified numeric values stay null.

Evidence: [CELL: Small-area device fabrication; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf); [BLADE_MODULE: Blade-coated module fabrication; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### U05. Replicate and allocation counts

Scatter distributions are shown but independent-device/sample counts and cross-assay reuse lineage are not stated unambiguously. Default one distinct symbolic specimen per condition, with configurable authored replicate count. Never count scans/points as independent samples.

Evidence: [F1: Main Figure 1; PDF 2](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S1: Supplementary Figure S1; PDF 8](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S2: Supplementary Figure S2; PDF 9](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S3: Supplementary Figure S3; PDF 10](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S4: Supplementary Figure S4; PDF 11](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S7: Supplementary Figure S7; PDF 14](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### U06. Molar-percent denominator

Concentration-series prose and Methods do not use a universally explicit common denominator; crystallization microscopy explicitly references 1.0 M PbI2. Store mol% labels and absolute source concentrations independently; do not convert between them without a resolved card.

Evidence: [CELL: Small-area device fabrication; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf); [FILM_MEASURE: Film characterization: XRD, GIWAXS, microscopy, DLS, SEM, absorption, XPS, PL, TRPL, PLQY; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S3: Supplementary Figure S3; PDF 10](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S4: Supplementary Figure S4; PDF 11](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### U07. Film-specific substrate preparation

Quartz, sapphire and FTO/c-TiO2/m-TiO2 optical substrates are named; the complete mesoporous-layer fabrication route is not provided. Separate raw-substrate-to-optical-film proxy with unresolved preparation metadata, not a claim that the device stack is equivalent.

Evidence: [S20: Supplementary Figure S20; PDF 28, 29](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [TRMC: TRMC measurement and derived mobility; PDF 10](https://www.nature.com/articles/s41586-024-07228-z.pdf); [T4: Supplementary Table S4; PDF 48](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### U08. Phase snapshot acquisition geometry

Fig.4 gives 100 C snapshots at 2,5,10,15,20,30 s; in situ acquisition versus withdrawn sister coupons is not specified. Authored independent sister-film checkpoints; preserve this choice and never assert source chronology.

Evidence: [F4: Main Figure 4; PDF 4](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### U09. Destructive measurement preparation

SEM cross-section cutting method, protective coatings, HIM region reuse and ToF depth calibration details are absent. Closed destructive-preparation proxy, independent sister specimens/regions by default; no pristine reuse.

Evidence: [F1: Main Figure 1; PDF 2](https://www.nature.com/articles/s41586-024-07228-z.pdf); [FILM_MEASURE: Film characterization: XRD, GIWAXS, microscopy, DLS, SEM, absorption, XPS, PL, TRPL, PLQY; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [HIM: HIM-SIMS surface composition and initial/final film preparation; PDF 9, 10](https://www.nature.com/articles/s41586-024-07228-z.pdf); [TOF: ToF-SIMS depth profiling; PDF 10](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### U10. Calibration and derived quantities

PV irradiance, EQE integration spectrum, PLQY detailed reference procedure, TRMC K/FA/I/beta and absolute depth calibration are incompletely supplied. Records may remain raw or derived-unknown. External method refs 36/38 are dependencies, not silently imported procedures.

Evidence: [PV: Device characterization and masking; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [FILM_MEASURE: Film characterization: XRD, GIWAXS, microscopy, DLS, SEM, absorption, XPS, PL, TRPL, PLQY; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [TRMC: TRMC measurement and derived mobility; PDF 10](https://www.nature.com/articles/s41586-024-07228-z.pdf); [TOF: ToF-SIMS depth profiling; PDF 10](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### U11. Ageing allocation and environment details

Ten-day PPS storage temperature/conditions, film removal/reinsertion schedule, long-run cadence and full ISOS implementation details are not specified. Use explicitly authored sealed storage and service clock; predeclare same-specimen versus sister-specimen sampling, record gaps.

Evidence: [S13: Supplementary Figure S13; PDF 20](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S31: Supplementary Figure S31; PDF 40](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S32: Supplementary Figure S32; PDF 41, 42](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S33: Supplementary Figure S33; PDF 43](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [AGE: Film thermal stability and operational module stability; PDF 6, 9](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### U12. Certification is external evidence

NPVM certificate is reported; shipping/selection chain and full external test procedure are absent. Authored mock dispatch/receipt task may assess chain of custody; never imply new certification or send anything externally.

Evidence: [S5: Supplementary Figure S5; PDF 12](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S6: Supplementary Figure S6; PDF 13](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [F1: Main Figure 1; PDF 2](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### U13. Unreported model solutions

S27 names NaPbI3 and comparison solutions but does not give a complete preparation route for each. Closed model-solution proxy with source-known identities, unresolved concentration/preparation; not a newly invented synthesis.

Evidence: [S27: Supplementary Figure S27; PDF 36](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### U14. Source interpretation is not direct observation

Depth distribution, grain-boundary location, acidity mechanism, defect passivation and nucleation mechanism include interpretations and different evidence strengths. Keep mock observations separate from optional interpretation; no reward for repeating causal claims as measured facts.

Evidence: [S24: Supplementary Figure S24; PDF 33](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S25: Supplementary Figure S25; PDF 34](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S26: Supplementary Figure S26; PDF 35](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S28: Supplementary Figure S28; PDF 37](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S29: Supplementary Figure S29; PDF 38](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S30: Supplementary Figure S30; PDF 39](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [N2: Supplementary Note 2: computational surface interpretations; PDF 7](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### U15. NMR clock endpoints

Methods specify 96 time points at 15 min across 24 h; inclusive start/end convention is not explicit. Record timestamp grid from issued clock card; do not silently turn 96 acquisitions into 97.

Evidence: [NMR: NMR spectroscopy, model interactions, HBA, operando VT/time-dependent and EXSY measurements; PDF 10, 11](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S11: Supplementary Figure S11; PDF 18](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S12: Supplementary Figure S12; PDF 19](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### U16. Crystal radiation identifier

Instrument name includes Cu, while S5 explicitly lists Mo K-alpha and wavelength 0.71073 A. Preserve instrument identifier and explicit radiation entry separately; no inferred source selection.

Evidence: [CRYSTAL: Model-adduct preparation and single-crystal characterization; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf); [T5: Supplementary Table S5; PDF 49](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

### U17. Missing tolerances and service yield

No task-ready acceptance tolerances, processing yields, exact stock consumption or minimum film size for every test are given. Symbolic inventory conservation and observable mock success are authored. No quantitative chemical mass/yield claim.

Evidence: [CELL: Small-area device fabrication; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf); [FILM_MEASURE: Film characterization: XRD, GIWAXS, microscopy, DLS, SEM, absorption, XPS, PL, TRPL, PLQY; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [NMR: NMR spectroscopy, model interactions, HBA, operando VT/time-dependent and EXSY measurements; PDF 10, 11](https://www.nature.com/articles/s41586-024-07228-z.pdf)

### U18. Shared fabrication route versus assay-specific preparation

Most film assay descriptions do not repeat a complete per-assay preparation route or every substrate/interface. Growth observation gives a different explicit PbI2 basis. Reusing a common fabrication prefix on compatible assay substrates is an authored connection. Source-specific named stacks and the growth precursor override it; unreported settings remain unknown.

Evidence: [CELL: Small-area device fabrication; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf); [FILM_MEASURE: Film characterization: XRD, GIWAXS, microscopy, DLS, SEM, absorption, XPS, PL, TRPL, PLQY; PDF 9](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S13: Supplementary Figure S13; PDF 20](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S18: Supplementary Figure S18; PDF 25, 26](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S20: Supplementary Figure S20; PDF 28, 29](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S25: Supplementary Figure S25; PDF 34](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S30: Supplementary Figure S30; PDF 39](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

## 11. Explicit nonmanual coverage

- CHEMICAL_MECHANISM: Decomposition/equilibrium/exchange schemes and proposed stabilization mechanism; interpretation task only. No extra chemical reaction procedure inferred. [F2: Main Figure 2; PDF 3](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S8: Supplementary Figure S8; PDF 15](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S9: Supplementary Figure S9; PDF 16](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S16: Supplementary Figure S16; PDF 23](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S17: Supplementary Figure S17; PDF 24](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S28: Supplementary Figure S28; PDF 37](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [N1: Supplementary Note 1: alternative NMR explanations and control preparations; PDF 6](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)
- DFT_SURFACES: Reported PBE-D3/CP2K structures, surface terminations, adsorption energies and Born-Oppenheimer dynamics are explicitly nonmanual. No code installed or calculation executed. [COMPUTE: Computational details; not a hands-on branch; PDF 11](https://www.nature.com/articles/s41586-024-07228-z.pdf); [N2: Supplementary Note 2: computational surface interpretations; PDF 7](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S26: Supplementary Figure S26; PDF 35](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)
- STRUCTURE_REFINEMENT: ShelXT/Olex2/ShelXL solution/refinement and crystallographic tables are analytical outputs from SCXRD, not extra robot motion. No new structure solved. [CRYSTAL: Model-adduct preparation and single-crystal characterization; PDF 8](https://www.nature.com/articles/s41586-024-07228-z.pdf); [T5: Supplementary Table S5; PDF 49](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)
- TRANSPORT_DERIVATION: Fits, phi-weighted mobility and diffusion length require units, calibration, temperature and explicit substrate-transfer assumptions; no paper numbers injected as observations. [TRMC: TRMC measurement and derived mobility; PDF 10](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S20: Supplementary Figure S20; PDF 28, 29](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [T4: Supplementary Table S4; PDF 48](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)
- KINETIC_FITS: Apparent kinetic fits and percentage decomposition from NMR series are separate derived records; Q10 unit issue retained. [S11: Supplementary Figure S11; PDF 18](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [NMR: NMR spectroscopy, model interactions, HBA, operando VT/time-dependent and EXSY measurements; PDF 10, 11](https://www.nature.com/articles/s41586-024-07228-z.pdf)
- PHASE_FRACTION: Selected diffraction-peak integrated-intensity ratios are reported analysis; not automatically absolute calibrated phase mass fractions. [S32: Supplementary Figure S32; PDF 41, 42](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)
- LITERATURE_CERTIFICATES: External certification and literature comparison table are evidence-only. Mock custody task cannot issue a genuine certificate. [T1: Supplementary Table S1; PDF 44, 45](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S5: Supplementary Figure S5; PDF 12](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S6: Supplementary Figure S6; PDF 13](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)
- PERFORMANCE_STATISTICS: Distribution/mean/uncertainty analysis requires genuinely separate mock specimens and declared sample count. Published values are source results, not reward targets. [F1: Main Figure 1; PDF 2](https://www.nature.com/articles/s41586-024-07228-z.pdf); [S1: Supplementary Figure S1; PDF 8](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S2: Supplementary Figure S2; PDF 9](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S3: Supplementary Figure S3; PDF 10](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S4: Supplementary Figure S4; PDF 11](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf); [S7: Supplementary Figure S7; PDF 14](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41586-024-07228-z/MediaObjects/41586_2024_7228_MOESM1_ESM.pdf)

The analysis ledger covers proposed chemical mechanisms, DFT, crystal refinement, kinetic fits, transport derivation, diffraction ratios, performance distributions and literature/certification evidence. These are never inflated into additional robot-made specimens or new experimental routes.

## 12. Static verification and completion boundary

Separate release checks cover JSON parsing, unique IDs, operation/source/card/issue references, source-family and figure/table/note dispositions, actor/reference boundaries, action expansion, source hashes, module ordering, conditional routes, source-specific exceptions and export hygiene. Check reports and historical authoring status are intentionally outside this task-only export; this document makes no new runtime-validation claim.

These checks do not establish reachability, grasp success, sensor realism, correct instrument APIs, physically valid chemistry, scientific reproducibility or runtime reward correctness. No robot rollout, mock execution, simulator, hardware process, external calculation, installation or remote change was performed. Hooke scene binding and any future authorized runtime review remain separate work.

## 13. Source attribution and export policy

All experimental facts are paraphrased from the retained publisher paper and linked supplement. Main and SI hashes and exact page locators are in provenance.json. PDF page numbers are one-based; SI printed numbering is offset by one page. The article reports a [CC BY 4.0 licence](https://creativecommons.org/licenses/by/4.0/). This package nevertheless exports only newly authored task specifications and factual condition summaries, with no publisher PDFs, text dumps, screenshots or copied graphics.
