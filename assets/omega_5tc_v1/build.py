"""Source-constrained 5TC-TT-K-36-36 probe in an authored coiled storage shape."""
import json
from pathlib import Path
import sys
import numpy as np
import trimesh

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'assets/cooling_lab_v1'))
from geometry_tools import Geometry,sha,write_json


def sweep(points,half_width,half_height,sections=12):
    points=np.asarray(points);tangent=np.gradient(points,axis=0);tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    radial=np.cross(tangent,[0,0,1]);radial/=np.linalg.norm(radial,axis=1)[:,None]
    vertical=np.cross(radial,tangent)
    angle=np.arange(sections)*2*np.pi/sections
    vertices=(points[:,None,:]+half_width*np.cos(angle)[None,:,None]*radial[:,None,:]+half_height*np.sin(angle)[None,:,None]*vertical[:,None,:]).reshape((-1,3))
    faces=[]
    for i in range(len(points)-1):
        for j in range(sections):
            k=(j+1)%sections;a=i*sections;b=(i+1)*sections
            faces.extend([[a+j,b+j,b+k],[a+j,b+k,a+k]])
    for j in range(1,sections-1):
        faces.extend([[0,j+1,j],[(len(points)-1)*sections,(len(points)-1)*sections+j,(len(points)-1)*sections+j+1]])
    mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=True);mesh.fix_normals();return mesh


def path_segment(path,start,end,count):
    distance=np.r_[0,np.linalg.norm(np.diff(path,axis=0),axis=1).cumsum()]
    at=np.linspace(start,end,count)
    return np.column_stack([np.interp(at,distance,path[:,i]) for i in range(3)])


def build():
    theta=np.linspace(0,6*np.pi,361);radius=.9/(6*np.pi);pitch=.00038
    coil=np.column_stack([radius*np.cos(theta),radius*np.sin(theta),.00019+pitch*theta/(2*np.pi)])
    tail=(1-np.linalg.norm(np.diff(coil,axis=0),axis=1).sum())/2
    path=np.vstack([coil[0]-[0,tail,0],coil,coil[-1]+[0,tail,0]])
    g=Geometry()
    jacket=path_segment(path,.002,.980,420)
    g.add('pfa_outer_jacket',sweep(jacket,.00035,.00019),[189,143,47],role='inferred_insulation_envelope')
    # Short welded junction and split stripped lead termination. The catalogue
    # establishes the type, not these selected local stripping dimensions.
    for i,side in enumerate([-1,1]):
        junction=path_segment(path,0,.002,16);junction[:,0]+=side*.00014*np.linspace(0,1,len(junction))
        g.add('junction_conductor_'+str(i),sweep(junction,.000065,.000065),[169,171,176],role='thermocouple_conductor',metal=.8)
        terminal=path_segment(path,.980,1.,50);terminal[:,0]+=side*(.00014+.0048*np.linspace(0,1,len(terminal))**2)
        g.add('terminal_insulation_'+str(i),sweep(terminal[:31],.000125,.000125),[222,179,62] if i==0 else [158,40,34],role='inferred_insulation_envelope')
        g.add('stripped_terminal_'+str(i),sweep(terminal[30:],.000065,.000065),[169,171,176],role='thermocouple_conductor',metal=.8)
    bead=trimesh.creation.icosphere(subdivisions=2,radius=.00011);bead.apply_translation(path[0]);g.add('welded_junction',bead,[160,165,171],role='inferred_weld',metal=.75)
    for mesh in g.scene.geometry.values():
        mat=mesh.visual.material;c=np.asarray(mat.baseColorFactor[:3],dtype=float)/255
        mat.baseColorFactor=np.r_[np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4),1.]
    (HERE/'geometry').mkdir(exist_ok=True);file=HERE/'geometry/omega_5tc_tt_k_36_36.glb';file.write_bytes(g.scene.export(file_type='glb'))
    model=dict(schema_version=1,id='omega_5tc_tt_k_36_36',manufacturer='Omega',model='5TC-TT-K-36-36',
        geometry=dict(path=str(file.relative_to(ROOT)),sha256=sha(file),bounds_m=g.scene.bounds.tolist(),parts=g.parts),
        nominal_cable_centerline_m=path.tolist(),centerline_length_m=float(np.linalg.norm(np.diff(path,axis=0),axis=1).sum()),
        conductor_diameter_m=.00013,selected_outer_insulation_width_height_m=[.0007,.00038],
        source_ledger_sha256=sha(HERE/'sources.json'),builder_sha256=sha(__file__),
        source_constraints=['36 AWG conductor diameter 0.13 mm','TT insulation is PFA','Length suffix 36 selects nominal 1 m in this catalogue','Stripped lead termination; welded measurement junction'],
        inference_scope=['Coiled rest shape, jacket envelope, stripping lengths, local weld and insulation colours are authored estimates.',
          'The nominal bundle centerline is 1 m; split-end strand lengths and historical supplied length are not measured.',
          'Hidden conductor interiors are omitted. These are static visual parts, not a deformable/electrical model.'],
        dynamic_cable_qualified=False,electrical_termination_qualified=False,temperature_measurement_implemented=False,
        scene_quantity_selected=8,complete_campaign_quantity_accepted=False,
        assembly_state='loose_stored_probe_not_attached_or_connected')
    write_json(HERE/'model.json',model)
    print(json.dumps({'probe_model':'5TC-TT-K-36-36','nominal_centerline_m':model['centerline_length_m'],'parts':len(g.parts)}))


if __name__=='__main__':build()
