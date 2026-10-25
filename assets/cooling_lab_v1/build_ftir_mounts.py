"""Inspectable ordinary mounting hypotheses; retain failed installation fits.

The source instrument and loose accessory meshes are immutable inputs. A new
factory-floor candidate and ordinary adapter parts expose the installation
datums. Neither this assembly nor an open cover grants optical compatibility.
"""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
from geometry_tools import Geometry, HERE, ROOT, sha, write_json
from build_supplies import solid, export_review, STEEL, DARK, BLACK

CX, CY = -.011, -.160
FLOOR_TOP = .060
FOCUS = [CX+.103-.095, CY-.126+.132, FLOOR_TOP+.090]


def box(x,y,z,center):
    return cq.Workplane('XY').box(x,y,z).val().translate(center)


def hole(shape,x,y,r,z,length):
    return shape.cut(cq.Solid.makeCylinder(r,length,cq.Vector(x,y,z)))


def screw(g, name, x, y, underside, diameter, length, head_d, head_h, hex_af):
    # A smooth thread envelope is intentional: no thread/contact simulation.
    shank=cq.Solid.makeCylinder(diameter/2,length,cq.Vector(x,y,underside-length))
    head=cq.Solid.makeCylinder(head_d/2,head_h,cq.Vector(x,y,underside))
    socket=cq.Workplane('XY').center(x,y).polygon(6,hex_af/np.cos(np.pi/6)).extrude(head_h*.60).val().translate((0,0,underside+head_h*.45))
    solid(g,name,shank.fuse(head).cut(socket),STEEL,.8,role='ordinary_fastener_thread_envelope')


def build():
    # Millimetres for CAD, metres for the exported scene and all interface data.
    plate=box(206,252,6,(CX*1000,CY*1000,57))
    # Slot/finger-hole positions and diameters are drawing-informed hypotheses.
    for x in [-60,0,60]:
        for y in [-54,54]:
            slot=cq.Workplane('XY').center(CX*1000+x,CY*1000+y).slot2D(44,4,0).extrude(8).val().translate((0,0,53))
            plate=plate.cut(slot)
    plate=hole(plate,CX*1000-40,CY*1000-93,10,53,8)
    plate=hole(plate,FOCUS[0]*1000,FOCUS[1]*1000,2.5,53,8)
    # Rear-right mounting position leaves the purge-outlet insertion corridor.
    fasteners=[(-50,-117),(50,-117),(-50,117),(10,117)]
    for x,y in fasteners:
        plate=hole(plate,CX*1000+x,CY*1000+y,1.8,53,8)
    g=Geometry();solid(g,'factory_floor_candidate',plate,STEEL,.65,role='source_dimensioned_floor_candidate')
    g.box('inferred_rear_registration_block',[.024,.016,.010],[CX+.080,CY+.113,.065],DARK,role='unmeasured_factory_registration')
    factory=export_review(g,'ftir_factory_floor_candidate')
    models=json.loads((HERE/'angular_accessories.json').read_text())
    configs=[]
    for identity in ['harrick_hrs','spectratech_500']:
        model=next(i for i in models['items'] if i['id']==identity)
        is_hrs=identity=='harrick_hrs'
        # HRS remains mechanically centred. Translating its inferred front
        # mirror line onto the instrument ray would run through the rear wall.
        translation=[CX,CY,.066] if is_hrs else [CX,FOCUS[1]+.025,.083]
        mounting=[(x,y) for x in ([-82,82] if is_hrs else [-78,78]) for y in ([-91,91] if is_hrs else [-40,40])]
        adapter=box(200,244,6,(CX*1000,CY*1000,63))
        # Ordinary relief for the visibly separate factory registration block.
        adapter=adapter.cut(box(70,26,8,(CX*1000+68,CY*1000+113,63)))
        for x,y in fasteners:adapter=hole(adapter,CX*1000+x,CY*1000+y,2.3,59,8)
        g=Geometry();interfaces=[]
        for number,(x,y) in enumerate(mounting):
            wx=translation[0]*1000+x;wy=translation[1]*1000+y
            adapter=hole(adapter,wx,wy,1.7,59,8)
            if not is_hrs:
                spacer=cq.Solid.makeCylinder(6,17,cq.Vector(wx,wy,66))
                spacer=hole(spacer,wx,wy,2.25,65,19)
                solid(g,'spacer_'+str(number),spacer,STEEL,.6,role='ordinary_optical_standoff')
            upper=translation[2]*1000+(10 if is_hrs else 8)
            washer=cq.Solid.makeCylinder(5,.8,cq.Vector(wx,wy,upper))
            washer=hole(washer,wx,wy,2.15,upper-.1,1)
            solid(g,'accessory_washer_'+str(number),washer,STEEL,.8)
            length=16 if is_hrs else 30
            screw(g,'accessory_M4_'+str(number),wx,wy,upper+.8,4,length,7,4,3)
            interfaces.append(dict(id='accessory_M4_'+str(number),center_xy_m=[wx*.001,wy*.001],
                nominal_diameter_m=.004,selected_length_m=length*.001,
                engagement_m=(66-(upper+.8-length))*.001,plate_bottom_clearance_m=(upper+.8-length-60)*.001,
                basis='Selected ordinary M4 envelope; thread geometry, grade, torque and load rating unresolved'))
        solid(g,'ordinary_adapter_plate',adapter,BLACK,.25,role='authored_ordinary_adapter_not_oem')
        for number,(x,y) in enumerate(fasteners):
            wx=CX*1000+x;wy=CY*1000+y
            washer=cq.Solid.makeCylinder(4.5,.8,cq.Vector(wx,wy,66))
            washer=hole(washer,wx,wy,2.2,65.9,1)
            solid(g,'floor_washer_'+str(number),washer,STEEL,.8)
            screw(g,'floor_8_32_'+str(number),wx,wy,66.8,4.166,12.7,6.9,4.2,3.18)
            interfaces.append(dict(id='floor_8_32_'+str(number),center_xy_m=[wx*.001,wy*.001],
                nominal_diameter_m=.004166,selected_length_m=.0127,engagement_m=.0059,plate_bottom_clearance_m=.0001,
                basis='Authored four-hole pattern and 8-32 x 1/2-inch envelopes. Specac documents a DIFFERENT two-screw system; no OEM compatibility inference'))
        hardware=export_review(g,'ftir_mount_'+identity)
        loose=[m['part'] for m in model['details']['masks']]
        if not is_hrs:loose+=['alignment_mirror_7004_001','blank_plate']
        configs.append(dict(id=identity,label=model['label'],hardware=hardware,accessory_geometry=model['geometry'],
            accessory_translation_m=translation,excluded_loose_parts=loose,fasteners=interfaces,
            plate_dimensions_m=[.200,.244,.006],standoff_height_m=0 if is_hrs else .017,
            sample_point_m=(np.array([0,-.009,.0901] if is_hrs else model['details']['sample_center_m'])+translation).tolist(),
            accessory_input_ray_yz_m=[translation[1]+(-.054 if is_hrs else -.025),translation[2]+(.084 if is_hrs else .067)],
            input_ray_basis='Inferred front-fold mirror centre line, NOT an established HRS input interface' if is_hrs else 'Authored model-500 entry and exit ray, not a manufacturer optical prescription',
            status='unaccepted_mounting_hypothesis',mounting_qualified=False,manipulation_qualified=False))
    interfaces=json.loads((ROOT/'assets/nicolet_6700_v1/interfaces.json').read_text())
    write_json(HERE/'ftir_mounts.json',dict(schema_version=1,units='m',axes='+Z up; -Y instrument front',
        instrument=dict(path='assets/nicolet_6700_v1/geometry/nicolet_6700.glb',sha256=sha(ROOT/'assets/nicolet_6700_v1/geometry/nicolet_6700.glb'),source_y_up=True),
        instrument_cover=next(i for i in interfaces['interfaces'] if i['id']=='sample_cover'),
        factory_floor=factory,datums=dict(factory_plate_center_xy_m=[CX,CY],factory_plate_top_m=FLOOR_TOP,
            factory_plate_dimensions_m=[.206,.252,.006],beam_focus_m=FOCUS,cover_clearance_m=.190,
            source_dimensions=['plate X/Y 206/252 mm','focus 132 mm from front / 95 mm from right','focus height approximately 90 mm','cover clearance approximately 190 mm'],
            authored_dimensions=['plate thickness 6 mm','existing support bosses 4 mm','local chassis floor Z50 mm','all hole/slot/registration-block and adapter dimensions'],
            precision='The 90 and 190 mm dimensions are approximate; checks use nominal values, not a manufacturer tolerance specification'),
        configurations=configs,source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in
            [Path(__file__),HERE/'geometry_tools.py',HERE/'build_supplies.py',HERE/'ftir_mount_sources.json',HERE/'angular_accessories.json',HERE/'ftir_mount_rejected_purge.json',ROOT/'assets/nicolet_6700_v1/interfaces.json']],
        load_path=['accessory base','adapter plate or four ordinary standoffs','factory-floor candidate','four existing inferred instrument bosses','chassis','bench'],
        limits=['Factory floor registration/retention and its hole pattern are unmeasured',
            'Adapter hardware is an ordinary authored optical mount, not an OEM Harrick/Spectra-Tech part or a robot-specific fixture',
            'Smooth screw envelopes do not simulate threads, clamp forces or rated load capacity',
            'Open-cover inspection is not authorization to operate the spectrometer with its cover open',
            'Source instrument and bench-staged accessories remain unchanged; this is a separate installation review'],
        owner_acceptance=None,installed_compatibility_qualified=False))
    print(json.dumps(dict(configurations=len(configs),hardware_parts=sum(c['hardware']['parts'] for c in configs),factory_parts=factory['parts'])))


if __name__=='__main__':build()
