# Independent static-scene review

Verdict: **PASS — static review assets only.** No remaining blocking issue. This does not qualify physical support, equipment, robot operation or scientific reproduction.

## What was actually checked

- Inspected the pixels of all three final 1680 × 1080 PNGs. Every preview visibly says “STATIC REVIEW ONLY”, “NO EXPERIMENT EXECUTED” and “PHYSICAL ACTUATION DISABLED”. Closed services, the parked robot, distinct M1/M2/M3 carriers, retained custody and separate experimental/numerical evidence are legible.
- Independently reopened the compressed Blender file: 322 objects, 11 AS collections and 32 exact named anchors. No actions, animation data, scripted drivers, physics modifiers, rigid bodies, constraints, embedded scripts, external images or linked libraries.
- Independently reimported the GLB: 310 objects and all 32 anchors, with **0.0 m native-to-GLB position error** and no anchor-property mismatch. Manifest-to-native error is below 0.000001 m.
- Compared all 11 AS families and 14 R operations with the accepted review and verified the scene binding contract is byte-identical to the paired operation contract. All operation targets exist.
- Checked 31 specimen/fixture/equipment/floor contact pairs and both roof-bracket interfaces. All meet or overlap within 0.000001 m; this verifies the drawing’s support continuity only.
- Ran the supplied 42-test guard suite and added reproducible independent probes: **479/479** semantic/binding assertions plus **170/170** field-type fuzz cases pass without exceptions, hardware commands, enabled physics or actuation.

## Source and evidence distinctions

M1 alone retains the reported 77.7 × 20.2 × 11.1 mm envelope, with a clearly marked authored 4× display scale in the object properties and manifest. The actual combined M1 illustration measures approximately 0.3108 × 0.0808 × 0.0444 m. M2 and M3 source envelopes remain unknown; their authored illustrations are 0.300 × 0.090 × 0.050 m and 0.205 × 0.084 × 0.048 m. The symbolic 9/9/6 ridge counts are not the reported 30/30/20 source cell counts. No source-exact or manufacturing geometry is claimed.

M1, M2 and M3 remain separate specimen families; runtime specimen/carrier IDs and physical replicate counts are unbound. Experimental B01–B05 and numerical A01–A04 remain distinct in both labels and guard routes. No source field map, observations, force result or scientific solver output is generated.

The inspected construction uses original procedural primitives and labels. No evidence of copied publisher artwork, source CAD, raw observation data or author code was found. Source facts are referenced as facts. Final PNG metadata is empty; native and GLB resources are self-contained.

## Issues found and resolved during review

1. Removed the 8.5 mm gaps beneath the three specimen illustrations
2. Rejected malformed/unknown branch, identifier and custody/lease/epoch inputs
3. Rejected numerical specimen handling, experimental R11 requests and unsupported contradictory fields
4. Grounded the retained support column and completed secondary support/contact geometry
5. Replaced the floor’s qualification-implying wording with “CLOSED SERVICES / REVIEW ONLY”

The corrected native file, GLB and every final preview were checked again. The scene remains on HOLD_QUALIFICATION: static appearance and synthetic fixture acceptance cannot establish real safe state, custody, calibration, grasp validity or experiment completion.

Detailed hashes and measured evidence: `independent_review.json`. Reproducible adversarial probes: `independent_guard_probes.py`; results: `independent_guard_probe_results.json`.
