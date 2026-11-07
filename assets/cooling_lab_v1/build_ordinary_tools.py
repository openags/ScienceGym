"""Ordinary catalog tools, selected for review rather than robot-only fixtures."""
import json
import numpy as np
import trimesh
from PIL import Image,ImageDraw,ImageFont
from trimesh.visual.material import PBRMaterial
from geometry_tools import Geometry,HERE,ROOT,sha,write_json

STEEL=[187,195,204];DARK=[38,41,46]

def plate(g,name,outline,thickness,z,color):
    # Earcut is unnecessary for these convex jaw outlines.
    n=len(outline);vertices=[[x,y,zz] for zz in [z,z+thickness] for x,y in outline]
    faces=[]
    for i in range(1,n-1):faces.extend([[0,i+1,i],[n,n+i,n+i+1]])
    for i in range(n):j=(i+1)%n;faces.extend([[i,j,n+j],[i,n+j,n+i]])
    mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=True);mesh.fix_normals()
    return g.add(name,mesh,color,role='tool_part',metal=.85)

def caliper():
    g=Geometry()
    g.box('beam',[.229,.016,.0035],[.1145,0,.00175],STEEL,metal=.85)
    plate(g,'fixed_outer_jaw',[(0,-.008),(.010,-.008),(.010,-.048),(.006,-.048),(0,-.020)],.0035,0,STEEL)
    plate(g,'fixed_inner_jaw',[(0,.008),(.004,.029),(.008,.024),(.008,.008)],.0035,0,STEEL)
    # Rest state 20 mm jaw gap; inspection slider adds up to 130 mm.
    plate(g,'moving_outer_jaw',[(.030,-.008),(.042,-.008),(.036,-.043),(.030,-.048)],.004,0,STEEL)
    plate(g,'moving_inner_jaw',[(.030,.008),(.030,.029),(.036,.024),(.039,.008)],.004,0,STEEL)
    g.box('slider_back',[.048,.022,.001],[.054,0,.0005],STEEL,metal=.85)
    for suffix,y in [('upper',.010),('lower',-.010)]:g.box('slider_'+suffix,[.048,.004,.006],[.054,y,.003],STEEL,metal=.85)
    g.box('vernier_face',[.048,.008,.001],[.054,-.006,.005],STEEL,metal=.85)
    g.cylinder('lock_screw',.003,.005,[.059,.010,.0085],DARK,metal=.5)
    g.cylinder('thumb_grip',.005,.004,[.066,-.015,.003],STEEL,metal=.85)
    g.box('depth_rod',[.198,.002,.001],[.148,.0,-.0005],STEEL,metal=.85)
    for i in range(151):
        length=.0035 if i%10==0 else .0025 if i%5==0 else .0014
        g.box('main_tick_'+str(i),[.00009,length,.00004],[.010+i*.001,-.0035+length/2,.00353],DARK)
    for i in range(21):g.box('vernier_tick_'+str(i),[.00008,.0017,.00004],[.030+i*.00095,-.0065,.00553],DARK)
    # Original metric engraving; no third-party photograph or logo texture.
    picture=Image.new('RGBA',(2048,128),(0,0,0,0));draw=ImageDraw.Draw(picture)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',55)
    for i in range(16):draw.text((30+i*130,64),str(i*10),font=font,fill=(24,24,24,255),anchor='mm')
    m=trimesh.Trimesh(vertices=[[.008,0,.00357],[.162,0,.00357],[.162,.006,.00357],[.008,.006,.00357]],faces=[[0,1,2],[0,2,3]],process=False)
    g.add('metric_numerals',m,DARK,role='original_engraving')
    m.visual=trimesh.visual.TextureVisuals(uv=[[0,0],[1,0],[1,1],[0,1]],material=PBRMaterial(baseColorTexture=picture,alphaMode='BLEND',roughnessFactor=.65,metallicFactor=0))
    out=g.export('mitutoyo_530_104')
    out['moving_parts']=[p['id'] for p in g.parts if p['id'].startswith(('moving_','slider_','vernier_')) or p['id'] in ['lock_screw','thumb_grip','depth_rod']]
    return out

def driver():
    from build_precision_driver_repair import driver as repaired_driver
    return repaired_driver('ph00').export('wiha_26100')

def rounded_ring(width,depth,r,z):
    points=[]
    for sx,sy,angle in [(1,1,0),(-1,1,90),(-1,-1,180),(1,-1,270)]:
        for a in np.radians(np.linspace(angle,angle+90,13)):
            points.append([sx*(width/2-r)+r*np.cos(a),sy*(depth/2-r)+r*np.sin(a),z])
    return points

def tray():
    g=Geometry();loops=[rounded_ring(.278,.178,.018,0),rounded_ring(.300,.200,.022,.050),
                        rounded_ring(.2976,.1976,.0208,.050),rounded_ring(.2756,.1756,.0168,.0012)]
    vertices=np.concatenate(loops);n=len(loops[0]);faces=[]
    for a,b in [(0,1),(1,2),(2,3)]:
        for i in range(n):j=(i+1)%n;faces.extend([[a*n+i,a*n+j,b*n+j],[a*n+i,b*n+j,b*n+i]])
    for i in range(1,n-1):faces.extend([[0,i+1,i],[3*n,3*n+i,3*n+i+1]])
    mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=True);mesh.fix_normals();g.add('formed_tray',mesh,STEEL,role='ordinary_catalog_tray',metal=.9)
    return g.export('buerkle_4208_0022')

def build():
    sources=json.loads((HERE/'ordinary_tools_sources.json').read_text())
    records=[]
    for key,fn in [('mitutoyo_530_104',caliper),('wiha_26100',driver),('buerkle_4208_0022',tray)]:
        records.append(dict(id=key,geometry=fn(),identity=sources['items'][key]['identity'],
                            appearance_accepted=False,interaction_qualified=False))
    write_json(HERE/'ordinary_tools.json',dict(schema_version=1,status='catalog_reconstructions_pending_review',
      source_ledger_sha256=sha(HERE/'ordinary_tools_sources.json'),builder_sha256=sha(__file__),items=records,
      source_artifacts=[dict(path=str((HERE/name).relative_to(ROOT)),sha256=sha(HERE/name)) for name in ['build_precision_driver_repair.py','build_fastener_tools.py','build_apparatus_mounting.py','geometry_tools.py']],
      scope='Ordinary tool candidates; one driver is not a complete fastener kit, and a tray does not prove fragile-film or heavy-payload handling'))
    print(json.dumps({'ordinary_tool_types':len(records)}))

if __name__=='__main__':build()
