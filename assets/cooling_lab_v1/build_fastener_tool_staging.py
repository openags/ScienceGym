"""Allocate four reusable ordinary tools to explicit initial bench positions."""
import json
from pathlib import Path
from geometry_tools import HERE, ROOT, sha, write_json


def build():
    tools=json.loads((HERE/'fastener_tools.json').read_text());by_id={i['id']:i for i in tools['items']};items=[]
    for identity,model,label,component,x in [
        ('hex_driver_2','wiha_26320','Wiha 26320 · 2 mm 内六角','2 mm straight hex driver',2.28),
        ('hex_driver_2_5','wiha_26325','Wiha 26325 · 2.5 mm 内六角','2.5 mm straight hex driver',2.53),
        ('hex_driver_3','wiha_26330','Wiha 26330 · 3 mm 内六角','3 mm straight hex driver',2.78),
        ('wrench_8','stahlwille_40080808','Stahlwille OPEN BOX 13 · 8 mm','8 mm open and box wrench',3.03)]:
        model=by_id[model];assert sha(ROOT/model['geometry']['path'])==model['geometry']['sha256']
        items.append(dict(id=identity,label=label,model_id=model['id'],geometry=model['geometry'],resource_id='tools:fastener_driver',
            component_label=component,unit='reusable_hand_tool',selected_required_units=1,
            station='assembly_white',position_m=[x,3.35,.9],
            units=[dict(id=identity,parts=[p['id'] for p in model['geometry']['part_records']])],
            scope='One shared reusable tool for sequential assembly of the selected pair; selected reconstruction, not paper procurement or qualified two-hand use.',
            initial_state_qualified=False,quantity_accepted=False,owner_acceptance=None))
    record=dict(schema_version=1,status='selected_initial_tool_stock',items=items,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [Path(__file__),HERE/'fastener_tools.json',HERE/'fastener_tools_sources.json']],
        stock_units=4,selected_policy='Reuse one of each hex size and one wrench; a driver and wrench are separate simultaneous physical objects. Device-accessory fasteners not covered by these selections remain unresolved.',
        retry_tool_replacement_budget=None,stock_qualified=False,owner_acceptance=None)
    write_json(HERE/'fastener_tool_staging.json',record);print(json.dumps(dict(tool_units=4,stock_qualified=False)))


if __name__=='__main__':build()
