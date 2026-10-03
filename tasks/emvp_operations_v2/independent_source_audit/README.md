# Independent EmVP source audit

The main article and primary SI support a broad, source-bounded physical task family. They do not provide a turnkey replication package. This audit checks source coverage and scientific provenance; it does not validate robot implementation, experiments or numerical simulation.

## High-impact findings

- SI Fig2 visually supplies R805 levels 2, 4, 8 and 12 percent. The main text identifies the loading comparison as Mat2. The full recipe basis and allocation remain qualified inputs.
- SI Fig4 visually supplies straight-channel diameters 2.00, 1.50, 1.00, 0.50 and 0.30 mm, all 4 mm long. This still does not provide full CAD.
- Neither pure-VAM resolution-control caption explicitly assigns a resin. Selecting Mat2 is an authored choice, not a verified historical material mapping. Mandatory CT was removed from the SI Fig4 control after review; any later addition would be an authored characterization extension.
- Gelation values 59.8/64.7 s start at measurement acquisition; illumination starts at 30 s. Keep both clocks.
- Source recovery values are Mat1 4.7 s and Mat2 1.7 s. The Fig4 panel/caption mapping is d=Mat1 and e=Mat2; a prose panel reference conflicts.
- SI Table1 chip names and Fig3 panel labels conflict. The two timing rows must remain unresolved rather than silently swapped. Table1 times cover printing stages, not washing or postcuring.
- Cast tensile samples and printed hardness samples are different specimen families. Four hardness sites do not establish four specimens.
- Acetone amount/fate and CQ/EDAB percentage interpretation remain genuine recipe gaps.

## Coverage and boundaries

The structured audit covers all physical Methods, main Figs1-4, SI Figs1-11, Table1 timing, and the boundaries around SI Fig12 simulation and Table2 comparison. It records material mappings, clocks, source conflicts, geometry gaps and source-specific findings.

Full 18-page visual review is documented in the source preflight. This independent audit re-read the relevant main/SI text and visually rechecked main p6 and SI pp4-5. Source PDFs, extracted text and images are absent from this audit directory. No new download or third-party code execution was performed. Parallel authorship continued; the JSON includes hashes of the design files reviewed rather than implying an audit of every later revision.

Source: Tisato et al., *Nature Communications* 16, 6730 (2025), [DOI 10.1038/s41467-025-62057-6](https://doi.org/10.1038/s41467-025-62057-6). Article and primary SI are available under CC BY 4.0, subject to credit-line exceptions. This is independently authored analysis, with no source figure reproduction.

## Final targeted recheck

The final design incorporates both figure-only lists with appropriate gates, explicitly labels both pure-VAM material choices as authored, removes mandatory CT from the pure-VAM negative control, and separates the three cage-comparison routes. The conflict register retains the source ambiguities. No remaining substantive source-grounding defect was identified. Unresolved source omissions still prevent a turnkey execution or exact-replication claim.
