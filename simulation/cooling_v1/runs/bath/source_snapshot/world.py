"""MuJoCo workcell with a torque-limited Panda and explicit fixture geometry."""
from copy import deepcopy
import json
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from bootstrap import CACHE, HERE

TOP = .74
HOME = np.array([0., -.35, 0., -2.05, 0., 1.72, .7854])


def vec(v):
    return ' '.join(f'{float(x):.9g}' for x in v)


class World:
    def __init__(self):
        self.root = ET.parse(CACHE/'panda.xml').getroot()
        self.root.set('model', 'ScienceGym cooling contact workcell')
        self.root.find('compiler').set('meshdir', '')
        for mesh in self.root.findall('asset/mesh'):
            mesh.set('file','robot/'+mesh.get('file'))
        self.root.find('option').attrib.update(timestep='.002', integrator='implicitfast', iterations='80', cone='elliptic')
        ET.SubElement(self.root.find('default'),'geom',solref='.004 1',solimp='.95 .99 .0005',condim='4')
        self.root.remove(self.root.find('keyframe'))
        self.w = self.root.find('worldbody'); self.assets = self.root.find('asset')
        ET.SubElement(self.root, 'visual')
        ET.SubElement(self.root.find('visual'), 'global', offwidth='1280', offheight='800')
        ET.SubElement(self.assets, 'texture', name='floor_tex', type='2d', builtin='checker', rgb1='.17 .21 .26', rgb2='.2 .24 .29', width='512', height='512')
        ET.SubElement(self.assets, 'material', name='floor_mat', texture='floor_tex', texrepeat='5 5', reflectance='.05')
        ET.SubElement(self.w, 'geom', name='floor', type='plane', size='5 5 .1', material='floor_mat')
        self.box(self.w, 'bench', [.68, .67, .04], [.45, 0, TOP-.04], [.72, .75, .78, 1])
        for x in [-.14, 1.04]:
            for y in [-.57, .57]:
                self.box(self.w, 'leg_'+str(x)+'_'+str(y), [.035,.035,TOP/2], [x,y,TOP/2], [.22,.27,.32,1])
        self.w.find("body[@name='link0']").set('pos', '0 0 .74')
        for light in self.w.findall('light'):
            light.attrib.update(pos='0 -1 3', diffuse='.8 .8 .8', directional='true', dir='0 .2 -1')
        ET.SubElement(self.w, 'light', pos='1 1 3', diffuse='.5 .5 .5')
        hand = self.w.find(".//body[@name='hand']")
        ET.SubElement(hand, 'site', name='tcp', pos='0 0 .1034', size='.003', rgba='0 .5 1 1')
        # Original arm geometry and torque limits are retained. Fingertip
        # material friction is an explicit simulated rubber-pad assumption.
        for default in self.root.findall('.//default'):
            if default.get('class', '').startswith('fingertip_pad'):
                default.find('geom').set('friction', '1.4 .01 .006')
                default.find('geom').set('condim', '6')
        finger_actuator=self.root.find("actuator/general[@name='actuator8']")
        finger_actuator.attrib.update(gainprm='.31372549 0 0',biasprm='0 -2000 -40',forcerange='-40 40')
        self.objects = {}
        self.catalog = json.loads((HERE/'geometry/catalog.json').read_text())['parts'] if (HERE/'geometry/catalog.json').exists() else []
        self.mesh_names = {}

    def box(self, parent, name, size, pos=(0,0,0), rgba=(.6,.6,.6,1), **kwargs):
        attrs = dict(name=name, type='box', size=vec(size), pos=vec(pos), rgba=vec(rgba), friction='1 .005 .0001')
        attrs.update({k:str(v) for k,v in kwargs.items()})
        return ET.SubElement(parent, 'geom', **attrs)

    def cylinder(self, parent, name, radius, halfheight, pos=(0,0,0), rgba=(.6,.6,.6,1), **kwargs):
        attrs=dict(name=name,type='cylinder',size=vec([radius,halfheight]),pos=vec(pos),rgba=vec(rgba),friction='1 .005 .0001')
        attrs.update({k:str(v) for k,v in kwargs.items()})
        return ET.SubElement(parent,'geom',**attrs)

    def body(self, name, pos, free=True):
        b=ET.SubElement(self.w,'body',name=name,pos=vec(pos))
        if free: ET.SubElement(b,'freejoint',name=name+'_free')
        self.objects[name]=dict(initial_pos=list(pos),free=free)
        return b

    def handle(self, body, height=.05):
        name=body.get('name')
        # 24 mm-wide positive grip adapter, a declared task-authored fixture.
        self.box(body,name+'_handle',[.013,.012,.025],[0,0,height],[.06,.5,.65,1],mass='.025')
        ET.SubElement(body,'site',name=name+'_grasp',pos=vec([0,0,height]),size='.002')
        self.objects[name]['grasp_offset']=[0,0,height]

    def ring(self, parent, name, inner, outer, height, z=0, rgba=(.7,.73,.76,1), mass=.1):
        # Decomposed collision ring: never a convex hull sealing the aperture.
        for i in range(48):
            angle=2*np.pi*i/48
            r=(inner+outer)/2
            self.box(parent,name+'_'+str(i),[(outer-inner)/2,np.pi*r/48*1.03,height/2],
                     [r*np.cos(angle),r*np.sin(angle),z],rgba,
                     euler=vec([0,0,angle]),mass=str(mass/48))

    def nest(self, name, pos, half=.04, height=.012):
        b=self.body(name,pos,False)
        self.box(b,name+'_floor',[half,half,height/2],[0,0,height/2],[.18,.25,.32,1])
        for sign in [-1,1]:
            self.box(b,name+'_wallx'+str(sign),[.003,half,height],[sign*(half+.003),0,height],[.18,.25,.32,1])
            self.box(b,name+'_wally'+str(sign),[half,.003,height],[0,sign*(half+.003),height],[.18,.25,.32,1])
        return b

    def original(self, parent, root, exclude=(), prefix='source', only=None):
        for part in self.catalog:
            if part['root']!=root or any(s in part['id'] for s in exclude): continue
            if only and not any(s in part['id'] for s in only):continue
            key=part['file']
            if key not in self.mesh_names:
                if hashlib.sha256((HERE/'geometry'/key).read_bytes()).hexdigest()!=part['file_sha256']:
                    raise ValueError('Source mesh cache changed: '+key)
                mesh='source_'+key[:-4]
                ET.SubElement(self.assets,'mesh',name=mesh,file='equipment/'+key)
                self.mesh_names[key]=mesh
            ET.SubElement(parent,'geom',name=prefix+'_'+part['id'],type='mesh',mesh=self.mesh_names[key],
                          pos=vec(part['pos']),rgba=vec(part['rgba']),contype='0',conaffinity='0',group='2',mass='0')

    def save(self, path):
        ET.indent(self.root)
        ET.ElementTree(self.root).write(path,encoding='unicode')
        return self.objects


def assembly_scene(path):
    w=World()
    # Source-size emitter, insulation and removable plate. Initial stock
    # supports are task-authored and separately identified from paper facts.
    center=[.51,.13,TOP]
    base=w.body('assembly_base',center,False)
    w.cylinder(base,'base_plinth',.08,.012,[0,0,.012],[.13,.18,.23,1])
    w.ring(base,'assembly_alignment_fixture',.0254,.031,.008,.028,rgba=[.06,.45,.60,1],mass=.03)
    for i in range(4):
        a=np.pi/4+i*np.pi/2
        w.cylinder(base,'alignment_pin_'+str(i),.0025,.023,[.028*np.cos(a),.028*np.sin(a),.047],rgba=[.06,.45,.60,1],mass='.005')
    for name,xy,radius,height,color in [
        ('foam_lower',[.38,-.25],.025,.025,[.62,.38,.56,1]),
        ('foam_upper',[.54,-.25],.025,.025,[.62,.38,.56,1]),
        ('emitter',[.7,-.22],.025,.0005,[.95,.95,.94,1]),
    ]:
        b=w.body(name,[*xy,TOP+height/2+.002])
        w.cylinder(b,name+'_shape',radius,height/2,rgba=color,mass='.0088' if name=='emitter' else '.02')
        # Temporary lift tool remains attached to the rear/edge fixture;
        # it must be removed before an optical exposure can be accepted.
        if name=='emitter':
            w.ring(b,'emitter_edge_carrier',.026,.032,.006,rgba=[.08,.5,.65,1],mass=.02)
            for sign in [-1,1]:
                w.box(b,'emitter_carrier_post'+str(sign),[.003,.006,.025],[sign*.03,0,.025],[.08,.5,.65,1],mass='.006')
                w.box(b,'emitter_carrier_edge_seat'+str(sign),[.004,.006,.0005],[sign*.025,0,-.00075],[.08,.5,.65,1],mass='.002')
            w.box(b,'emitter_carrier_bridge',[.033,.006,.004],[0,0,.05],[.08,.5,.65,1],mass='.008')
            w.handle(b,.068)
        else:
            ET.SubElement(b,'site',name=name+'_grasp',pos='0 0 .004',size='.002')
            w.objects[name]['grasp_offset']=[0,0,.004]
    lid=w.body('baseline_lid',[.73,.28,TOP+.012])
    w.cylinder(lid,'baseline_lid_plate',.065,.003,mass='.08')
    w.handle(lid,.04)
    w.nest('lid_stand',[.73,.28,TOP],.073,.009)
    button=w.body('acquisition_button',[.71,-.05,TOP+.045],False)
    ET.SubElement(button,'joint',name='button_travel',type='slide',axis='0 0 -1',range='0 .008',damping='2',stiffness='400',springref='0')
    w.cylinder(button,'button_cap',.017,.006,rgba=[.15,.65,.32,1],mass='.015')
    for sign in [-1,1]:
        w.box(w.w,'button_console_side'+str(sign),[.02,.04,.02],[.71+sign*.045,-.05,TOP+.02],[.12,.17,.23,1])
        w.box(w.w,'button_console_end'+str(sign),[.025,.0075,.02],[.71,-.05+sign*.0325,TOP+.02],[.12,.17,.23,1])
    # Original commercial geometry remains visible with source IDs; no body
    # collision or actuator qualification is inferred from this display.
    console=w.body('source_usb_tc',[.36,.44,TOP],False)
    w.original(console,'MCC_USB_TC',prefix='daq')
    return w.save(path)


def probe_scene(path):
    w=World()
    block=w.body('copper_block',[.53,.12,TOP],False)
    hole=.0025;half=.035;height=.06
    for sign in [-1,1]:
        w.box(block,'block_x'+str(sign),[(half-hole)/2,half,height/2],
              [sign*(half+hole)/2,0,height/2],[.65,.36,.18,1])
        w.box(block,'block_y'+str(sign),[hole,(half-hole)/2,height/2],
              [0,sign*(half+hole)/2,height/2],[.65,.36,.18,1])
    probe=w.body('probe',[.45,-.22,TOP+.064])
    w.cylinder(probe,'probe_sheath',.0015,.04,rgba=[.72,.75,.79,1],mass='.005')
    w.cylinder(probe,'probe_stop_collar',.012,.004,rgba=[.06,.45,.60,1],mass='.008')
    w.box(probe,'probe_handling_fixture',[.012,.012,.016],[0,0,.025],[.06,.45,.60,1],mass='.012')
    ET.SubElement(probe,'site',name='probe_grasp',pos='0 0 .025',size='.002')
    w.objects['probe']['grasp_offset']=[0,0,.025]
    stand=w.body('probe_stand',[.45,-.22,TOP],False)
    w.ring(stand,'probe_stand_rim',.003,.019,.06,.03,rgba=[.2,.25,.3,1])
    # Only optical/reference geometry is reused. Its visual presence does not
    # certify the inferred drilling pattern or the added robot handling collar.
    bath=w.body('source_bath',[.84,.38,TOP],False)
    w.original(bath,'THERMO_A25_AC150_HYPOTHESIS',prefix='bath')
    return w.save(path)


def lid_scene(path):
    w=World()
    receiver=w.body('aperture_support',[.51,.13,TOP],False)
    w.ring(receiver,'aperture_wall',.054,.065,.065,.0325,mass=.2)
    lid=w.body('baseline_lid',[.48,-.23,TOP+.012])
    w.cylinder(lid,'baseline_lid_plate',.065,.003,mass='.08')
    w.handle(lid,.04)
    w.nest('lid_stand',[.48,-.23,TOP],.073,.009)
    return w.save(path)


def door_scene(path):
    w=World()
    # Original inference: a retained optical-access fixture. This is not an
    # unverified replacement for a specific manufacturer's door mechanism.
    base=w.body('access_base',[.55,-.04,TOP],False)
    w.box(base,'access_floor',[.10,.12,.008],[0,.08,.008],[.16,.21,.27,1])
    for sign in [-1,1]:
        w.box(base,'access_wall'+str(sign),[.008,.10,.045],[sign*.092,.08,.045],[.16,.21,.27,1])
    lid=w.body('access_lid',[.55,-.04,TOP+.09],False)
    ET.SubElement(lid,'joint',name='access_hinge',type='hinge',axis='1 0 0',range='0 1.6',damping='.3',frictionloss='.22')
    w.box(lid,'access_panel',[.10,.10,.006],[0,.10,.006],[.75,.77,.8,1],mass='.12')
    w.box(lid,'access_handle',[.013,.012,.022],[0,.15,.034],[.06,.5,.65,1],mass='.025')
    ET.SubElement(lid,'site',name='access_lid_grasp',pos='0 .15 .034',size='.002')
    w.objects['access_lid']['grasp_offset']=[0,.15,.034]
    return w.save(path)


if __name__=='__main__':
    print(json.dumps(assembly_scene(HERE/'workcell.xml'),indent=2))
