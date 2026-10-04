# Source-to-asset audit

Reference: https://www.nature.com/articles/s41467-024-46319-3

All six final main figures were inspected as original source pixels, alongside the source auditor’s main/SI readings and role plan. Source pixels were inspection-only and are absent from Blender, GLBs, renders and the public archive.

- Figures 1–2: cavity-coupled MZI/PIC and detector roles are represented by sealed-package identity and a separate original role legend. Circuit topology, micrograph pads, mask and electrode layout were not copied. The Figure 2 caption/implementation text supplies the native 0.95 × 0.48 mm nominal footprint, represented as a zero-thickness reference plane
- Figure 3: the reported ring width/circumference and 220 nm silicon cross-section remain metadata. No ring CAD or field simulation was reconstructed
- Figure 4: capped ECDL/VOA calibration roles and separate sniffer/error record names. No calibration, response curve or grating alignment is inferred
- Figure 5: three disabled DFB modules; closed TIA/PID panel; final comb-referenced independent heterodyne service separated from relative FPGA in-loop acquisition. No PSD, linewidth, suppression or lock result appears
- Figure 6 and SI numerical studies: design console only. No physical SiN setup or numerical solver is supplied

The source audit’s 18 roles are covered by ten grouped assets. Exact mappings and evidence IDs are in source_comparison.json. Task-side stable IDs, 46 canonical anchors and 44 operation roles are copied into task_binding_snapshot.json and operation_bindings.json. Two additional unqualified grasp anchors support the empty carrier visual only.

Both physical heaters remain off. The 100 nm process label is not substituted for the reported 220 nm silicon geometry. Final comb-referenced acquisition governs over historical delayed self-heterodyne review material. SiN’s unresolved density discrepancy does not get silently repaired; numerical reproduction remains unavailable. Source outcomes and private evaluator fixtures are not exported in this asset package.

All apparatus/package/PCB/cable/fiber dimensions and placements are original unqualified choices. Native 0.95 × 0.48 mm reference and 1000× display are distinct scenes/GLBs, with the scale applying only to the planar footprint. Fifteen AFM carrier/clamp meshes retain original topology and scale and carry zero new credit. The sealed package is visibly separate from the empty carrier. There is no physical fit, collision, optical, thermal or electronics validation.
