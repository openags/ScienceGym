# Ideal-tek AA.SA.T.6 passive tool candidate

This candidate is **not selected for the laboratory or qualified for robot
grasping**. It separates a source-based rest shape from the prescribed
deformation in the existing workflow movie. No existing laboratory asset,
movie or robot trial is changed by this directory.

The [manufacturer product page](https://www.ideal-tek.com/scheda.php?c=ptfe-coated-tweezers&f=8&idp=4384&l=3&m=search)
gives a 130 mm length, 11.5 mm width, 12.5 mm height, 8 mm unloaded tip opening,
0.5 × 0.4 mm tips and 18 g net mass. The
[product sheet](https://www.ideal-tek.com/public/upload/PDS/AA.SA.T.6.IT.pdf),
[SA material sheet](https://www.ideal-tek.com/public/files/SA%20Technical%20DataSheet.pdf)
and [T coating sheet](https://www.ideal-tek.com/public/files/T%20Technical%20DataSheet.pdf)
describe PTFE-coated steel. Material calculations use the source's nominal
316L density of 8,000 kg/m³ and Young's modulus of 200 GPa. These values do
not provide a calibrated assembled-tool force curve. Local PDF downloads
failed with HTTP 403; sources were read through web access. No manufacturer
PDF is redistributed.

Interior thickness, spring profile, coating contribution, damping and
pairwise friction are inferred. The rest geometry matches the listed
dimensions and nominal mass; this is not manufacturer CAD or an established
visual match to every detail. Each revision preserves its builder and source
manifest. The original revision-01 source snapshot contains an incorrect
cache description; the current `sources.json` corrects that provenance.

The first candidate used a single bending mode per arm with internal joint
couplings. Subsequent candidates use independent passive rotational springs
along segmented steel arms. They have no tool actuators, attachment welds or
runtime pose assignments. The contact-characterization fixture mounts the
heel, disables gravity, and uses two motorized spherical indenters. It is a
component test fixture, not robot execution or an allowable laboratory aid.

| Revision / contact fixture | Result |
| --- | --- |
| 01 | Coupled-mode model unstable before useful contact. |
| 02 | Distributed springs unstable at 2 ms; the highest mounted-heel mode is about 110 kHz. |
| 03 | Rayleigh damping and 0.5 ms step complete closure/release, but contact penetration reaches 1.485 mm and fails. |
| 04 | Stiffer contact at 0.5 ms becomes unstable. |
| 05 | At 0.1 ms, basic closure/release, penetration and exact replay checks pass. Additional hold review fails: contact chatters and the held tip gap varies by 2.169 mm. |

Fixture 05 closes the 8 mm opening to a minimum of 2.494 mm and returns to
8 mm. Maximum intended penetration is 0.209 mm; replay position and velocity
errors are zero. Its approximate peak linear bending stress is 130 MPa,
below the material sheet's 200 MPa minimum yield value, but this is not a
validated stress field. Its failed hold review overrides any interpretation
that these basic checks establish a usable grasp. The hold-quality gates were
introduced after observing chatter and are explicitly development checks.

Contact stability, integration with the laboratory's time step, spatial
torsion, discretization convergence, measured mechanics, handheld operation
and specimen retention remain open. All failed fixtures are retained.

From the repository root, use the simulation environment and fresh output
directories:

```sh
python assets/idealtek_aa_sa_t6_v1/build_passive.py /tmp/tweezer-new
python assets/idealtek_aa_sa_t6_v1/check_passive_contact.py /tmp/tweezer-new /tmp/tweezer-contact-new
python assets/idealtek_aa_sa_t6_v1/review_passive_hold.py /tmp/tweezer-new /tmp/tweezer-contact-new
```

Run the hold review even when investigating a failed initial contact review.
The current candidate is expected to fail hold quality; no grasping or full
paper-branch success is credited.
