"""Readable captions for original static renders; no invented measurements."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,sys,os
OUT=Path(__file__).resolve().parents[1]
FONT=os.environ.get('THERMO_FONT','DejaVuSans.ttf');BOLD=os.environ.get('THERMO_BOLD_FONT','DejaVuSans-Bold.ttf')
BG='#0d1d2b';FG='#eff7f6';DIM='#b1c8cd';CYAN='#52dfd5';ORANGE='#ff8752'
def font(n,b=False):return ImageFont.truetype(BOLD if b else FONT,n)
def wrap(d,xy,text,width,size=18,color=FG,bold=False,gap=5):
 x,y=xy;f=font(size,bold)
 for para in text.split('\n'):
  line=''
  for word in para.split():
   t=(line+' '+word).strip()
   if d.textlength(t,font=f)>width and line:d.text((x,y),line,font=f,fill=color);y+=size+gap;line=word
   else:line=t
  d.text((x,y),line,font=f,fill=color);y+=size+gap
 return y
def tag(d,a,off):
 x,y=a['xy'];y+=100
 if not 10<x<1230 or not 110<y<885:return
 t={'robot':'MOBILE G1 / AUTHORED POSE','target':'HAND / OBJECT TARGET','object':'CURRENT LINEAGE STATE'}[a['kind']];c=ORANGE if a['kind']=='target' else CYAN;f=font(15,True);w=d.textlength(t,font=f)+20;tx=max(12,min(1228-w,x+off[0]));ty=max(112,min(863,y+off[1]));d.line((x,y,tx+10,ty+12),fill=c,width=2);d.ellipse((x-4,y-4,x+4,y+4),fill=c);d.rounded_rectangle((tx,ty,tx+w,ty+29),5,fill=BG,outline=c);d.text((tx+10,ty+5),t,font=f,fill=c)
def base(raw,title,kicker):
 im=Image.new('RGB',(1660,1000),BG);im.paste(Image.open(raw).convert('RGB').resize((1240,800)),(0,100));d=ImageDraw.Draw(im)
 d.text((28,17),kicker,font=font(16,True),fill=CYAN);d.text((26,45),title,font=font(28,True),fill=FG);d.line((1240,100,1240,900),fill='#385b68',width=2)
 d.text((27,919),'STATIC / KINEMATIC STORYBOARD  |  No physics, process backend, robot execution or contact validation',font=font(19,True),fill=DIM)
 d.text((27,951),'P: 3.3 x 3.3 x 6.6 mm  |  N: 2.9 x 2.9 x 6.6 mm  |  Leg/module visuals: 20x linear display scale; N cut direction unknown',font=font(16),fill=DIM)
 d.text((27,979),'Apparatus / interfaces / poses: authored proxies. Unitree G1 visuals: BSD-3-Clause. Orange = active target. No scientific readings generated.',font=font(13),fill=DIM)
 return im,d
m=json.loads((OUT/'frame_manifest.json').read_text())
if (OUT/'raw/overview.png').exists():
 im,d=base(OUT/'raw/overview.png','Thermoelectric PAIRED_TWO: one evolving, four-leg module','RAW P / N  >  SEPARATE PROCESSING  >  FOUR LEGS  >  ONE MODULE  >  FOUR BOUNDARIES  >  ARCHIVE')
 y=125
 for h,t in [('EPISODE START','Sealed raw stock and idle equipment. No powder, billets, legs or finished modules exist yet.'),('ONE BOUNDED ROUTE','45 illustrated keyframes map 66 reference-operation occurrences. Individual P1, N1, P2 and N2 placements are shown.'),('LABORATORY','13 active station roles in the reused 16-station lab. B melt, segmented joining and contact scan stay inactive.'),('HONEST SCOPE','Four thermal-boundary chapters share one module. Current-grid repeats are aggregated; values and counts remain unknown.')]:
  y=wrap(d,(1265,y),h,365,17,CYAN,True)+9;y=wrap(d,(1265,y),t,365,20)+28
 im.save(OUT/'overview.jpg',quality=93)
for f in m['frames']:
 raw=OUT/'raw'/f"{f['index']:02d}_{f['id']}.png"
 if not raw.exists():continue
 im,d=base(raw,f['title'],f"KEYFRAME {f['index']:02d} / 45  |  PAIRED_TWO  |  {f['station'].replace('WS_','')}  |  {f['id']}")
 for a in f.get('projected_annotations',[]):tag(d,a,(-285,-130) if a['kind']=='robot' else (100,-75) if a['kind']=='target' else (120,80))
 y=121;detail=OUT/f.get('detail_image','missing')
 if detail.is_file():
  d.text((1265,y),'SAME OBJECT / INSPECTION VIEW',font=font(14,True),fill=CYAN);im.paste(Image.open(detail).convert('RGB').resize((360,270)),(1265,149));y=433
  for a in f.get('detail_labels',[]):
   x=1265+a['xy'][0]*.75;yy=149+a['xy'][1]*.75
   if 1275<x<1615 and 160<yy<408:
    col='#ffbb8b' if a['material']=='P' else '#72d7ff';d.rounded_rectangle((x-15,yy-13,x+18,yy+13),4,fill=BG,outline=col);d.text((x-10,yy-9),a['label'],font=font(14,True),fill=col)
  y=wrap(d,(1265,y),'Occluders hidden only in this detail view',365,12,DIM)+13
 else:
  y=wrap(d,(1265,y),'ACTIVE OBJECTS',365,16,CYAN,True)+10;y=wrap(d,(1265,y),f['objects'],365,22,FG,True)+28
 if f['visual_kind']=='boundary':
  d.rounded_rectangle((1265,y,1629,y+103),8,fill='#123d4b',outline=CYAN);d.text((1282,y+12),f"Th {f['source_target_Th_K']} K",font=font(32,True),fill=FG);d.text((1282,y+55),'Tc 293 K / source targets only',font=font(17),fill=CYAN);y+=128
  y=wrap(d,(1265,y),'CURRENT -> ACQUIRE -> KEEP HISTORY',365,17,ORANGE,True)+13;y=wrap(d,(1265,y),'Repeat over an unspecified current grid. No numeric values or point-count claim.',365,20)+25
 for h,k in [('BEFORE','sample_state_before'),('INTENDED AFTER','sample_state_after')]:
  y=wrap(d,(1265,y),h,365,15,CYAN,True)+6;y=wrap(d,(1265,y),f[k],365,18)+18
 if detail.is_file():y=wrap(d,(1265,y),'HANDLED: '+f['objects'],365,16,ORANGE)+16
 material='P = MgAgSb + 0.625 wt% C18H36O2' if f['phase']=='P' else 'N = Mg3.2In0.02Sb0.595Bi1.4Te0.005' if f['phase']=='N' else 'One module: P1 + N1 + P2 + N2'
 y=wrap(d,(1265,y),material,365,15,DIM)
 if f['visual_kind'] in ['boundary','data','powerdown']:
  y+=10;wrap(d,(1265,y),'Values, calibration and achieved conditions: UNKNOWN',365,16,ORANGE,True)
 im.save(OUT/f['image'],quality=91)
print('Annotated',len(list((OUT/'frames').glob('*.jpg'))),'frames')
