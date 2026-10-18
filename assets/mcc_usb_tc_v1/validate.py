"""Inspect exported passages, screw slots, envelope and source pin identities."""
import hashlib
import json
from pathlib import Path
import numpy as np
import trimesh

HERE=Path(__file__).resolve().parent


def main():
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    scene=trimesh.load(HERE/'geometry/mcc_usb_tc.glb',force='scene');meshes={}
    for node in scene.graph.nodes_geometry:
        matrix,geometry=scene.graph[node];mesh=scene.geometry[geometry].copy();mesh.apply_transform(matrix)
        mesh.vertices=np.asarray(mesh.vertices)@np.array([[1,0,0],[0,0,1],[0,-1,0]])
        meshes[node]=mesh
    parts=json.loads((HERE/'parts.json').read_text());interfaces=json.loads((HERE/'interfaces.json').read_text());checks=[]
    def check(name,passed,**values):checks.append(dict(name=name,passed=bool(passed),**values))
    check('all_parts_exported',{p['id'] for p in parts}==set(meshes),parts=len(parts),meshes=len(meshes))
    housing=trimesh.util.concatenate([meshes[p['id']] for p in parts if p['role']=='housing'])
    check('manufacturer_enclosure_envelope',np.max(abs(housing.extents-[.12852,.08839,.03556]))<2e-6,measured_m=housing.extents.tolist())
    check('bottom_datum',abs(housing.bounds[0,2])<1e-7,minimum_z_m=float(housing.bounds[0,2]))
    terminals=interfaces['terminals'];pins={t['pin']:t for t in terminals}
    check('52_unique_numbered_terminals',len(terminals)==52 and set(pins)==set(range(1,53)))
    channel_pins=[(3,4),(7,8),(13,14),(17,18),(44,43),(40,39),(34,33),(30,29)]
    check('source_channel_polarity',all(pins[p]['signal']==f'C{i}H' and pins[n]['signal']==f'C{i}L' for i,(p,n) in enumerate(channel_pins)))
    check('four_physically_separate_blocks',len([p for p in parts if p['role']=='terminal_legend_strip'])==4
          and pins[11]['screw_center_m'][0]-pins[10]['screw_center_m'][0]>.008
          and pins[37]['screw_center_m'][0]-pins[36]['screw_center_m'][0]>.008)
    check('two_cjc_sensors',len([p for p in parts if p['role']=='cold_junction_sensor'])==2)
    blocked=[];missing_wall=[];slot_depths=[];blocked_seats=[];blocked_shafts=[];blocked_head_travel=[]
    # A 16 AWG bare conductor has nominal 1.29 mm diameter. Sample its
    # complete circular section along the selected 5.5 mm insertion path.
    angle=np.arange(16)*2*np.pi/16
    radial=np.vstack([np.zeros((1,2)),np.c_[np.cos(angle),np.sin(angle)]*.000645])
    for t in terminals:
        pin=t['pin'];entry=np.array(t['wire_entry_m']);axis=np.array(t['insertion_axis'])
        centers=entry+np.linspace(.0005,.0055,12)[:,None]*axis
        points=centers[:,None,:]+np.c_[radial[:,0],np.zeros(len(radial)),radial[:,1]][None,:,:]
        passage=trimesh.util.concatenate([meshes[t['parts']['housing']],meshes[t['parts']['clamp']]])
        if passage.contains(points.reshape(-1,3)).any():blocked.append(pin)
        control=entry+axis*.002+np.array([.00135,0,0])
        if not meshes[t['parts']['housing']].contains([control])[0]:missing_wall.append(pin)
        clamp=meshes[t['parts']['clamp']]
        points=np.array([[x,y,z] for x in np.linspace(*clamp.bounds[:,0],5)[1:-1]
            for y in np.linspace(*clamp.bounds[:,1],5)[1:-1] for z in np.linspace(*clamp.bounds[:,2],5)[1:-1]])
        if meshes[t['parts']['housing']].contains(points).any():blocked_seats.append(pin)
        shaft=meshes[t['parts']['shank']];points=shaft.vertices*.99+shaft.centroid*.01
        if meshes[t['parts']['housing']].contains(points).any():blocked_shafts.append(pin)
        screw=meshes[t['parts']['screw']];center=np.array(t['screw_center_m']);origin=center+[0,0,.002]
        surface=screw.vertices*.99+screw.centroid*.01
        sweep=np.concatenate([surface+[0,0,-depth] for depth in np.linspace(0,.0022,12)])
        if meshes[t['parts']['housing']].contains(sweep).any():blocked_head_travel.append(pin)
        locations,_,_=screw.ray.intersects_location([origin],[[0,0,-1]],multiple_hits=True)
        if not len(locations):slot_depths.append(None)
        else:slot_depths.append(float(screw.bounds[1,2]-locations[:,2].max()))
    check('52_open_wire_passages',not blocked,blocked_pins=blocked,conductor_diameter_m=.00129,depth_m=.0055,
          scope='Static sampled geometric clearance, no wire friction or electrical contact qualification')
    check('wire_passage_walls_present',not missing_wall,pins_without_control_wall=missing_wall)
    check('52_internal_clamp_seats',not blocked_seats,blocked_pins=blocked_seats)
    check('52_screw_shaft_clearances',not blocked_shafts,blocked_pins=blocked_shafts)
    check('52_recessed_head_travel_clearances',not blocked_head_travel,blocked_pins=blocked_head_travel,selected_travel_m=.0022)
    check('52_real_driver_slots',all(x is not None and .00015<x<.00025 for x in slot_depths),slot_depths_m=slot_depths)
    check('separate_screw_and_clamp_parts',all(all(t['parts'][role] in meshes for role in ['screw','shank','clamp']) for t in terminals))
    shell=meshes['usb_B_shell'];entry=np.array(interfaces['usb']['entry_m'])
    mouth=np.array([[entry[0]-.001,entry[1]+y,entry[2]+z] for y in [-.003,0,.003] for z in [-.003,0,.003]])
    check('open_chamfered_usb_mouth',not shell.contains(mouth).any()
          and shell.contains([entry+[-.001,.0048,0]])[0])
    check('four_usb_contacts_and_tongue',len([p for p in parts if p['role']=='usb_contact'])==4 and 'usb_B_contact_tongue' in meshes)
    leds=[meshes['LED_'+n].centroid for n in ['power','activity']]
    check('vertically_stacked_status_leds',leds[1][2]>leds[0][2] and abs(leds[1][1]-leds[0][1])<1e-6)
    receipt=json.loads((HERE/'build_receipt.json').read_text())
    check('source_and_builder_pins',receipt['builder_sha256']==sha(HERE/'build.py') and receipt['source_sha256']==sha(HERE/'sources.json')
          and receipt['shared_pinmap_sha256']==sha(HERE.parent/'cooling_scene_assets_v2/interaction_geometry.py'))
    check('geometry_hashes',all(sha(HERE/p)==digest for p,digest in receipt['artifacts_sha256'].items()))
    report=dict(passed=all(c['passed'] for c in checks),checks=checks,validator_sha256=sha(Path(__file__)),
        glb_sha256=sha(HERE/'geometry/mcc_usb_tc.glb'),vendor_cad=False,contact_qualified=False,
        scope='Original manufacturer-informed geometry; source envelope/pin map and reconstructed open interfaces. No screw mechanics, wire retention, USB mating or electronics acceptance.')
    (HERE/'geometry_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],checks=len(checks),failed=[c for c in checks if not c['passed']]),indent=2))
    return report['passed']


if __name__=='__main__':raise SystemExit(0 if main() else 1)
