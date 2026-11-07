"""Actual exported tool solids, vial voids and isolated mast-seat geometry."""
import itertools
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE,ROOT,sha,write_json
from check_weather_assets import overlap


def load_domains(ref):
    assert sha(ROOT/ref['path'])==ref['sha256']
    scene=trimesh.load(ROOT/ref['path'],force='scene');parts={}
    for name in scene.graph.nodes_geometry:
        matrix,key=scene.graph[name];mesh=scene.geometry[key].copy()
        mesh.apply_transform(matrix);mesh.merge_vertices(digits_vertex=8)
        # Do not turn inward cavity boundaries into additional positive solids.
        parts[name]=mesh
    return parts


def oriented_boundaries(mesh):
    groups=trimesh.graph.connected_components(mesh.face_adjacency,nodes=np.arange(len(mesh.faces)))
    result=[]
    for group in groups:
        m=trimesh.Trimesh(vertices=mesh.vertices,faces=mesh.faces[group],process=False)
        m.remove_unreferenced_vertices();result.append(m)
    return result


def build():
    record=json.loads((HERE/'post_level_assets.json').read_text());parts=load_domains(record['geometry']);checks=[]
    def check(name,passed,**details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        if not passed:raise AssertionError(name+' '+str(details))
    for ref in record['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    solids={n:m for n,m in parts.items() if not n.endswith('_identification')}
    check('part_counts',len(solids)==record['physical_part_count']==26 and len(parts)==28)
    for n,m in solids.items():
        boundaries=oriented_boundaries(m);cavity=n.endswith('_acrylic') or n.endswith('_liquid')
        positive=[b for b in boundaries if b.volume>0];negative=[b for b in boundaries if b.volume<0]
        check('closed_material_domain_'+n,m.is_volume and all(b.is_watertight for b in boundaries)
            and len(positive)==1 and len(negative)==int(cavity),signed_boundary_volumes_m3=[float(b.volume) for b in boundaries])
        if cavity:check('inner_boundary_nested_'+n,np.all(positive[0].contains(negative[0].vertices)))
    hits=[]
    for (n,a),(other,b) in itertools.combinations(solids.items(),2):
        volume=overlap(a,b)
        if not np.isfinite(volume) or volume>.001:hits.append(dict(parts=[n,other],volume_mm3=volume))
    check('no_unexplained_material_overlap',not hits,intersections=hits)
    body=solids['orange_molded_body'];check('selected_body_height',abs(body.extents[2]-.1397)<2e-7)
    check('selected_face_widths',np.allclose(body.bounds[1,:2],[.0889,.0889],atol=2e-7))
    # Empty edge waists are actually cut out of both face sheets.
    check('left_side_waist_is_open',not body.ray.intersects_any([[.078,-.04,.073]],[[0,1,0]])[0])
    check('right_side_waist_is_open',not body.ray.intersects_any([[-.04,.078,.073]],[[1,0,0]])[0])
    check('hanging_hole_is_open',not body.ray.intersects_any([[-.03,-.03,.123]],[[1,1,0]])[0])
    for row in record['vials']:
        n=row['id'];centre=np.array(row['centre_m']);axis=np.array(row['axis'])
        transform=trimesh.geometry.align_vectors([0,0,1],axis);transform[:3,3]=centre
        shell=solids[n+'_acrylic'];fluid=solids[n+'_liquid'];gas=solids[n+'_air']
        chamber=trimesh.creation.cylinder(.0041,.0315,sections=128);chamber.apply_transform(transform)
        expected=np.pi*.0041**2*.0315
        check('vial_length_'+n,abs(np.ptp(shell.vertices@axis)-.034)<2e-7)
        check('gas_and_fluid_fill_chamber_'+n,abs((fluid.volume+gas.volume)-expected)/expected<.004,
            occupied_m3=float(fluid.volume+gas.volume),analytic_chamber_m3=float(expected))
        check('gas_centre_in_real_void_'+n,not fluid.contains([gas.center_mass])[0] and not shell.contains([gas.center_mass])[0])
        check('gas_inside_chamber_'+n,np.all(chamber.contains(gas.vertices)))
        expected_wall=np.pi*.0048**2*.034-expected
        check('acrylic_is_hollow_'+n,abs(shell.volume-expected_wall)/expected_wall<.004)
        # The molded body leaves a visible centre ray through each vial window.
        normal=np.array([0,-1,0]) if n=='right' else np.array([-1,0,0]) if n=='left' else np.array([-1,-1,0])/np.sqrt(2)
        check('vial_window_'+n,not body.ray.intersects_any([centre+normal*.035],[-normal])[0])
    mast=trimesh.creation.cylinder(.0205,.13,sections=160);mast.apply_translation([.0205,.0205,.06985])
    check('isolated_41mm_mast_seat_clear',all(overlap(mast,m)<.001 for n,m in solids.items() if n!='detached_rubber_strap'))
    misplaced=mast.copy();misplaced.apply_translation([-.003,-.003,0])
    check('negative_mast_through_body_rejected',overlap(misplaced,body)>1.)
    fakefluid=trimesh.creation.cylinder(.0041,.0315,sections=128);fakefluid.apply_translation([-.0035,-.0035,.065])
    check('negative_unsubtracted_bubble_rejected',overlap(fakefluid,solids['corner_air'])>1.)
    strap=solids['detached_rubber_strap'];check('strap_has_real_opening',not strap.ray.intersects_any([[-.000025,-.055,-.01]],[[0,0,1]])[0])
    check('selected_flat_strap_envelope',np.allclose(strap.extents,[.220,.018,.002],atol=3e-5,rtol=0),
        actual_m=strap.extents.tolist(),cad_tessellation_chord_tolerance_m=.00003)
    check('no_unearned_qualification',not any(record[k] for k in ['staged_in_lab','initial_stock_credit','measurement_qualified','strap_retention_qualified','robot_use_qualified','owner_acceptance']))
    refs=[Path(__file__),HERE/'post_level_assets.json',HERE/'check_weather_assets.py']
    report=dict(passed=True,checks=checks,source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        measurement_qualified=False,strap_retention_qualified=False,robot_use_qualified=False,owner_acceptance=None,
        scope='Closed static geometry, real openings, disjoint vial material domains and one isolated mast-seat candidate. No gravity-sensitive reading, retention, complete station or robot motion.')
    write_json(HERE/'post_level_checks.json',report);print(json.dumps(dict(passed=True,checks=len(checks),parts=len(parts))))


if __name__=='__main__':build()
