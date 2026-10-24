"""Original ProtoMAX reconstruction from manufacturer dimensions and diagrams.

Selected for the authored laboratory, not identified as the paper's machine.
The transparent lid and access geometry are inspectable; no process/safety
interlock, hydraulic circuit, cutting controller or robot execution is implied.
"""
import math
import numpy as np
import trimesh
from geometry_tools import Geometry,HERE,sha,write_json

WHITE=[215,220,224];BLACK=[24,29,33];STEEL=[145,157,168]

class CatalogGeometry(Geometry):
    def add(self,name,mesh,color,role='structure',metal=0,alpha=255):
        c=np.asarray(color[:3])/255
        linear=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
        return super().add(name,mesh,np.round(linear*255).astype(int).tolist(),role,metal,alpha)

def build():
    g=CatalogGeometry()
    # The selected table enclosure occupies part of the published system
    # footprint. Local proportions and separate pump placement are estimates.
    for x in [-.28,.28]:
        for y in [-.34,.34]:
            g.cylinder(f'caster_{x}_{y}',.045,.030,[x,y,.045],BLACK,axis=(1,0,0))
            g.box(f'caster_fork_{x}_{y}',[.052,.038,.07],[x,y,.095],STEEL,metal=.7)
            g.box(f'frame_post_{x}_{y}',[.035,.035,.70],[x,y,.47],STEEL,metal=.7)
    for z in [.15,.43,.79]:
        g.box('frame_front_'+str(z),[.595,.035,.035],[0,-.34,z],STEEL,metal=.7)
        g.box('frame_back_'+str(z),[.595,.035,.035],[0,.34,z],STEEL,metal=.7)
    for side in [-1,1]:
        g.rounded_panel('side_panel_'+str(side),.65,.68,.008,[side*.31,0,.47],.025,WHITE)
        # Rounded panels use XZ by default; turn side panels into YZ.
        mesh=g.scene.geometry['side_panel_'+str(side)]
        mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[0,0,1],point=[side*.31,0,.47]))
        g.parts[-1]['bounds_m']=mesh.bounds.tolist()
    g.rounded_panel('front_panel',.575,.68,.008,[0,-.365,.47],.025,WHITE)
    g.rounded_panel('rear_panel',.575,.68,.008,[0,.348,.47],.025,WHITE)
    g.label('front_identity','ProtoMAX',.30,.065,[0,-.370,.64],[215,220,224],[32,36,39])
    # Catcher tank is hollow: bottom, separate walls and rim, no opaque top.
    g.box('catcher_bottom',[.64,.72,.018],[0,0,.75],BLACK)
    for x in [-.325,.325]:g.box('catcher_side_'+str(x),[.025,.78,.18],[x,0,.84],BLACK)
    for y in [-.39,.39]:g.box('catcher_edge_'+str(y),[.675,.025,.18],[0,y,.84],BLACK)
    for x in [-.337,.337]:g.box('upper_rim_side_'+str(x),[.025,.805,.03],[x,0,.945],BLACK)
    for y in [-.4025,.4025]:g.box('upper_rim_edge_'+str(y),[.70,.025,.03],[0,y,.945],BLACK)
    # Manufacturer table 368 x 393 mm, distinct from 304 x 304 XY travel.
    for i in range(24):g.box('bed_slat_'+str(i),[.002,.393,.035],[-.184+i*.368/23,0,.91],STEEL,metal=.85)
    for y in [-.20,.20]:g.box('bed_support_'+str(y),[.39,.018,.025],[0,y,.88],STEEL,metal=.8)
    for x in [-.24,.24]:
        g.box('stage_rail_'+str(x),[.027,.58,.03],[x,.02,.99],STEEL,metal=.85)
        g.box('stage_bearing_'+str(x),[.06,.075,.045],[x,.13,1.025],BLACK)
    g.box('gantry',[.56,.065,.06],[0,.13,1.07],STEEL,metal=.8)
    for i in range(32):
        g.cylinder('bellows_'+str(i),.034 if i%2==0 else .028,.014,[-.23+i*.014,.13,1.12],BLACK,axis=(1,0,0))
    g.box('nozzle_carriage',[.06,.075,.11],[-.05,.08,1.065],STEEL,metal=.8)
    g.cylinder('nozzle_body',.012,.055,[-.05,.04,1.00],STEEL,metal=.85)
    g.cylinder('mixing_tube',.0035,.05,[-.05,.04,.955],STEEL,metal=.85)
    g.cylinder('splash_guard',.025,.004,[-.05,.04,.94],[189,148,35])
    # Rear mounted abrasive hopper remains fixed while the lid opens.
    g.profile('abrasive_hopper',[(0,0),(.018,0),(.048,.08),(.048,.20),(0,.20)],
              [115,89,68],position=(-.25,.27,1.235),alpha=150)
    g.cylinder('hopper_cap',.050,.008,[-.25,.27,1.431],STEEL,metal=.8)
    g.tube('abrasive_feed',[[-.25,.27,1.235],[-.22,.15,1.18],[-.05,.04,1.05]],.004,BLACK)
    # Clear clamshell: front window, roof and two end windows; no hidden
    # release mechanism is claimed. 85 degrees is an inspection hypothesis.
    for key,size,p in [('front',[.64,.004,.32],[0,-.39,1.12]),
      ('roof',[.64,.74,.004],[0,-.02,1.282]),
      ('left',[.004,.74,.32],[-.32,-.02,1.12]),('right',[.004,.74,.32],[.32,-.02,1.12])]:
        g.box('lid_'+key,size,p,[202,222,230],role='transparent_cover',alpha=65)
    g.tube('lid_front_gasket',[[-.32,-.393,.962],[-.32,-.393,1.28],[.32,-.393,1.28],[.32,-.393,.962]],.006,BLACK)
    g.tube('lid_handle',[[-.055,-.23,1.285],[-.055,-.23,1.32],[.055,-.23,1.32],[.055,-.23,1.285]],.008,BLACK)
    for x in [-.31,.31]:g.cylinder('lid_hinge_'+str(x),.019,.04,[x,.35,.96],STEEL,axis=(1,0,0),metal=.85)
    for x in [-.26,.26]:
        for z in [.20,.72]:g.cylinder('panel_screw_'+str(x)+'_'+str(z),.004,.003,[x,-.354,z],STEEL,axis=(0,1,0),metal=.8)
    g.cylinder('isolator_plate',.047,.008,[.300,-.15,.52],[221,181,32],axis=(1,0,0))
    g.cylinder('isolator_knob',.027,.020,[.311,-.15,.52],[160,28,25],axis=(1,0,0))
    # Separate pump subassembly inside the cabinet, as shown in the exploded
    # table assembly. Covers remain fitted; hoses are inactive geometry.
    g.box('pump_base',[.28,.30,.035],[0,0,.23],STEEL,metal=.75)
    g.box('pump_cover',[.20,.21,.16],[0,0,.3275],WHITE)
    g.cylinder('pump_motor',.074,.22,[0,0,.47],BLACK,axis=(0,1,0))
    for i in range(12):g.ring('motor_fin_'+str(i),.071,.079,.004,[0,-.10+i*.018,.47],STEEL,axis=(0,1,0),metal=.75)
    g.tube('inactive_pump_line',[[0,0,.52],[.20,.28,.65],[.20,.28,.90],[.17,.27,1.11]],.006,STEEL)
    g.box('rear_electrical_enclosure',[.32,.224,.27],[.13,.527,1.04],WHITE)
    for i in range(11):g.box('rear_vent_'+str(i),[.13,.001,.004],[.13,.6395,.955+i*.012],BLACK)
    # Standard laptop shelf and generic computer (historical laptop unspecified).
    g.box('laptop_support',[.30,.29,.018],[-.504,-.02,1.02],BLACK)
    g.box('laptop_base',[.28,.23,.012],[-.504,-.02,1.035],BLACK)
    g.box('laptop_display',[.28,.012,.18],[-.504,.09,1.13],BLACK)
    g.box('laptop_screen',[.25,.001,.15],[-.504,.083,1.13],[45,62,68])
    for i in range(10):
        for j in range(4):g.box(f'laptop_key_{i}_{j}',[.018,.015,.001],[-.604+i*.022,-.065+j*.020,1.042],[67,72,77])
    out=g.export('omax_protomax')
    source=HERE/'waterjet_sources.json'
    record=dict(schema_version=1,id='omax_protomax',status='selected_catalog_reconstruction_not_accepted',
      geometry=out,source_ledger_sha256=sha(source),builder_sha256=sha(__file__),
      paper_model_identified=False,process_qualified=False,safety_interlocks_implemented=False,
      inspection=dict(kind='hinge',parts=[p['id'] for p in g.parts if p['id'].startswith('lid_') and not p['id'].startswith('lid_hinge')],
        axis=[1,0,0],pivot_m=[0,.35,.96],maximum=-math.radians(85),
        basis='85 degree visual opening hypothesis; actual hinge limits and internal clearances unqualified'),
      manufacturer_dimensions=dict(system_footprint_m=[1.054,1.004],closed_height_m=1.435,open_height_m=1.854,table_m=[.368,.393],xy_travel_m=[.304,.304]),
      limits=['Local shape and subassembly placements estimated from manufacturer illustrations',
        'Overall envelope constrained by published footprint; enclosure/laptop local dimensions remain inferred, not an installation drawing',
        'Closed hopper envelope matches 1.435 m; selected lid sweep is not the manufacturer 1.854 m measurement',
        'No qualified clamping, nozzle setup, control UI, abrasive/water supply, drain, grounding or pressure circuit'])
    write_json(HERE/'waterjet.json',record)
    print('ProtoMAX source-based geometry candidate: '+str(out['parts'])+' parts')

if __name__=='__main__':build()
