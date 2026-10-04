# Task-design boundary

## Purpose and scene
One atmospheric-optics paper is translated into eight route families and 28 branches. Protected sensor components and telescope interfaces are physical objects; the atmosphere and astronomical target are observed, not transported specimens. Frame sequences, local fields, inferred layers and model samples do not increase the paper count.

## Physical workflow
Prepare identified components, carry them in a qualified protected carrier, load the guarded alignment station, read stage/camera/MLA identity and geometry calibration, and retrieve a qualified module. Transfer it to the observatory-owned dock, verify support and retention at the native image plane, obtain an authorized acquisition job, read actual camera settings and frame/timestamp completeness, then retrieve data and return hardware through a safe-release/park gate. Daytime imaging is a separate qualified apparatus branch because its written configuration is incomplete. All poses, forces, adapter geometry and hazardous service programs remain unresolved.

## Measurement and computation
A registered observation may enter REALIGN without fresh capture. Calibration, data hashes, frame membership and target/timebase remain attached through slope and Noll reconstruction. Each use is an explicit branch instance: correction can use set-29-like 15 Hz lineage while prediction uses qualified 30 Hz lineage. No dependency edge asserts that different historical experiments used the same frames. Correction joins compatible image/wavefront lineage; prediction requires chronological train/test targets and train-only fitted normalization. DIMM is a read-only calibrated record service. SLODAR output is an altitude inference from correlations. TIS never moves a piezo stage.

## Source tensions and gaps
Keep the 1000/7000 covariance scopes, 856/865 arcsec field values, and 195 nm versus 224.10-to-109.84 nm RMSE statements. The 6000-frame prediction corpus is not fully mapped from the 7000 frames listed by SI. Fine-tuning corpus membership is unknown. General 1000-frame SLODAR guidance is distinct from the 300-frame demonstration. Camera gain, bit depth, format, readout, synchronization, thermal stabilization and calibration are unspecified. Main equations require independent implementation checks; main figures were not inspected as pixels.

## Numerical and conceptual boundaries
Pitch/noise/C-SHWS/plenoptic/phase-screen/outer-scale/point-source branches are numerical optics. They are not robot or atmosphere simulators. The source communication diagrams do not supply an operating uplink; no laser or deformable-mirror command is present. The meta-sensor piezo route is an external comparison, not WWS actuation.

## Verification
The package tests state progression, provenance, calibration, readout binding, safety and information separation using visibly synthetic records. No measured arrays, operating card, qualified scene, production authority or physics implementation is supplied. Successful tests cannot establish real execution, replication or apparatus readiness.

## Mounted custody and capture continuity
MOUNT leaves the sensor installed under a versioned mounted lease. Camera LOAD/RETRIEVE transfer jobs and records, never hardware. An episode closes every observation job before qualified park/isolation, supported detach and safe storage. Remounting invalidates the lease and requires new geometry calibration. Prediction windows must stay within an individual timestamp-contiguous capture and within a train/test partition. Historical sets 20-26 have capture gaps and must not be concatenated as uninterrupted time. The source training loss compares shifted output sequences; next-frame testing is separately specified.
