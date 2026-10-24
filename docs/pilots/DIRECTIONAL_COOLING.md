# Directional cooling reconstruction pilot

This pilot revises Bhatia et al., *Passive directional sub-ambient daytime radiative cooling*, Nature Communications 9, 5001 (2018), [DOI 10.1038/s41467-018-07293-9](https://doi.org/10.1038/s41467-018-07293-9). It is the first application of the paper-to-robot workflow and equipment reconstruction standard to an existing ScienceGym family. The historical `directional_cooling_operations_v2` task and `cooling_scene_assets_v1` assets retain their original records.

## Selection

The existing 44-family index was inspected. Directional cooling was selected for a complete, locally obtainable eight-page article and 25-page supplement; explicit dimensions and apparatus photographs; named commercial instruments; and a varied physical program spanning fabrication, coating, thin-film assembly, calibration, spectroscopy, outdoor paired measurements, configuration changes and cleanup. The publisher lists no experiment movie dependency. Historical raw measurements are author-request-only and are not available for exact reanalysis.

The pilot represents the entire reported physical program, with theoretical modeling and proposed applications classified separately. Its sample and weather conditions cannot be reduced to one favorable demonstration. New robot handling and missing manufacturing details are reconstructed choices with explicit provenance, rather than additional source claims.

## Work and acceptance

1. Reinspect the article, all supplement text and all experimental figures; save source identities, byte hashes, locators and discrepancies.
2. Reconstruct physical operations from starting stock through every experimental branch, with resource allocation, state transitions, observations, recovery and final disposition.
3. Identify instruments and accessories separately; inspect official manuals, product images, dimensional resources and available CAD before geometry authoring.
4. Build a revised metric apparatus and device assets, with removable/movable parts and operation-to-part bindings. Compare source and reconstructed views.
5. Validate package structure and causal walkthroughs, exercise meaningful negative cases, review visual evidence and retain separate design, geometry and execution decisions.

## Initial findings from renewed source inspection

- The supplement's apparatus drawing includes a 30.5 cm frame span that was absent from the earlier material card. Its measurement endpoints must be recorded rather than treated as every base dimension.
- The rooftop photograph shows paired apparatus, individual foil-covered bases and support stands, a separate protected DAQ enclosure, ambient radiation shield and weather station. They are distinct physical objects.
- The thermal-map illustration supplies sensor surface/radial relationships, although exact attachment coordinates and tolerances are not manufacturing specifications. Those relationships can support explicit inferred placement instead of a disconnected probe rack.
- The source identifies the Cary 5000 with DRA-2500, Nicolet 6700 with PIKE IntegratIR and separate angular accessories, USB-TC, Keithley 2000 and 2425, Thermo A25, EKO instruments and HOBO U30. Generic optical and logger consoles lose those identities and interfaces.
- The source retains a nominal 15 cm reflector height in text and a 10 cm dimension in the supplement drawing. The revised reconstruction must name its selected datum/geometry and preserve the unresolved historical discrepancy.

Review of this pilot does not certify the other 43 families. Dataset totals must count this as a revision of the existing cooling DOI, not a new paper.

## Reviewable implementation

The [v3 task package](../../tasks/directional_cooling_operations_v3/README.md)
contains 64 operation definitions, 352 observable reference steps, all 11 physical
branch definitions, source/inference records and a fixture-dependent 365-occurrence
symbolic walkthrough. The [v2 asset revision](../../assets/cooling_scene_assets_v2/README.md)
contains editable metric geometry, a GLB export, named parts and inspection renders.
The [conversion review](../../tasks/directional_cooling_operations_v3/review.json)
and [visual review](../../assets/cooling_scene_assets_v2/VISUAL_REVIEW.md) retain open
gates; this is an initial review revision, not an accepted gold-standard release.

## Current focus

The pilot is being polished as one complete paper-derived manipulation task chain.
The [manipulation dossier](../../tasks/directional_cooling_operations_v3/MANIPULATION_REVIEW.md)
shows all 200 manual steps alongside the experimental conditions and checks that
connect them. Each manual step identifies its object/interface, tool, retained
support, observable completion and recovery. Scientific-result agreement and
robot execution are separate validation questions.

The October 17 pass corrects calibration preparation and terminal compatibility,
angular reference ordering, apparatus disassembly/reassembly and thermal-map
probe placement. Source-based terminal geometry now uses exact numbered pin IDs;
the fixed-band variant has two nominal 50 micrometre LDPE layers. Remaining
interface gaps are itemized, and the earlier review remains preserved.

The October 19 contact workbench adds robot records for
six rigid layers, a prebonded two-film cover, a full-length cabled RTD, physical
multimeter button actuation, 241 installed-reflector adjustments and a cabled
source-meter plug. The [visual workbench](../../simulation/cooling_v1/sample.html)
shows the full recordings and links their evidence. Its
[reproduction instructions](../../simulation/cooling_v1/README.md) include the
local server and lossless trace archives. Keithley 2000/2425, Omega P-M RTD and
KHR-2/2-P assets have separate source, part, interface and geometry records.

The cover record is rejected by the added triangle/solid audit: its earlier
force/position checks missed film penetration into the PE tube. The other
records establish bounded physical capabilities. The complete seven-layer
candidate, frame and film preparation, paired apparatus, station handoffs and
remaining instrument work still require acceptance. No complete branch or new
paper is counted from these records.
