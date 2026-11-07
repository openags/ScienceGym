"""FST 11000-20 ordinary 200 mm serrated forceps, source-informed reconstruction.

Length, mass, material and 3.75 x 1.9 mm tip section are manufacturer values.
The unmeasured body contour, opening, serration pitch and elastic shape are
explicit inferences from the manufacturer's photograph, not vendor CAD.
Coordinates: X along the tool (tip at -0.1 m), Y closes, Z blade width.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
import trimesh
from source_geometry import ROOT

LENGTH = .200
TIP = np.array([-.100, 0., .006])
OPEN_GAP = .016
CLOSED_GAP = .00210
FLEX_LENGTH = .160
OUT = ROOT/'assets/fst_11000_20_v1'
STEEL = trimesh.visual.material.PBRMaterial(name='matte_surgical_stainless_steel',
    baseColorFactor=[183, 189, 196, 255], metallicFactor=1., roughnessFactor=.32)


def width(x):
    if x < .001875:
        return max(.00001, 2*np.sqrt(max(0., .001875**2-(x-.001875)**2)))
    if x > .195:
        return max(.00001, 2*np.sqrt(max(0., .005**2-(x-.195)**2)))
    return float(np.interp(x, [.001875,.025,.070,.100,.120,.140,.160,.195],
                            [.00375,.00375,.0045,.009,.012,.011,.010,.010]))


def rectangle(y0, y1, half_width):
    r = min(.00015, (y1-y0)/4, half_width/3)
    points = []
    for cy, cz, first in [(y1-r, half_width-r, 0), (y0+r, half_width-r, 90),
                          (y0+r, -half_width+r, 180), (y1-r, -half_width+r, 270)]:
        for angle in np.deg2rad(np.linspace(first, first+90, 4)):
            points.append([cy+r*np.cos(angle), cz+r*np.sin(angle)])
    return np.array(points)


def loft(xs, sections):
    vertices = np.array([[x-.100, y, z+.006] for x, points in zip(xs, sections) for y, z in points])
    n = len(sections[0])
    faces = []
    for i in range(len(xs)-1):
        for j in range(n):
            a, b = i*n+j, i*n+(j+1)%n
            faces.extend([(a,b,b+n),(a,b+n,a+n)])
    for j in range(1,n-1):
        faces.append((0,j+1,j))
        a = (len(xs)-1)*n
        faces.append((a,a+j,a+j+1))
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=True)
    if mesh.volume < 0:
        mesh.invert()
    mesh.visual = trimesh.visual.TextureVisuals(material=STEEL.copy())
    return mesh


def meshes(closure=0.):
    if not 0 <= closure <= 1:
        raise ValueError('Selected closure outside [0,1]')
    # Extra knots preserve the actual serration crests in collision meshes.
    xs = sorted({round(float(x),12) for x in [*np.linspace(0,FLEX_LENGTH,161),
                    *np.arange(0,.02401,.0002), *np.arange(.075,.13501,.0002)]})
    result = {}
    for sign in [-1,1]:
        sections = []
        for x in xs:
            a = 1-x/FLEX_LENGTH
            shape = a*a*(3-a)/2
            gap = (OPEN_GAP-(OPEN_GAP-CLOSED_GAP)*closure)*shape/2
            thickness = float(np.interp(x,[0,.025,.060,.160],[.0019,.0019,.0016,.0016]))
            inner = gap
            outer = gap+thickness
            if x < .024:
                inner += .00012*(1-np.cos(2*np.pi*x/.0008))/2
            if .075 <= x <= .135:
                outer -= .00012*(1-np.cos(2*np.pi*(x-.075)/.0008))/2
            lo, hi = (inner,outer) if sign>0 else (-outer,-inner)
            sections.append(rectangle(lo,hi,width(x)/2))
        result['serrated_arm_'+str(sign)] = loft(xs,sections)
    xs = sorted({round(float(x),12) for x in [*np.linspace(FLEX_LENGTH,LENGTH,61),.195,.199,.1995,.1999]})
    result['joined_heel'] = loft(xs,[rectangle(-.0016,.0016,width(x)/2) for x in xs])
    return result


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    outputs = {}
    for name, closure in [('open',0.),('clamp_grip',1.)]:
        source = trimesh.Scene()
        for part, mesh in meshes(closure).items():
            assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0,part
            source.add_geometry(mesh,node_name=part)
        path = OUT/(name+'.glb')
        path.write_bytes(source.export(file_type='glb'))
        outputs[name] = dict(geometry=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                             bounds_m=source.bounds.tolist())
    urls = dict(product='https://finescience.com/anatomical-standard-forceps-straight/11000-20',
        datasheet='https://cdn.finesciencetools.shop/downloads/product-data-sheet_11000-20?download=true&lang=en',
        photograph='https://finescience.com/media/fb/e9/5c/1780903438/11000-20-iso-C.jpg?ts=1780903438',
        tip_sketch='https://finescience.com/media/75/a0/ee/1780903440/11000-20_Sketch_front.jpg?ts=1780903440')
    cached = {}
    for name in ['fst_11000_20_datasheet.pdf','fst_11000_20_iso.jpg','fst_11000_20_front.jpg']:
        path = Path('/tmp/sciencegym-pilot-sources')/name
        cached[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    report = dict(scope=__doc__,manufacturer='Fine Science Tools',part_number='11000-20',
        manufacturer_CAD=False,contact_qualified=False,source_urls=urls,cached_reference_sha256=cached,
        source_values=dict(length_m=LENGTH,mass_kg=.050,tip_width_m=.00375,
                           tip_thickness_m=.0019,material='Surgical stainless steel (Inox)',tips='Serrated'),
        inferred=dict(body_maximum_width_m=.012,body_thickness_m=.0016,joined_heel_length_m=.040,
                      initial_tip_gap_m=OPEN_GAP,actuator_grip_tip_gap_m=CLOSED_GAP,
                      serration_pitch_m=.0008,serration_depth_m=.00012,
                      spring_model='Selected cubic bending shape; no stiffness or retention-force calibration'),
        geometry_license='Original generated reconstruction under the repository license; manufacturer photographs/PDF are external references, not redistributed.',
        variants=outputs,generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        limitations=['Dimensions absent from the datasheet are not presented as measured factory dimensions.',
                     'No approved grasp, tool actuation force, spring law or complete robot operation yet.'])
    (OUT/'revision.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(outputs),flush=True)


if __name__=='__main__':
    main()
