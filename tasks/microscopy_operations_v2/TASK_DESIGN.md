# Deconwolf: paper-wide hands-on task family

> Public task-specification snapshot: source packets, scenes, models and runtime dependencies referenced below are not included. See ../../EXPORT_NOTES.md for current export boundaries. This is a design specification, not an executable or experimentally validated benchmark.

## Delivered decision

This is **one paper-wide task design**, with six preparation-and-imaging branches and seven source-data workstation branches. It expands the earlier single tubulin route into the reported manual program. Preparation is in scope: cell-line setup, routine fixation, staining, FISH, tissue preparation, mounting, transport, microscopy controls, acquisition, unloading, cleanup and data lineage all have object actions.

This is a task-design delivery, not a laboratory SOP, implemented simulator, gameplay trace or experimental replication. The science backend is explicitly preset; no physical, optical, chemical or biological process is computed. A future task can complete with these authored presets without waiting for physics. Exact source protocol completeness is a different claim: missing source parameters and contradictions remain visible.

Paper: Wernersson et al., *Deconwolf enables high-performance deconvolution of widefield fluorescence microscopy images*, Nature Methods (2024), DOI [10.1038/s41592-024-02294-7](https://www.nature.com/articles/s41592-024-02294-7). Main article, Methods, main/Extended Data captions and retained main SI were read. Separate probe tables and original image datasets were not retained in this packet. This adaptation contains paraphrased facts, authored task mechanics and source locators; it does not package original source imagery.

## What the agent actually does

The agent starts at receiving with stock/sample identity tokens, empty compatible carriers and closed reagent props. No required specimen is already stained, mounted or imaged. It opens containers, selects stock/reagent identities, uses a pipette with fresh tips, transfers task aliquots, mixes source-defined recipes, washes through individual cycles, closes vessels, carries them in a tray on a wheeled base, docks at incubation or imaging stations, sets controls and waits on virtual timers. It mounts each specimen, selects the correct microscope variant, locates the field from preview cues, focuses, acquires, saves raw records, unloads and cleans up.

Scientific recipe values are source-bound. Source-unreported volumes, durations, support-slide geometry and handling paths are never filled in as paper facts. A clearly marked task-only gap card supplies the missing operational bridge, using categorical aliquots/timers rather than invented lab parameters. Those bridge actions still require manipulation; they are not free completion flags.

Each branch is an independent specimen lineage, not six consecutive treatments of one specimen. The task family supports one branch per episode or a long paper-program episode. Paper-program task completion requires all six specimen branches and all seven data branches; completing tubulin alone is not whole-paper task completion.

## Files and visibility

- `initialstate.json`: agent-visible initial objects, locations, labels and control states
- `agentgoal.json`: agent-visible outcomes; no hidden acceptance predicates
- `operation_sequences.json`: designer/reference preparation program, source settings, acquisition variants and analysis obligations
- `interaction_design.json`: actual manipulation/navigation macros and discrete-action semantics, not a new CLI
- `evaluator_reference.json`: separate evaluator conditions and source controls; not given to the agent
- `preset_output_contract.json`: state-conditioned semantic output fixtures, including failed focus/field/channel states
- `asset_bindings.json`: existing detailed assets and honestly labeled reuse variants/proxies
- `recovery_design.json`: error handling and restart rules
- `paper_coverage.json`: complete branch ledger and explicit source gaps
- `source_bindings.json`: source line/XML locators and digests

## Reuse of existing detailed assets

The Ti-E-like station, iXon Ultra 888, Zyla 4.2P and coverslip/plate assemblies already exist as GLB/Blender files. Their contact sheet was inspected. The selected station is the original iFISH/iXon/100×/square-carrier depiction. Tubulin substitutes the separately existing 18 mm round carrier with an authored insert. Zyla, 60× oil, 20× air and caption-only GFAP 100× configurations are explicitly separate variants, not simultaneous cameras or silently equivalent microscope models. A Zyla USB3/air-cooled depiction does not establish the original paper's interface or cooling mode.

Leica SP8, Leica STED, Zeiss LSM980, incubator, microtome, pipette, mobile base and support-slide details use labeled task proxies where no complete model exists. Those are design bindings, not claims that new detailed meshes were produced. Existing `stage_x`, `stage_y`, `objective_retract`, carrier-lift and lid controls are display controls; this design adds independent logical affordances without pretending their ranges are calibrated motion.

## Evaluation and scientific outputs

The evaluator reads trusted world events, object-support relations, reagent lineage, timers, control histories and immutable acquisition records. It ignores an agent's success booleans. A stage transition requires the relevant objects and operations, not merely the right operation name in a plan. A nominal preset observation unlocks only for the correct prepared specimen, carrier, station, field, focus and settings. Wrong focus, saturation, wrong field, wrong channel and mounting faults produce different authored QC cues and retain failed attempts.

The presets are semantic records in this delivery; pixel arrays are not provided. They can drive an implementation's images or UI later. Published numbers are literature-reference values, not new task measurements. Selecting an attractive preset result cannot replace performing sample preparation and acquisition. All raw data and derivatives keep specimen, carrier, field, modality, settings and parent identity. Source data comparisons use explicitly authored stand-ins because raw arrays are absent.

## Required controls

- Tubulin: same specimen and same FOV, **confocal first**, then widefield
- GFAP: same 4×4 ROI mosaic and 10% overlap for 60×/63×; source gives no inter-modality order
- GFAP 100×: distinct caption-backed variant; no camera/stack settings inherited from 60×
- Tissue: ten 20× acquisition FOVs and a corresponding 60× subset; five analyzed fields in figures are a separate count
- Nuclear pores: STED then confocal; source identity and fluorophore contradictions remain attached
- iFISH: per-nucleus/four-channel pairing; the 51-plane HAP1 boundary example does not supply a general iFISH setting
- PSF comparison: ChrX-36plex remains separate from ChrX-46plex tracing
- RLN comparison: published screenshot reference is never labeled as a rerun output

## Source gaps and honest task bridges

The source reports inconsistent or incomplete values: “human PtK2” and mismatched nuclear-pore fluorophore wording; iFISH pre-hybridization mg/ml versus hybridization µg/ml; a catalase concentration with source-literal mM units; 63 versus 65 loci in different source listings; Lanczos-3 versus Lanczos-5; directly labeled MKI67 alongside a statement inheriting SKBR3 steps. These are not silently corrected. The tissue task includes separately labeled direct-label and literal-inherited-step interpretations. The nuclear-pore task uses a declared source-literal demonstration fixture, never a claim of verified fluorophore compatibility.

Probe production relies on a cited prior pipeline and unretained sequence tables. The entry resource is therefore a source-identified probe lot, not an invented synthesis recipe. SKBR3 upstream fixation/permeabilization, nuclear-pore upstream preparation, GFAP dewaxing details and numerous volumes/timings have explicit task-only bridge cards. Source-unreported values remain unknown even when task play can proceed. No laboratory safety, chemistry or equipment operating approval is implied by these task cards.

## Full preparation and acquisition program

All parameters below are transcribed/paraphrased from the bound source sections unless marked unknown or authored. Task reagent tokens are visual/discrete materials, not real chemical preparation instructions for a laboratory. The JSON is the structured version of this program.


### U-2 OS tubulin: culture → immunostain → matched confocal/widefield

Entry: U-2 OS stock identity token, not a pre-stained or pre-mounted specimen

Carrier: 18 mm round #1.5 high-precision coverslip, VWR 630-2200

1. **Place round carrier in an authored culture dish; seed source U-2 OS stock** (`seed`). Source: M64, M80. Reported settings: {"medium": "DMEM high glucose/GlutaMAX/pyruvate + 10% FBS"}.
   - Source gap: Seeding density, dish identity and volume unreported
2. **Load closed culture carrier into incubator and grow** (`incubate`). Source: M80. Reported settings: {"temperature_C": 37, "CO2_percent": 5, "duration_days_range": [1, 3]}.
3. **Exchange growth medium for source fixation solution** (`exchange_incubate`). Source: M80. Reported settings: {"formaldehyde_percent": 8, "solvent": "1× PBS", "solution": "pre-warmed", "duration_min": 10, "temperature": "room temperature"}.
   - Source gap: Pre-warm temperature and volume unreported; preserve 8%, do not silently halve
4. **Permeabilize same coverslip** (`exchange_incubate`). Source: M80. Reported settings: {"Triton_X100_percent_volvol": 0.5, "solvent": "1× PBS"}.
   - Source gap: Duration unreported
5. **Block same coverslip** (`exchange_incubate`). Source: M80. Reported settings: {"BSA_percent_wvol": 5, "glycine_M": 0.1, "solvent": "1× PBS", "duration_min": 30, "temperature": "room temperature"}.
6. **Apply primary anti-alpha-tubulin antibody** (`exchange_incubate`). Source: M80. Reported settings: {"antibody": "T6074", "dilution": "1:250", "BSA_percent_wvol": 5, "glycine_M": 0.1, "solvent": "1× PBS", "duration_h": 1, "temperature": "room temperature"}.
7. **Wash primary-labeled specimen** (`wash`). Source: M80. Reported settings: {"repeats": 5, "buffer": "1× PBS"}.
   - Source gap: Wash dwell unreported
8. **Reblock specimen** (`exchange_incubate`). Source: M80. Reported settings: {"BSA_percent_wvol": 5, "glycine_M": 0.1, "solvent": "1× PBS"}.
   - Source gap: Reblock duration unreported
9. **Apply AF555 secondary and DAPI** (`exchange_incubate`). Source: M80. Reported settings: {"secondary": "ab150118", "dilution": "1:400", "counterstain": "DAPI D1306", "duration_h": 1, "temperature": "room temperature"}.
   - Source gap: DAPI concentration unreported
10. **Wash secondary-labeled specimen** (`wash`). Source: M80. Reported settings: {"repeats": 5, "buffer": "1× PBS"}.
   - Source gap: Wash dwell unreported
11. **Mount stained round coverslip with Prolong Gold** (`mount`). Source: M80. Reported settings: {"mounting_medium": "Prolong Gold P10144"}.
   - Source gap: Medium volume, support-slide identity, orientation and curing duration unreported

Required acquisition variants:
- **tub_confocal**: zeiss_lsm980_proxy; confocal detector, model unreported; Plan Apochromat 63× 1.4 NA oil; {"bit_depth": 16, "zoom": 5.0, "xy_pixel_nm": 26.3, "pinhole_AU": 1, "line_average": 2, "scan_speed_setting": 10, "pixel_dwell_us": 0.42, "z_step_um": 0.3, "number_of_steps_source_literal": 52}. first
- **tub_widefield**: tie_ixon100; iXon Ultra 888 EMCCD; Plan Apochromat Lambda 100× 1.45 NA oil; {"bit_depth": 16, "xy_pixel_nm": 129.8, "z_step_um": 0.25, "number_of_steps_source_literal": 81}. after tub_confocal; same specimen and same FOV

Required analysis actions:
- Preserve paired raw stacks and sampling per modality
- Select the matching widefield PSF metadata and obtain preset DW derivative
- Register the same FOV across modalities; inspect lateral and axial views
- Compare structures and retain low-intensity discrepancies rather than declaring every sharper output true

Other boundaries: No numerical exposure, illumination power, EM gain, oil type or field-coordinate registration procedure supplied; Support slide/holder, carrier transfer and cleaning mechanics are authored


### HAP1 chromosome-16 iFISH: culture → two hybridizations → widefield

Entry: HAP1 stock identity token and separately supplied probe-lot tokens

Carrier: 22×22 mm #1.5 coverslip, VWR 631-0125; culture in CLS3506 six-well plate

1. **Place square coverslip in labeled six-well position and seed HAP1** (`seed`). Source: M64, M75. Reported settings: {"medium": "IMDM + 10% FBS"}.
   - Source gap: Seeding density, volume and growth duration unreported
2. **Incubate HAP1 culture and inspect confluency fixture** (`incubate_until`). Source: M64, M75. Reported settings: {"temperature_C": 37, "CO2_percent": 5, "target_confluency_percent_approx": 90}.
3. **Fix coverslip culture** (`exchange_incubate`). Source: M75. Reported settings: {"PBS": "1×", "paraformaldehyde_percent": 4, "duration_min": 10, "temperature": "room temperature"}.
4. **Quench unreacted fixative** (`exchange_incubate`). Source: M75. Reported settings: {"PBS": "1×", "glycine_mM": 125, "duration_min": 5, "temperature": "room temperature"}.
5. **Wash fixed sample** (`wash`). Source: M75. Reported settings: {"repeats": 3, "each_min": 5, "PBS": "1×", "Triton_X100_percent": 0.05, "temperature": "room temperature"}.
6. **Permeabilize fixed sample** (`exchange_incubate`). Source: M75. Reported settings: {"PBS": "1×", "Triton_X100_percent": 0.5, "duration_min": 20, "temperature": "room temperature"}.
7. **Wash after permeabilization** (`wash`). Source: M75. Reported settings: {"repeats": 3, "each_min": 5, "PBS": "1×", "Triton_X100_percent": 0.05, "temperature": "room temperature"}.
8. **Perform source HCl incubation** (`exchange_incubate`). Source: M75. Reported settings: {"HCl_N": 0.1, "duration_min": 5, "temperature": "room temperature"}.
9. **Wash after HCl** (`wash`). Source: M75. Reported settings: {"repeats": 2, "each_min": 5, "PBS": "1×", "Triton_X100_percent": 0.05, "temperature": "room temperature"}.
10. **Rinse in SSC** (`wash`). Source: M75. Reported settings: {"repeats": 1, "SSC": "2×", "mode": "rinse"}.
11. **Optional stored-sample branch or proceed directly** (`optional_storage`). Source: M75. Reported settings: {"SSC": "2×", "NaN3_percent": 0.05, "temperature_C": 4, "max_duration": "1 month"}.
   - Source gap: Task provides sealed prepared storage buffer; no sodium-azide handling recipe authored
12. **Pre-hybridization equilibration** (`exchange_incubate`). Source: M75. Reported settings: {"formamide_percent": 50, "SSC": "2×", "phosphate_buffer_mM": 50, "duration": "overnight", "temperature": "room temperature"}.
13. **Load pre-hybridization mix into sealed humidity chamber** (`exchange_incubate`). Source: M75. Reported settings: {"formamide_percent": 50, "SSC": "2×", "Denhardt": "5×", "sodium_phosphate_mM": 50, "EDTA_mM": 1, "salmon_sperm_DNA_source_literal_mg_ml": 100, "human_Cot1_DNA_source_literal_mg_ml": 100, "pH_range": [7.5, 8], "temperature_C": 37, "duration_h": 1}.
   - Source gap: Source reports mg/ml here and µg/ml in hybridization mix: do not normalize; use literal source-labeled task reagent token
14. **Select validated supplied chr16 probe lot and prepare primary hybridization mix** (`mix`). Source: M75. Reported settings: {"probe_dilution": "tenfold in 1.1× hybridization buffer", "stock_buffer": {"formamide_percent": 55, "SSC": "2.2×", "Denhardt": "5.5×", "sodium_phosphate_mM": 55, "EDTA_mM": 1.1, "salmon_sperm_DNA_ug_ml": 100, "human_Cot1_DNA_ug_ml": 100, "dextran_sulfate_percent": 11, "pH_range": [7.5, 8]}, "final_probe_nM_per_oligo": 0.06}.
   - Source gap: Probe production delegated by paper to prior iFISH pipeline; sequences not retained; 63 loci in methods/results versus 65 in supplement listing remains unresolved
15. **Replace pre-hybridization buffer and seal with Fixogum** (`seal_exchange`). Source: M75. Reported settings: {"sealant": "Fixogum LK071A"}.
16. **Transfer sealed carrier to denaturation station** (`incubate`). Source: M75. Reported settings: {"temperature_C": 75, "duration_s": 70}.
17. **Return carrier to sealed humidity chamber** (`incubate`). Source: M75. Reported settings: {"temperature_C": 37, "duration": "overnight"}.
18. **Rinse primary-hybridized coverslip** (`wash`). Source: M75. Reported settings: {"repeats": 1, "SSC": "2×", "Tween_percent": 0.02, "mode": "rinse"}.
19. **Transfer to warmed wash buffer** (`wash`). Source: M75. Reported settings: {"repeats": 2, "each_min": 5, "SSC": "0.2×", "Tween_percent": 0.2, "temperature_C": 60}.
20. **Quick rinse in high SSC buffer** (`wash`). Source: M75. Reported settings: {"repeats": 1, "SSC": "4×", "Tween_percent": 0.2, "mode": "quick rinse"}.
21. **Rinse in SSC** (`wash`). Source: M75. Reported settings: {"repeats": 1, "SSC": "2×", "mode": "rinse"}.
22. **Final wash before second hybridization** (`wash`). Source: M75. Reported settings: {"repeats": 1, "SSC": "2×", "formamide_percent": 25}.
   - Source gap: Duration unreported
23. **Prepare and apply secondary fluorescent oligonucleotide mix** (`mix_exchange_incubate`). Source: M75. Reported settings: {"secondary_oligo_nM_each": 20, "SSC": "2×", "formamide_percent": 25, "dextran_sulfate_percent": 10, "E_coli_tRNA_mg_ml": 1, "BSA_percent": 0.02, "temperature_C": 30, "duration": "overnight", "environment": "sealed humidity chamber"}.
24. **Wash secondary-hybridized sample** (`wash`). Source: M75. Reported settings: {"repeats": 1, "duration_h": 1, "temperature_C": 30, "SSC": "2×", "formamide_percent": 25}.
25. **Counterstain specimen** (`exchange_incubate`). Source: M75. Reported settings: {"Hoechst33342_ng_ml": 1, "SSC": "2×", "formamide_percent": 25, "temperature_C": 30, "duration_min": 30}.
26. **Final SSC washes** (`wash`). Source: M75. Reported settings: {"repeats": 2, "each_min": 5, "SSC": "2×"}.
27. **Mount square coverslip in carrier adapter** (`mount`). Source: M75. No numeric source setting supplied.
   - Source gap: Mount medium, support geometry, orientation and volume not reported

Required acquisition variants:
- **if_widefield**: tie_ixon100; iXon Ultra 888 EMCCD; CFI Plan Apochromat Lambda 100× 1.45 NA oil; {}. 
  - Unknown: Acquisition bit depth, xy sampling, z step and plane count unreported here; never borrow tubulin 81-plane settings

Required analysis actions:
- Keep four iFISH channels and nuclear identity separate
- Preserve raw and preset DW derivatives
- Compare per-nucleus/per-channel nearest neighbors at source threshold 260 nm
- Label Raw&DW, DW&Raw, Lost and New; exclude nuclei with no dots in either comparison image
- Retain FWHM/NCR outputs; upscaling to 23 nm for ED7 is display processing, not acquisition sampling

Other boundaries: Probe synthesis is a source-cited upstream input, represented as identity-checked probe lots, not invented chemistry; 51-plane boundary example is a separate data subtask, not a global iFISH acquisition setting


### SKBR3 GAPDH: culture → hybridization → widefield and detection controls

Entry: SKBR3 stock identity token, source-specific probe lots and empty authored carrier

Carrier: Source carrier shape/size unspecified; explicitly authored generic slide adapter

1. **Seed carrier and incubate SKBR3 source stock** (`seed_incubate`). Source: M64. Reported settings: {"medium": "McCoy 5A + 10% heat-inactivated FBS", "temperature_C": 37, "CO2_percent": 5}.
   - Source gap: Culture duration, carrier and seeding density unspecified
2. **Execute labeled generic fixation/permeabilization preparation card** (`authored_gap_connector`). Source: M71. No numeric source setting supplied.
   - Source gap: Paper begins detailed SKBR3 method at hybridization; no source fixation/permeabilization procedure given
3. **Verify target and fluorophore identity of supplied probe lot** (`select`). Source: M71, M73. Reported settings: {"GAPDH": "indirectly labeled probe produced through prior iFISH pipeline", "MKI67": "classical directly fluorescent-labeled probe"}.
   - Source gap: Sequence tables and probe production procedures not retained; no invented synthesis
4. **Prepare RNA hybridization mix and incubate** (`mix_exchange_incubate`). Source: M71. Reported settings: {"formamide_percent": 25, "SSC": "2×", "dextran_sulfate_percent": 10, "E_coli_tRNA_mg_ml": 1, "BSA_percent": 0.02, "vanadyl_ribonucleoside_complex_mM": 10, "temperature_C": 30, "duration_h_range": [16, 18], "environment": "humidity chamber"}.
   - Source gap: Primary probe final concentration unreported
5. **Wash after primary hybridization** (`wash`). Source: M71. Reported settings: {"repeats": 1, "formamide_percent": 25, "SSC": "2×", "temperature_C": 30, "duration_min": 30}.
6. **Apply secondary oligonucleotides where required** (`mix_exchange_incubate`). Source: M71. Reported settings: {"secondary_oligo_nM": 20, "buffer": "RNA hybridization buffer", "temperature_C": 30, "duration_h": 3, "environment": "humidity chamber"}.
7. **Wash in RNA wash buffer** (`wash`). Source: M71. Reported settings: {"repeats": 1, "buffer": "RNA wash buffer", "temperature_C": 30}.
   - Source gap: Duration unreported
8. **Counterstain with Hoechst** (`exchange_incubate`). Source: M71. Reported settings: {"SSC": "2×", "formamide_percent": 25, "Hoechst33342_ng_ml": 1.23, "temperature_C": 30, "duration_min": 30}.
9. **Select and apply source-described mounting-buffer token** (`mount`). Source: M71. Reported settings: {"SSC": "2×", "glucose_percent": 0.4, "Tris_HCl_mM": 10, "Trolox_mM": 10, "glucose_oxidase_ng_ul": 37, "catalase_source_literal_mM": 32}.
   - Source gap: Catalase unit is source-literal; not independently verified or normalized; Mount volume, support geometry and storage duration unreported

Required acquisition variants:
- **gap_widefield**: tie_zyla100; Zyla 4.2P sCMOS; CFI Plan Apochromat Lambda 100× 1.45 NA oil; {"z_span_um_range": [8, 15], "z_step_um_range": [0.2, 0.6], "control_software": "NIS Elements"}. 
  - Unknown: Exact per-stack depth/step, exposure, bit depth and xy pixel size not reported

Required analysis actions:
- Retain matching raw, DW, DL2 and Huygens preset records
- For ED6 display comparison manually choose DW intensity threshold and match raw brightest-dot count
- Separately compare Intensity and DoG detection across paired raw/DW fields; do not collapse the two tests
- Record FWHM and per-FOV counts without requiring raw counts always be lower

Other boundaries: Generic pre-hybridization preparation is authored and cannot earn source-reproduction credit; Prepared microscope/coverslip object alone is not a completion condition


### MKI67 TMA: frozen section preparation → 20× survey → matched 60× fields

Entry: Purchased 5 µm frozen TMA section token, US Biomax FMC282e; no donated-person identifying data

Carrier: Slide support not dimensioned by source; authored generic tissue-slide proxy

1. **Fix supplied frozen tissue section** (`exchange_incubate`). Source: M73. Reported settings: {"PBS": "1×", "paraformaldehyde_percent": 4, "temperature": "room temperature"}.
   - Source gap: Fixation duration unreported
2. **Rinse section twice** (`wash`). Source: M73. Reported settings: {"repeats": 2, "PBS": "1×", "temperature": "room temperature", "mode": "rinse"}.
3. **Rinse twice with ice-cold ethanol** (`wash`). Source: M73. Reported settings: {"repeats": 2, "ethanol_percent": 70, "temperature": "ice cold", "mode": "rinse"}.
4. **Incubate in ethanol** (`incubate`). Source: M73. Reported settings: {"ethanol_percent": 70, "duration_h": 3, "temperature_C": 4}.
5. **Replace ethanol with RNA wash buffer** (`exchange`). Source: M73. Reported settings: {"buffer": "RNA wash buffer"}.
6. **Verify target and fluorophore identity of supplied probe lot** (`select`). Source: M73, M71. Reported settings: {"GAPDH": "indirectly labeled probe produced through prior iFISH pipeline", "MKI67": "classical directly fluorescent-labeled probe"}.
   - Source gap: Sequence tables and probe production procedures not retained; no invented synthesis
7. **Prepare RNA hybridization mix and incubate** (`mix_exchange_incubate`). Source: M73, M71. Reported settings: {"formamide_percent": 25, "SSC": "2×", "dextran_sulfate_percent": 10, "E_coli_tRNA_mg_ml": 1, "BSA_percent": 0.02, "vanadyl_ribonucleoside_complex_mM": 10, "temperature_C": 30, "duration_h_range": [16, 18], "environment": "humidity chamber"}.
   - Source gap: Primary probe final concentration unreported
8. **Wash after primary hybridization** (`wash`). Source: M73, M71. Reported settings: {"repeats": 1, "formamide_percent": 25, "SSC": "2×", "temperature_C": 30, "duration_min": 30}.
9. **Apply secondary oligonucleotides where required** (`source_ambiguity_choice`). Source: M73, M71. Reported settings: {"secondary_oligo_nM": 20, "buffer": "RNA hybridization buffer", "temperature_C": 30, "duration_h": 3, "environment": "humidity chamber"}.
   - Source gap: MKI67 is called directly labeled, yet Methods says all steps from hybridization follow SKBR3; secondary application is ambiguous. Provide two explicitly labeled task branches, not a false single true protocol.
   - Task interpretations: direct-label interpretation: skip secondary-specific application while retaining wash/counterstain; literal inherited-steps interpretation: execute secondary stage with source ambiguity recorded
10. **Wash in RNA wash buffer** (`wash`). Source: M73, M71. Reported settings: {"repeats": 1, "buffer": "RNA wash buffer", "temperature_C": 30}.
   - Source gap: Duration unreported
11. **Counterstain with Hoechst** (`exchange_incubate`). Source: M73, M71. Reported settings: {"SSC": "2×", "formamide_percent": 25, "Hoechst33342_ng_ml": 1.23, "temperature_C": 30, "duration_min": 30}.
12. **Select and apply source-described mounting-buffer token** (`mount`). Source: M73, M71. Reported settings: {"SSC": "2×", "glucose_percent": 0.4, "Tris_HCl_mM": 10, "Trolox_mM": 10, "glucose_oxidase_ng_ul": 37, "catalase_source_literal_mM": 32}.
   - Source gap: Catalase unit is source-literal; not independently verified or normalized; Mount volume, support geometry and storage duration unreported

Required acquisition variants:
- **tis20**: tie_tissue20_proxy; not independently restated for tissue branch; CFI Plan Apo VC 20× 0.75 NA air; {"FOVs": 10}. 
  - Unknown: Camera inheritance from SKBR3 is not independently established; Stack settings and exposure unknown
- **tis60**: tie_tissue60_proxy; not independently restated for tissue branch; CFI Plan Apochromat Lambda 60× 1.4 NA oil; {"FOVs": "subset of the 20× regions"}. 
  - Unknown: Exact subset mapping supplied as authored fixture, not paper data

Required analysis actions:
- Survey 10 labeled authored FOV slots at 20× and retain matching selected 60× regions
- Use DoG dot detection, 60× nuclear masks and rescale to corresponding 20× sampling
- Review intensity/CNR plots; select local-minimum threshold where the two clouds exist
- 20× raw has a distinct tail-selection condition; do not force the same threshold logic
- Compare HQ dots against shared 60× raw/DW reference and retain translation/deformation registration metadata

Other boundaries: Ten FOVs acquired in Methods and five analyzed FOVs in figure results are distinct counts; Directly labeled MKI67 versus inherited secondary step unresolved; both task variants flagged


### GFAP brain TMA: section → bake/dewax/retrieve → stain → mosaic comparison

Entry: FFPE human cerebral-cortex TMA block token from source-described biobank-derived array

Carrier: 4 µm section cut during task; authored support slide

1. **Set section thickness and cut/place section using authored microtome proxy** (`section`). Source: M66, M78. Reported settings: {"thickness_um": 4}.
   - Source gap: Sectioning instrument and support-slide identity unspecified
2. **Transfer section to heating plate** (`incubate`). Source: M78. Reported settings: {"temperature_C": 55, "duration_min": 25}.
3. **Manually dewax section using explicit source-gap task card** (`authored_gap_connector`). Source: M78. Reported settings: {"operation": "manual dewaxing reported"}.
   - Source gap: Solvent identity, sequence and durations absent
4. **Load pressure-cooker proxy and run epitope retrieval** (`exchange_incubate`). Source: M78. Reported settings: {"buffer": "citrate pH 6", "instrument": "Bio SB TintoRetriever", "temperature_C_range": [114, 121], "duration_min": 20}.
   - Source gap: Ramp, cool-down, vessel fill and pressure settings absent; authored safe locked preset
5. **Prepare primary GFAP antibody in TNB and apply** (`mix_exchange_incubate`). Source: M78. Reported settings: {"antibody": "AMAb91033", "dilution": "1:500 vol/vol", "TNB": {"Tris_HCl_M": 0.1, "NaCl_M": 0.15, "blocking_reagent_percent": 0.5, "pH": 7.5}, "duration": "overnight", "temperature_C": 4}.
6. **Apply secondary AF555 antibody and DAPI** (`mix_exchange_incubate`). Source: M78. Reported settings: {"antibody": "A-21424", "dilution": "1:800 vol/vol", "buffer": "TNB + DAPI", "duration_min": 90, "temperature": "room temperature"}.
   - Source gap: DAPI concentration and intervening wash steps unspecified
7. **Mount stained section in Fluoromount-G** (`mount`). Source: M78. Reported settings: {"medium": "Fluoromount-G"}.
   - Source gap: Volume and cure time unreported

Required acquisition variants:
- **g60**: tie_zyla60_proxy; Zyla 4.2P sCMOS; CFI Plan Apochromat Lambda 60× 1.4 NA oil; {"bit_depth": 16, "z_step_um": 0.25, "number_of_steps_source_literal": 41, "mosaic": [4, 4], "overlap_percent": 10}. 
- **g63**: leica_sp8_proxy; confocal detector, source gain 10 V; HC PL APO 63× 1.40 oil CS2; {"bit_depth": 16, "zoom": 1.4, "pinhole_AU": 1, "line_average": 4, "z_step_um": 0.25, "number_of_steps_source_literal": 61, "antibody_detector_gain_V": 10, "mosaic": [4, 4], "overlap_percent": 10}. 
- **g100**: tie_gfap100_caption_proxy; unknown in caption-supported variant; 100× 1.45 NA oil; {}. 
  - Unknown: No inheritance of camera, 41 planes or 60× sampling permitted

Required analysis actions:
- Acquire same ROI mosaic on 60× widefield and 63× confocal; either order is allowed
- Create separate 100× comparison branch with unknown settings labeled task presets
- Preserve raw/DW/DL2 comparisons and axial views
- Record structural agreement and loss of low-intensity details as separate observations

Other boundaries: Paper does not order GFAP confocal before widefield; do not import tubulin chronology; 100× caption variant distinct from Methods 60× variant


### Nup153 nuclear pores: immunolabel → STED → confocal

Entry: Source-literal PtK2 identity token with unresolved species label; no live biological material instantiated

Carrier: Source carrier unspecified; authored generic slide proxy

1. **Read unresolved source identity/fluorophore warning and register task specimen** (`source_ambiguity_choice`). Source: M82. Reported settings: {"source_wording": "human PtK2", "identity_resolution": null}.
   - Source gap: Human/PtK2 labeling and secondary versus Oregon Green fluorophore wording conflict; do not resolve by guess
2. **Run explicit generic preparation card for source-unreported culture/fixation/permeabilization** (`authored_gap_connector`). Source: M82. No numeric source setting supplied.
   - Source gap: No upstream cell culture, fixation, permeabilization, block or mounting recipe provided
3. **Apply reported Nup153 primary** (`exchange_incubate`). Source: M82. Reported settings: {"antibody": "ab24700", "concentration_ug_ml": 1}.
   - Source gap: Dwell, temperature and buffer unreported
4. **Apply reported goat anti-mouse IgG secondary** (`exchange_incubate`). Source: M82. Reported settings: {"antibody": "ST635P-1002-500UG", "dilution": "1:400"}.
   - Source gap: Dwell, temperature, washes and fluorescence compatibility unresolved
5. **Mount task specimen with authored medium token** (`mount`). Source: M82. No numeric source setting supplied.
   - Source gap: Source mounting medium and geometry unreported

Required acquisition variants:
- **p_sted**: leica_sp8_3x_sted_proxy; Leica Hybrid Detectors; HC PL APO 100×/1.40 OIL STED WHITE; {"excitation_nm": 490, "depletion_nm": 592, "depletion_mode": "continuous wave", "pinhole_AU": 0.9, "frame_pixels": [1024, 1024], "line_rate_Hz": 200, "line_average": 4, "pixel_nm": 25, "filters": "dichroic plus notch STED filter"}. first; source-literal preset channel, compatibility unresolved
- **p_confocal**: leica_sp8_3x_sted_proxy; Leica Hybrid Detectors; HC PL APO 100×/1.40 OIL STED WHITE; {"line_rate_Hz": 1000}. thereafter, same specimen
  - Unknown: Do not assume STED 25 nm sampling applies to confocal

Required analysis actions:
- Keep STED-first and thereafter-confocal acquisitions linked to one specimen
- Compare raw/Huygens/DW results with correct modality-specific PSF card
- Keep widefield Born-Wolf, confocal and STED PSF choices distinct
- Report unresolved physical fluorescence compatibility; task preset is not experimental validation

Other boundaries: This branch is fully represented as an authored task with explicit source-gap stages, not represented as a complete physical protocol; No assertion that the contradictory source fluorophore identifiers are experimentally compatible


## Source-data workstation branches
These are data-entry tasks because this paper reused or generated the inputs computationally. Inventing new wet-lab preparation for them would change the paper. Operator actions remain concrete selection, comparison, annotation, parameter and lineage tasks with preset outputs.


### Compare deconvolution tools on source-described benchmark inputs
Inputs: synthetic microtubule reference; synthetic hollow bar reference; external C. elegans whole-embryo reference

1. Select source-matched raw/truth pair; preserve identity
2. Choose DW SHB versus unaccelerated RL iteration series
3. Compare DW, DL2, Huygens and RedLionfish preset results without executing proprietary software
4. Inspect MSE-versus-iteration and time records with hardware context
5. Use wrap boundary assumption only on source synthetic inputs identified as wrapped
Sources: R_BENCH, ED1, SIN4. Boundaries: No real input arrays, executable comparisons or timing measurements supplied here


### Compare PSF calculator versus PSF Generator
Inputs: ChrX-36plex PSF-comparison source token

1. Verify 36plex identity, distinct from 46plex tracing data
2. Select two PSF-method cards with all other DW parameters held equal
3. Link raw to both preset derivatives
4. Compare dot FWHM/PSF displays
5. Record main Lanczos-3 versus SI Lanczos-5 discrepancy without silently choosing
Sources: R_BENCH, M87, SI1, SIN13. Boundaries: Full optical metadata and original image arrays not retained


### Handle lateral and axial boundary comparisons
Inputs: external embryo stack; HAP1 Hoechst boundary-example stack with 51 planes

1. Select original and derived cropped copies; preserve raw full stack
2. Split embryo into four cuboids for lateral comparison
3. Create distinct HAP1 derivative after removing bottom 12 planes for Fig. 2 comparison
4. Select DW versus DL2 boundary/padding/apodization presets
5. Inspect lateral/axial profiles and label crops; never treat crop as sample removal
Sources: R_BENCH, ED2, SI2, SIN4. Boundaries: Connection between boundary-example HAP1 specimen and iFISH specimen not established; no forced same-sample link


### Inspect dot-density/noise simulation comparisons through preset outputs
Inputs: authored stand-ins for source synthetic truth/noisy widefield/confocal conditions

1. Choose declared density/noise condition
2. Keep truth separate from observed noisy input
3. Choose widefield/confocal and DW/DL2 derivative records
4. Compare detection overlap against truth and inspect MSE
5. Tag source synthetic result as best-case matched-PSF condition; do not present as empirical specimen result
Sources: M97, R_FISH, ED4, SI56. Boundaries: No optical simulation implemented; all task observations are presets


### Process reused ISST dataset without inventing new wet-lab preparation
Inputs: previously generated 120-gene middle-temporal-gyrus image dataset token

1. Import raw cycle/FOV/channel lineage
2. Select raw and preset DW branches
3. Align cycles and stitch FOVs using operator workstation cards
4. Select FindSpots masking radius 15 and compare threshold sweep
5. Record source selected normalized threshold 2% and decode assigned versus improper barcode outputs
6. Compare cell-typing results for 18 types with identical underlying cell inventory
Sources: M105, R_ISST, ED10. Boundaries: Raw images and gene table absent; preset data token only; This paper reused images, so no new ISST wet-lab protocol is invented


### Inspect reused ChrX-46plex decoding and tracing comparisons
Inputs: ChrX-46plex O-eLIT source dataset token; seven replicate dataset slots

1. Keep five imaging/sequencing cycles in source data lineage
2. Select raw, NIS and DW derivatives
3. Manually match nucleus-pair records using fixture identification cues; source reports 168 nuclei
4. Run two-tier every-pixel analysis card on the paired dataset tokens
5. Inspect tracing nodes and interpolation flags
6. Compare contact maps against linked Hi-C reference
7. Keep seven biological replicate datasets distinct from 1,000 bootstrap resamples
Sources: M107, R_OLIGO, R_ISST, ED10. Boundaries: No upstream OligoFISSEQ probe production or sequencing procedure invented; 168 match operations may be task-batched with coverage record, never claimed as observed here


### Inspect downloaded raw image against a published RLN screenshot comparator
Inputs: external U-2 OS mitochondria/actin/tubulin raw token; published RLN screenshot-reference token

1. Keep this external U-2 OS sample separate from in-paper alpha-tubulin specimen
2. Prepare visualization-only derivative in image-viewer card
3. Select DW 50-iteration preset derivative
4. Inspect paired zoom regions
5. Mark comparator as screenshot from published figure, not rerun RLN
Sources: SI9. Boundaries: No screenshot or raw image redistributed; task uses authored stand-ins


## Concrete field and material fixtures

The task uses shared `TUB_F1` for the two tubulin modalities; a 4×4 `GFAP_RxCy` map for the 60×/63× mosaics; `TIS_F1`–`TIS_F10` for the 20× survey and an explicitly authored F1–F5 matched 60× subset; and paired `PORE_F1` for STED/confocal. Two GAPDH fields and one iFISH field are workload choices, not original paper sample counts. These field IDs and categorical landmarks are authored, while source pairing requirements remain independently bound.

Task aliquots are discrete material tokens without inferred microliter volumes. Mixture cards carry source concentrations, and the agent must select the right components and transfer their tokens. This does not pretend to solve source-unreported dilution volumes. Source “number of steps” values remain labeled that way; any controller plane/interval interpretation is an explicit adapter choice.

## Recovery and terminal state

Wrong carrier before use can be returned; wrong reagent after dispensing invalidates the specimen lineage and requires a new branch specimen. Missing washes can be completed before the next stage. Focus, field, saturation and mounting faults require inspection and reacquisition. Source-unspecified interruption tolerance is an authored rule, not a biological stability claim. Failed attempts remain visible. The agent cannot repair errors by renaming samples or overwriting records.

The terminal world state has all required raw/comparison manifests, archived specimens with locations, no active acquisition, empty stages, closed shutters, parked/retracted objectives, closed reagents, accounted-for waste and returned tools. Branch outcomes report source facts, task choices and unresolved facts separately.

## Delivery boundary

Completed here: paper-level task design, all retained manual branches accounted for, preparation actions expanded, detailed asset reuse bound, independent evaluator reference separated, output/recovery contracts specified, and ordinary file/schema/reference checks performed. Not completed here: a runtime, new detailed meshes, pixel fixtures, embodied playthrough, physical experiments or scientific replication. No source or prior task files were changed, and no main repository Git operation was performed.
