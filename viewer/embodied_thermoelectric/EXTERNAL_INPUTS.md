# Optional external inputs for a visual rebuild

The public player and all 45 JPEG frames are self-contained within this folder. Opening `index.html` requires no source assets, server, network service, controller or physics engine. The static renders and documentation can be reviewed without running any Python or Blender command.

The following existing inputs are intentionally not redistributed. Obtain only copies you are authorized to use; their expected hashes are recorded in `external_inputs.json` and the original `render_receipt.json`.

| Environment variable | Required input |
| --- | --- |
| `THERMO_SCENE` | The first-party `thermoelectric_scene_v3` folder, including `assets/thermoelectric_lab_scene.blend`, `station_parts.json`, `sample_instances.json` and the provenance/integrity JSON files listed in `external_inputs.json` |
| `G1_ASSETS` | The licensed G1 visual source folder, containing `g1_with_hands.xml` and its referenced `assets/` STL files |
| `THERMO_TASKS` | The public English `tasks/thermoelectric_operations_v2` folder at the pinned ScienceGym commit, including `branches.json` and `operations.json` |

The task source is [ScienceGym at commit 2f926a9d2c2b8a0c71e8939feaa6ca5696e14c27](https://github.com/openags/ScienceGym/tree/2f926a9d2c2b8a0c71e8939feaa6ca5696e14c27/tasks/thermoelectric_operations_v2).

The scripts require explicit directory values for these variables and stop with a clear message if an input is missing. They have no private-directory fallback or automatic download. The older corrected importer package is not required: its transform logic is included in `scripts/build_visual.py`, and its historical SHA-256 remains recorded solely for provenance.

Use Blender 4.3.2, CPU Cycles with denoising disabled, and Python 3 with Pillow. DejaVu Sans regular and bold fonts are used for the existing captions. `THERMO_FONT` and `THERMO_BOLD_FONT` may point to alternative authorized font files; changed fonts produce different image hashes. Node.js is needed only for `node test_player.js`.

Rebuilding creates local `raw/` intermediates and replaces local renders/metadata, so work from a separate copy if you want to preserve the supplied image freeze. These scripts perform static/kinematic visualization only. They do not run MuJoCo, policies, dynamics, material processing, vacuum/thermal/electrical equipment or scientific acquisition.

After changing any public file, regenerate the public file manifest and checksums before treating an earlier export receipt as current. The original render receipt continues to describe the original image-producing run; it is not evidence that a later rebuild was validated.
