"""Source-surface identity regression for millimetre-scaled proximity queries."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'assets/unitree_g1_inspire_v1'))
from build_distal_collision import clean, surface_distance

source = ROOT / 'assets/unitree_g1_inspire_v1/vendor/unitree_ros/meshes/right_thumb_4.STL'
components = clean(trimesh.load(source, force='mesh')).split(only_watertight=False)
outer = max((p for p in components if p.is_watertight and p.volume > 0), key=lambda p:p.volume)
points = np.vstack([outer.vertices, outer.triangles_center, outer.vertices[outer.edges_unique].mean(axis=1)])
raw = trimesh.proximity.closest_point(outer, points)[1]
metric = surface_distance(outer, points)
report = dict(scope=__doc__, samples=len(points), source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
              unscaled_max_identity_distance_m=float(raw.max()), scaled_max_identity_distance_m=float(metric.max()),
              identity_threshold_m=1e-8, passed=bool(metric.max()<1e-8),
              physical_qualification=False, builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(HERE/'metric_scale_review.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report), flush=True)
if not report['passed']:
    raise SystemExit(1)
