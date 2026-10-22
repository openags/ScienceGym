"""Attach original source-reconstructed meshes in each actual moving frame."""
import numpy as np
from world import vec

PART_NAMES={
    'foam_lower':['foam_1','foam_mylar_1'],
    'foam_upper':['foam_2','foam_mylar_2'],
    'emitter':['emitter_copper','emitter_white_coating'],
    'pe_tube':['PE_support','PE_support_mylar'],
    'shield':['radiation_shield'],
    'aperture':['aperture_plate'],
    'cover':['film_spacer'],
}


def moving_part(world,body,name):
    """Preserve authored vertices/material colors; relocate the part frame only."""
    labels=PART_NAMES[name]
    catalog={p['id']:p for p in world.catalog}
    ids=['COOLER_WHITE__'+label for label in labels]
    origin=np.asarray(catalog[ids[0]]['pos'])
    existing=list(body.findall('geom'))
    world.original(body,'COOLER_WHITE',only=ids,prefix='physical_'+name)
    for geom in body.findall('geom'):
        if geom in existing:
            geom.set('group','3')
        else:
            geom.set('pos',vec(np.fromstring(geom.get('pos'),sep=' ')-origin))


def fixed_frame(world,body):
    """Source base/frame with collision geometry, including open hollow rods."""
    selected=['__acrylic_base','__mylar_base','__lift_foot','__lift_thread','__lift_plate',
              '__rail_','__orange_insert_','__upright_bracket','__bracket_bolt']
    world.original(body,'COOLER_WHITE',only=selected,prefix='physical_frame')
    for geom in body.findall('geom'):
        # These structural elements are individually convex. The extrusion
        # consists of its separate core/flange parts, not one filled AABB.
        geom.set('contype','1');geom.set('conaffinity','1')
    for x in [-.1625,.1625]:
        rod=world.body('frame_rod_'+str(x),np.asarray(world.objects[body.get('name')]['initial_pos'])+[x,.03,.158],False)
        world.ring(rod,'frame_rod_wall_'+str(x),.007,.010,.275,rgba=[.48,.52,.57,1])
        previous=list(rod.findall('geom'))
        world.original(rod,'COOLER_WHITE',only=['COOLER_WHITE__upright_'+str(x)],prefix='physical_rod')
        for geom in rod.findall('geom'):
            if geom in previous:geom.set('group','3')
            else:geom.set('pos',vec(np.fromstring(geom.get('pos'),sep=' ')-[x,.03,.158]))
