"""Bind guarded State to Blender objects. Run from the package Blend, not a GLB.
Example: blender -b geometry/cooling_operations_lab.blend --python geometry/apply_demo_state.py -- open_clamp grasp_carrier
Without --save, changes exist only in the Blender session. No physics / device calls.
"""
import bpy, sys, json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
from semantic_controls import State, transition, validate

def bind(s):
    validate(s)
    objects=bpy.data.objects
    # Preserve canonical poses once. Every subsequent bind is absolute, not additive.
    for o in objects:
        if 'demo_canonical_location' not in o:o['demo_canonical_location']=list(o.location)
        if 'demo_canonical_rotation' not in o:o['demo_canonical_rotation']=list(o.rotation_euler)
        o.location=o['demo_canonical_location'];o.rotation_euler=o['demo_canonical_rotation']
    for o in objects:
        if o.name.startswith('carrier.') or o.name=='handling.film_frame' or o.name.startswith('handling.film.'):
            if s.carrier=='held_demo':o.location.z+=.10
        if o.name.startswith('clamp.') and o.name.endswith('.lever'):
            o.rotation_euler.z=1.5707963267948966 if s.clamp=='open' else 0
            if s.clamp=='open':o.location.x-=.018;o.location.y+=.018
            o['semantic_state']=s.clamp
    for layer in ['lower','upper']:
        state=getattr(s,layer+'_film')
        intact=objects['handling.film.'+layer]
        intact.hide_render=state!='intact';intact.hide_viewport=state!='intact'
        objects['handling.film.'+layer+'.display_tab'].hide_render=state=='removed'
        objects['handling.film.'+layer+'.display_tab'].hide_viewport=state=='removed'
        intact['component_identity']=f'handling.pe.{layer}.rev{getattr(s,layer+"_film_revision")}'
    torn=objects.get('handling.film.lower.torn_variant')
    if torn:
        torn.hide_render=s.lower_film!='torn_demo';torn.hide_viewport=s.lower_film!='torn_demo'
        torn['component_identity']=f'handling.pe.lower.rev{s.lower_film_revision}'
    for sample in ['white','black']:
        lid=objects[sample+'.aperture_lid'];knob=objects[sample+'.lid_knob']
        if s.lid=='closed':
            delta=__import__('mathutils').Vector(lid['closed_pose_m'])-lid.location
            lid.location+=delta;knob.location+=delta
        lid['semantic_state']=s.lid
        dx={'left':-.06,'center':0,'right':.06}[s.reflector_pose]
        for suffix in ['reflector_carriage','reflector_arm','reflector_disk']:objects[sample+'.'+suffix].location.x+=dx
        objects[sample+'.reflector_carriage']['semantic_state']=s.reflector_pose
    objects['dock.nameplate.text'].data.body='CARRIER / '+s.carrier.upper().replace('_',' ')+' / CLAMPS '+s.clamp.upper()
    objects['logger.readback'].data.body='LOGGER: '+('ARMED DEMO' if s.logger=='armed_demo' else 'IDLE')
    objects['optical.config.text'].data.body='CONFIG: '+s.optical_config.upper()+' / DEMO'
    reference=objects['optical.reference_disk']
    if s.optical_sample!='none':
        if s.optical_config=='ftir_angle':reference.location=(.43-.147,.17+.100,.284)
        else:reference.location=(.43+.035,.17-.192,.291);reference.rotation_euler.x=1.5707963267948966
    reference['semantic_identity']=s.optical_sample
    bpy.context.scene['semantic_state_json']=json.dumps(__import__('dataclasses').asdict(s),sort_keys=True)
    bpy.context.scene['physical_execution']=False
    bpy.context.view_layer.update()
    return s

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    save='--save' in args;args=[a for a in args if a!='--save']
    s=State()
    for e in args:s=transition(s,e)
    bind(s)
    if save:bpy.ops.wm.save_as_mainfile(filepath=str(P/'geometry'/'cooling_demo_state.blend'),compress=True)
    print(json.dumps({'mode':'static_bound_state_only','events':args,'state':__import__('dataclasses').asdict(s)}))
