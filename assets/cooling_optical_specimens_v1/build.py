"""Build identified 25 mm optical witnesses in ordinary annular holders.

The task reconstruction selects the coupon diameter and annular retention.
The holder, masked rim, paint thickness and spring-clip dimensions below are
explicit engineering inferences, not a commercial product or qualified fixture.
Fabrication, curing and clip tightening are authored initial conditions for the
presentation; this package grants no execution or physical qualification.
"""
import hashlib
import json
import sys
from pathlib import Path

import cadquery as cq
import numpy as np
import trimesh

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'assets/cooling_lab_v1'))
from geometry_tools import Geometry
from build_supplies import cad_mesh


def linear_materials(tree):
    for material in tree.get('materials',[]):
        pbr=material.get('pbrMetallicRoughness',{});rgba=pbr.get('baseColorFactor')
        if rgba:pbr['baseColorFactor']=[c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgba[:3]]+[rgba[3]]


def build(kind):
    g=Geometry();color=[225,224,213] if kind=='white' else [24,24,23];solids={}
    # All CadQuery dimensions are mm. The underside of the carrier defines Z=0.
    carrier=cq.Workplane('XY').circle(17.5).circle(12.6).extrude(2.0).union(cq.Workplane('XY').circle(12.6).circle(11.0).extrude(.11))
    clip_profile=[(11.4,.61),(12.0,.61),(14.2,2.0),(16.2,2.0),(16.2,2.18),(14.2,2.18),(12.0,.79),(11.4,.79)]
    for angle in [0,120,240]:
        relief=cq.Workplane('XY').box(3.3,2.6,2.1,centered=(False,True,False)).translate((11.,0,.20)).rotate((0,0,0),(0,0,1),angle)
        hole=cq.Workplane('XY').center(15.2,0).circle(.5).extrude(3).rotate((0,0,0),(0,0,1),angle)
        carrier=carrier.cut(relief).cut(hole)
    g.add('annular_carrier',cad_mesh(carrier.val()),[68,72,77],role='ordinary_sample_holder',metal=.7)
    solids['annular_carrier']=carrier
    g.cylinder('copper_witness',.0125,.0005,[0,0,.00036],[172,94,47],role='identified_copper_witness',metal=.9)
    solids['copper_witness']=cq.Workplane('XY').circle(12.5).extrude(.5).translate((0,0,.11))
    for i in range(3):
        mesh=g.cylinder('paint_coat_'+str(i+1),.0108,.00002,[0,0,.00006+i*.00002],color,role='optical_coating')
        mesh.visual.material.roughnessFactor=.9
        solids['paint_coat_'+str(i+1)]=cq.Workplane('XY').circle(10.8).extrude(.02).translate((0,0,.05+i*.02))
    for angle in [0,120,240]:
        clip=cq.Workplane('XZ').polyline(clip_profile).close().extrude(1.2,both=True)
        hole=cq.Workplane('XY').center(15.2,0).circle(.5).extrude(3)
        clip=clip.cut(hole).rotate((0,0,0),(0,0,1),angle)
        g.add('spring_clip_'+str(angle),cad_mesh(clip.val()),[167,173,177],role='specimen_retainer',metal=.8)
        solids['spring_clip_'+str(angle)]=clip
        screw=cq.Workplane('XY').center(15.2,0).circle(.45).extrude(1.18).translate((0,0,1.0))
        head=cq.Workplane('XY').center(15.2,0).circle(.9).extrude(.30).translate((0,0,2.18))
        slot=cq.Workplane('XY').box(2.0,.25,.16).translate((15.2,0,2.48))
        screw=screw.union(head.cut(slot)).rotate((0,0,0),(0,0,1),angle)
        g.add('retainer_screw_'+str(angle),cad_mesh(screw.val()),[125,133,139],role='ordinary_retaining_screw',metal=.85)
        solids['retainer_screw_'+str(angle)]=screw
    if kind=='white':
        (HERE/'design').mkdir(exist_ok=True)
        for name,solid in solids.items():cq.exporters.export(solid,str(HERE/'design'/(name+'.step')))
    output=HERE/('witness_'+kind+'.glb');output.write_bytes(g.scene.export(file_type='glb',include_normals=True,tree_postprocessor=linear_materials))
    reread=trimesh.load(output,force='scene',process=False)
    maximum_error=0.
    for name in g.scene.graph.nodes_geometry:
        _,a=g.scene.graph[name];transform,b=reread.graph[name]
        expected=g.scene.geometry[a].vertices;actual=trimesh.transform_points(reread.geometry[b].vertices,transform)
        assert expected.shape==actual.shape
        maximum_error=max(maximum_error,float(np.abs(expected-actual).max()))
    assert maximum_error<1e-8
    return dict(id='optical_witness_'+kind,path=str(output.relative_to(ROOT)),sha256=hashlib.sha256(output.read_bytes()).hexdigest(),part_names=list(reread.graph.nodes_geometry),
                bounds_m=reread.bounds.tolist(),source_to_export_maximum_vertex_error_m=maximum_error,
                lineage=dict(apparatus_parent=kind,material='copper',coating='Krylon Colormaster flat '+kind,coat_count=3,
                             distinction='Independent optical witness, not the 50 mm apparatus emitter; material/paint lot matching is an inferred allocation, not a measured fabrication receipt'))


def main():
    reconstruction=ROOT/'tasks/directional_cooling_operations_v3/selected_reconstruction.json';cards=json.loads(reconstruction.read_text())['cards'];selected=cards['optical_card']['sample_mount']['value'];assert selected['coupon_diameter_m']==.025
    assets=[build(kind) for kind in ['white','black']]
    result=dict(scope=__doc__,generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),status='development_geometry_asset',assets=assets,
                design_solids=[dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),unit='millimetre') for p in sorted((HERE/'design').glob('*.step'))],
                source=dict(path=str(reconstruction.relative_to(ROOT)),sha256=hashlib.sha256(reconstruction.read_bytes()).hexdigest(),optical_selection=cards['optical_card']['sample_mount'],reported_emitter=cards['fabrication_card']['part_manifest']['value']['copper_emitter']),
                selected_dimensions_m=dict(coupon_diameter=.025,copper_thickness=.0005,holder_outer_diameter=.035,holder_clear_aperture_diameter=.022,holder_height=.002,painted_diameter=.0216,paint_total_thickness=.00006,optical_face_above_holder_support_plane=.00005),
                inferences=['Copper witnesses reuse the reported 0.5 mm emitter stock and coating type; the paper does not specify these optical-witness dimensions.',
                            'Three 20 micrometre visual coating layers and a masked, uncoated rim are selected for geometry; neither thickness nor reflectance is a measured result.',
                            'A conventional annular carrier supports the uncoated copper rim; three pre-tightened spring clips retain its back. All holder details and fastener sizes are authored.',
                            'The optical face is recessed 50 micrometres above the holder support plane. Alignment, optical effects of this gap, support forces and contamination remain unqualified.',
                            'The holder is an ordinary specimen mount, without robot-specific attachment features or fiducials.'],
                review_records=dict(assembly='assets/cooling_optical_specimens_v1/assembly_review.json',supported_staging='viewer/cooling_concept_v2/specimen_staging.json',ordinary_tweezer_fit='viewer/cooling_concept_v2/previews/specimen_tool_fit.json',ftir_port_lift='viewer/cooling_concept_v2/previews/specimen_port_refined.json'),
                remaining=['Whole-workflow integration and independent robot/environment review of the optical handling sequence','Physical pickup, measurement mounting, release and return','Cary/FTIR identity-preserving transfer and background/sample control','Two-layer nanoporous/LDPE film specimens remain separate required assets and procedures'])
    (HERE/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(assets=assets,dimensions=result['selected_dimensions_m'])),flush=True)


if __name__=='__main__':main()
