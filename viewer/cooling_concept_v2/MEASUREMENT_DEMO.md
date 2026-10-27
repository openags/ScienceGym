# Continuous cross-workstation FTIR demonstration

This demonstration follows one already fabricated white witness through the
mid-infrared measurement operation described by Bhatia et al.,
DOI [10.1038/s41467-018-07293-9](https://doi.org/10.1038/s41467-018-07293-9).
It uses the existing complete laboratory, one official Unitree G1 29DoF
rev1.0 and Inspire FTP hands. The Cary-side bench is a material pickup point;
Cary spectroscopy is outside this particular procedure.

From the repository root:

```bash
python simulation/cooling_v1/serve.py --port 8769 --bind 127.0.0.1
```

The repository server supports the byte ranges needed for video seeking.

The player also includes a synchronized workstation map, a full-laboratory
view and clickable stations. Share `measurement_demo.html#t=40.564` to start
at the outbound walk or `#t=94.801` at the loaded return. The map follows
3,325 samples extracted from the 12,988 published video-frame poses, including
phase changes and the final frame. Its room and furniture footprints come
from the same scene manifest. These navigation samples describe the authored
video, not sensor observations or a qualified physical trajectory.

To rebuild the map after restoring the publication's frame archive:

```bash
python viewer/cooling_concept_v2/build_measurement_route.py
```

The builder checks the video, capture receipt, source scene, episode and
uncompressed frame digest against the published record. The page refuses
to display a map associated with a different video hash. Adding this player
navigation does not modify the clean video or its geometry review.

Open `http://localhost:8769/viewer/cooling_concept_v2/measurement_demo.html`
for the video and chapter navigation, or
`http://localhost:8769/viewer/cooling_concept_v2/index.html?episode=ftir_measurement`
for interactive playback. The video page becomes available when
`measurement_delivery.json` records a successful publication.

The 541.14-second timeline has 103 continuous segments: open the prepared
instrument; collect ordinary tweezers; walk to the material bench; collect
and carry back the same white witness; install the gold standard; close the
cover and press BACKGROUND / OK; protect and store the standard; install the
witness; close the cover and press SAMPLE / OK; unload, return the tool and
close the compartment. Both acquisition waits are compressed to 12 seconds.
The flow and source manuals are recorded in `single_measurement_demo.json`.
The executable timeline is `single_measurement_episode.json`.

The independent checks use source triangles and exported robot-link poses,
including actual tweezer deformation. `measurement_delivery.json` links the
review of every encoded video frame as well as the independent 0.1-second
sampling with operation boundaries. The video itself has no text overlays,
watermarks or diagnostic panels. The acquisition configuration is an initial
condition; neither measured spectra nor physical controller success are
claimed. Contact forces, balance, sensor-only control, full-paper branches
and repeatability remain separate work.

To rerun a review, restore a chunked trace if needed and run:

```bash
python viewer/cooling_concept_v2/audit_frames_archive.py PATH_TO_AUDIT --restore
python viewer/cooling_concept_v2/review_measurement_episode.py PATH_TO_AUDIT --run
```

Review folders are immutable evidence. For a fresh run, use a new folder with
`export.json`, `source/` and the matching `frames.jsonl.gz`; existing `verifiers/`
are not overwritten. The exact executed checker sources are retained there.
Independent self-collision checks are partitioned by frame for parallelism;
ordered joint-velocity checks use the entire unsplit trace.

The operating-clearance variant in `assets/nicolet_6700_mechanism_v1` changes
four stationary parts and preserves 189 others. Its hinge seats, seams and
key wells are inferred reconstruction details. The instrument's original
source meshes remain available. `measurement_failures.json` records the
rejected compositions and aborted renders that led to this delivery.
