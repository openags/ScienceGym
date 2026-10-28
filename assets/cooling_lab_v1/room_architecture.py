"""Original architectural design, in metres; not a survey of the paper's lab.

Windows are openings in segmented walls. Ceiling, door headers and services
have explicit bounds so visual cutaways never remove them from layout checks.
No service capacity, ventilation performance or fire rating is implied.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import trimesh
from trimesh.visual.material import PBRMaterial

PAINT = [224, 227, 221]
BASE = [115, 139, 143]
FRAME = [164, 177, 178]
TRIM = [72, 91, 96]


def build_room(g, box, obstacle):
    def solid(name, size, center, color=PAINT, role='wall_upper', collision=True):
        mesh = g.box(name, size, center, color, role)
        mesh.visual.material.roughnessFactor = .82
        if collision:
            obstacle(name, mesh.bounds.tolist(), role)
        return mesh

    # Fine-grain seamless resin surface; generated from a fixed random seed.
    rng = np.random.default_rng(2018)
    grain = rng.normal(0, 1.7, (512, 512, 1))
    pixels = np.clip(np.array([150, 160, 157]) + grain, 0, 255).astype('uint8')
    floor_texture = Image.fromarray(pixels)
    for name, size, pos in [('indoor_floor', [12, 10, .12], [6, 5, -.06]),
                            ('annex_floor', [6, 10, .12], [-3, 5, -.06]),
                            ('outdoor_floor', [12, 8, .12], [6, 16, -.06]),
                            ('outdoor_access_path', [3, 2, .12], [6, 11, -.06])]:
        if name in ['indoor_floor','annex_floor']:size=[size[0]+.2,size[1]+.2,size[2]]
        mesh = g.box(name, size, pos, [188, 198, 194], 'floor')
        mesh.visual = trimesh.visual.TextureVisuals(uv=mesh.vertices[:, :2] / 1.5,
            material=PBRMaterial(baseColorTexture=floor_texture, roughnessFactor=.58, metallicFactor=0))

    # Each opening is expressed along the wall's horizontal local coordinate.
    def wall(name, a, b, openings=()):
        horizontal = a[1] == b[1]
        start, end = (a[0], b[0]) if horizontal else (a[1], b[1])
        fixed = a[1] if horizontal else a[0]
        cuts = sorted({start, end, *[v for opening in openings for v in opening[:2]]})
        def piece(suffix, lo, hi, z0, z1, color, role, thickness=.16):
            size = [hi-lo, thickness, z1-z0] if horizontal else [thickness, hi-lo, z1-z0]
            center = [(lo+hi)/2, fixed, (z0+z1)/2] if horizontal else [fixed, (lo+hi)/2, (z0+z1)/2]
            return solid('wall_'+name+'_'+suffix, size, center, color, role)
        for i, (lo, hi) in enumerate(zip(cuts[:-1], cuts[1:])):
            opening = next((o for o in openings if o[0] <= (lo+hi)/2 <= o[1]), None)
            ranges = [(0, opening[2]), (opening[3], 3.4)] if opening else [(0, 3.4)]
            for j, (z0, z1) in enumerate(ranges):
                for k, (p, q) in enumerate([(z0, min(z1, .9)), (max(z0, .9), z1)]):
                    if q > p:
                        piece(f'{i}_{j}_{k}', lo, hi, p, q, BASE if q <= .9 else PAINT,
                              'wall_lower' if q <= .9 else 'wall_upper')
            # Thin coved base is entirely inside the registered wall footprint.
            piece(f'base_{i}', lo, hi, .005, .12, TRIM, 'wall_lower', .18)
        for i, (lo, hi, sill, head) in enumerate(openings):
            prefix = 'window_'+name+'_'+str(i)
            def window_part(suffix, span, depth, height, along, z, color, alpha=255):
                size = [span, depth, height] if horizontal else [depth, span, height]
                center = [along, fixed, z] if horizontal else [fixed, along, z]
                mesh = g.box(prefix+'_'+suffix, size, center, color, 'window', alpha=alpha)
                mesh.visual.material.roughnessFactor = .12 if alpha < 255 else .65
                obstacle(prefix+'_'+suffix, mesh.bounds.tolist(), 'window')
                return mesh
            for j, z in enumerate([sill+.025, head-.025]):
                window_part('horizontal_'+str(j), hi-lo, .15, .05, (lo+hi)/2, z, FRAME)
            for j, along in enumerate([lo+.025, (lo+hi)/2, hi-.025]):
                window_part('mullion_'+str(j), .05, .15, head-sill, along, (sill+head)/2, FRAME)
            for j,along in enumerate([lo+.057,hi-.057]):
                window_part('gasket_vertical_'+str(j),.012,.155,head-sill-.09,along,(sill+head)/2,[55,63,64])
            for j,z in enumerate([sill+.057,head-.057]):
                window_part('gasket_horizontal_'+str(j),hi-lo-.09,.155,.012,(lo+hi)/2,z,[55,63,64])
            window_part('glass', hi-lo-.07, .012, head-sill-.07, (lo+hi)/2, (sill+head)/2, [187, 217, 225], 55)
            window_part('sill', hi-lo+.03, .19, .025, (lo+hi)/2, sill, [197, 204, 202])
            window_part('blind_housing', hi-lo, .18, .07, (lo+hi)/2, head-.035, [208, 214, 209])
            for j in range(5):
                window_part('blind_'+str(j), hi-lo-.08, .09, .012, (lo+hi)/2, head-.10-j*.045, [197, 205, 201])

    segments = [('south_west', [-.1,-.1], [5,-.1], []),
        ('south_east', [7,-.1], [12.1,-.1], []),
        ('north_west', [0,10.1], [5,10.1], [(1,4.3,1.65,2.85)]),
        ('north_east', [7,10.1], [12.1,10.1], [(7.7,11.2,1.65,2.85)]),
        ('east', [12.1,0], [12.1,10.1], [(1,3.5,1.25,2.85),(6.6,9.3,1.65,2.85)]),
        ('annex_west', [-6.1,0], [-6.1,10.1], []),
        ('annex_south', [-6.1,-.1], [0,-.1], []),
        ('annex_north', [-6.1,10.1], [0,10.1], []),
        ('annex_split', [-6.1,5], [0,5], []),
        ('partition_low', [0,0], [0,1.5], []),
        ('partition_mid', [0,3.5], [0,6.5], [(3.8,4.8,1.2,2.4),(5.2,6.2,1.2,2.4)]),
        ('partition_high', [0,8.5], [0,10.1], [])]
    for name, a, b, openings in segments:
        wall(name, a, b, openings)

    # Paired doors shown open. Clear leaf-to-leaf gap exceeds the 2 m route.
    for name, x, y, axis in [('entry',6,0,'x'),('yard',6,10.1,'x'),
                             ('fabrication',0,2.5,'y'),('coating',0,7.5,'y')]:
        def door_part(suffix, size, center, color=FRAME, role='door_open'):
            return solid('door_'+name+'_'+suffix, size, center, color, role)
        def mapped(along, depth, z):
            return [x+along,y+depth,z] if axis=='x' else [x+depth,y+along,z]
        def dims(a,b,c):return [a,b,c] if axis=='x' else [b,a,c]
        door_part('header_wall', dims(2,.16,1.08), mapped(0,0,2.86), PAINT, 'wall_upper')
        door_part('lintel', dims(2.16,.42,.12), mapped(0,-.12,2.26), TRIM, 'wall_upper')
        for side in [-1,1]:
            door_part('jamb_'+str(side),dims(.075,.42,2.2),mapped(side*1.09,-.12,1.1),TRIM)
            # Panel divisions leave a genuine glazed vision aperture.
            for part, d0, d1, z0, z1 in [('bottom',-.92,0,0,1.05),('top',-.92,0,1.85,2.2),
                                        ('edge1',-.92,-.78,1.05,1.85),('edge2',-.14,0,1.05,1.85)]:
                door_part(str(side)+'_'+part,dims(.045,d1-d0,z1-z0),mapped(side*1.025,(d0+d1)/2-.2,(z0+z1)/2),BASE)
            glass = g.box('door_'+name+'_'+str(side)+'_glass',dims(.012,.64,.8),mapped(side*1.025,-.66,1.45),[165,201,208],'door_glass',alpha=65)
            obstacle('door_'+name+'_'+str(side)+'_glass',glass.bounds.tolist(),'door_glass')
            for z in [.27,1.1,1.95]:
                hinge=g.cylinder('door_'+name+'_'+str(side)+'_hinge_'+str(z),.012,.10,mapped(side*1.032,-.225,z),[168,176,179],metal=.85)
                obstacle('door_'+name+'_'+str(side)+'_hinge_'+str(z),hinge.bounds.tolist(),'door_open')
                door_part(str(side)+'_hinge_plate_'+str(z),dims(.004,.065,.09),mapped(side*1.05,-.25,z),FRAME)
            # Handles project away from the opening, preserving registered clearance.
            door_part(str(side)+'_handle',dims(.035,.18,.025),mapped(side*1.073,-.99,1.0),[179,185,183])
            normal=(side,0,0) if axis=='x' else (0,side,0)
            for j,depth in enumerate([-.925,-1.055]):
                for suffix,r,length,along in [('rosette',.022,.006,1.052),('stem',.009,.040,1.075)]:
                    handle=g.cylinder('door_'+name+'_'+str(side)+'_handle_'+str(j)+'_'+suffix,r,length,mapped(side*along,depth,1.0),[174,181,184],axis=normal,metal=.85)
                    obstacle('door_'+name+'_'+str(side)+'_handle_'+str(j)+'_'+suffix,handle.bounds.tolist(),'door_open')
            door_part(str(side)+'_kickplate',dims(.004,.88,.23),mapped(side*1.05,-.66,.17),FRAME)

    # Actual 600 x 1200 mm infill cells: fixtures replace infill panels and
    # share their edges with the suspension grid. Cut border panels close gaps.
    light_positions=[];ceiling_panels=0
    for name,xmin,xmax,ymin,ymax in [('main',0,12,0,10),('fab',-6,0,0,5),('coat',-6,0,5,10)]:
        solid('ceiling_'+name+'_plenum',[xmax-xmin+.16,ymax-ymin+.16,.025],[(xmin+xmax)/2,(ymin+ymax)/2,3.3875],[106,114,111],'ceiling')
        xc=np.append(np.arange(xmin,xmax-.001,.6),xmax);yc=np.append(np.arange(ymin,ymax-.001,1.2),ymax)
        lights={(4,1),(15,1),(4,4),(15,4),(4,6),(15,6)} if name=='main' else {(2,1),(7,2)}
        vents={(9,0),(9,7)} if name=='main' else {(4,0),(4,3)}
        for i,(x0,x1) in enumerate(zip(xc[:-1],xc[1:])):
            for j,(y0,y1) in enumerate(zip(yc[:-1],yc[1:])):
                x=(x0+x1)/2;y=(y0+y1)/2;w=x1-x0;d=y1-y0;prefix='ceiling_'+name+'_'+str(i)+'_'+str(j)
                if (i,j) in lights:
                    light='light_'+name+'_'+str(i)+'_'+str(j)
                    # A frame around an open aperture, rather than a box with
                    # a coplanar luminous face (which causes z-fighting).
                    for side in [-1,1]:
                        solid(light+'_frame_x_'+str(side),[.022,d-.004,.030],[x+side*(w/2-.013),y,3.325],FRAME,'ceiling_fixture')
                        solid(light+'_frame_y_'+str(side),[w-.048,.022,.030],[x,y+side*(d/2-.013),3.325],FRAME,'ceiling_fixture')
                    solid(light+'_housing',[w-.008,d-.008,.010],[x,y,3.351],[119,129,127],'ceiling_fixture')
                    mesh=solid('light_'+name+'_'+str(i)+'_'+str(j)+'_diffuser',[w-.05,d-.05,.008],[x,y,3.314],[246,246,235],'ceiling_fixture')
                    mesh.visual.material.emissiveFactor=[.85,.83,.77]
                    light_positions.append([round(x,3),round(y,3),3.20])
                elif (i,j) in vents:
                    solid(prefix+'_vent_frame',[w-.004,d-.004,.035],[x,y,3.325],FRAME,'ceiling_fixture')
                    solid(prefix+'_vent_recess',[w-.045,d-.045,.004],[x,y,3.305],[47,54,54],'ceiling_fixture')
                    for k,yy in enumerate(np.arange(y0+.055,y1-.03,.07)):
                        solid(prefix+'_vent_louver_'+str(k),[w-.07,.022,.016],[x,yy,3.30],[197,204,202],'ceiling_fixture')
                else:
                    shade=int((i*7+j*3)%5)-2
                    solid(prefix+'_tile',[w-.006,d-.006,.018],[x,y,3.339],[227+shade,230+shade,223+shade],'ceiling')
                    ceiling_panels+=1
        for i,x in enumerate(xc):
            solid('ceiling_'+name+'_grid_x_'+str(i),[.014,ymax-ymin,.012],[x,(ymin+ymax)/2,3.324],[198,205,201],'ceiling')
        for j,y in enumerate(yc):
            solid('ceiling_'+name+'_grid_y_'+str(j),[xmax-xmin,.014,.012],[(xmin+xmax)/2,y,3.324],[198,205,201],'ceiling')
        for x in [xmin+.012,xmax-.012]:
            solid('ceiling_'+name+'_perimeter_x_'+str(x),[.024,ymax-ymin,.035],[x,(ymin+ymax)/2,3.315],FRAME,'ceiling')
        for y in [ymin+.012,ymax-.012]:
            solid('ceiling_'+name+'_perimeter_y_'+str(y),[xmax-xmin,.024,.035],[(xmin+xmax)/2,y,3.315],FRAME,'ceiling')

    # Wall-mounted capped service raceways; no fabricated live connections.
    for name,x0,x1,y in [('north_left',.25,4.6,10.0),('north_right',7.4,11.8,10.0),('fabrication',-5.8,-.25,4.9),('coating',-5.8,-.25,9.99)]:
        solid('service_tray_'+name,[x1-x0,.065,.09],[(x0+x1)/2,y,1.04],[200,207,202],'service_raceway')
        for i,x in enumerate(np.arange(x0+.25,x1,.75)):
            solid('service_tray_'+name+'_blank_'+str(i),[.13,.01,.075],[x,y-.038,1.04],[91,106,109],'service_raceway')
    for name,text,width,center in [('room','SCIENCEGYM',2.4,[2.6,10.006,3.08]),
                                   ('optics','OPTICAL MEASUREMENT',2.75,[9.4,10.006,3.08]),
                                   ('exit','OUTDOOR LAB',1.45,[6,9.997,2.61]),
                                   ('fabrication','MATERIAL PREPARATION',2.6,[-3.8,4.91,2.65]),
                                   ('coating','COATING ROOM',2.2,[-3.8,10.006,2.66])]:
        label=g.label('wall_sign_'+name,text,width,.21,center,[53,77,84],[228,237,226])
        # Use the physical sign's aspect ratio, so long text is neither clipped
        # nor stretched by the general device-label texture template.
        image=Image.new('RGB',(round(width/.21*192),192),(53,77,84))
        draw=ImageDraw.Draw(image);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',108)
        draw.text((image.width/2,96),text,font=font,fill=(228,237,226),anchor='mm')
        label.visual.material.baseColorTexture=image

    return dict(ceiling_underside_m=3.33,lowest_ceiling_fixture_m=3.292,
        light_positions_m=light_positions,ceiling_infill_panels=ceiling_panels,ceiling_module_m=[.6,1.2],
        nominal_door_clear_height_m=2.2,window_openings=sum(len(s[3]) for s in segments),
        design_status='Original architectural candidate; not historical reconstruction or engineered services',
        walk_camera_eye_height_m=1.65)
