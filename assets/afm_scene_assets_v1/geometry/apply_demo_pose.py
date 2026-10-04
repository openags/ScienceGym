"""Run in Blender after opening .blend; sets authored held/open or docked/closed geometry.
blender -b geometry/afm_operations_lab.blend --python geometry/apply_demo_pose.py -- held
No reachability/force/collision check and no physical execution.
"""
import bpy,sys,math
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'held'
if mode not in ['held','docked']:raise ValueError('Use held or docked')
r=bpy.data.objects['afm.sample_carrier_demo']
r.location.z=0 if mode=='held' else -.057
for o in r.children:
 if o.name.startswith('clamp.demo.open_arm'):
  left=o.name=='clamp.demo.open_arm'
  px=.327 if left else .473;py=-.263
  angle=0 if mode=='held' else (-math.pi/2 if left else math.pi/2)
  o.location.x=px-.021*math.sin(angle);o.location.y=py+.021*math.cos(angle);o.rotation_euler.z=angle
r['demo_state']=mode;r['physical_execution']=False
print('STATIC_DEMO_POSE',mode)
