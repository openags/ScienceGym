"""Reconcile foil, source-scale central mounting and nominal frame geometry.

The historical Blender bundle is immutable input. Derived changes are listed
explicitly. Commercial dimensions and authored apparatus connections remain
distinct; no static mesh grants physical assembly or owner acceptance.
"""
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE,ROOT,sha,write_json,imported_scene
from build_apparatus_mounting import apply_mount, build_stock
from build_apparatus_frame import apply_frame

THICKNESS=.000012
LAP=.003


def wrap(radius,height,center,position_guard):
    # A nominal rolled strip with a selected 3 mm overlap. The second turn
    # lies outside the first; the short radial transition is a bend hypothesis.
    theta=np.r_[np.linspace(0,2*np.pi,1025),np.linspace(2*np.pi,2*np.pi+LAP/radius,33)[1:]]
    # Circumscribe the substrate's measured outer circle. An inscribed coarse
    # mesh cuts through differently tessellated substrate faces. The sub-micron
    # faceting/float32 allowance is recorded separately from the film gauge.
    faceting_allowance=radius/np.cos(np.diff(theta).max()/2)-radius+position_guard
    base_radius=radius+faceting_allowance
    extra=THICKNESS*np.clip((theta-(2*np.pi-.001/radius))/(.001/radius),0,1)
    vertices=[];faces=[]
    for angle,offset in zip(theta,extra):
        for r,z in [(base_radius+offset,-height/2),(base_radius+offset+THICKNESS,-height/2),(base_radius+offset+THICKNESS,height/2),(base_radius+offset,height/2)]:
            vertices.append([r*np.cos(angle),r*np.sin(angle),z])
    for i in range(len(theta)-1):
        for j in range(4):
            a=4*i+j;b=4*i+(j+1)%4;c=b+4;d=a+4;faces.extend([[a,b,c],[a,c,d]])
    faces.extend([[0,2,1],[0,3,2]])
    a=4*(len(theta)-1);faces.extend([[a,a+1,a+2],[a,a+2,a+3]])
    m=trimesh.Trimesh(vertices=np.array(vertices)+center,faces=faces,process=False);m.fix_normals()
    assert m.is_watertight
    return m,float(faceting_allowance)


def build():
    build_stock()
    source='assets/cooling_scene_assets_v2/geometry/cooling_pilot.glb';items=[]
    for identity,prefix in [('cooler_white','COOLER_WHITE__'),('cooler_black','COOLER_BLACK__'),('cooler_fixed','COOLER_FIXED_BAND__')]:
        g=imported_scene(source,prefix=prefix);changes=[]
        def mesh(suffix):
            matrix,key=g.graph[prefix+suffix];assert np.allclose(matrix,np.eye(4));return key,g.geometry[key]
        key,base=mesh('acrylic_base');key,old=mesh('mylar_base')
        size=base.extents.copy();size[2]=THICKNESS;center=base.bounds.mean(axis=0);center[2]=base.bounds[1,2]+THICKNESS/2
        new=trimesh.creation.box(size);new.apply_translation(center);new.visual=trimesh.visual.TextureVisuals(material=old.visual.material.copy());g.geometry[key]=new
        changes.append(dict(part=prefix+'mylar_base',old_dimensions_m=old.extents.tolist(),new_dimensions_m=size.tolist(),basis='Cover the complete selected acrylic top, with the same 12 micrometre candidate film as stock'))
        for substrate,foil in [('foam_1','foam_mylar_1'),('foam_2','foam_mylar_2'),('PE_support','PE_support_mylar')]:
            _,under=mesh(substrate);key,old=mesh(foil);center=under.bounds.mean(axis=0)
            radius=float(np.linalg.norm(under.vertices[:,:2]-center[:2],axis=1).max());height=float(under.extents[2])
            guard=2*float(np.spacing(np.float32(np.abs(under.vertices).max())))
            new,allowance=wrap(radius,height,center,guard);new.visual=trimesh.visual.TextureVisuals(material=old.visual.material.copy());g.geometry[key]=new
            changes.append(dict(part=prefix+foil,substrate=prefix+substrate,radius_m=radius,height_m=height,thickness_m=THICKNESS,lap_m=LAP,mesh_faceting_and_quantization_allowance_m=allowance,
                                basis='Paper requires curved-surface coverage; thickness is the selected stock, seam and bending shape are engineering inferences'))
        mounting=apply_mount(g,prefix)
        frame=apply_frame(g,prefix)
        path=HERE/'geometry'/('apparatus_'+identity+'.glb');path.write_bytes(g.export(file_type='glb',include_normals=True))
        items.append(dict(id=identity,geometry=dict(path=str(path.relative_to(ROOT)),sha256=sha(path),parts=len(g.geometry)),changes=changes,mounting=mounting,frame=frame))
        if identity=='cooler_white':
            core=trimesh.Scene()
            for name in mounting['core_inspection_parts']:
                mesh=g.geometry[name].copy();mesh.apply_translation([-mounting['jack_translation_m'][0],-mounting['jack_translation_m'][1],-mounting['base_bottom_m']])
                core.add_geometry(mesh,node_name=name,geom_name=name)
            inspection=HERE/'geometry'/'apparatus_mount_inspection.glb';inspection.write_bytes(core.export(file_type='glb',include_normals=True))
            items[-1]['mounting_inspection']=dict(path=str(inspection.relative_to(ROOT)),sha256=sha(inspection),parts=len(core.geometry),
                scope='Actual white candidate core; thermal, reflector and legacy frame parts are hidden to inspect the mounting')
            frame_scene=trimesh.Scene()
            for name in frame['review_parts']:
                m=g.geometry[name].copy();m.apply_translation([-mounting['jack_translation_m'][0],-mounting['jack_translation_m'][1],0])
                frame_scene.add_geometry(m,node_name=name,geom_name=name)
            frame_path=HERE/'geometry'/'apparatus_frame_inspection.glb'
            frame_path.write_bytes(frame_scene.export(file_type='glb',include_normals=True))
            items[-1]['frame_inspection']=dict(path=str(frame_path.relative_to(ROOT)),sha256=sha(frame_path),parts=len(frame_scene.geometry))
    write_json(HERE/'apparatus_stock_reconciliation.json',dict(schema_version=1,items=items,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [ROOT/source,Path(__file__),HERE/'stock_sources.json',TASK_MATERIALS,
            HERE/'build_apparatus_mounting.py',HERE/'apparatus_mount_sources.json',HERE/'lift_mount_stock.json',HERE/'build_apparatus_frame.py',HERE/'apparatus_frame_sources.json',ROOT/'assets/thorlabs_l200_v1/model.json',ROOT/'assets/thorlabs_l200_v1/checks.json']],
        accepted=False,scope='Selected foil, source-scale central mounting and nominal frame connections in completed-state reference geometry; not assembly qualification or initial stock',
        limitations=['Historical Mylar SKU/thickness is unspecified; selected Goodfellow metallized PET is a candidate, not proven material equivalence',
                     'Foil optics, flexure, seam bonding and attachment tools are unqualified; sub-micron mesh faceting allowance is not a physical adhesive layer',
                     'Central mounting has real holes and ordinary fastener envelopes; preload, thread contact and structural load capacity are not qualified',
                     'Legacy sensor-lead/contact placeholders are removed; sourced probes remain staged and are not installed',
                     'Nominal frame/base/upright/track connections are reconstructed; elastic clamps, machining/tools, reflector travel and cover load path remain unresolved; stock is reviewed separately']))
    print(json.dumps(dict(apparatus=len(items),reconciled_foil_parts=sum(len(i['changes']) for i in items))))


TASK_MATERIALS=ROOT/'tasks/directional_cooling_operations_v3/material_cards.json'
if __name__=='__main__':build()
