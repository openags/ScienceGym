#!/usr/bin/env python3
"""Inspect the hash-pinned R01 scene; optionally render an unchanged fixed review view.
Run with Blender, not system Python. No source save, simulation, imports or GPU use.
See README.md for the complete invocation. All published paths are package-relative.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import time

import bpy
from mathutils import Matrix, Vector

EXPECTED_SHA256 = "bbcf496ca4c1eaa16a56db472e54d944a8d54bc19c7e00073afe32fe9e6ca915"
SOURCE_REL = "assets/r01_complete_route_scene.blend"
SOURCE_FILES = [SOURCE_REL, "assets/r01_complete_route_scene.metadata.json",
                "station_parts.json", "operation_affordances.json", "README_ZH.md",
                "build_r01_scene.py", "static_mesh_helpers.py", "finalize_preview.py",
                "inputs/compression_workstation_authored_v2.mesh.json",
                "inputs/scene_layout_authored_v2.json", "AUTHORED_ALLOWLIST.json"]
# A newly authored human review viewpoint in source world coordinates, not a sensor.
REVIEW_LOCATION = (7.0, 0.3, 2.9)
REVIEW_TARGET = (10.15, 2.25, 1.03)
REVIEW_SCALE = 2.6


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def vec(v):
    return [float(x) for x in v]


def mat(m):
    return [vec(row) for row in m]


def safe(value):
    if isinstance(value, str):
        if not value.isascii():
            return {"text_omitted": "Non-English source text is not republished.",
                    "original_utf8_sha256": hashlib.sha256(value.encode()).hexdigest()}
        if value.startswith("/") or "/workspace/" in value or "/home/" in value:
            return {"text_omitted": "Machine-local source path is not republished.",
                    "original_utf8_sha256": hashlib.sha256(value.encode()).hexdigest()}
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if hasattr(value, "to_dict"):
        return safe(value.to_dict())
    if hasattr(value, "items"):
        return {str(k): safe(v) for k, v in value.items()}
    try:
        return [safe(v) for v in value]
    except TypeError:
        return {"unserialized_type": type(value).__name__}


def bounds(points):
    points = list(points)
    if not points:
        return None
    low = [min(p[i] for p in points) for i in range(3)]
    high = [max(p[i] for p in points) for i in range(3)]
    return {"min": low, "max": high,
            "dimensions": [high[i] - low[i] for i in range(3)]}


def mesh_record(o):
    if o.type != "MESH":
        return None
    me = o.data
    h = hashlib.sha256()
    # Binary little-endian float64 positions, then uint32 topology/material index.
    h.update(struct.pack("<II", len(me.vertices), len(me.polygons)))
    for v in me.vertices:
        h.update(struct.pack("<ddd", *v.co))
    for p in me.polygons:
        h.update(struct.pack("<II?", len(p.vertices), p.material_index, p.use_smooth))
        h.update(struct.pack("<" + "I" * len(p.vertices), *p.vertices))
    return {"datablock_name": me.name, "vertices": len(me.vertices),
            "edges": len(me.edges), "polygons": len(me.polygons),
            "positions_topology_material_indices_smoothing_sha256": h.hexdigest()}


def visibility(o):
    return {"hide_render": bool(o.hide_render), "hide_viewport": bool(o.hide_viewport),
            "hide_get_current_view_layer": bool(o.hide_get()),
            "visible_get_current_view_layer": bool(o.visible_get()),
            **{key: bool(getattr(o, key)) for key in (
                "visible_camera", "visible_diffuse", "visible_glossy",
                "visible_transmission", "visible_volume_scatter", "visible_shadow")
               if hasattr(o, key)}}


def object_record(o, station_matrices):
    sid = o.get("station_id")
    wm = o.matrix_world.copy()
    sm = station_matrices.get(sid)
    verts = [v.co.copy() for v in o.data.vertices] if o.type == "MESH" else []
    result = {"name": o.name, "type": o.type,
              "parent": o.parent.name if o.parent else None,
              "collections": sorted(c.name for c in o.users_collection),
              "matrix_world": mat(wm), "matrix_local": mat(o.matrix_local),
              "matrix_basis": mat(o.matrix_basis), "location": vec(o.location),
              "rotation_mode": o.rotation_mode,
              "rotation_euler_rad": vec(o.rotation_euler), "scale": vec(o.scale),
              "dimensions": vec(o.dimensions),
              "mesh_local_bounds": bounds(verts),
              "world_bounds": bounds(wm @ v for v in verts),
              "station_id": sid,
              "matrix_in_authored_station_frame": mat(sm.inverted() @ wm) if sm else None,
              "authored_station_local_bounds": bounds(sm.inverted() @ wm @ v for v in verts) if sm else None,
              "custom_properties": {k: safe(o[k]) for k in o.keys()},
              "source_visibility": visibility(o),
              "material_slots": [s.material.name if s.material else None for s in o.material_slots],
              "modifiers": [{"name": m.name, "type": m.type,
                             "show_render": m.show_render, "show_viewport": m.show_viewport}
                            for m in o.modifiers],
              "constraints": [{"name": c.name, "type": c.type, "mute": c.mute}
                              for c in o.constraints],
              "rigid_body_present": o.rigid_body is not None,
              "mesh": mesh_record(o)}
    result["record_sha256"] = canonical_hash(result)
    return result


def layer_record(layer):
    return {"name": layer.name, "exclude": layer.exclude,
            "hide_viewport": layer.hide_viewport, "holdout": layer.holdout,
            "indirect_only": layer.indirect_only,
            "children": [layer_record(c) for c in layer.children]}


def camera_record(o):
    d = o.data
    return {"name": o.name, "matrix_world": mat(o.matrix_world),
            "location": vec(o.location), "rotation_euler_rad": vec(o.rotation_euler),
            "type": d.type, "lens_mm": d.lens, "ortho_scale": d.ortho_scale,
            "clip_start": d.clip_start, "clip_end": d.clip_end,
            "shift_x": d.shift_x, "shift_y": d.shift_y,
            "sensor_width_mm": d.sensor_width, "sensor_height_mm": d.sensor_height,
            "sensor_fit": d.sensor_fit, "dof_enabled": d.dof.use_dof}


def lighting_record(scene):
    lights = []
    for o in sorted(scene.objects, key=lambda o: o.name):
        if o.type == "LIGHT":
            d = o.data
            lights.append({"name": o.name, "type": d.type, "energy": d.energy,
                           "color": vec(d.color), "matrix_world": mat(o.matrix_world),
                           "size": getattr(d, "size", None), "shape": getattr(d, "shape", None),
                           "use_shadow": d.use_shadow, "visibility": visibility(o)})
    world = scene.world
    return {"lights": lights, "world": None if not world else {
        "name": world.name, "color": vec(world.color), "use_nodes": world.use_nodes,
        "nodes": [{"name": n.name, "type": n.type,
                   "inputs": {s.name: safe(s.default_value) for s in n.inputs if hasattr(s, "default_value")}}
                  for n in world.node_tree.nodes] if world.use_nodes else []}}


def render_settings(s):
    return {"engine": s.render.engine, "cycles_device": s.cycles.device,
            "cycles_samples": s.cycles.samples, "cycles_seed": s.cycles.seed,
            "cycles_use_animated_seed": s.cycles.use_animated_seed,
            "cycles_use_denoising": s.cycles.use_denoising,
            "cycles_use_adaptive_sampling": s.cycles.use_adaptive_sampling,
            "cycles_max_bounces": s.cycles.max_bounces,
            "cycles_diffuse_bounces": s.cycles.diffuse_bounces,
            "cycles_glossy_bounces": s.cycles.glossy_bounces,
            "cycles_transmission_bounces": s.cycles.transmission_bounces,
            "cycles_transparent_max_bounces": s.cycles.transparent_max_bounces,
            "threads_mode": s.render.threads_mode, "threads": s.render.threads,
            "resolution_x": s.render.resolution_x, "resolution_y": s.render.resolution_y,
            "resolution_percentage": s.render.resolution_percentage,
            "pixel_aspect_x": s.render.pixel_aspect_x, "pixel_aspect_y": s.render.pixel_aspect_y,
            "film_transparent": s.render.film_transparent,
            "use_compositing": s.render.use_compositing, "use_sequencer": s.render.use_sequencer,
            "use_border": s.render.use_border,
            "view_transform": s.view_settings.view_transform, "look": s.view_settings.look,
            "exposure": s.view_settings.exposure, "gamma": s.view_settings.gamma,
            "view_use_curve_mapping": s.view_settings.use_curve_mapping,
            "display_device": s.display_settings.display_device,
            "format": s.render.image_settings.file_format,
            "color_mode": s.render.image_settings.color_mode,
            "color_depth": s.render.image_settings.color_depth,
            "compression": s.render.image_settings.compression,
            "frame_current": s.frame_current}


def strip_text_chunks(path):
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    result = bytearray(data[:8]); i = 8; removed = []
    while i < len(data):
        n = struct.unpack(">I", data[i:i + 4])[0]
        kind = data[i + 4:i + 8]
        chunk = data[i:i + n + 12]
        if kind in (b"tEXt", b"zTXt", b"iTXt", b"eXIf", b"tIME"):
            removed.append(kind.decode())
        else:
            result.extend(chunk)
        i += n + 12
    path.write_bytes(result)
    return removed


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--repeat", type=int, default=2, choices=(1, 2))
    ap.add_argument("--reveal-hidden", action="store_true",
                    help="Reveal originally hidden source mesh objects, logging every changed flag. Never hide geometry.")
    args = ap.parse_args(argv)
    source = args.source.resolve(); out = args.out.resolve(); root = source.parent.parent
    if sha(source) != EXPECTED_SHA256:
        raise RuntimeError("The supplied scene does not match the pinned source SHA256.")
    if root in out.parents or out == root:
        raise RuntimeError("Evidence output must be outside the source package.")
    out.mkdir(parents=True, exist_ok=True)
    source_files = [{"path": rel, "bytes": (root / rel).stat().st_size, "sha256": sha(root / rel)}
                    for rel in SOURCE_FILES]
    metadata = json.loads((root / "assets/r01_complete_route_scene.metadata.json").read_text())
    stations = json.loads((root / "station_parts.json").read_text())["workstations"]
    station_matrices = {}
    for st in stations:
        if "world_center_xy_m" not in st or "authored_yaw_deg" not in st:
            continue
        station_matrices[st["station_id"]] = (Matrix.Translation((*st["world_center_xy_m"], 0)) @
            Matrix.Rotation(math.radians(st["authored_yaw_deg"]), 4, "Z"))
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    if scene.rigidbody_world is not None or any(o.rigid_body for o in scene.objects):
        raise RuntimeError("Unexpected rigid-body configuration; bounded static inspection stopped.")
    bpy.context.view_layer.update()
    objects = [object_record(o, station_matrices) for o in sorted(scene.objects, key=lambda o: o.name)]
    objnames = {o["name"] for o in objects}
    test_names = sorted(o.name for o in scene.objects if o.get("station_id") == "WS_TEST")
    test_manifest = next(st for st in stations if st["station_id"] == "WS_TEST")
    mounted_names = [n for n in test_names if n.startswith("WS_TEST__mounted_")]
    mounted_objects = [bpy.data.objects[n] for n in mounted_names]
    mounted_world = bounds(o.matrix_world @ v.co for o in mounted_objects for v in o.data.vertices)
    sm_inv = station_matrices["WS_TEST"].inverted()
    mounted_station = bounds(sm_inv @ o.matrix_world @ v.co for o in mounted_objects for v in o.data.vertices)
    inv = {"schema_version": "r01_source_inventory_v1", "source_scene_sha256": EXPECTED_SHA256,
           "source_scene": SOURCE_REL, "source_files": source_files,
           "tool": {"name": "Blender", "version": bpy.app.version_string,
                    "build_hash": bpy.app.build_hash.decode(), "inspection": "CPU, static mesh and metadata; no simulation"},
           "scene": {"name": scene.name, "frame_current": scene.frame_current,
                     "object_count": len(objects), "rigid_body_world_present": False,
                     "units": {"system": scene.unit_settings.system, "scale_length": scene.unit_settings.scale_length,
                               "length_unit": scene.unit_settings.length_unit,
                               "rotation_unit": scene.unit_settings.system_rotation,
                               "source_metadata_units": metadata["units"]},
                     "source_active_camera": scene.camera.name if scene.camera else None,
                     "cameras": [camera_record(o) for o in sorted(scene.objects, key=lambda o: o.name) if o.type == "CAMERA"],
                     "lighting": lighting_record(scene), "render_settings": render_settings(scene),
                     "collections": [{"name": c.name, "hide_render": c.hide_render, "hide_viewport": c.hide_viewport}
                                     for c in sorted(bpy.data.collections, key=lambda c: c.name)],
                     "view_layers": [{"name": v.name, "use": v.use,
                                      "layer_collection": layer_record(v.layer_collection)} for v in scene.view_layers]},
           "frame_convention": {"handedness": "right", "up_axis": "Z", "length_unit": "metre",
                                "evidence": "inputs/compression_workstation_authored_v2.mesh.json declares meter/right/Z; source Blender unit scale is recorded above.",
                                "matrices": "row arrays; column-vector transforms; world = matrix_world @ mesh_local_point",
                                "matrix_local_note": "Blender parent-local object matrix; NOT necessarily the authored station-local frame.",
                                "station_local_note": "Derived using station_parts.json origin and yaw, separately from Blender object-local coordinates.",
                                "object_origins": "Authored mesh origins only; no grasp, contact, sensor or joint frames certified."},
           "stations": [{"station_id": st["station_id"], "world_center_xy_m": st.get("world_center_xy_m"),
                         "authored_yaw_deg": st.get("authored_yaw_deg"),
                         "station_to_world": mat(station_matrices[st["station_id"]]) if st["station_id"] in station_matrices else None} for st in stations],
           "ws_test_object_names": test_names,
           "ws_test_resolution": {"declared_count": len(test_manifest["part_ids"]), "actual_count": len(test_names),
                                  "missing_declared_names": sorted(set(test_manifest["part_ids"]) - objnames),
                                  "actual_station_names_not_declared": sorted(set(test_names) - set(test_manifest["part_ids"]))},
           "mounted_sample": {"object_names": mounted_names, "object_count": len(mounted_names),
                              "display_world_bounds_m": mounted_world,
                              "display_station_local_bounds_m": mounted_station,
                              "physical_reference_envelope_m": metadata["dimensions"]["source_specimen_reference_m"],
                              "physical_reference_is": "Source sidecar statement, not a fresh measurement or dimensionally certified mesh.",
                              "display_scale_multiplier": None,
                              "display_scale_note": "No explicit display enlargement factor is declared in the source. Object scales and measured authored mesh bounds are recorded; these do not establish physical calibration.",
                              "robot_compatibility": "Unverified. Do not infer gripper feasibility from this image or object scale."},
           "scope": {"stage_instances": "Simultaneous separately named stage props; not a single live specimen or executable episode initial state.",
                     "physics_executed": False, "robot_executed": False, "collision_validated": False,
                     "visibility_validated_for_robot": False, "grasp_validated": False,
                     "source_device_model": None},
           "objects": [o for o in objects if o["name"] in test_names],
           "object_record_scope": "Full records for the 215 resolved WS_TEST objects; all-scene names and source visibility below.",
           "all_scene_objects": [{"name": o["name"], "type": o["type"],
                                  "source_visibility": o["source_visibility"],
                                  "full_record_sha256": o["record_sha256"]} for o in objects],
           "objects_record_set_sha256": canonical_hash([o for o in objects if o["name"] in test_names]),
           "all_source_object_records_sha256": canonical_hash(objects)}
    (out / "source_inventory.json").write_text(json.dumps(inv, ensure_ascii=True, allow_nan=False, separators=(",", ":")) + "\n")
    write_json(out / "ws_test_object_names.json", {"source_scene_sha256": EXPECTED_SHA256, "object_names": test_names})
    print(json.dumps({"inventory_written": "source_inventory.json", "object_count": len(objects),
                      "ws_test": inv["ws_test_resolution"], "mounted_sample": inv["mounted_sample"],
                      "hidden_mesh_count": sum(o.type == "MESH" and (o.hide_render or o.hide_viewport or o.hide_get()) for o in scene.objects)}), flush=True)
    if not args.render:
        assert sha(source) == EXPECTED_SHA256
        return
    original_visibility = {o.name: visibility(o) for o in scene.objects}
    overrides = []
    if args.reveal_hidden:
        for o in scene.objects:
            if o.type != "MESH":
                continue
            for key in ("hide_render", "hide_viewport"):
                if getattr(o, key):
                    overrides.append({"object": o.name, "property": key, "before": True, "after": False})
                    setattr(o, key, False)
            if o.hide_get():
                overrides.append({"object": o.name, "property": "hide_get_current_view_layer", "before": True, "after": False})
                o.hide_set(False)
        # Collection flags are intentionally not changed; report a blocker rather than silently bypassing them.
    blockers = ["An authored collection has render hiding enabled: " + c.name for c in bpy.data.collections if c.hide_render]
    def excluded(l):
        return ([l.name] if l.exclude or l.holdout or l.indirect_only else []) + [n for c in l.children for n in excluded(c)]
    blockers += ["Excluded, holdout or indirect-only view-layer collection: " + n for n in excluded(bpy.context.view_layer.layer_collection)]
    if blockers:
        write_json(out / "render_receipt.json", {"status": "blocked", "blockers": blockers,
                    "source_scene_sha256": EXPECTED_SHA256, "visibility_overrides": overrides})
        return
    cam_data = bpy.data.cameras.new("REVIEW_WS_TEST_FIXED_camera_data")
    cam = bpy.data.objects.new("REVIEW_WS_TEST_FIXED", cam_data)
    scene.collection.objects.link(cam); cam.location = REVIEW_LOCATION
    cam.rotation_euler = (Vector(REVIEW_TARGET) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam_data.type = "ORTHO"; cam_data.ortho_scale = REVIEW_SCALE
    cam_data.clip_start = 0.01; cam_data.clip_end = 100.0
    scene.camera = cam
    scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"
    scene.cycles.samples = 24; scene.cycles.seed = 0
    scene.cycles.use_animated_seed = False; scene.cycles.use_denoising = False
    scene.cycles.use_adaptive_sampling = False
    scene.render.threads_mode = "FIXED"; scene.render.threads = 4
    scene.render.resolution_x = 1400; scene.render.resolution_y = 1100; scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = 1; scene.render.pixel_aspect_y = 1
    scene.render.film_transparent = False; scene.render.use_border = False
    scene.render.use_compositing = False; scene.render.use_sequencer = False
    scene.render.image_settings.file_format = "PNG"; scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"; scene.render.image_settings.compression = 15
    scene.render.use_stamp = False
    bpy.context.view_layer.update()
    fixed_camera = camera_record(cam)
    expected_visibility = {o.name: visibility(o) for o in scene.objects if o != cam}
    receipt = {"schema_version": "r01_static_review_render_v1", "status": "rendering",
               "source_scene": SOURCE_REL, "source_scene_sha256": EXPECTED_SHA256,
               "source_inventory_sha256": sha(out / "source_inventory.json"),
               "script": "inspect_source.py", "script_sha256": sha(Path(__file__)),
               "tool": inv["tool"], "camera": fixed_camera, "camera_target_world_m": list(REVIEW_TARGET),
               "camera_role": "New fixed human review viewpoint; not a source robot sensor or validated robot observation.",
               "visibility_overrides": overrides,
               "visibility_policy": "No source geometry removed, moved, enlarged or hidden for rendering. Source material transparency is unchanged. All occluding geometry is retained; originally hidden objects are revealed only when listed.",
               "material_overrides": [], "lighting_overrides": [], "lighting": lighting_record(scene),
               "render_settings": render_settings(scene),
               "setting_changes": {}, "outputs": [],
               "source_visibility_unchanged_except_listed": True,
               "physical_and_robot_validation": "Not performed: physics, contacts, collisions, reachability, grasping, robot sensing, manufacturing and scientific measurement.",
               "source_unchanged": None}
    receipt["setting_changes"] = {k: {"before": inv["scene"]["render_settings"].get(k), "after": v}
                                  for k, v in receipt["render_settings"].items()
                                  if v != inv["scene"]["render_settings"].get(k)}
    write_json(out / "render_receipt.json", receipt)
    for index in range(args.repeat):
        assert camera_record(cam) == fixed_camera
        filename = "ws_test_review.png" if index == 0 else "ws_test_review_repeat.png"
        output = out / filename; scene.render.filepath = str(output)
        start = time.monotonic(); bpy.ops.render.render(write_still=True); elapsed = time.monotonic() - start
        removed = strip_text_chunks(output)
        receipt["outputs"].append({"path": filename, "bytes": output.stat().st_size, "sha256": sha(output),
                                   "elapsed_seconds": round(elapsed, 3), "metadata_chunks_removed": removed,
                                   "camera_unchanged": camera_record(cam) == fixed_camera})
        write_json(out / "render_receipt.json", receipt)
    receipt["repeat_file_hash_identical"] = len(receipt["outputs"]) == 2 and receipt["outputs"][0]["sha256"] == receipt["outputs"][1]["sha256"]
    receipt["source_unchanged"] = sha(source) == EXPECTED_SHA256
    receipt["source_object_transforms_unchanged"] = all(o.matrix_world == Matrix(next(r["matrix_world"] for r in objects if r["name"] == o.name)) for o in scene.objects if o != cam)
    receipt["source_mesh_data_unchanged"] = all(mesh_record(o) == next(r["mesh"] for r in objects if r["name"] == o.name) for o in scene.objects if o != cam)
    receipt["source_visibility_unchanged_except_listed"] = all(visibility(o) == expected_visibility[o.name] for o in scene.objects if o != cam)
    receipt["source_lighting_unchanged"] = lighting_record(scene) == inv["scene"]["lighting"]
    receipt["status"] = "complete"
    assert receipt["source_unchanged"]
    assert receipt["source_object_transforms_unchanged"]
    assert receipt["source_mesh_data_unchanged"]
    assert receipt["source_visibility_unchanged_except_listed"]
    assert receipt["source_lighting_unchanged"]
    assert {o.name for o in scene.objects if o != cam} == set(original_visibility)
    assert all(o.matrix_world == Matrix(next(r["matrix_world"] for r in objects if r["name"] == o.name)) for o in scene.objects if o != cam)
    write_json(out / "render_receipt.json", receipt)
    print(json.dumps({"render_status": receipt["status"], "outputs": receipt["outputs"],
                      "repeat_file_hash_identical": receipt["repeat_file_hash_identical"],
                      "source_unchanged": receipt["source_unchanged"]}), flush=True)


if __name__ == "__main__":
    main()
