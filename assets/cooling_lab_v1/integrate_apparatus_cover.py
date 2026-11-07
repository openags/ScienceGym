"""Apply the reviewed cover geometry to each completed reference configuration.

This changes asset states only. Stock, controls, membrane forces and owner
acceptance are separate requirements.
"""
import json
import numpy as np
import trimesh
from geometry_tools import HERE, ROOT, sha
from build_stock_cutplan import load_parts
from build_apparatus_cover import membrane
from build_apparatus_mounting import display


def apply_cover(scene, prefix, film_gauge):
    record=json.loads((HERE/'apparatus_cover_candidate.json').read_text())
    assert sha(ROOT/record['geometry']['path'])==record['geometry']['sha256']
    ledger=json.loads((HERE/'apparatus_cover_sources.json').read_text())
    parts=load_parts(record['geometry']['path'])
    center=scene.geometry[prefix+'lift_plate'].bounds.mean(axis=0)
    center[2]=scene.geometry[prefix+'lift_plate'].bounds[1,2]
    rebuilt=[];added=[]
    if film_gauge!=.000016:
        selection=ledger['selected_geometry_hypothesis']
        adhesive=ledger['adhesive_candidate']['nominal_adhesive_thickness_mm']*.001
        bottom=selection['ring_bottom_above_platform_mm']*.001
        top=bottom+ledger['paper']['facts']['ring_thickness_mm']*.001
        lower=membrane(film_gauge,selection['pe_support_height_mm']*.001,bottom-adhesive,
                       np.array(selection['lower_membrane_transition_radius_mm'])*.001)
        upper=trimesh.creation.cylinder(.0635,film_gauge,sections=256)
        upper.apply_translation([0,0,top+adhesive+film_gauge/2])
        for name,m in [('cover_lower',lower),('cover_upper',upper)]:
            m=display(m);m.visual=parts[name].visual.copy();parts[name]=m
    for suffix,m in parts.items():
        if suffix=='emitter_white_coating' and prefix=='COOLER_BLACK__':suffix='emitter_black_coating'
        name=prefix+suffix
        if name in scene.geometry:
            # Keep the source configuration's white/black coating appearance;
            # the repaired shape does not silently turn both emitters white.
            if suffix.startswith('emitter_') and suffix.endswith('_coating'):
                m.visual=scene.geometry[name].visual.copy()
            rebuilt.append(name)
        else:added.append(name)
        # Keep thin films close to their local origin. Baking the fixed
        # configuration's 1.65 m offset into float32 vertices creates actual
        # foil/substrate intersections; a node translation preserves precision.
        if name in scene.geometry:scene.delete_geometry(name)
        scene.add_geometry(m,node_name=name,geom_name=name,transform=trimesh.transformations.translation_matrix(center))
    return dict(rebuilt_parts=rebuilt,added_parts=added,translation_m=center.tolist(),
        nominal_film_gauge_m=film_gauge,material='LDPE' if film_gauge==.000050 else 'nanoporous_PE',
        template_geometry=record['geometry'],platform_size_m=[.180,.180,.005],coordinate_storage='local_vertices_with_node_translation',
        physical_installation_qualified=False,
        scope='Completed-state asset candidate. Fixed-band film is rebuilt at 50 micrometres; tracked films retain 16 micrometres. No initial-stock, adhesion, membrane equilibrium or controller credit.')
