# Seven layers: continuous assembly and reverse recovery

Two initial arm states each complete 456.150 simulated seconds in one
persistent MuJoCo world. Both exact recordings pass 192 independent checks.
The sequence includes 13 rigid transfers, two flexible-cover transfers and
six bound paper steps: BASE.03, EMITTER.02, EMITTER.03, SHIELD.02, SHIELD.03 and
SHIELD.04. Each step receipt pins its before/after physical state, object
instances, preceding receipt and source inputs.

The nominal [execution](runs/selected_assembly/result.json),
[independent verification](runs/selected_assembly/verification.json) and
[second initial state](runs/selected_assembly_tests/seed_1/verification.json)
retain their complete source snapshots. The lossless trace shards preserve
the original NPZ byte stream and execution hash, without resampling.

The two 16 µm membranes use the declared elastic model and permanent edge
bonds. The selected 1 ms solver converges on every step; the nominal maximum
is 1,612 of 3,200 allowed iterations, with no warnings. Every saved membrane
edge remains below the 1% strain limit; the nominal maximum is 0.7834%.
All 91,236 saved states per recording pass the independent triangle/solid
audit with a 0.1 mm intersection tolerance. This does not certify extrema
between saved states or measured material properties.

The source-sized aperture is supported by the shield rather than the film.
Selected 9 mm fixture shims provide clearance. Explicit finite contact pairs
for the 1 mm aperture and 0.5 mm emitter prevent the regularized grasp creep
seen in development trials. Geometry, friction coefficients, force limits
and failed earlier attempts remain recorded.

The first verification incorrectly assumed that MuJoCo kept the XML ordering
of the two geoms in each contact pair. The compiler canonicalizes that order.
The corrected verifier identifies both body orderings and checks the same
pair counts, friction, impedance, reference time and six contact dimensions.
The original failed receipts are retained in each recording's
`verification_history/before_pair_order_correction.json`.

The [chaptered playback](runs/selected_assembly/playback_manifest.json)
presents the entire recorded interval. Presentation checks are separate from
physical acceptance. The earlier isolated cover attempt remains rejected and
is preserved for comparison; acceptance belongs to these exact new episodes.

These records start with prebuilt frames and prebonded sheets. They do not
qualify fabrication, bonding, paired apparatus construction, sensor leads,
optical workflows, tool exchange or continuity between workstations. The
controller uses simulator observations. Whole-paper acceptance remains 0/11.

```bash
python simulation/cooling_v1/verify_selected_assembly.py simulation/cooling_v1/runs/selected_assembly
python simulation/cooling_v1/verify_selected_assembly.py simulation/cooling_v1/runs/selected_assembly_tests/seed_1
python simulation/cooling_v1/verify_playback.py simulation/cooling_v1/runs/selected_assembly
```
