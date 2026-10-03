# Acoustic edge-detection task design

Original ScienceGym whole-paper design for Molerón and Daraio, *Acoustic metamaterial for subwavelength edge detection*, Nature Communications 6, 8037 (2015), DOI [10.1038/ncomms9037](https://doi.org/10.1038/ncomms9037).

Read `TASK_DESIGN.md` first. Seven physical acquisition branches share explicit printed-guide fabrication, target preparation and four-channel rig setup. The package also covers the paper’s numerical/theoretical program without executing it.

Schema: `acoustic_edge_paper_task.v1`. This is a package-local schema, not a universal ScienceGym runtime API. There is no supported robot execution command.

Run from this directory:

```sh
python3 -B -m unittest discover -s tests -v
python3 -B tests/verify_package.py
```

These checks inspect static contracts and synthetic records only. They do not establish physical feasibility, trusted event authentication, scientific replication, solver correctness or real hardware safety.

Main article and all required supplementary text were available for the audit. Main PDF bytes were not obtained; its hash remains null. Only original English task descriptions, concise metadata and tests are bundled. Publisher PDFs, full text, figure pixels and private source receipts are excluded. All numerical outcomes and reference routes are evaluator/author context, never default actor input.
