"""Authored level-earth site with flush ordinary paths and bench pads.

This candidate replaces the *material and geometry* of the outdoor hard slab.
It does not create invisible fixed anchors or certify soil bearing strength.
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import box,LineString
from shapely.ops import unary_union
import trimesh
from trimesh.visual.material import PBRMaterial
from geometry_tools import Geometry,HERE,ROOT,sha,write_json

AREA=(0.,12.,12.,20.)
PAD_BOUNDS={
    'white_bench':(1.8,15.2,3.2,16.4),
    'black_bench':(8.8,15.2,10.2,16.4),
    'weather_service':(8.75,18.1,10.25,19.1),
    'tracker_support':(1.75,18.1,3.25,19.1)}


def footprints():
    area=box(*AREA)
    path=unary_union([
        LineString([[2.5,14.2],[9.5,14.2]]).buffer(.8),
        LineString([[6,12],[6,14.2]]).buffer(.8),
        LineString([[6,14.2],[6,15.75]]).buffer(.7)]).intersection(area)
    pads={name:box(*bounds) for name,bounds in PAD_BOUNDS.items()}
    earth=area.difference(unary_union([path,*pads.values()]))
    return area,path,pads,earth


def texture(kind):
    rng=np.random.default_rng(730 if kind=='earth' else 731)
    pixels=np.zeros((1024,1024,3))
    if kind=='earth':
        pixels[:]=[133,117,91];noise=rng.normal(0,4,(1024,1024,1));pixels+=noise
        # Multi-scale generated aggregate variation, not a photographic scan.
        for n,amplitude in [(32,8),(128,5)]:
            low=Image.fromarray(np.uint8(np.clip(rng.normal(128,20,(n,n)),0,255)))
            pixels+=(np.asarray(low.resize((1024,1024),Image.Resampling.BILINEAR),dtype=float)[:,:,None]-128)*amplitude/20
    else:
        pixels[:]=[174,177,167];pixels+=rng.normal(0,2.4,(1024,1024,1))
    return Image.fromarray(np.uint8(np.clip(pixels,0,255)))


def add_ground(g,section=False):
    area,path,pads,earth=footprints();textures={kind:texture(kind) for kind in ['earth','concrete']}
    def layer(name,poly,bottom,top,kind):
        if section:poly=poly.intersection(box(6,12,12,20))
        if poly.is_empty:return
        m=trimesh.creation.extrude_polygon(poly,top-bottom);m.apply_translation([0,0,bottom])
        # Preserve separate face UVs at sharp corners. Horizontal projection
        # alone collapses a vertical soil face into artificial vertical stripes.
        m.unmerge_vertices();uv=np.zeros((len(m.vertices),2))
        for face,normal in zip(m.faces,m.face_normals):
            axis=int(np.argmax(abs(normal)));axes={0:[1,2],1:[0,2],2:[0,1]}[axis]
            uv[face]=m.vertices[face][:,axes]/2.
        g.add(name,m,[255,255,255],role='outdoor_ground_candidate')
        m.visual=trimesh.visual.TextureVisuals(uv=uv,material=PBRMaterial(baseColorTexture=textures[kind],roughnessFactor=.94 if kind=='earth' else .87,metallicFactor=0))
    layer('outdoor_floor_soil_substrate',area,-1.5,-.2,'earth')
    patches=list(earth.geoms) if hasattr(earth,'geoms') else [earth]
    for i,p in enumerate(patches,1):layer('outdoor_floor_level_earth_'+str(i),p,-.2,0.,'earth')
    layer('outdoor_floor_flush_walkway',path,-.2,0.,'concrete')
    for name,p in pads.items():layer('outdoor_floor_bench_pad_'+name,p,-.2,0.,'concrete')
    return dict(area_bounds_m=list(AREA),surface_elevation_m=0.,soil_bottom_m=-1.5,
        selected_path_and_pad_thickness_m=.2,pad_bounds_m=PAD_BOUNDS,
        main_path_width_m=1.6,station_approach_width_m=1.4,
        earth_surface_area_m2=float(earth.area),hard_surface_area_m2=float(path.area+sum(p.area for p in pads.values())),
        geometry_is_authored=True,actual_paper_site_survey=False,ground_strength_qualified=False,
        surface_friction_qualified=False,stake_retention_qualified=False)


def build():
    g=Geometry();details=add_ground(g);geometry=g.export('weather_outdoor_ground_candidate')
    section=Geometry();add_ground(section,section=True);section_geometry=section.export('weather_outdoor_ground_section')
    refs=[Path(__file__),HERE/'geometry_tools.py',HERE/'tripod_sources.json']
    record=dict(schema_version=1,status='authored_outdoor_ground_candidate',geometry=geometry,
        section_geometry=section_geometry,section_plane=dict(axis='X',coordinate_m=6.,retained_half='x >= 6; actual capped solids'),
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        design=details,
        basis=['Onset two-metre tripod requires level firm ground. The old outdoor resin slab cannot represent an earth-stake installation.',
            'All surface composition, layer depths, paths and bench pad dimensions are authored site choices, not surveyed features of the paper laboratory.',
            'The 1.5 m earth volume is an explicit geometric extent for reviewing selected stakes and the 1.2192 m rod; it is not a soil mechanics model.',
            'Paths and ordinary bench footing pads meet the earth at z=0 without an invented step. There are no hidden robot fixtures or preinstalled anchors.'],
        source_installation_url='https://www.onsetcomp.com/sites/default/files/resources-documents/12317-B%20MAN-TRIPOD.pdf',
        staged_in_lab=False,installation_qualified=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'outdoor_ground_assets.json',record);print(json.dumps(dict(parts=geometry['parts'],design=details)))


if __name__=='__main__':build()
