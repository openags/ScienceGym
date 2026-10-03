# Whole-paper task design

## Purpose and evidence boundary

This original ScienceGym package converts the reported physical experimental program into reviewable robot-and-service contracts. It is neither a laboratory recipe nor a robot controller. Its scope is the full main article and textual Supplementary Information of DOI 10.1038/s41467-023-41170-4, including preparation and all reported physical families. The inspected source audit covers five main figures, twelve supplementary figures and two parameter tables. Eight movie descriptions were read, but the movie files, raw-data workbook and original modeling code were not inspected. Exact movie trajectories and transient timing remain unresolved.

There are 76 reusable operation definitions, 32 physical branches, six numerical/analytical dispositions, 19 unknown-input gates, 24 supported-transport contracts and seven loop types. These are authored design subdivisions. They are not sample counts, independent experiments or completed trials.

## How to read the contracts

Each operation states its actor, physical objects, station/port, required before-state, actions, observable after-state, failure response, source locator, authored translation and unresolved gates. Object identity and version are mandatory. An operation list is branch membership, not historical chronology. Individual occurrences additionally bind campaign, condition, specimen, cycle and attempt. Repeated moves or observations cannot collapse into a single record.

The source establishes material families and reported tests. It does not establish robot grasps, carrier design, safe loading geometry, calibration validity, fixture tolerances or complete service settings. Those are authored interfaces or unresolved qualified inputs. Scale bars and symbolic hinge cross sections are not manufacturing drawings.

## Preparation and custody

1. Bind the authorized work order, nonempty condition schedule, independent-sample allocation, cycle scope and retry limits
2. Verify supported carriers, containment, identifiers, destination docks and qualified route cards
3. Exchange closed materials with the resin-preparation service. Preserve reagent-lot to resin-batch lineage and obtain actual batch release and cleanup receipts
4. Bind resin, CAD/material-map and build-carrier revisions to a qualified grayscale print job. Require current pre-print radiometer qualification
5. Keep guards closed during printing and obtain safe-to-exchange output receipts. Generic washing or post-curing is not supplied. The low-cure organogel is integral to the demonstrated behavior and additional UV can deactivate it
6. Inspect each released specimen under qualified geometry/material criteria. Record rejection as faithfully as acceptance
7. Allocate destructive tensile coupons before scheduling repeated or shape-morphing work. Sibling coupons inherit batch provenance, not each other's identity or history

Safe transfer requires support, retained payload, a valid origin release, a ready destination and no live tether. A location label alone does not move an object. Damaged, hot, loaded, leaking or electrically connected payloads cannot be treated as ordinary return-to-storage objects.

## Physical branch families

### Materials and model-supporting measurements

- RESIN_BATCH and FABRICATE cover primary preparation, grayscale fabrication, release, inspection and allocation
- TENSILE_RT and TENSILE_HOT cover material-class comparisons at room and elevated temperature. Coupon geometry, gauge conversion, stop criteria and safe fixtures remain qualified-service inputs. The elevated-temperature source axis is printed in kPa; it must not be silently rewritten
- DMA_SWEEP covers temperature-dependent storage modulus and loss tangent
- DMA_IDENTIFICATION covers measured multi-temperature/multi-frequency data. The reported temperature grid is retained, but the exact frequency list and amplitude are unresolved
- STRAIN_RATE covers measured rate-dependent B1/B2 tensile data, separate from the later constitutive fits
- MEMORY_HOT and MEMORY_COLD preserve source-known specimen temperatures, strain, rate and hold context. These values do not supply a complete safe device program and do not automatically apply to geometric demonstrations
- MEMORY_VISUAL and MEMORY_TEN_CYCLES separately cover staged visual recovery and ten-cycle material histories. The latter does not silently inherit a complete hot/cold recipe from another figure
- B1_FIXITY_SERIES explicitly allocates homogeneous B1 specimens for fixed-strain versus programming-strain data. It cannot be replaced by composite hinge-angle measurements or fitted predictions

### Hinge and shape families

- GRADED_STRIP and GRADED_MIDDLE separate staged end recovery from elastic stretching of the soft middle. The source does not establish that every photograph shares a single historical specimen
- GRADED_LATTICE records compression, unloaded state and staged recovery. The inconsistent source layer naming is preserved as a conflict
- HINGE_ANGLE_FORCE retains the composite-hinge angle and force subseries. Five experimental results support the angle error bars only; no universal independent-specimen count is inferred
- HINGE_FORTY_CYCLES requires a retained forty-cycle H13 history. Five checkpoint photographs cannot substitute for all forty program/release/recovery/integrity records
- MODULAR_STRIPS and HELIX_STRIPS preserve layout, orientation and applied-strain distinctions
- LOCAL_HAND and LOCAL_STRIP bind the selected hinge and neighboring joints before local deformation. The hand is a printed polymer demonstrator
- DUAL_AXIS_PANEL and SYMMETRIC_PANEL bind x/y datums, hinge orientation and qualified loading order. The unknown two-axis order must not become an assumed simultaneous action
- INTERLOCK_ARCHITECTURE preserves every component ID/version and supported mating/release step. Joining and separation both need observable fit and integrity checks
- THERMAL_HINGES and HYBRID_STRIPS distinguish constituent combinations, passive temperature response and layout variants
- MICRO_PIPE includes microfeature inspection and shape/thermal observations. Pictured liquid flow does not become an invented quantitative flow experiment
- ALT_RESIN_BATCH, ALT_FABRICATE, ALT_TENSILE and ALT_HINGE preserve the supplementary alternative-resin family. Its ambiguous component label and missing processing details stay gates; primary additives and primary material identities are not inherited

### Electronic strip boundary

ELECTRONIC_STRIP separates sealed channel filling, isolated connection, qualified power observation, disconnection and supported deformation/transfer. The source supports qualitative illuminated-LED observations. Disconnect/reconnect snapshots at successive shapes do not prove uninterrupted conductivity during motion, and illumination does not establish resistance invariance. A future continuous-motion measurement would need a separate qualified integrated fixture, synchronized records and an explicitly scoped test card. No such hardware is supplied here.

## Closed-service boundary

Chemical handling, resin formulation, UV exposure, active mechanical loading, heating, liquid-metal filling and power application belong to qualified enclosed services. The robot may present an approved carrier at a safe exchange port, withdraw, inspect permitted readbacks and retrieve it after an authoritative release. It may not open active process interiors, invent recipes or translate literature numbers directly into device commands.

For each service, the package distinguishes preparation, safe loading, program verification, request, acknowledgement, autonomous processing, safe release, unloading and record commitment. A requested job is not a completed job. A successful completion is not a safe release. An accepted process record is not proof that a desired scientific outcome occurred.

## Numerical dispositions

N_CONSTITUTIVE, N_IMPLEMENTATION, N_DMA_FIT, N_RATE_FIT, N_FEA and N_HINGE_THEORY remain unexecuted numerical or analytical work. Measured calibration datasets, fitted parameters, theoretical predictions and simulated fields retain distinct provenance. Fitting and validating against the same curve is not independent confirmation. Parameter tables do not supply absent subroutines, mesh convergence, boundary-condition code or qualified material parameters for a new batch.

## State, failure and repetition

Any failure preserves the attempt, input state and observations. Quarantined or consumed specimens cannot reappear as accepted inventory. Replacement creates a new ID. Repair or qualified reuse creates a new state/version and retains prior damage and exposure. Thermal and programming histories follow each specimen through all cycles. Independent specimens, technical repeats, phase observations and camera frames are different entities.

Unknown repeat counts never become zero or a successful empty loop. The ten-cycle and forty-cycle counts are retained in their proper branches. Additional retries require the declared bounded policy; deleting a failed attempt to reach a target result is prohibited.

## Evaluation and privacy

Only agent_visible.json is actor-public. It allows current inventory, selected goals, qualified current inputs and observations already acquired. Literature outcomes, evaluator routes, future measurements and hidden fault schedules stay outside actor input.

Success means the authorized scope, qualified prerequisites, material/condition cells, actual observations, lineage, controls, safe recovery and cleanup were completed and honestly reported. A valid result may differ from the paper. Selected-episode completion is not whole-paper completion.

The Python validators exercise static references and synthetic bookkeeping. They check explicit record structure and selected contradiction cases, but cannot authenticate a device receipt, validate an actual material safety program, establish camera calibration, prove robot feasibility or reproduce the science. No live runtime is implemented, and raw-record validation rejects live-evidence use.

## Local inspection

Run from the package directory:

- python3 -B tests/verify_package.py
- python3 -B -m unittest discover -s tests -v

Consult VERIFICATION.json for the exact checked revision, counts and limitations, and review/ for independent findings and their disposition. EXPORT_ALLOWLIST.json is the exact original-file boundary; publisher assets are excluded.
