"""Article-sized ordinary T50L reference; no preload or force qualification."""
import json
from pathlib import Path
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from build_supplies import export_review
from build_cable_ties import stock_tie,BLACK

PARAMETERS=dict(length=.390,head_length=.0072,head_width=.0081,width=.0046,thickness=.0014)


def build():
    g=Geometry();mesh=stock_tie(**PARAMETERS);assert mesh.is_volume and len(mesh.split())==1
    g.add('molded_head_pawl_and_serrated_strap',mesh,BLACK,role='ordinary_long_nonreleasable_cable_tie')
    geometry=export_review(g,'hellermann_t50l_11105440_cable_tie')
    refs=[Path(__file__),HERE/'long_cable_tie_sources.json',HERE/'build_cable_ties.py',HERE/'build_supplies.py',HERE/'weather_station_routes.py',HERE/'geometry_tools.py']
    record=dict(schema_version=1,status='unaccepted_ordinary_long_cable_tie_candidate',geometry=geometry,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        source_dimensions_m=PARAMETERS,selected_family_head_height_m=.0058,conservative_bundle_diameter_m=.110,
        scope='Article-specific nominal dimensions with explicit family drawing differences and inferred local detail. Flattened stock inspection pose only.',
        staged_in_lab=False,initial_stock_credit=False,retention_qualified=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'long_cable_tie_assets.json',record);print(json.dumps(dict(parts=geometry['parts'],geometry=geometry['path'])))


if __name__=='__main__':build()
