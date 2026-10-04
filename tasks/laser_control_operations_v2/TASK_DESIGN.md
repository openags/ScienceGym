# Modulation-free laser stabilization: whole-paper task design

## Scope and completion classes

This original English design accounts for the complete final article, six main figures, all 17 supplementary pages, six notes, eight supplementary figures and both tables for DOI 10.1038/s41467-024-46319-3. Peer-review history is ancillary version evidence. Fifteen scientific design routes preserve the entire paper workflow. Whole-paper design coverage is distinct from verified execution: no fabrication, hardware operation, source-data reproduction or scientific simulation occurred here.

The task includes the full PIC design, qualified foundry fabrication, PCB and wirebond packaging route. Missing design files and settings are required-input gates, not reasons to delete preparation from the design. A separate prepared-package entry does not earn preparation credit. All laser, electrical, alignment and control work is represented by closed qualified-service interfaces. No real command adapter is supplied.

## Design and preparation

Freeze application wavelength, target linewidth, area/cost, platform loss, cavity/TRN budget and optical/electronic link budget. Preserve the silicon cavity-coupled MZI, Euler ring, balanced detection, tuners and sniffer roles. Require released foundry-authorized PIC design, independent mode/coupling validation and process cards before requesting fabrication. Bind its PIC lot/serial to independently released PCB, bond map, assembly inspection and final package. The source's 100 nm AIM process label is not the 220 nm silicon thickness shown in the ring cross-section. Exact PIC layout and board files are unavailable.

Equal-area cavity-MZI/PDH/unbalanced-MZI comparison, ring-gain sensitivity, electronic and shot-noise budgets, waveguide TRN, ring analytical/FEM TRN and cavity-technology tradeoffs remain separate model contracts. The approximation and validity domain of each model must travel with its results. No solver is run here.

## Physical characterization and three DFB routes

Receive and inspect an identified safe package; verify qualified optical/electrical services; dock it under a fresh mount revision; independently verify the closed enclosure and interlocks; request alignment; independently confirm coupling, polarization and optical power plane. Calibrate the time-frequency axis using the qualified reference; request an open-loop sweep; acquire simultaneous sniffer and balanced-error traces; fit the ring response; calibrate signed, dimensional discriminator gain and its linear range with uncertainty. A request acknowledgement never proves completion. Source heaters were off during reported open-loop and locking measurements.

For each of the three identified DFB devices, verify its driver and laser FM response, current-noise condition and source-independent safe limits. Verify the independent reference laser/FP/comb chain, repetition and CEO locks, filtered beat identity, digitizer and reference floor. The source deliberately adjusted the laser bias-current noise to accentuate the demonstration; this condition must remain visible when interpreting results. Freeze TIA/PID/filter/polarity/current limits, bias-noise, power, temperature, heater and analysis cards before acquiring the matched free-running baseline. Request lock; independently observe lock stability without clipping, saturation or cycle slip; acquire separate FPGA in-loop and comb-referenced independent heterodyne records. Changing a DFB, mount, calibration, gain, bias-noise, reference lock or other frozen condition invalidates dependent comparisons.

Validate raw lineage, clocks, sample rate, anti-aliasing, PSD convention, frequency units, window, RBW/ENBW, stationarity, reference floor and complete analyzed support before calculating suppression, declared-band RMS, unity-crossing loop bandwidth and finite-band beta-separation linewidth. In-loop error measures laser relative to the cavity and cannot establish absolute laser noise or remove cavity TRN. Preserve negative suppression and servo bumps. RMS, integral linewidth and Lorentzian linewidth are not interchangeable. Report missing integration tails and uncertainty rather than extending unmeasured spectra.

Finally request qualified safe off, independently verify optical/electrical isolation, undock the supported package, inspect, archive both successful and failed attempts, and store or quarantine it. Unknown isolation keeps the package contained. Damage prevents reuse until qualified release. Neither a UI card nor a command acknowledgement establishes safety.

## Numerical SiN example and source-version limits

The silicon-nitride example is numerical only. Preserve its model geometry, optical and electronic assumptions, current-driver/servo bandwidths and source Table 1 values separately from the silicon experiment. The printed density is 3.29 x 10^2 kg/m3; retain the anomaly and require an explicit model-input decision and sensitivity analysis before a reproduction claim. Do not silently replace it with an expected density. No physical SiN station is required.

The final paper uses comb-referenced heterodyne and FPGA in-loop analysis. Earlier delayed self-heterodyne methods and earlier RMS/linewidth claims in peer review are superseded. Reported final outcomes are evaluator reference only, never acceptance thresholds or generated data. The paper does not establish independent replicate counts or complete raw analysis settings.

## Offline verification boundary

Actor events contain only an event ID, operation ID and evidence ID. The synthetic evaluator supplies a fixed registry independently; exact fixture identity and content are checked before typed semantics and sequence checks. The full-preparation route checks external-service records without performing fabrication. The prepared route never claims upstream work. Three DFB identities, preparation choices, repeat variants, safe holds, interrupted-lock closure and damage quarantine exercise the contract. Synthetic values are authored independently of published outcomes.

The implemented arithmetic validates scalar V/Hz conversion and complete finite one-sided PSD arrays, integrates RMS by trapezoids and clips linear PSD segments against the beta line for a finite-band linewidth estimate. It is not a measured spectrum, FFT, servo simulator, physical safety controller or authenticated real-service record system. A malicious evaluator can forge a new external world; public test fixtures are intentionally audit-readable.

Scene assets are original rigid illustrative meshes. Native source PIC dimensions and display enlargement remain separate. No source figures, traced geometry, datasets, author code, fabrication recipes or hidden hazardous instructions are exported. The exact export allowlist excludes local source copies, scratch files, caches and logs.
