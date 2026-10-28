"""Assemble the existing optical assets in their instrument sample bays.

This is an authored initial configuration, not a robot installation receipt.
The source manuals establish the assembly relationships; the exact local
mount datums remain inferred and are recorded explicitly below.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial.transform import Rotation

from source_geometry import ASSETS, ROOT

HERE = Path(__file__).resolve().parent


def translation(point):
    result = np.eye(4)
    result[:3, 3] = point
    return result


def about(source, destination, rotation=None):
    result = np.eye(4)
    if rotation is not None:
        result[:3, :3] = rotation
    result[:3, 3] = np.asarray(destination) - result[:3, :3] @ source
    return result


def build():
    config = dict(
        scope='Authored installed initial state; no installation, optical alignment, cable mating or physical qualification credit',
        original_geometry_preserved=True, parts={}, ports={},
        assumptions=[
            'Instruments and integrating spheres are installed and initialized before the filmed specimen-handling sequence.',
            'Cary receiver locations are inferred from the reconstructed DRA feet and front pin, not manufacturer CAD.',
            'The Cary DRA base sits on the existing 8 mm high rear receiver ledges. Its optical alignment remains unverified.',
            'A 5 mm instrument mounting plate with an alignment-pin bore supports the IntegratIR; the Nicolet-specific factory mounting kit is unresolved.',
            'The two reference standards are initially seated at their own integrating-sphere sample ports.',
            'The inferred gold-reference optical face is recessed 0.05 mm behind the non-optical shoulder plane, correcting the earlier 0.5 mm protruding part datum. The manufacturer photograph shows the central face within its surrounding holder but supplies no recess dimension; this selected datum is not a manufacturer tolerance.',
            'Detector connectors and complete cable mating are not established by this geometric setup.',
        ],
        sources=[])
    for filename, url, pages in [
        ('cary-internal-dra-manual.pdf', 'https://mmrc.caltech.edu/Cary%20UV-Vis%20Int.Sphere/manuals/Cary%20manuals/4000_5000_6000i_Internal%20DRA.pdf', 'Installation and reflectance-measurement sections'),
        ('cary-extended-bay-legacy.pdf', 'https://mmrc.caltech.edu/Cary%20UV-Vis%20Int.Sphere/manuals/Cary%20manuals/4000_6000i_extended_sample_compartment.pdf', 'pp. 2–5'),
        ('pike-dtgs-manual.pdf', 'https://www.piketech.com/files/user-manuals/MidIntegratIRwDTGSManual.pdf', 'printed pp. 1, 3–5'),
    ]:
        path = Path('/tmp/sciencegym-pilot-sources') / filename
        config['sources'].append(dict(url=url, inspected_sections=pages,
                                     sha256=hashlib.sha256(path.read_bytes()).hexdigest()))

    source = {name: json.loads((ROOT/'assets'/folder/'interfaces.json').read_text())
              for name, folder in [('cary', 'cary_5000_v1'), ('dra', 'cary_internal_dra_2500_v1'),
                                   ('pike', 'pike_integratir_dtgs_v1')]}
    frames = {name: translation(a['position_m']) @ np.asarray(a['normalization_matrix'])
              for name, a in ASSETS.items() if name in ['cary', 'dra', 'nicolet', 'pike']}
    dra_origin = np.array([.185, -.021, .148])
    pike_origin = np.array([-.011, -.160, .055])
    installed = {'dra': frames['cary'] @ translation(dra_origin),
                 'pike': frames['nicolet'] @ translation(pike_origin)}

    def assign(asset, names, original_to_world, reason):
        # GLB coordinates already include their normalization transform.
        transform = (translation(-np.asarray(ASSETS[asset]['position_m'])) @
                     original_to_world @ np.linalg.inv(ASSETS[asset]['normalization_matrix']))
        for name in names:
            config['parts'].setdefault(asset, {})[name] = dict(matrix=transform.tolist(), reason=reason)

    cary = source['cary']
    extension = cary['extension']
    ex = about(extension['presentation_origin_m'], [.185, -.450, .134])
    assign('cary', cary['extension_base_parts']+cary['extension_cover_parts'], frames['cary'] @ ex,
           'Extension base pins located at reconstructed keyhole sockets; inferred installed datum')

    # Preserve the detached standard front wall; lay it on the neighboring bench.
    scene = trimesh.load(ROOT/ASSETS['cary']['geometry'], force='scene', process=False)
    front_vertices=[]
    for name in cary['front_panel_parts']:
        transform, key=scene.graph[name]
        front_vertices.append(trimesh.transform_points(scene.geometry[key].vertices,
                                                       np.linalg.inv(ASSETS['cary']['normalization_matrix']) @ transform))
    vertices=np.concatenate(front_vertices)
    rot=Rotation.from_euler('x', np.pi/2).as_matrix()
    rotated=vertices@rot.T
    center=(rotated.min(0)+rotated.max(0))/2
    target=np.array([3.35, 8.20, .851+(rotated[:,2].max()-rotated[:,2].min())/2])
    parked=np.eye(4);parked[:3,:3]=rot;parked[:3,3]=target-center
    assign('cary', cary['front_panel_parts'], parked, 'Removed standard front wall stored flat on optical bench')
    assign('cary', ['lockdown_front_post','lockdown_front_lever'], frames['cary'] @ translation([0,.109,0]),
           'Inferred receiver datum corrected to DRA front pin')
    assign('cary', [n for n in ASSETS['cary']['part_names'] if n.startswith('lockdown_rear_ledge_')],
           frames['cary'] @ translation([0,.019,0]), 'Inferred rear receiver datums corrected to DRA rear feet')

    dra_reference = source['dra']['reference_parts']
    assign('dra', [n for n in ASSETS['dra']['part_names'] if n not in dra_reference], installed['dra'],
           'Internal DRA module inside Cary sample compartment')
    dra_reference_pose=about([.125,-.085,.034], [0,-.122,.084], Rotation.from_euler('z',np.pi).as_matrix())
    assign('dra', dra_reference, installed['dra'] @ dra_reference_pose,
           'PTFE optical face toward and flush with the front reflectance port')
    # Existing clamp is displayed in its open position in the source asset.
    for name in ['sample_clamp_slider','sample_clamp_arm','sample_clamp_contact']:
        assign('dra',[name],installed['dra'] @ translation([0,.019,0]),
               'Authored closed clamp position against back of reference holder; spring mechanics unresolved')

    pike = source['pike']
    assign('pike', pike['module_parts'], installed['pike'], 'IntegratIR installed inside Nicolet sample compartment')
    ref_pose=about([.145,-.06,.0375], [.04,-.01,.1015], Rotation.from_euler('x',np.pi).as_matrix())
    assign('pike', pike['reference_parts'], installed['pike'] @ ref_pose,
           'Gold optical face downward on upper sample port; substitution method, selector in SAMPLE')
    assign('pike', ['diffuse_gold_reference_face'], installed['pike'] @ ref_pose @ translation([0,0,-.00055]),
           'Inferred part-datum correction: optical face recessed 0.05 mm behind the supporting shoulder; manufacturer manual figure 1 shows the face within its holder, exact recess unreported')
    # The ordinary protective cap supports the non-optical holder shoulder.
    # Its internal fit is a versioned inference, not manufacturer CAD.
    cap_floor=json.loads((HERE/'reference_transfer.json').read_text())['cap_floor_m']
    assign('pike',pike['cap_parts'],about([.210,-.060,.004],cap_floor),
           'Protective cap staged on FTIR bench, clear of housing; inferred internal shoulder support, see cap_support revision')
    # Ground the unused sample plate as a complete assembly; normalization
    # of the module's bottom alignment pin must not leave inventory floating.
    inventory=trimesh.load(ROOT/ASSETS['pike']['geometry'],force='scene',process=False)
    bottom=float('inf')
    for name in pike['optional_plate_parts']:
        local,key=inventory.graph[name];world=translation(ASSETS['pike']['position_m'])@local
        bottom=min(bottom,float((inventory.geometry[key].vertices@world[2,:3]+world[2,3]).min()))
    assign('pike',pike['optional_plate_parts'],translation([0,0,.850001-bottom])@frames['pike'],
           'Unused optional plate rests on the FTIR bench; not installed for direct reflectance')

    for name, identity, local, normal in [('cary_reflectance','dra',[0,-.122,.084],[0,-1,0]),
                                           ('ftir_sample','pike',[.04,-.01,.102],[0,0,1])]:
        config['ports'][name]=dict(position_m=trimesh.transform_points([local],installed[identity])[0].tolist(),
                                    normal=normal, asset=identity)

    # A source-independent plate, with a real aperture for the bottom alignment pin.
    # Triangulate four strips around the pin's enclosing square; all solid support
    # lies outside that square and the 5 mm pin therefore has clearance.
    plate=[];cx,cy=0,.02;h=.003
    for lo,hi in [((-.0875,-.0975),(cx-h,.0975)),((cx+h,-.0975),(.0875,.0975)),
                  ((cx-h,-.0975),(cx+h,cy-h)),((cx-h,cy+h),(cx+h,.0975))]:
        mesh=trimesh.creation.box(extents=[hi[0]-lo[0],hi[1]-lo[1],.005])
        mesh.apply_translation([(lo[0]+hi[0])/2,(lo[1]+hi[1])/2,-.0025]);plate.append(mesh)
    mesh=trimesh.util.concatenate(plate)
    mesh.apply_transform(installed['pike'])
    config['mount_plate']=dict(id='ftir_instrument_mount_plate',vertices=mesh.vertices.tolist(),
                              faces=mesh.faces.tolist(),inferred=True,
                              reason='Ordinary instrument mounting plate with 6 mm square clearance around 5 mm pin; factory adapter unresolved')
    config['generator_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    config['source_geometry_sha256']={a:ASSETS[a]['geometry_sha256'] for a in frames}
    (HERE/'optical_setup.json').write_text(json.dumps(config,indent=2)+'\n')
    print(json.dumps(dict(parts={k:len(v) for k,v in config['parts'].items()},ports=config['ports']),indent=2))


if __name__=='__main__':
    build()
