# Laboratory long-horizon concept video

This is the owner's requested **conceptual presentation** in the existing ScienceGym laboratory. The exported film is clean: no text overlay, watermark, implementation notes or validation labels. It shows one source-derived Unitree G1 / Inspire robot moving between the existing laboratory stations and outdoor area. Open `watch.html` through the repository's localhost server for the video and chapter navigation; `index.html` provides the interactive choreography.

The selected paper route is temperature-probe calibration, optical reference/sample handling, preparation of the identified white and black apparatus, acquisition wiring, cart transport, outdoor placement, covered baseline, aluminum-lid removal, reflector adjustment, acquisition shutdown and collection. The same two apparatus and the same cart persist through the route. The scene loads all 81 base asset instances and the original architecture with their SHA-256 values checked. Existing furniture and rooms are retained; the apparatus, cart and selected acquisition electronics receive explicit staging and handling transforms.

`workflow.json` maps each chapter to the existing paper operation package and records assumptions. It starts from already fabricated/coated assemblies and prepared calibration/optical inputs. Fine fastening, film handling, individual terminations, settling and repeated readings are visually condensed. The five-minute covered baseline is compressed for presentation, with lid removal kept after that interval in the logical sequence. No numerical scientific result is generated. This film does not depict every alternative configuration or weather-dependent paper branch.

Motion is authored kinematic animation. Arm poses and a grounded foot cycle use the source robot joint chain; they are not a physical simulation qualification. The earlier contact experiment remains a separate component test in `simulation/g1_cooling_demo/`. Conceptual motion does not add skill, branch or campaign qualification credit.

To reproduce on the current workstation, run from the repository root:

```sh
python -m http.server 8769 --bind 127.0.0.1
OPENBLAS_NUM_THREADS=1 MUJOCO_GL=egl /tmp/sciencegym-sim-venv/bin/python viewer/cooling_concept_v1/build_poses.py
/tmp/sciencegym-sim-venv/bin/python viewer/cooling_concept_v1/capture.py
```

The exporter uses the installed Chromium headless shell, NVIDIA Vulkan rendering, deterministic scene time and FFmpeg H.264 output at 1280 × 720 / 24 fps. `export_receipt.json` pins source files, loaded asset hashes and the resulting video, and checks that source files were unchanged during export. Chromium hardware backend selection follows the [Chromium headless GPU documentation](https://chromium.googlesource.com/chromium/src.git/+/main/docs/gpu/using-gpu-hardware-in-headless-chrome.md). The on-screen controls are outside the captured canvas.
