# Deconwolf: a paper-wide task design from preparation through imaging and cleanup

## Scope of this package

This package converts the **existing Deconwolf source paper in the frozen collection** into a paper-wide task family. It adds no newly read paper to the count. It covers six physical preparation/imaging branches and seven data-comparison branches that begin with existing images. It is not limited to transporting a finished slide, and the different specimens are not treated as one continuous experiment.

**Completed: task design and structured specifications. Not supplied: a runnable environment, preset microscopy image pixels, real experiments or physical simulation.** Scientific outputs are currently conditional semantic contracts. Preset images can be connected later without first developing optical or biological process models.

See [TASK_DESIGN.md](TASK_DESIGN.md) for detailed parameters, source locators and the technical specification. This guide is a reading entry point, not a real laboratory SOP.

## Six physical action sequences

All sequences include reading labels, locating materials, opening containers, selecting the correct reagent, loading a fresh tip, transferring or exchanging liquid, recording specimen identity, closing containers, placing them in a transport tray and moving to the next station. Virtual timers represent waiting; chemical and biological outcomes are not physically computed.

### 1. U-2 OS / tubulin

Select an **18 mm round coverslip** and the cell source → place in a culture vessel and seed → culture → fix → permeabilize → block → primary antibody → successive washes → block again → AF555 secondary antibody and DAPI → successive washes → mount with Prolong Gold → close the tray and transport to the Zeiss confocal proxy station → load, locate the field, focus, set parameters and acquire → unload and transfer to the Ti-E / iXon / 100× station → relocate the **same specimen and field** and acquire → save raw data and comparison records → unload, archive and clean up.

Key controls: **confocal precedes widefield**; the round coverslip cannot be replaced by HAP1's square coverslip; each modality retains its own sampling parameters.

### 2. HAP1 / chr16 iFISH

Select a **22×22 mm square coverslip and a six-well plate** → seed and culture to the source-described state → fix → quench → three washes → permeabilize → three washes → source-described acid treatment → two washes and an SSC rinse → choose immediate continuation or the source-permitted storage branch → prehybridization equilibration → prehybridization → select the correct probe lot and prepare the task mixture → exchange to the main hybridization solution and seal with Fixogum → heat treatment → main hybridization → rinse and successive warm washes → second fluorescent-oligonucleotide hybridization → wash, stain with Hoechst and final wash → mount → transport to Ti-E / iXon / 100× → locate the field, focus and acquire separate channels → preserve raw/DW correspondence and nuclear identities → unload, archive and clean up.

Key controls: the culture plate is a preparation vessel; do not treat the entire six-well plate as the source imaging carrier. The **51-plane HAP1 images** in the boundary comparison are not universal settings for all iFISH acquisitions.

### 3. SKBR3 / GAPDH smFISH

Cell source, medium and task carrier → culture → execute an **explicitly benchmark-authored upstream preparation card** bridging fixation/permeabilization details absent from the source → select the GAPDH probe → prepare the mixture and perform main hybridization → wash → fluorescent secondary-oligonucleotide hybridization → wash and Hoechst staining → source-identified mounting-medium task prop → mount and transport to Ti-E / Zyla / 100× → locate the field, focus, configure the z-stack and acquire → inspect separate Intensity and DoG raw/DW comparisons → unload, archive and clean up.

Key controls: do not substitute iXon. Intensity and DoG are separate comparison conditions; more detected spots is not a universal criterion for improvement. Unreported preparation details are not presented as source facts.

### 4. MKI67 / frozen TMA

Begin with the source's purchased **5 µm frozen tissue sections** → fix → two PBS rinses → two ice-cold ethanol rinses and incubation → exchange liquid for rehydration → probe/hybridization operations → wash, stain and mount → transport to the 20× air-objective station → locate and acquire ten task fields individually → switch to the 60× oil-objective configuration and relocate the designated subset → save matching records → inspect DoG, CNR, threshold and high-quality-spot comparisons → unload, archive and clean up.

Key controls: the source describes MKI67 as directly fluorescently labeled but also inherits the SKBR3 post-hybridization steps. The task therefore offers labeled **direct-label interpretation** and **literal-inheritance interpretation** branches without claiming to resolve that ambiguity. Ten acquired fields and five analyzed fields in the figure are different counts.

### 5. GFAP / FFPE brain-tissue TMA

Start from an FFPE TMA block → set thickness and section with the sectioning proxy → bake the slides → execute the dewaxing task card whose details are not expanded in the source → antigen-retrieval proxy station → prepare TNB/primary antibody and incubate → AF555 secondary antibody and DAPI → mount with Fluoromount-G → transport and load → use Zyla / 60× and Leica / 63× to locate the same ROI for a **4×4 mosaic with 10% overlap** → separately complete the caption-supported 100× comparison branch → preserve raw/DW/DL2, axial and low-intensity differences → unload, archive and clean up.

Key controls: do not copy the 60× camera and plane count directly to 100×. The source does not require confocal-first acquisition for GFAP; the tubulin ordering rule does not apply here.

### 6. Nup153 / nuclear pores

Read the source-species/dye conflict card first → create a clearly labeled task specimen → execute the upstream preparation task card absent from the source → select the source Nup153 primary and secondary antibodies and complete task processing → mount through a benchmark-authored bridging card → transport to a **separate Leica STED proxy station** → set source-supported optical and acquisition conditions → acquire STED → then acquire confocal → inspect modality-specific PSFs and raw/Huygens/DW comparisons → unload, archive and clean up.

Key controls: preserve the source's conflicting “human PtK2” and secondary-antibody/Oregon Green descriptions. Preset views do not establish real dye/wavelength compatibility. This branch is not a complete, reliable real-world recipe.

## Agent initial state and goal

- Initial state: at receiving, with empty tools; cell/tissue sources, reagents, probe lots and empty carriers are separately labeled. Microscopes are unloaded, unfocused and have not acquired data. Necessary upstream resources enter at the source's actual starting point, such as purchased frozen sections or probe lots produced by referenced prior methods
- Actions: move the base to a station, grasp/place, open/close, transfer/exchange liquid, mix, time, mount/clamp, set optical controls, focus and locate using previews, acquire/save, unload and clean up
- Goal: complete the corresponding preparation and imaging branch, save traceable raw and comparison records, archive specimens and return stations to a safe idle state. The paper-wide long task requires all physical and data branches; tubulin alone does not stand for the whole paper
- The agent may read `initialstate.json`, `agentgoal.json` and source-parameter/unknown cards. The separate `evaluator_reference.json` is withheld from the agent

## Acceptance

Acceptance reads trusted environment events, not an agent-written passed=true flag. It must verify each material transfer, wash count, timer, carrier identity, microscope configuration, field pairing and raw-data parent–child relationship. Raw data is immutable; postprocessed outputs must have a genuine task acquisition/import record as their parent.

Nominal outputs appear only when preparation state, loading, focus, field and parameters satisfy their requirements. Wrong channels, defocus, overexposure, wrong fields and bubbles produce distinct **benchmark-preset** feedback. A specimen failed by the wrong reagent cannot recover through renaming; preserve the failure record and restart with a new specimen identity.

Cleanup requires an archived specimen location, no specimen awaiting unloading, stopped acquisition, closed shutters, objectives in loading/parking configuration, sealed reagents, accounted-for waste liquid/tips and returned tools.

## Source unknowns, asset substitutions and boundaries

- Bind available source parameters individually; retain unavailable values as unknown. Explicitly labeled bridging operations connect the task. **Unreported volumes, times and culture conditions are not invented as paper facts**
- Preserve the literal source and conflict labels for questionable 32 mM catalase, iFISH concentration-unit differences, 63/65 loci, Lanczos-3/5 and other discrepancies; they are not real-SOP recommendations
- The full workspace reuses detailed Ti-E, iXon, Zyla, coverslip and six-well-plate assets. Missing objective variants, Leica/Zeiss instruments, pipettes, mobile bases and other components carry explicit proxy labels; no newly completed detailed models are claimed. Referenced assets are absent from this task-only public snapshot
- The seven data branches include software benchmarks, PSF, boundary, synthetic spots, ISST, OligoFISSEQ and RLN comparisons. They begin with existing/computed images in the original paper, so no new wet experiments are invented
- `preset_output_contract.json` currently supplies **conditions and semantic outputs**, not microscopy pixels. This package is not a runnable simulation or completed experiment

The next implementation step can select one branch for interaction development while retaining the other paper-wide designs. There is no need to return to a phase limited to counting papers or building more tools.
