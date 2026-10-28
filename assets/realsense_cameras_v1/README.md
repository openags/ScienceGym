# Added camera candidates

One RealSense D455 is selected for head RGB-D and two D405 units for wrist RGB.
They are separately staged on the assembly bench. None is mounted, calibrated
or producing an observation stream. D405 depth is not added to the wrist actor
channels merely because the hardware supports it.

`vendor/` retains unmodified mesh and nominal-frame inputs from the manufacturer's
`realsenseai/realsense-ros` repository at the commit in `sources.json`, with its
Apache 2.0 license. The generated GLBs retain the source triangles; conversion
changes millimetres to metres and rotates the source axes to Z-up. Independently
named shallow front-glass/lens appearance overlays and material assignments are
authored from the linked photographs and drawing optical spacing. Local panel
insets, lens diameters and overlay relief are inferred. They do not qualify optical
or collision geometry. Source photographs
and the full datasheet are not redistributed.

The D455 source mesh has open edges and is only used for visual inspection.
No mesh repair, smoothing or invented closed collision shell is credited as
manufacturer geometry. The D405 source mesh is closed; neither model has a
qualified dynamic description. Installation requires a revision-specific
mount, USB routing and strain relief, calibrated optics/extrinsics, and a
clearance check through the robot's full arm motion.

```bash
OPENBLAS_NUM_THREADS=1 python assets/realsense_cameras_v1/build.py
OPENBLAS_NUM_THREADS=1 python assets/realsense_cameras_v1/validate.py
```

Validation independently checks original-input hashes, bidirectional vertex
distance, triangle counts, metric envelopes, selected channels and unqualified
installation/calibration state. It does not certify camera accuracy or mounting.
