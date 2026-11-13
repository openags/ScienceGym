"""Author the cooling pilot's inspectable operation decomposition.

The emitted JSON is the portable task contract. This source retains the compact
authored decomposition and pins the historical input rather than modifying it.
Run from any directory; only this v3 package's generated records are written.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "directional_cooling_operations_v2"
SCHEMA = "sciencegym.directional_cooling.v3"


def read(name):
    return json.loads((OLD / name).read_text())


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n")


# Each line is a particular action and its observable end condition. These are
# proposed robot handling steps, not recovered historical human trajectories.
# P perception; M manipulation; T motion; D decision; A analysis; X device process.
DETAIL = {
    "PLAN": [
        ("D", "Select whole-paper campaign or named experimental leaves", "Scope includes an explicit obligation list and all prerequisite work"),
        ("D", "Allocate separate white and black specimen identities, witness samples and sessions", "Each required condition has nonempty allocations; reuse and independent specimens are distinguished"),
        ("P", "Inspect source conflicts, installed equipment and required operating inputs", "Missing inputs identify affected operations without deleting those operations"),
        ("D", "Reserve instruments, tools, work surfaces and compatible observation channels", "No exclusive resource is assigned to simultaneous incompatible work"),
    ],
    "STOCK": [
        ("P", "Read copper sheet, polymer tube, aluminum stock, foam, film and coating lot identities", "Material, thickness and intended branch agree with the bill of materials"),
        ("M", "Open the appropriate stock compartment and separate supported items into labeled tray slots", "Different coatings, film types and raw stock remain individually identifiable"),
        ("M", "Secure sheets, tubes and fragile films in compatible retainers", "The carrier supports edges without contacting the active film or optical faces"),
        ("P", "Count stock and reserve offcuts, witness samples and replacement allowances", "Allocation ledger accounts for produced parts, consumed stock and retained remainder"),
    ],
    "MOVE": [
        ("P", "Inspect the payload identity, source support, destination dock and any attached leads", "Payload is supported; live tethers and obstructions are resolved"),
        ("M", "Grasp the carrier's structural handles, close retainers and lift clear of source supports", "The same payload is retained without gripping films, tracks or sensor wires"),
        ("T", "Retract the manipulator and transport the supported carrier along the supplied route", "Robot and payload reach the destination without an unexplained location change"),
        ("M", "Seat and secure the carrier at the destination before releasing the grasp", "Support transfers to the destination; the gripper is clear"),
        ("P", "Recheck identity, orientation, intactness and station occupancy", "A destination observation belongs to this actual transfer occurrence"),
    ],
    "FAB_LOAD": [
        ("D", "Select a part drawing, stock and fabrication method for each required part", "Track water-jet cutting is source-reported; other machining choices have inference records"),
        ("P", "Inspect material thickness, blank support and cutter/fixture compatibility", "The drawing uses real units and the loaded stock covers the part envelope"),
        ("M", "Place aluminum track stock onto the water-jet bed and fasten its supports", "The sheet is retained and the cut path clears clamps and support hardware"),
        ("M", "Set the work origin and load the site/date-specific track job through the machine interface", "The selected job and actual sheet datum agree"),
        ("P", "Verify the work region is clear and the installed machine's required guards are engaged", "The machine's own permissive readback supports starting the process"),
    ],
    "FAB_RUN": [
        ("D", "Select the qualified water-jet program for the reported 1.5 mm aluminum track stock", "Cutting settings and limits are supplied independently of the paper's missing settings"),
        ("M", "Start the loaded track program from the machine control interface", "The controller acknowledges the intended job and work origin"),
        ("X", "Monitor the machine-owned cut and stop on its reported fault", "Completion or interruption is recorded for the actual stock and job"),
        ("P", "Observe motion and process stop before accessing the bed", "The machine reports an accessible stopped state; a receipt alone does not move a part"),
    ],
    "FAB_UNLOAD": [
        ("M", "Release the accessible bed clamps while supporting the cut track and surrounding stock", "The track is separated without falling or bending"),
        ("M", "Lift the cut track into its supported carrier and segregate offcuts", "Part and remainder identities link to the original sheet"),
        ("M", "Deburr the supported edges using the selected compatible finishing tool", "No retained burr obstructs the slider, fasteners or handling surfaces"),
        ("P", "Measure thickness and compare the cut path and mounting endpoints with the job drawing", "Inspection records measured deviations and rejects mismatched geometry"),
    ],
    "COAT_LOAD": [
        ("P", "Inspect the fabricated copper disk and identify its intended white or black condition", "The disk identity, diameter, thickness and intended optical face are recorded"),
        ("M", "Clean the supported disk using the selected compatible surface-preparation procedure", "The face is free of visible debris; process chemistry remains tied to its operating card"),
        ("M", "Mask the back and fixture contact region, then place the disk on a coating support", "The top optical face is exposed and the disk is mechanically supported"),
        ("P", "Read the Krylon product and color label and inspect the coating workspace", "Selected coating matches the assigned condition; product-specific preparation inputs exist"),
    ],
    "COAT_RUN": [
        ("M", "Prepare the identified spray can and remove its cap at the coating station", "The nozzle is accessible and the can remains identified with its color and lot"),
        ("M", "Aim and sweep the nozzle over the supported optical face using the selected coating card", "One coat is applied to the intended face; spray motion is an inferred robot action"),
        ("X", "Wait for the coating card's intercoat condition while retaining the part on its support", "Elapsed time and observed readiness are recorded; no unreported duration is invented"),
        ("D", "Repeat the apply-and-wait body until three separately recorded coats have been applied", "Exactly three coats are accounted for, rather than one event labeled three coats"),
        ("X", "Allow the final coating to meet the selected cure condition", "Cure evidence belongs to this disk and coating batch"),
        ("M", "Release the nozzle, replace the cap and return the can to its assigned storage", "Coating equipment is left in its declared idle state"),
    ],
    "COAT_UNLOAD": [
        ("P", "Inspect coating coverage, contamination, runs and damage under the declared lighting", "Acceptance or rejection is recorded without assigning literature optical properties"),
        ("M", "Remove masking without touching or peeling the optical face", "Backside attachment region is accessible and the optical face is intact"),
        ("M", "Release the disk from its support and return it to the identified edge-supported carrier", "No unrecorded specimen substitution occurs"),
        ("D", "Retain failed disks and select a new identified blank for replacement if needed", "Replacement consumes a new allocation and does not erase the failed attempt"),
    ],
    "LAYOUT": [
        ("P", "Read the fabricated-part and coated-emitter identities at the assembly station", "Required parts and their inspections are present"),
        ("M", "Place the acrylic base, rails, foam layers, support tube, ring and shield in assembly order", "Parts occupy distinct supported locations and retain their identities"),
        ("D", "Select the white or black build instance and its drawing revision", "The selected emitter cannot silently change color during assembly"),
    ],
    "BASE": [
        ("M", "Seat the acrylic base on a stable assembly fixture and attach the framing rails", "Rail spacing and fastener engagement match the selected reconstruction drawing"),
        ("M", "Attach the base shielding and position the lower foam disk", "The foam is centered and supported; shielding does not create an unintended optical obstruction"),
        ("M", "Place the second 25 mm foam disk above the first and inspect the stack", "Two separately identified layers support the emitter location"),
        ("P", "Measure the assembled support stack and identify the emitter datum", "Height and datum are recorded rather than assumed from a display model"),
    ],
    "EMITTER": [
        ("P", "Confirm the selected disk's coating, backside lead routing and clean support surface", "The active face is identified and cables will not be pinched"),
        ("M", "Grasp the disk at its qualified edge and seat it on the insulation stack", "The disk remains supported with its optical face upward"),
        ("M", "Lower the PE support tube around the stack without contacting the emitter edge or leads", "Tube and emitter are concentric within the declared tolerance"),
        ("P", "Inspect radial clearance and the future cover support plane", "The cover will remain separated from the emitter"),
    ],
    "FILM": [
        ("P", "Identify two separate nanoporous PE sheets and inspect them against a contrasting background", "Both sheet identities are present and neither is torn or contaminated"),
        ("M", "Support the spacer ring in a film jig and prepare its lower attachment face", "The annular attachment region is accessible without unsupported film handling"),
        ("M", "Present the lower sheet with edge supports and attach it to the first ring face", "The sheet spans the aperture and its attachment is continuous under the selected method"),
        ("M", "Turn the supported ring using the jig, then present and attach the second sheet", "The second sheet occupies the opposite face with its own identity"),
        ("M", "Trim excess film outside the retained annulus using the selected cutting support", "Trimming leaves both attachments and the optical opening intact"),
        ("P", "Inspect wrinkles, holes, attachment and interlayer separation before releasing the jig", "Both films and the 6.4 mm spacer relationship are independently inspected"),
    ],
    "SHIELD": [
        ("M", "Wrap the prescribed lateral support and base surfaces with aluminized Mylar", "Reflective coverage avoids the emitter and cover aperture"),
        ("M", "Keep the cover ring retained by its jig while lowering the lower film onto the PE tube rim; inspect the selected membrane-supported load path before releasing the jig", "The 107 mm ring bore is not falsely treated as resting directly on the 102 mm tube; release requires observed stable film/attachment support, acceptable sag and emitter clearance under qualified criteria"),
        ("M", "Lower the polished aluminum cylinder over the assembly without trapping sensor leads", "The cylinder is supported and the lead exit remains accessible"),
        ("M", "Fit the aperture plate and align its 50 mm opening with the emitter", "The opening has a clear optical path and does not contact the cover films"),
    ],
    "REFLECTOR": [
        ("M", "Attach the two hollow support rods to the framing and set their selected height datum", "Both supports are retained and the recorded height is an explicit reconstruction choice"),
        ("M", "Fasten the site/date track between the supported rods", "Mounts are secure and the slider has a continuous accessible path"),
        ("M", "Install the 60 mm reflector disk on its movable carriage", "The disk is retained while the carriage can be deliberately repositioned"),
        ("P", "Inspect full carriage travel, cable clearance and disk orientation", "No support or clamp blocks the intended tracking interval"),
    ],
    "ASSEMBLY_QC": [
        ("P", "Inspect every connection against the assembly membership list", "Base, two foam layers, emitter, support, two films, ring, shield and reflector are accounted for"),
        ("P", "Measure cover gaps, aperture alignment and reflector geometry from declared datums", "Reported dimensions and inferred geometry remain distinguishable"),
        ("P", "Inspect the assembly from loading and sensor-access viewpoints", "Thin films are intact and needed interfaces can be reached"),
        ("D", "Accept this design assembly revision or route a specific defect to repair", "A repair creates a new inspection requirement for the changed revision"),
    ],
    "CAL_MOUNT": [
        ("M", "Open the A25 bath lid and inspect the bath and copper-block support", "The accessible bath is ready for the supplied calibration program"),
        ("M", "Seat the identified immersion RTD and each labeled thermocouple in its block hole", "Probe tips occupy declared immersion positions without identity swaps"),
        ("M", "Lower and secure the supported block in the bath and route the leads clear of the lid", "Block immersion and lead retention are observed"),
        ("M", "Connect the reference RTD to the Keithley 2000 and thermocouples to USB-TC terminals", "Terminal polarity, channel labels and the cold-junction enclosure configuration are checked"),
        ("P", "Compare live channel readbacks with probe identities before the bath sweep", "Open channels, reversed polarity and mismapped probes are detected"),
    ],
    "CAL_ACQUIRE": [
        ("M", "Enter one supplied bath setpoint through the installed circulator controls", "Actual controller readback matches the requested calibration point"),
        ("X", "Wait for the declared equilibration predicate using reference and bath observations", "A time delay alone cannot replace the required stability observations"),
        ("X", "Acquire synchronized reference and thermocouple readings for the specified observation window", "Raw records retain sensor, channel, setpoint and timestamps"),
        ("D", "Repeat for all nonempty supplied calibration points and required repeats", "Every scheduled occurrence has an explicit result or blocker"),
    ],
    "CAL_FIT": [
        ("A", "Fit each thermocouple against the paired immersion-reference observations using the declared method", "Each correction refers to that probe's actual calibration data"),
        ("A", "Calculate residuals and retain slope uncertainty under the selected uncertainty convention", "No numerical error bar is imported from the literature as a new measurement"),
        ("D", "Accept or reject each sensor/channel configuration against declared criteria", "Validity and invalidating changes are explicit for every accepted calibration"),
    ],
    "CAL_UNLOAD": [
        ("M", "Stop the calibration program and establish the bath's declared removal state", "Observed bath and block conditions permit the selected unloading procedure"),
        ("M", "Lift the supported block and withdraw probes without pulling their wires", "All probes retain identities and are placed on a dry support"),
        ("M", "Disconnect and coil leads into labeled sensor tray positions", "Channel mapping and calibration references are preserved for subsequent attachment"),
        ("M", "Close the bath lid and return its support tools", "Calibration station is left in the recorded idle state"),
    ],
    "TC_ATTACH": [
        ("M", "Support the emitter or open the supported assembly to expose its backside", "The active face is protected and no component is unsupported"),
        ("M", "Position the identified calibrated K-type junction near the backside center", "Probe identity and placement agree with the selected location card"),
        ("M", "Apply the selected thermally conducting silver paste and retain the junction during setting", "Junction contact and setting condition are inspected"),
        ("M", "Route and strain-relieve the lead through the declared exit, then restore the assembly", "The lead is neither pinched nor substituted and the assembly revision is recorded"),
        ("P", "Check continuity, channel mapping and any disturbed assembly interfaces", "Readback and renewed inspection match the current configuration"),
    ],
    "OPT_REFERENCE": [
        ("P", "Identify Cary 5000/DRA-2500 or Nicolet 6700/IntegratIR and its installed accessory", "Instrument, accessory and selected optical mode agree"),
        ("M", "Open the sample compartment and install the matched accessory on its locating base", "The accessory is retained and any detector/purge connections match its manual"),
        ("M", "Set the required reference standard, port plugs and specular-inclusion configuration", "Reference and sphere ports correspond to direct-hemispherical measurement"),
        ("M", "After checking connections, restore required power, satisfy instrument warm-up, close the required cover and select the scan/background configuration", "Software readback identifies the source, detector, range and configuration"),
        ("X", "Acquire the background/reference and inspect it before sample loading", "A valid reference is tied to this instrument and accessory configuration"),
    ],
    "OPT_MOUNT": [
        ("P", "Identify the reflector, two-layer cover, white emitter, black emitter or LDPE witness specimen", "Sample ancestry and optical surface match the required material condition"),
        ("M", "Open sample access and release the holder while supporting its current contents", "The correct port and a compatible empty holder are accessible"),
        ("M", "Place and retain the specimen at the measurement port without touching the optical face", "The specimen covers the required port and fits the actual accessory"),
        ("P", "Inspect orientation, aperture coverage and film spacing, then close access as required", "Mounting observations belong to this specimen/configuration rather than the entire device by assumption"),
    ],
    "OPT_SCAN": [
        ("M", "Select the sample identity and the supplied solar or infrared scan settings", "Settings and reference belong to the actual instrument currently holding the sample"),
        ("X", "Start the scan and monitor acquisition and instrument fault feedback", "A raw scan is produced only by an acquisition backend, never by a task state label"),
        ("P", "Inspect saturation, missing bands, reference validity and specimen movement", "Rejected scans remain in the attempt history"),
        ("A", "Save raw signal/reference parents, units, wavelength axis and configuration", "The saved record can be traced to one sample and one scan occurrence"),
    ],
    "ANGLE_MOUNT": [
        ("M", "Stop the Nicolet scan, remove the sphere specimen and release the sphere accessory", "Sample and accessory are separately supported before the configuration changes"),
        ("M", "Install the Harrick 12-degree or SpectraTech variable-angle accessory as applicable", "The actual accessory and its locating interface match the selected angle route"),
        ("M", "Mount the white or black emitter specimen and set its optical face and incidence datum", "Angle reference and specimen identity are observed"),
        ("M", "Install and inspect the selected polarization optics before acquiring the separate angular reference", "The configured optical path and polarization are identified; a sphere reference cannot be reused"),
    ],
    "ANGLE_SCAN": [
        ("M", "Set and read back one angle from 12, 30, 40, 50, 60, 70 and 80 degrees", "The requested angle is bound to the appropriate actual accessory"),
        ("M", "Set the declared s or p polarization condition", "Polarization has an observable configuration or a documented qualified averaging method"),
        ("X", "Acquire and save the corresponding infrared reflectance scan", "Record identity includes emitter, angle, polarization and reference configuration"),
        ("D", "Continue through the full angle/polarization allocation with remounting when required", "Symmetric plotted angles are not counted as separately acquired negative-angle trials"),
    ],
    "OPT_UNLOAD": [
        ("M", "Stop acquisition and open the sample access required by the accessory", "Instrument feedback permits removal and the sample remains supported"),
        ("M", "Support the specimen, release its holder and lift it by its allowed edges", "The same specimen leaves the instrument without optical-face contact"),
        ("M", "Place the specimen in its labeled carrier and inspect it", "The sample has one supported location and any damage is retained"),
        ("M", "Restore port plugs, holder and compartment cover", "The instrument is left empty or in its declared storage configuration"),
    ],
    "OPT_SUMMARY": [
        ("A", "Process accepted reference-linked spectra using the declared optical model", "Reflectance, transmittance and emissivity retain separate measurement/assumption bases"),
        ("A", "Combine angular s/p results only under the declared weighting rule", "Each derived spectrum retains all raw parents"),
        ("D", "Report missing channels or unjustified absorption assumptions as incomplete quantities", "Transmission is not silently set to one minus reflection for an absorbing film"),
    ],
    "SITE_SETUP": [
        ("P", "Inspect outdoor supports, horizon, eligible session and the selected solar track", "Site/date and geometry match the intended experimental condition"),
        ("M", "Seat and retain the two devices by their robust bases at separate supports", "White and black identities remain distinct and their shadows do not overlap"),
        ("M", "Orient each frame and adjust the reflector supports using observed solar geometry", "A full-aperture shadow is established without replacing the physical adjustment by a label"),
        ("M", "Route sensor and heater leads to protected instruments with strain relief", "Connections do not load films, obscure apertures or obstruct the reflector path"),
        ("P", "Inspect final component membership, condition and current assembly revision", "Outdoor setup evidence refers to the actually installed versions"),
    ],
    "ENV_SETUP": [
        ("M", "Mount the exposed-element ambient RTD inside the ventilated radiation shield", "The sensing element is shaded with airflow and positioned about five feet above ground"),
        ("M", "Inspect and connect the HOBO U30 weather-station sensors and power", "GHI, humidity and weather temperature channels have known identities"),
        ("M", "Mount and level the EKO STR-32G and connect MS-56 and MS-402 on its sensor supports", "Both solar sensors have sun-normal orientation and unobstructed views"),
        ("M", "Check tracker location/time configuration and initiate its automatic sun tracking", "Tracker pointing feedback is distinct from manual cooler-reflector positioning"),
        ("M", "Place USB-TC in its reflective protective enclosure and route leads through retained exits", "Cold-junction and sensor configuration match the calibration basis"),
        ("P", "Inspect the ambient shield, tracker, weather station and DAQ from their actual working viewpoints", "No generic console substitutes for the separate instruments"),
    ],
    "SYNC": [
        ("P", "Read all instrument clocks and bind local time, UTC and site coordinates", "Clock offsets and conversions are documented"),
        ("M", "Configure each acquisition stream's supplied cadence and channel map", "HOBO's reported 300-second cadence is not imposed on temperature or PID streams"),
        ("P", "Check a contemporaneous sample from every required stream", "Missing channels and excessive clock offsets are detected before interpreting paired observations"),
    ],
    "ENV_LOG": [
        ("X", "Acquire concurrent ambient, weather, DNI and sun-normal GTI streams", "Environmental records overlap the experimental acquisition interval"),
        ("A", "Calculate diffuse irradiance from aligned GTI minus DNI with synchronized records", "GHI is not substituted for GTI; inconsistent negative differences remain diagnostic"),
        ("P", "Observe cloud, wind and instrument interruptions throughout the session", "Ineligible intervals retain their timestamps and reasons"),
    ],
    "LID_BASELINE": [
        ("M", "Place an identified aluminum lid over each aperture while retaining both PE films", "Both apertures are covered independently and films remain installed"),
        ("M", "Start the paired temperature acquisition and record the baseline start time", "Both device channels and environmental records are acquiring"),
        ("X", "Retain covered baseline observations for the source's five-minute interval", "Baseline duration and covered states are linked by actual timestamps"),
    ],
    "LID_REMOVE": [
        ("P", "Confirm baseline elapsed time and each lid's accessible grasp region", "The active object is the removable metal lid, not a convection film"),
        ("M", "Lift the first lid and place it on its assigned support", "First aperture is open and its opening timestamp is recorded"),
        ("M", "Lift the second lid and place it on its separate support", "Second aperture is open with a separate timestamp; both PE covers remain intact"),
        ("T", "Retract from the optical region and record any transient operator shadow", "Acquisition continues with intervention intervals preserved"),
    ],
    "TRACK_ADJUST": [
        ("P", "Observe the disk shadow relative to the full emitter aperture", "The need and direction of adjustment follow observable geometry"),
        ("M", "Release the carriage retainer while supporting the disk carriage", "The carriage can move without detaching the reflector"),
        ("M", "Slide the carriage along the computed track and secure it at the new position", "The disk is physically retained at the selected location"),
        ("P", "Verify aperture shading and retract from the optical path", "Adjustment and operator-shadow times remain recorded; no unreported fixed cadence is assumed"),
    ],
    "STAG_LOG": [
        ("X", "Acquire the paired open-aperture temperature time series during the eligible noon window", "Separate white/black, ambient and environment records cover the declared session"),
        ("P", "Inspect shading, film integrity, channel status and weather during acquisition", "Any invalid interval is retained with a detectable reason"),
        ("D", "Continue, repeat an interrupted session, or close it as partial according to observations", "The paper's temperature reduction is not a required observed outcome"),
    ],
    "HEATER_ATTACH": [
        ("M", "Return the isolated supported assembly to the bench and expose the emitter backside", "Output is off and the emitter remains supported with its sensor identity intact"),
        ("M", "Fit the identified Omega KHR-2/2-P heater using the selected attachment geometry", "The heater fits the 50 mm disk; any overhang or sensor interference is explicitly resolved"),
        ("M", "Attach separate force and sense lead pairs at the heater's electrical nodes", "Voltage sense is at the heater terminals rather than at the power supply"),
        ("M", "Route and strain-relieve all leads, restore the assembly and connect the Keithley 2425", "Four-wire topology, polarity and the current assembly version are recorded"),
        ("P", "Inspect heater isolation, temperature-sensor contact and disturbed support interfaces", "New wiring/attachment invalidates any incompatible earlier assembly inspection"),
    ],
    "POWER_CHECK": [
        ("P", "Read output-off state, selected terminals and four-wire mode on each Keithley 2425", "The intended heater circuit is identified before enabling output"),
        ("P", "Verify temperature feedback, force/sense continuity and supplied output limits", "An open sensor, misplaced sense lead or absent limit blocks the power step"),
        ("D", "Associate each control loop with one heater and its own emitter sensor", "White and black feedback channels cannot be exchanged"),
    ],
    "PID_CONFIG": [
        ("D", "Bind the supplied nonempty temperature-target list, gains and independent limits", "Unreported numerical values remain declared inputs rather than copied plot estimates"),
        ("M", "Load the selected PID configuration and verify its sensor/heater association", "Controller readback names the intended pair and current calibration"),
        ("P", "Check stop behavior and confirm heaters remain off until the baseline is accepted", "Controller readiness does not itself energize the devices"),
    ],
    "POWER_BASELINE": [
        ("P", "Verify both heaters are off while temperature and environment streams run", "Passive baseline has no undeclared electrical input"),
        ("X", "Observe emitter stabilization using the declared equilibrium criterion", "Baseline acceptance is based on acquired observations"),
        ("D", "Start the controlled series only after the current session and feedback are valid", "Missing equilibrium or feedback retains an incomplete result"),
    ],
    "PID_STEP": [
        ("M", "Command one bound temperature target and verify feedback selection", "The target belongs to this plateau occurrence and condition"),
        ("X", "Regulate heater power while recording current, heater-terminal voltage and temperature for 300 seconds", "Data remain attributable to this actual five-minute plateau"),
        ("P", "Monitor output limits, temperature validity, shading and environmental interruptions", "Faults end or invalidate the affected plateau without fabricating stabilization"),
    ],
    "STEP_SUMMARY": [
        ("A", "Select the last 120 seconds of a valid 300-second plateau using timestamps", "The averaging window contains actual retained observations"),
        ("A", "Calculate heater power from the four-wire voltage/current and divide by measured emitter area", "W and W/m^2 are separate quantities with sample-specific area provenance"),
        ("A", "Calculate temperature/power summaries and uncertainty under the supplied processing card", "Rejected or missing samples and uncertainty assumptions remain explicit"),
        ("D", "Advance to the next allocated target or the output-off transition", "Each target has its own attempt and summary; missing targets are not silently skipped"),
    ],
    "HEATER_OFF": [
        ("M", "Command both heater outputs off and read back their actual state", "Output-off is observed independently for both source meters"),
        ("X", "Continue temperature acquisition through the declared passive-recooling interval", "Recooling observations follow the output-off event"),
        ("P", "Inspect sensor continuity and retain any unexpected response", "Expected paper cooling is not inserted as a measured trace"),
    ],
    "FIXED_SWAP": [
        ("M", "Return isolated devices to the assembly supports and release the disk/track assemblies", "Removed reflectors are supported and archived with their identities"),
        ("M", "Remove the cover rings and detach each nanoporous sheet using the selected release method", "Both former sheet identities are retired from the current assembly"),
        ("M", "Cut, support and attach two identified LDPE sheets to opposite spacer faces", "Both approximately 50 micrometre layers have traceable stock and inspected attachments"),
        ("M", "Install the 60 mm-wide site/date band reflector and restore the cover and shield", "The fixed band and LDPE are actual replacement components in a new assembly revision"),
    ],
    "FIXED_QC": [
        ("P", "Inspect both LDPE layers, ring separation and aperture alignment", "No earlier nanoporous-cover inspection is reused after replacement"),
        ("P", "Check the band identity, mounting endpoints and computed shading interval", "The band is fixed and spans the intended solar trajectory"),
        ("D", "Accept the changed configuration only with an updated component and condition record", "Both reflector and cover changes are retained in comparison provenance"),
    ],
    "BAND_CHECK": [
        ("P", "Inspect the fixed band's shadow and actual device orientation at session start", "The full emitter aperture is shaded"),
        ("P", "Check shading against the site/date/time interval and observe it during the run", "A fixed band is not adjusted under the tracked-disk operation"),
        ("D", "Invalidate affected intervals if shading is lost", "The fixed-route claim cannot be preserved by silently moving the band"),
    ],
    "MAP_ATTACH": [
        ("M", "Open the supported white device to access the six additional sensor locations", "Emitter and each removed part remain supported and identified"),
        ("M", "Attach six separately calibrated probes at the declared insulation, PE and shield locations", "Each probe is matched to a source-related surface and an explicitly inferred coordinate"),
        ("M", "Route the six leads without bridging gaps or pinching them under the cover", "Probe routes preserve the selected assembly geometry"),
        ("M", "Restore the cover, shield and reflector and connect all seven temperature channels", "Emitter plus six extra channels have distinct labels and a new assembly revision"),
        ("P", "Check each channel and location against the installation map", "A rack of unattached probes does not satisfy sensor installation"),
    ],
    "MAP_CONDITION": [
        ("P", "Observe actual sky condition and local solar time for the selected map leaf", "Clear/scattered-cloud afternoon, clear night and hazy noon remain separate conditions"),
        ("D", "Admit the session only if it meets the supplied condition classification rule", "Weather cannot be established by selecting a route label"),
        ("D", "Disable disk-tracking obligations only for the night condition", "The conditional exclusion is recorded rather than deleting daytime tracking"),
    ],
    "MAP_LOG": [
        ("M", "Start synchronized acquisition for the emitter and all six installed additional sensors", "All seven channels and environmental streams are present"),
        ("X", "Record the selected thermal-map session for 3600 seconds", "The source's one-hour duration applies to this condition occurrence"),
        ("P", "Monitor sensor contact, shading when applicable and environmental eligibility", "Interrupted or invalid intervals retain explicit provenance"),
    ],
    "MAP_SUMMARY": [
        ("A", "Select the declared post-equilibrium interval from each valid sensor trace", "Averaging starts from observed equilibrium rather than a source figure value"),
        ("A", "Associate every average and uncertainty with its physical sensor location", "Measured and modeled temperatures remain distinct records"),
        ("D", "Report unresolved position or contact uncertainty with the affected comparison", "No exact historical coordinate is claimed from an approximate schematic"),
    ],
    "COMPARE": [
        ("A", "Join records only with compatible sample, assembly, calibration and session identities", "Revisions and distinct weather sessions are retained"),
        ("A", "Compute paired white/black and declared configuration comparisons", "Band/LDPE changes and different dates are not represented as a single-variable controlled comparison"),
        ("D", "Classify valid, incomplete and rejected observations without forcing literature agreement", "A valid negative scientific result remains a valid procedural record"),
    ],
    "STOP_SAFE": [
        ("M", "Stop active scans, motion and heater outputs through the actual station interfaces", "Each relevant device reports its stopped/output-off state"),
        ("P", "Inspect payload support, temperature/energy state and unfinished acquisitions", "Uncertain support or output state remains explicit"),
        ("A", "Finalize or mark partial each acquisition while retaining its raw records", "Interrupted attempts are not overwritten"),
    ],
    "UNMOUNT": [
        ("M", "Disconnect accessible isolated leads at the identified terminals and coil them", "Lead identities and endpoints are preserved; no live tether is pulled"),
        ("M", "Support each sample or assembly before releasing its station retainers", "The object transfers to a carrier rather than becoming unsupported"),
        ("P", "Inspect the unloaded object and the vacated fixture", "Damage, missing components and station occupancy are recorded"),
    ],
    "ARCHIVE": [
        ("T", "Transport supported samples and assemblies to their declared storage locations", "Archive location is established by an actual transfer occurrence"),
        ("M", "Seat each object on its labeled storage support and release the carrier retainers", "Physical storage and digital specimen identity agree"),
        ("A", "Save raw files, processing parents, configuration records and attempt histories", "Checksums identify actual stored files rather than hypothetical outputs"),
    ],
    "RESET": [
        ("M", "Return tools, unused materials and detachable accessories to identified supports", "Inventory accounts for remaining stock and all returned equipment"),
        ("M", "Separate offcuts, damaged films and coating residues according to their actual material procedures", "Rejected items cannot silently re-enter accepted sample inventory"),
        ("P", "Inspect and restore fixtures, optical ports, work surfaces and instrument covers", "Stations are left in explicit reusable or isolated states"),
    ],
    "REPORT": [
        ("A", "Compare required branch/condition occurrences with their actual final dispositions", "No selected obligation disappears from the completion denominator"),
        ("D", "Declare complete, partial or aborted only at the evidenced readiness level", "Symbolic walkthrough, rendered geometry and real execution remain different claims"),
    ],
}

EXTRA = [
    ("CAL_BLOCK_PREP", "Prepare the calibration block and probe holes", "WS_FAB", ["STOCK"], ["E_CAL"], ["U_FAB"], [
        ("P", "Identify copper block stock and the proposed hole layout for the reference RTD and eight K probes", "Stock, hole diameters/depths and immersion clearances are defined; these dimensions are reconstructed inputs"),
        ("M", "Seat the copper blank against the selected fixture datums and tighten its clamps", "Block is restrained without a clamp crossing a hole or tool path"),
        ("M", "Fit the selected drill and align the work origin with the marked hole layout", "Tool identity and actual work datum agree with the drawing"),
        ("M", "For each hole, set the bound depth stop and start the installed drilling control", "Each requested hole and depth has a distinct operation record"),
        ("X", "Complete each machine-owned drilling cycle and observe spindle stop", "No access is permitted before the actual stopped state; failed holes remain recorded"),
        ("M", "With tool motion stopped, clear chips and finish each supported hole edge", "Burrs and debris cannot obstruct probe seating"),
        ("M", "Support the block, release its clamps and place it in its labeled carrier", "Block is retained before fixture release"),
        ("P", "Inspect hole sizes, depths, spacing and probe insertion using the declared drawing", "Accepted block and actual hole-to-probe map are available before bath loading"),
    ]),
    ("WITNESS_CUT", "Cut and retain the selected optical specimen", "WS_FAB", ["WITNESS_PREP"], ["E_OPT", "E_FIXED"], ["U_OPT", "U_FAB"], [
        ("P", "Identify the allocated material lot and the compatible specimen/holder drawing", "Material, coating route and aperture coverage are bound to this specimen"),
        ("M", "Clamp the copper/aluminum blank or retain the polymer sheets in a supported cutting jig", "The selected material is supported without stretching or damaging its optical area"),
        ("M", "Cut the specimen profile with the material-appropriate qualified tool, retaining both film layers separately where required", "The produced coupon or film pair has actual dimensions and distinct component identities"),
        ("M", "Finish and clean metal edges or fit the two film layers to the declared optical carrier", "Offcuts are retained separately and the optical area is protected"),
        ("P", "Inspect the specimen and route white/black copper coupons to the explicit three-coat procedure", "Uncoated copper witnesses cannot be accepted as white/black optical samples"),
    ]),
    ("ANGLE_REFERENCE", "Acquire the angular accessory reference", "WS_FTIR", ["ANGLE_MOUNT"], ["E_ANGLE"], ["U_OPT"], [
        ("P", "Read back the installed Harrick or SpectraTech accessory, incidence setting and s/p polarization", "The reference configuration names the same angular optical path as the pending sample scan"),
        ("M", "Support the sample while positioning the qualified angular reference at the declared optical plane", "Sample and reference identities remain distinct and retained"),
        ("X", "Acquire and inspect the reference with the supplied angular scan settings", "The reference is bound to the selected angle and polarization, not a hemispherical sphere"),
        ("M", "Restore the identified sample at the same plane and recheck its angle and polarization", "The measurement configuration has not changed while replacing the reference"),
    ]),
    ("HEATER_REMOVE", "Remove the heater before returning to an unheated assembly", "WS_ASSEMBLY", ["STOP_SAFE"], ["E_POWER", "E_FIXED", "E_MAP"], ["U_WIRING", "U_FAB"], [
        ("P", "Verify both heater channels are isolated and the supported assembly can be opened", "Output-off readbacks and emitter support are established"),
        ("M", "Support the emitter, disconnect heater leads and remove the underside heater using a qualified release method", "Heater, leads and any adhesive residue retain an explicit disposition; the temperature probe is not pulled"),
        ("P", "Inspect the emitter backside, probe attachment and insulation seating after removal", "Damage or changed contact blocks reuse until repair and requalification; replacement creates a new specimen identity"),
        ("M", "Reseat the emitter and restore the insulation/cover stack, then request renewed inspection", "The assembly revision records heater removal and does not inherit earlier QC"),
    ]),
    ("MACHINE_PARTS", "Fabricate emitter, ring, shield and base parts", "WS_FAB", ["STOCK"], ["E_BUILD"], ["U_FAB", "U_GEOM"], [
        ("M", "Fixture the identified copper and aluminum blanks and cut the disk, ring and aperture profiles", "Emitter, reflector, ring and aperture identities link to their stock and drawing dimensions"),
        ("M", "Clamp the aluminum tube, cut its shield section and finish its supported edges", "Shield length and inner/outer diameters are inspected"),
        ("M", "Fixture and cut the PE support tube using the selected compatible machine", "Support dimensions and square seating faces match the reconstruction drawing"),
        ("M", "Cut and drill the supported acrylic base and fit its framing fasteners", "Base, hole positions and frame components are actual fabricated parts"),
        ("M", "Cut two separate foam disks per device using a supported template and guided cutter", "Each layer retains the source's nominal thickness and emitter diameter"),
        ("P", "Deburr, clean, inspect and label every part before transfer", "Accepted parts and offcuts have distinct identities; stock is not magically converted by a receipt"),
    ]),
    ("TRACK_DESIGN", "Compute the selected solar track and fixed-band geometry", "WS_RECORDS", ["PLAN"], ["E_TRACK", "E_GEOM_AMBIG"], ["U_GEOM", "U_OUTDOOR"], [
        ("D", "Bind site, date, solar-time window and selected reflector height datum", "The 100/150 mm source discrepancy remains in the geometry record"),
        ("A", "Calculate the intersection of each emitter-to-sun ray with the chosen horizontal reflector plane", "Every computed position has a time and height reference"),
        ("A", "Construct the track centerline and fixed-band swept region, including mounting interfaces", "Fabrication geometry covers the selected interval rather than an arbitrary straight bar"),
        ("P", "Check shading of the full finite emitter aperture over the interval", "Disk radius, solar angular extent and positioning tolerance are explicitly considered"),
    ]),
    ("WITNESS_PREP", "Allocate matched-lot optical specimens and supported stock", "WS_STOCK", ["STOCK", "COAT_UNLOAD", "FILM"], ["E_OPT", "E_FIXED"], ["U_OPT", "U_FAB"], [
        ("D", "Choose direct component measurement where it fits, or a documented same-batch witness specimen", "The choice is an inference; the paper does not establish every historical sample identity"),
        ("D", "Allocate distinct copper, polished-aluminum, nanoporous film and LDPE blank identities with material and paint parent lots", "White/black specimens are not considered coated merely because they were allocated"),
        ("M", "Pick the allocated stock into separate supported carriers and identify both sheets for each film pair", "The selected stock is physically retained and distinct from the finished cooler assemblies"),
        ("P", "Check the proposed specimen size, film spacing and actual fixture compatibility before cutting", "A full 127 mm cover ring is not assumed to fit every spectrometer holder"),
    ]),
    ("RESTORE_TRACKED", "Restore the tracked nanoporous configuration after the fixed-band route", "WS_ASSEMBLY", ["STOP_SAFE"], ["E_FIXED", "E_MAP"], ["U_GEOM", "U_FAB"], [
        ("M", "Support the isolated assembly and remove the band and LDPE cover", "Retired parts retain their identities and condition history"),
        ("M", "Install an inspected two-layer nanoporous cover and the identified disk track", "The physical configuration again matches the selected tracked route"),
        ("P", "Reinspect attachment, aperture, sensor routing and reflector travel", "A new assembly revision has fresh inspection evidence"),
    ]),
]


def main():
    pin_path=HERE/'historical_input_pins.json'
    if pin_path.exists():
        for name,expected in json.loads(pin_path.read_text()).items():
            actual=hashlib.sha256((OLD/name).read_bytes()).hexdigest()
            if actual!=expected:raise ValueError('Historical input changed; review before repinning: '+name)
    ops = read("operations.json")["operations"]
    for ident, title, station, deps, evidence, inputs, details in EXTRA:
        DETAIL[ident] = details
        ops.append({"id": ident, "title": title, "location_id": station,
                    "depends_on": deps, "evidence_ids": evidence,
                    "unknown_parameter_ids": inputs,
                    "preconditions": ["Identified inputs and required qualified parameter cards are available", "Payload is supported at the bound station"],
                    "postconditions": [d[2] for d in details],
                    "manipulated_objects": {
                        "CAL_BLOCK_PREP": ["copper block stock", "drill", "chips", "reference RTD and K-probe hole pattern"],
                        "WITNESS_CUT": ["allocated copper/aluminum coupon blank", "paired film sheets", "optical carrier", "offcuts"],
                        "ANGLE_REFERENCE": ["optical sample", "qualified angular reference", "angle accessory", "polarization optics"],
                        "HEATER_REMOVE": ["heater", "heater leads", "emitter", "temperature probe", "supported assembly"],
                        "MACHINE_PARTS": ["copper/aluminum stock", "PE tube", "foam sheets", "acrylic blank"],
                        "TRACK_DESIGN": ["site/date and dimensional records", "fabrication drawing"],
                        "WITNESS_PREP": ["identified optical specimens", "holders", "retained parent materials"],
                        "RESTORE_TRACKED": ["white assembly", "fixed band", "LDPE layers", "nanoporous cover", "disk track"]}[ident],
                    "tools_or_interfaces": {
                        "CAL_BLOCK_PREP": ["drilling machine", "block clamping fixture", "depth stop", "deburring tool", "hole and depth gauges"],
                        "WITNESS_CUT": ["material-appropriate cutter", "clamping or film support jig", "edge-finishing tool", "caliper"],
                        "ANGLE_REFERENCE": ["FTIR scan controls", "reference/sample mount", "angle and polarization readback"],
                        "HEATER_REMOVE": ["output-off readback", "emitter support jig", "qualified adhesive-release tool"],
                        "MACHINE_PARTS": ["qualified cutting machines", "clamps", "deburring tool", "caliper", "labeling fixture"],
                        "TRACK_DESIGN": ["solar position calculator", "CAD geometry inspection"],
                        "WITNESS_PREP": ["film support jig", "specimen cutter", "optical holder", "caliper"],
                        "RESTORE_TRACKED": ["assembly carrier", "supported film jig", "fastener driver"]}[ident]})
    # Correct actual producer and preparation gaps in the historical macro graph.
    patches = {
        "FAB_LOAD": ["STOCK", "TRACK_DESIGN"],
        "COAT_LOAD": ["MACHINE_PARTS"],
        "LAYOUT": ["MACHINE_PARTS", "FAB_UNLOAD", "COAT_UNLOAD"],
        "OPT_MOUNT": ["OPT_REFERENCE", "WITNESS_CUT"],
        "ANGLE_MOUNT": ["WITNESS_CUT"],
        "ANGLE_SCAN": ["ANGLE_REFERENCE"],
        "CAL_MOUNT": ["CAL_BLOCK_PREP"],
    }
    kinds = {"P": "perception", "M": "manipulation", "T": "motion",
             "D": "planning", "A": "analysis", "X": "device_process_or_wait"}
    for op in ops:
        ident = op["id"]
        if ident not in DETAIL:
            raise ValueError(f"Missing authored decomposition: {ident}")
        if ident in patches:
            op["depends_on"] = patches[ident]
        op["reference_steps"] = [
            {"id": f"{ident}.{i:02d}", "capability": kinds[kind],
             "action": action, "completion_observation": observation,
             "basis": "reconstruction_inference", "inference_id": f"INF_{ident}"}
            for i, (kind, action, observation) in enumerate(DETAIL[ident], 1)
        ]
        op["success_rule"] = "All required observations must establish the postconditions for this occurrence; an ended or failed attempt does not establish success"
        op["failure_rule"] = "Retain observed support/location/configuration and failed data; acquire missing observations before repair; retry only with a new attempt identity and bounded supplied retry policy"
        op["execution_mode"] = "reconstructed_design_not_controller"
        op["visibility"] = "trusted_author_evaluator"
        op["station_transfer_policy"] = "Insert a bound MOVE occurrence for every payload/station change; record origin, destination, payload, retained support and observations"
        if ident in {'CAL_MOUNT', 'ENV_SETUP'}:
            op['reference_steps'].append({
                'id': ident+'.%02d' % (len(op['reference_steps'])+1),
                'capability': 'perception',
                'action': 'Read back K-type channel configuration and confirm USB-TC manufacturer warm-up requirement before calibration or temperature measurement',
                'completion_observation': 'Channel pairs are configured for the installed probes and a 30-minute powered warm-up has elapsed',
                'basis': 'manufacturer_supplement', 'source_id': 'USB_TC_MANUAL',
                'source_locator': 'USB-TC User Guide, October 2016 Rev 10A, p7; default Type J differs from paper Type K'})
        if ident=='OPT_REFERENCE':
            for action,observation in [
                ('For the selected DTGS IntegratIR configuration, verify bench and accessory power off before connecting the detector cable and seat its model-specific locating pin','Power state, compatible FTIR interface and seated accessory are observed'),
                ('Remove the gold reference protective cap, place the reference over the top sample port and select the declared substitution or Taylor method','Reference identity, selector detent and method are recorded; the cap has a retained location'),
            ]:
                op['reference_steps'].append({'id':ident+'.%02d'%(len(op['reference_steps'])+1),
                    'capability':'manipulation','action':action,'completion_observation':observation,
                    'basis':'manufacturer_supplement','source_id':'PIKE_DTGS_MANUAL',
                    'source_locator':'PIKE PN350-048400-01, 2012, pp3-5; selected detector variant, not established historical configuration'})
            s=op['reference_steps']
            op['reference_steps']=[s[0],s[5],s[1],s[6],s[2],s[3],s[4]]
            for i,step in enumerate(op['reference_steps'],1):step['id']=ident+'.%02d'%i
        op['operator_actions']=[s['action'] for s in op['reference_steps']]
        op['device_process']={
            'FAB_RUN':'Loaded water-jet machine follows the selected cutting program; robot setup, stock clamping, unloading and finishing are separate obligations',
            'COAT_RUN':'Robot applies each coat; drying and curing are timed material processes with observed conditions',
            'OPT_SCAN':'Spectrometer acquires raw signals after physical mounting and reference qualification',
            'ANGLE_SCAN':'FTIR acquires the selected angular/polarized raw spectrum',
            'PID_STEP':'Independent bounded control loops regulate the two heaters while readback is logged',
        }.get(ident,'Only explicitly listed device_process_or_wait and analysis substeps are device/computation-owned; no hidden physical preparation is credited')
        if ident=='FAB_RUN':op['title']='Start and monitor the loaded water-jet cut'
        if ident=='COAT_LOAD':op['title']='Prepare and mask supported emitter disks for coating'
        if ident=='COAT_RUN':
            op.update(title='Apply three coats and observe cure',
                preconditions=['Identified disk is masked and supported','Correct paint can, coating workspace and qualified intercoat/cure inputs are available'],
                postconditions=['Three distinct coats and final cure condition have been observed for this disk'],
                manipulated_objects=['paint can and cap','supported emitter disk','masking'],
                tools_or_interfaces=['spray nozzle','coating fixture','timer and cure inspection'])
    from manipulation_refinement import refine
    ops = refine(ops)
    write("operations.json", {"schema_version": SCHEMA, "doi": read("operations.json")["doi"],
                              "operations": ops})
    branches = read("branches.json")
    branches["schema_version"] = SCHEMA
    for b in branches["branches"]:
        if b['id']=='CALIBRATE':
            b['operation_ids'].insert(b['operation_ids'].index('CAL_MOUNT'), 'CAL_BLOCK_PREP')
        if b["id"] == "BUILD_PAIR":
            b["operation_ids"][3:3] = ["TRACK_DESIGN", "MACHINE_PARTS"]
        if b["id"] in {"OPT_HEMISPHERICAL", "OPT_ANGULAR"}:
            b["operation_ids"].insert(2, "WITNESS_PREP")
            b['operation_ids'][3:3]=['WITNESS_CUT','COAT_LOAD','COAT_RUN','COAT_UNLOAD']
        if b['id']=='OPT_ANGULAR':
            b['operation_ids'].remove('OPT_REFERENCE')
            b['operation_ids'].insert(b['operation_ids'].index('ANGLE_MOUNT')+1,'ANGLE_REFERENCE')
        if b['id']=='BUILD_PAIR':b['notes']='This pilot expands fabrication and coating from identified stock; no prepared-sample service handoff is credited in its reference plan'
        b["count_semantics"] = "Definition membership is not an occurrence count or a physical completion result"
    branches["campaign_reconfiguration"] = {
        "rule": "When reusing a fixed-band/LDPE device for a tracked thermal-map session, run RESTORE_TRACKED and ASSEMBLY_QC before MAP_ATTACH; alternatively allocate a separately built tracked device",
        "historical_reuse_known": False,
        "default_reconstruction": "Restore and re-inspect the same identified white device; keep each assembly revision"
    }
    write("branches.json", branches)
    for name in ["provenance.json", "material_cards.json", "control_packages.json",
                 "unknown_parameters.json", "nonmanual_scope.json", "source_conflicts.json"]:
        d = copy.deepcopy(read(name)); d["schema_version"] = SCHEMA
        write(name, d)
    write("reconstruction_inferences.json", {
        "schema_version": SCHEMA,
        "inferences": [
            {"id": f"INF_{op['id']}", "operation_ids": [op["id"]],
             "source_basis": op.get("evidence_ids", []),
             "physical_basis": "The listed objects must remain identifiable and supported while the specific preparation, connection, measurement or closeout is performed",
             "selected_reconstruction": [s["action"] for s in op["reference_steps"]],
             "rationale": "Expands the macro-stage into observable physical work and explicit device-owned processing",
             "alternatives": ["Use an equivalent supported fixture/tool sequence after checking the same scientific conditions and state predicates"],
             "confidence": "Design hypothesis; source-supported macro purpose with inferred robot handling",
             "validation": "Review source locators, tool and part interfaces, intermediate states and failure paths; measure or qualify missing operating inputs before execution"}
            for op in ops
        ],
        "special_cases": [
            {"id": "INF_COVER_SUPPORT", "operation_ids": ["FILM", "SHIELD"], "source_basis": "SI Note 2 gives a 107 mm ring bore and 102 mm tube OD and calls the tube a cover support; the load-bearing attachment is not described", "selected": "Reconstruct the lower film as a tensioned membrane contacting the PE tube rim and supporting the outer spacer; keep the ring in its loading jig until stability, attachment and sag are qualified", "physical_rationale": "The ring cannot bear directly on a smaller-diameter tube, but the film spans both tube and ring; this supplies a possible continuous load path without silently adding a conductive bracket", "confidence": "Low; a physical reconstruction hypothesis, not established historical mounting or verified load capacity", "alternative": "A disclosed peripheral retaining fixture, with its extra contact and heat-transfer path included in the geometry and analysis", "validation": "Measure the actual ring load, film sag/creep, attachment strength and emitter gap using the installed material; if criteria fail, keep support retained and revise the design. The flat visual film is an unloaded approximation, not a support simulation"},
            {"id": "INF_OPTICAL_SPECIMENS", "selected": "Direct component measurement when compatible; otherwise matched-batch witnesses with explicit size and layer-spacing inputs", "alternative": "Custom holder accommodating the actual component", "validation": "Verify accessory aperture, coating/film equivalence and source interpretation; no historical serial reuse claim"},
            {"id": "INF_REFLECTOR_DATUM", "selected": "Use the text's nominal 150 mm emitter-to-reflector height for the reconstruction; retain the SI 100 mm dimension as unresolved", "alternative": "Reconstruct the schematic version after its datum is established", "validation": "Compare against source drawings and finite-aperture shadow geometry"},
            {"id": "INF_SENSOR_COORDINATES", "selected": "Two additional insulation points near the axis and four PE/shield/aperture contacts have explicit approximate coordinates in sensor_installation.json", "alternative": "Obtain original sensor-location data", "validation": "SI Figure5 p6 re-inspected October17; two insulation locations require explicit recess/layer-interface handling. Positions, azimuth, attachment and changed heat paths remain inferred"},
            {"id": "INF_FINE_WIRE_TRANSITION", "source_basis": ["E_CAL", "E_DAQ_MANUAL", "E_TC_WIRE"], "selected": "Install a K-compatible transition from the 36 AWG stripped probe to terminal-compatible extension conductors, with independent strain relief; calibrate the complete path", "rationale": "The manufacturer's 16-30 AWG terminal range does not cover the source's 36 AWG probe wire", "alternative": "A separately qualified fine-wire clamp/termination with documented thermoelectric behavior", "validation": "Select actual transition hardware, prove retention and polarity, inspect introduced junctions and include the complete connection in calibration. No historical adapter is asserted"},
        ],
    })
    write("revision_origin.json", {
        "schema_version": SCHEMA,
        "supersedes_for_pilot": "directional_cooling_operations_v2",
        "same_paper_not_new_family": True,
        "historical_input_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in sorted(OLD.glob("*.json"))},
        "generator": "authoring.py",
        "geometry_package": "../../assets/cooling_scene_assets_v2",
        "physical_execution_validated": False,
        "previous_published_revision": "f7137685961e3828ad32bf7d399cefa8824b1d62",
        "reconstruction_revision": "2026-10-17.manipulation.1",
        "step_id_policy": "Step IDs are scoped to package content hashes and reconstruction revision; replaced decompositions must not inherit prior step observations",
    })
    print(f"Authored {len(ops)} operations and {sum(len(o['reference_steps']) for o in ops)} reference steps")


if __name__ == "__main__":
    main()
