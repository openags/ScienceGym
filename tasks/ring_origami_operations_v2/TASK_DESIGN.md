# Reprogrammable origami rings: whole-paper robot task design

Hu, X., Tan, T., Wang, B. and Yan, Z. (2023), *A reprogrammable mechanical metamaterial with origami functional-group transformation and ring reconfiguration*, Nature Communications 14, 6709. [DOI 10.1038/s41467-023-42323-1](https://www.nature.com/articles/s41467-023-42323-1)

## Status and evidence boundary

This is an authored, paper-level experimental task-design draft. It is not an executable robot program, a reproduced experiment, a verified fabrication recipe, or a physical-feasibility claim. The task makes a mobile manipulator participate in material preparation, fabrication handling, fine assembly, transfers, tool use, fixture mounting, instrument configuration, observation, measurement, unloading and cleanup. Device-controlled printing and test motion remain separate from robot actions.

The main article is readable; the 60-page Supplementary Information (SI) has been text-inspected and relevant illustrated pages have been visually inspected. SI includes Discussions 1–8, Figures 1–44 and Tables 1–3. Twelve supplementary movies, their separate description document and the Source Data workbook have not been inspected. Movie 9 is explicitly method-bearing for assembly. Text and SI support the assembly macro-sequence; exact video choreography remains an unresolved input. No inaccessible material was bypassed. Source files and publisher pixels are excluded from public export.

Each operation distinguishes source evidence, an authored robot interface, and missing execution inputs. Unknowns block the relevant future action, not honest task design. Preassembled samples may be used only in an explicitly different receipt-only episode; they cannot satisfy fabrication/assembly credit.

## Finite whole-paper physical scope

1. Resin-facet and TPU-crease preparation; printed frames, supports and connectors; screw/hinge assembly of the thick-facet prototypes
2. Crease contraction/expansion demonstration; C-I, C-II, C-III and R element characterization; axial/transverse anisotropy comparison
3. C/R functional-group transformation and triangular and quadrilateral ring assembly/transformation
4. Triangular and square-ring torsional deformation, image-based geometry and semi-experimental torque derivation
5. Square-ring uniaxial and auxetic deformation across the reported element classes and supported loading directions
6. Reconfiguration into morphology I, including angle-dependent force response and long/short-axis mounting, and morphology II axial deformation
7. A separate fabrication route for 30 mm cardboard elements and a three-row/two-column, six-ring periodic array
8. Array C-III compression and C-I tension at 22.5, 45, 67.5, 90, 112.5, 135 and 157.5 degrees; qualitative C/R transformation and coexistence

Analytical geometry/energy maps, constitutive calculations and proposed robotic/electrical-logic applications are explicitly nonmanual scope. The source's locomotion, grasper, anchoring and logic-gate schematics do not establish fabricated, measured application hardware. The triangular periodic-network discussion is not promoted to a measured array campaign.

## Materials, components and assembly

The thick-facet route uses light-cured high-toughness photosensitive-resin facets and FDM TPU creases. SI Figures 26–27 identify facets I, II, III-1 and III-2, concentric hinge cylinders, crease mounting slots, locally thickened regions, a sliding facet-III interface, square frames and structural supports. A qualified CAD/BOM and process card must supply manufacturing geometry, quantities, tolerances, resin handling/wash/cure procedure, print settings and inspection limits. These are not recoverable from a schematic alone.

The source nominal facet thickness is 2 mm. TPU hardness is 95A; the flexible crease region is 0.5 mm thick and 5 mm wide, with crease length scaled to 0.36 of the thicknessless model. These are source design targets, not accepted as-built measurements. The thick prototype side length is 110 mm. Initial crease angles (1,2,3,4), verified in SI Fig. 13, are C-I (360,0,0,360), C-II (170,0,0,360), C-III (130,0,0,180), and R (0,0,0,0), in degrees. Rest-angle orientation and mountain/valley identity must remain explicit even where 0 and 360 look similar in a photograph.

Robot preparation includes retrieving labeled stock, separating part classes in trays, binding approved jobs to material lots, loading machines, checking readiness, starting each process, observing completion and receiving identified output. Enclosed devices carry out printing and any qualified postprocessing cycle. The robot then inspects and sorts accepted versus rejected parts; a job-complete signal alone does not establish a usable part.

For thick-element assembly, the source specifies crease order 2, 3, 1, 4. Adjacent cylinders are first joined with M1×3 mm self-tapping screws, followed by crease fixation with M1×3 mm screws. Protruding screw ends are cut with pliers. Four subcomponents form an element; facet III-2's thin section enters III-1's cavity, lower connecting strips join the halves, and an M1×4 pin limits opening. Frames attach using M1×6 mm screws. The robot translation uses a support jig, part indexing, controlled driver, captured-offcut cutting tool and inspection. Screw torque, cutting clearance, exact poses and safe force limits are unknown; Movie 9 remains unread. No autonomous fine-assembly readiness is claimed.

Frames, connecting straps and parallel rotation axes join a C element with an R element and then functional groups into a ring. The robot verifies connectivity and hinge placement, supports stored elastic load, changes configuration only with the specimen unloaded, and records the actual element graph and each configuration epoch. It does not replace a physical rotation with a C/R label change. Structural supports fix thick-ring angles; replacing these supports is distinct from the pin-indexing interface in the paper array.

## Mechanical and deformation routes

Every route includes sample receipt/inspection, supported transport, station docking, fixture mounting, baseline/calibration checks, condition readback, bounded loading or manipulation, observation, safe reset, unload, archive and cleanup. The base does not navigate with an exposed or tethered loaded specimen. A fixture holds the specimen while the robot clears moving parts; the testing device owns commanded motion until it reports a safe state.

The element and thick-ring test service uses the reported 10 mm/min displacement rate and 20 Hz force sampling as nominal settings, subject to a qualified stroke, force and fixture card. Source apparatus is HY-0580 with a nominal 1000 N load cell. Three prototypes per element type are reported; this does not establish three independent repeats for every ring/array condition. A future episode must supply its specimen/repetition allocation and retain every failed attempt. The source describes element tests collectively as compression while C-I/C-II branches include tension; final loading direction and clamp program therefore require a resolved condition card.

Anisotropy is a separate physical comparison: SI Fig. 25 distinguishes transverse F1/F2 from axial F3. Sample orientation, contact areas and stroke limits must be supplied and verified; no force curve is fabricated from the qualitative statement that transverse deformation is small.

For torsion, source apparatus includes a surrounding iron ring, distributed cords and ring supports. A robot may mount and manipulate this apparatus only through a qualified handling card. Record calibrated images, per-group element height, angle and inner/outer contour measures. The original torque curves are semi-experimental: measured element force response and measured geometry feed SI Eq. 43. They are not direct torque-transducer measurements. Preserve all input records, formula version and transformations. SI Fig. 29 depicts a circle around the outside while Methods mentions inner diameter; landmark/diameter-versus-radius correspondence is unresolved. No numeric radius or torque may be silently assigned from that illustration. A future direct torque sensor would be a separately labeled extension.

Triangular and square rings each retain C-I expansion, C-II expansion/compression, C-III contraction and R contraction possibilities. Transformation and mechanical deformation are separate epochs. A baseline configuration must be restored before converting a C-ring to its R counterpart. The robot verifies the actual hinge angles and load axis after every reconfiguration.

Square-ring axial and auxetic tests retain both physical loading orientations. C-I is tensile; C-II has tensile and compressive branches; C-III and R are compressive. Axes must be referenced to the current ring graph, because functional transformation changes their relation to the laboratory frame. Morphology I uses non-square intermediate configurations and preserves long/short-axis fixture choices; the exact experimentally sampled angle grid is not recovered from the unread workbook. Morphology II includes the endpoint configuration described at 0 or 180 degrees, with 0 degrees the explicit illustrated example. These endpoints are not automatically two independent measured conditions.

## Paper-element periodic-array route

This route is not a scaled resin/TPU recipe. The source uses precreased red/blue 180 g/m² cardboard, a cutting plotter, 30 mm elements, two printed square frames per element, connecting components, screws and removable indexing pins. Robot operations include sheet registration, approved plotter-job setup, crease/cut process handling, retrieving the cut sheets, controlled folding, frame attachment and graph-based array assembly. The crease net, cut-versus-score instruction, folds, seams and acceptance tolerances remain supplied inputs.

Frame fixation uses M1×3 screws; connector fixation uses M1×4 screws. The source hinge design indexes 22.5-degree increments with 0.7 mm holes. The robot unloads the array, supports it, removes pins, reconfigures hinges and reinstalls pins before applying load. It cannot reconfigure against the testing machine's load. Actual pin engagement and all required angles must be checked.

Assemble six rings as three rows and two columns without assuming that shared connector slots imply duplicate physical objects. Top/bottom rings connect to sliders on test rails. Side linear bearings are linked on each side by an optical shaft to coordinate deformation. Mounting, lateral freedom, parallelism and fixture travel require a qualified interface. The reported array crosshead rate is 20 mm/min; this is not a dimensionless strain rate. Longitudinal data come from the test system, while transverse dimensions are measured by a ruler at upper, middle and lower positions. The task preserves all three raw widths and computes the mean of the three strains, rather than substituting an unrecorded global width.

Seven angle conditions apply separately to C-III compression and C-I tension. Record each configuration, baseline length/width, time/displacement and transverse observations. The paper-array C/R roles must not inherit the thick TPU elements' measured stiffness. SI Fig. 41's recessed/protruding connector variant supports a distinct qualitative transformation route. Mixed C/R coexistence is text/Movie-12-referenced; the exact transformation sequence remains unread and cannot establish a measured mixed-array force curve.

## Controls, lineage and measurement integrity

- Actual part identity, material lot, fabrication receipt, rejection history and assembly membership survive every transformation
- New angle, support, pin, loading direction or fixture choice creates a new configuration epoch; a trial ID is not a specimen ID
- Preserve calibration, sign conventions, displacement zero, time alignment, raw images and raw force/position/width measurements
- Keep directly measured quantities separate from image-derived geometry, calculated stress/strain and semi-experimental torque
- Fit stiffness or compute Poisson's ratio only with a declared window, reference dimensions and uncertainty treatment; do not use source curves as synthetic measurements
- Match comparisons by material, geometry and loading mode; unexplained fabrication variation or damage must not be hidden as a new mechanical state
- Retain safe aborted and failed attempts; source agreement and procedural validity are different outcomes

## Unresolved inputs and honest closure

The main remaining gates are manufacturing files/process settings; resin postprocessing; fine-fastener and cutting limits; exact movie choreography; ring and array fixture dimensions/limits; calibrated imaging landmarks; acquisition/analysis details; repeat allocation beyond element tests; and source direction/angle inconsistencies. SI Figs. 32/33/35 use tension in some captions where panel labels and the main discussion indicate compression. The printed expression (0,90) intersection (90,180) is an empty set; the narrative indicates two non-square ranges, but a condition card must resolve it explicitly rather than execute the literal notation.

A complete future episode ends with valid evidence for every selected condition and safely archived samples/stations. An unresolved gate ends as partial-with-blocker, not successful physical execution. The campaign can be divided into independent physical families, but a single-family episode does not count as whole-paper completion. This package supplies design contracts and static validation only; it includes no CAD, viewer, robot runtime, simulator or evaluator implementation.
