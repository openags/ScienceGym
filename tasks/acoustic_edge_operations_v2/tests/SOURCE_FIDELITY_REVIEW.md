# Independent source and contract review

Review date: 2026-10-03. Scope: retained lawful main-article reader records, the five-page supplementary text and local supplementary page rendering, followed by independent read-only review of this package’s source and operation contracts. No new main-source retrieval was attempted. Test implementation was not independently reviewed.

## Source findings retained

- All seven physical acquisitions are supported: two frequency-response conditions, three aluminium 1D objects and two 2D objects
- The 10-mm rod dimension is a width, not a supplied cylinder diameter
- Fig. 2c is measured modal amplitude data, not an experimentally measured transmission matrix
- Physical 2D stepping is 1.6 mm; 0.8-mm interpolation and normalized display clipping are derived display operations
- Only an upper-half disc image is shown; historical full-disc acquisition remains unknown
- Rod apparent-size bias, ETH lower-T-stem loss and possible reflection artifacts remain limitations
- Main/SI directional, coordinate, spectral-range, summation, element-mapping and scattering-matrix conventions require explicit resolution
- The SI remains numerical/theoretical coverage, with no executable solver or silently repaired equations

## Contract findings addressed

1. Separate manufactured and supplied-target routes now prevent invented machining history
2. Manufactured targets are released at the preparation station before transport to inspection
3. Calibration is qualified in situ at the rig with a transported standard; no tethered-rig transfer is implied
4. Calibration recipes are inputs; raw standard observations and correction results are generated outputs
5. Actor goal inputs include shared fabrication/motion cards and applicable directional-resolution cards
6. Schedule references use consistent field names; scan-only fields are conditional and do not force sweep branches to invent a raster
7. Blocked or failed setup can archive and close without inventing source-enable or acquisition events
8. Raw/blocked-work archival does not require an unavailable scientific-analysis recipe
9. No-object handling and closure do not require a fictional target
10. All eight source conflicts are retained with physical/numerical applicability; published outcomes remain author/evaluator context

The focused recheck confirmed the principal fixes as coherent, then requested the final conditional scan-card and archival-gate clarifications, which were implemented and given regression tests. No major source drift was found. Acceptance is limited to a source-bounded design: no execution, replication, geometry, calibration or runtime-enforcement readiness is asserted. Parent release review remains required.
