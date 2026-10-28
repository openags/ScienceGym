"""Selected stock-to-part envelopes, independent of robot task/controller code."""
import json
from pathlib import Path
import numpy as np
import trimesh
from shapely.geometry import MultiPoint,box
from shapely.affinity import translate
from geometry_tools import HERE,ROOT,sha,write_json


def load_parts(path):
    scene=trimesh.load(ROOT/path,force='scene');out={}
    for node in scene.graph.nodes_geometry:
        matrix,key=scene.graph[node];m=scene.geometry[key].copy();m.apply_transform(matrix);out[node]=m
    return out


def derive():
    supplies=json.loads((HERE/'supplies.json').read_text());apparatus=json.loads((HERE/'apparatus_stock_reconciliation.json').read_text())
    frame_stock=json.loads((HERE/'frame_stock.json').read_text())
    cover_stock=json.loads((HERE/'cover_stock.json').read_text())
    stock={i['id']:load_parts(i['geometry']['path']) for i in supplies['items'] if i['id'] in
           ['copper_sheet_stock','aluminum_sheet_stock','foam_stock','acrylic_stock','pe_tube_stock','aluminum_tube_stock','nano_pe_stock','ldpe_stock','mylar_stock']}
    stock.update({i['id']:load_parts(i['geometry']['path']) for i in frame_stock['items']})
    stock.update({i['id']:load_parts(i['geometry']['path']) for i in cover_stock['items']})
    built={i['id']:load_parts(i['geometry']['path']) for i in apparatus['items']};sheets=[]
    def sheet(asset,part):
        m=stock[asset][part]
        entry=dict(id=asset+'/'+part,asset_id=asset,part=part,size_m=m.extents[:2].tolist(),thickness_m=float(m.extents[2]),
                   edge_and_cut_clearance_m=.001,cuts=[])
        sheets.append(entry);return entry
    def add(target,identity,profile,position,thickness,basis,**extra):
        profile=translate(profile,-profile.bounds[0]+position[0],-profile.bounds[1]+position[1])
        target['cuts'].append(dict(id=identity,outline_m=[list(p) for p in profile.exterior.coords],
            required_thickness_m=thickness,basis=basis,**extra))
    def part(target,identity,device,name,position):
        prefix={'cooler_white':'COOLER_WHITE__','cooler_black':'COOLER_BLACK__','cooler_fixed':'COOLER_FIXED_BAND__'}[device]
        mesh=built[device][prefix+name]
        add(target,identity,MultiPoint(mesh.vertices[:,:2]).convex_hull,position,float(mesh.extents[2]),
            'Conservative XY convex envelope of the actual selected output mesh; does not remove internal holes or prove machining',
            output_template=dict(asset_id=device,part=prefix+name))
    cu=sheet('copper_sheet_stock','raw_copper_sheet');foam=sheet('foam_stock','raw_foam_sheet')
    al1=sheet('aluminum_sheet_stock','raw_aluminum_1mm');al15=sheet('aluminum_sheet_stock','raw_aluminum_1_5mm');al64=sheet('aluminum_sheet_stock','raw_aluminum_6_4mm')
    al5=sheet('aluminum_sheet_stock','raw_aluminum_5mm')
    for i,color in enumerate(['white','black']):
        device='cooler_'+color
        part(cu,color+'_emitter',device,'emitter_copper',[.01+i*.07,.01])
        for layer in [1,2]:part(foam,color+'_foam_'+str(layer),device,'foam_'+str(layer),[.01+(i*2+layer-1)*.065,.01])
        acrylic=sheet('acrylic_stock','raw_acrylic_sheet_'+str(i+1));part(acrylic,color+'_base',device,'acrylic_base',[.02,.01])
        part(al1,color+'_aperture',device,'aperture_plate',[.01+i*.18,.01]);part(al1,color+'_reflector',device,'solar_reflector',[.01+i*.08,.20])
        part(al15,color+'_track',device,'reflector_track',[.002,.01+i*.05]);part(al15,color+'_fixed_band','cooler_fixed','fixed_reflector_band',[.002,.11+i*.095])
        part(al64,color+'_spacer',device,'film_spacer',[.01+i*.145,.01])
        part(al5,color+'_lift_platform',device,'lift_plate',[.01+i*.19,.01])
    add(cu,'unallocated_copper_witness_reserve',box(0,0,.200,.100),[.01,.10],.0005,
        'Reserved uncut region only; white/black optical sample shapes, multiplicity and holder compatibility remain unresolved',reservation_only=True)
    for i,color in enumerate(['white','black']):
        foil=sheet('mylar_stock','raw_film_'+str(i+1));device='cooler_'+color
        part(foil,color+'_base_foil',device,'mylar_base',[.01,.01])
        for layer in [1,2]:
            add(foil,color+'_foam_wrap_'+str(layer),box(0,0,.165,.027),[.325,.01+(layer-1)*.04],.000012,
                'Selected flat blank for a 50 mm diameter by 25 mm curved surface, 3 mm lap and trimming allowance',
                wrapped_surface=dict(diameter_m=.050,height_m=.025,lap_m=.003))
    foil=sheet('mylar_stock','raw_film_3')
    for i,color in enumerate(['white','black']):
        add(foil,color+'_support_wrap',box(0,0,.330,.060),[.01,.01+i*.08],.000012,
            'Selected flat blank for a 102 mm diameter by inferred 51 mm curved surface, 3 mm lap and trimming allowance',
            wrapped_surface=dict(diameter_m=.102,height_m=.051,lap_m=.003))
    for asset,count,thickness in [('nano_pe_stock',8,.000016),('ldpe_stock',6,.000050)]:
        for i in range(1,count+1):
            target=sheet(asset,'raw_film_'+str(i))
            if i<=4:role=['white','black'][(i-1)//2]+'_layer_'+str((i-1)%2+1)
            elif asset=='nano_pe_stock' and i<=6:role='white_restore_layer_'+str(i-4)
            else:role='shortwave_witness_reserve' if i==count-1 else 'infrared_witness_reserve'
            reserve='reserve' in role
            add(target,asset+'_'+role,box(0,0,.140,.140),[.01,.01],thickness,
                'Selected uncut reserve for a separate instrument; final specimen shape and holder fit are not established' if reserve else
                '140 mm square blank around the 127 mm selected cover outline; edge attachment and final trimming unqualified',
                reservation_only=reserve,finished_cover_diameter_m=None if reserve else .127)
    tube_rows=[]
    for asset,kind,inner,outer in [('pe_tube_stock','pe',.076,.102),('aluminum_tube_stock','aluminum',.140,.152)]:
        for i,color in enumerate(['white','black'],1):
            name='raw_'+kind+'_tube_'+str(i);m=stock[asset][name]
            tube_rows.append(dict(id=color+'_'+kind+'_section',asset_id=asset,part=name,raw_length_m=float(m.extents[2]),
                finished_length_m=.051 if kind=='pe' else .057,cut_allowance_m=.001,inner_diameter_m=inner,outer_diameter_m=outer,
                output_template=dict(asset_id='cooler_'+color,part='COOLER_'+color.upper()+'__'+('PE_support' if kind=='pe' else 'radiation_shield')),
                basis='PE height 51 mm is a cover reconstruction hypothesis; aluminum shield height 57 mm is source reported',qualified=False))
    adhesive_stock=next(i for i in cover_stock['items'] if i['id']=='cover_adhesive_stock')
    for reservation in adhesive_stock['reservations']:
        target=sheet(adhesive_stock['id'],reservation['raw_part']);diameter=reservation['outer_diameter_m']
        add(target,reservation['id'],box(0,0,diameter,diameter),[(.160-diameter)/2]*2,reservation['finished_gauge_m'],
            'Conservative square envelope around one selected adhesive annulus; liner handling and actual cutting unqualified',
            attachment_reservation=reservation)
    frame_sheets={name:sheet('frame_machining_stock',name) for name in ['frame_plate_3mm','frame_clamp_block_20mm','frame_carriage_plate_4mm']}
    used={name:0 for name in ['bridge','lower_clamp','upper_clamp','lower_carriage','upper_carriage']}
    for requirement in frame_stock['machining_requirements']:
        ref=requirement['output_template'];name=ref['part'];mesh=built[ref['asset_id']][name];target=frame_sheets[requirement['blank']]
        kind='bridge' if 'frame_bridge' in name else 'lower_clamp' if 'lower_clamp' in name else 'upper_clamp' if 'upper_clamp' in name else 'lower_carriage' if name.endswith('lower') else 'upper_carriage'
        i=used[kind];used[kind]+=1
        position={'bridge':[.010+(i%4)*.060,.010+(i//4)*.040], 'lower_clamp':[.010+i*.050,.010],
                  'upper_clamp':[.010+i*.050,.085], 'lower_carriage':[.250+i*.030,.010], 'upper_carriage':[.010+i*.035,.010]}[kind]
        thickness=target['thickness_m'];finished=float(mesh.extents[2])
        add(target,requirement['id'],MultiPoint(mesh.vertices[:,:2]).convex_hull,position,thickness,
            'Selected blank reserved for the actual machined-part envelope; bores, split, tap and surface-finish processes are not implemented',
            output_template=ref,output_finished_thickness_m=finished,facing_allowance_m=max(0.,thickness-finished))
    frame_profile=next(i for i in frame_stock['items'] if i['id']=='frame_profile_stock')
    for row in frame_profile['tube_cuts']:
        tube_rows.append(dict(**row,asset_id='frame_profile_stock',part=row['id'],axis_index=0,inner_diameter_m=.014,outer_diameter_m=.020,
            basis='Selected 250 mm hollow stock; finished length measured from the nominal frame, with separate 1 mm cutting allowance',qualified=False))
    profiles=[dict(id=u['id'],asset_id='frame_profile_stock',part=u['id'],length_m=.340,output_template=u['output_template'],
        basis='Selected vendor cut-to-length purchase; no historical SKU confirmation or supplier tolerance acceptance',qualified=False)
        for u in frame_profile['units'] if u['kind']=='purchased_340mm_profile']
    requirements=[
        ('consumables:consumable_01',None,'copper_sheet_stock',1),('consumables:consumable_02','aluminum sheet stock','aluminum_sheet_stock',7),
        ('equipment:COOLER','frame extrusion stock','frame_profile_stock',4),('equipment:COOLER','upright tube stock','frame_profile_stock',4),
        ('consumables:consumable_12','frame fasteners','frame_mount_hardware',84),
        ('consumables:consumable_02','aluminum angle stock','cover_angle_stock',1),
        ('consumables:consumable_12','shield attachment hardware','cover_mount_hardware',18),
        ('additional_reconstructed_materials:film_attachment_stock','film attachment adhesive stock','cover_adhesive_stock',12),
        ('consumables:consumable_12','height-adjuster mount fasteners','lift_mount_hardware',24),
        ('consumables:consumable_02','aluminum tube stock','aluminum_tube_stock',2),('consumables:consumable_03',None,'pe_tube_stock',2),
        ('consumables:consumable_04',None,'foam_stock',1),('consumables:consumable_10',None,'acrylic_stock',2),
        ('consumables:consumable_05',None,'nano_pe_stock',8),('consumables:consumable_06',None,'ldpe_stock',6),('consumables:consumable_09',None,'mylar_stock',3)]
    return dict(schema_version=1,status='selected_cut_envelopes_not_manufacturing_or_campaign_acceptance',
        sheets=sheets,tubes=tube_rows,profiles=profiles,angle_cuts=next(i for i in cover_stock['items'] if i['id']=='cover_angle_stock')['cuts'],component_allocations=[dict(resource_id=r,component_label=l,asset_id=a,selected_required_stock_units=q,
            additional_asset_ids=['frame_machining_stock'] if l=='aluminum sheet stock' else []) for r,l,a,q in requirements],
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [Path(__file__),HERE/'supplies.json',HERE/'apparatus_stock_reconciliation.json',HERE/'stock_sources.json',HERE/'frame_stock.json',HERE/'cover_stock.json']],
        limits=['Material identity, tolerances, kerf, ordinary workholding, tools, surface finishing and fabrication remain unqualified',
                'Convex profiles reserve material; they are not executable tool paths, manipulation steps or fabricated parts',
                'Optical witness stock is reserved separately, but holder-compatible sample formats and copper witness allocation remain unresolved',
                'The third PE tube is unallocated reserve. No retry, failed-cut or repeated-validation budget is claimed',
                'Frame stock quantities are selected, but machining, tool access, tolerances and stock restraint are unqualified; coatings, adhesive and service consumption still need allocation'],
        campaign_complete=False,owner_acceptance=None)


def build():
    out=derive();write_json(HERE/'stock_cutplan.json',out)
    print(json.dumps(dict(stock_sheets=len(out['sheets']),cut_envelopes=sum(len(s['cuts']) for s in out['sheets']),tube_sections=len(out['tubes']))))


if __name__=='__main__':build()
