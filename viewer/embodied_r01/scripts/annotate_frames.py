"""Readable English annotation and same-scene detail crops for authored Blender renders."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json,textwrap,sys,os
OUT=Path(os.environ.get('SCIENCEGYM_RENDER_OUT', str(Path(__file__).resolve().parents[1])))
FONT=os.environ.get('SCIENCEGYM_FONT','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf');BOLD=os.environ.get('SCIENCEGYM_BOLD_FONT','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
def font(n,b=False):return ImageFont.truetype(BOLD if b else FONT,n)
BG='#101e2c';FG='#eef6f4';DIM='#b9c9cd';CYAN='#53ded7';ORANGE='#ff773d'
def writewrap(d,xy,text,width,size=18,color=FG,bold=False,spacing=5):
 x,y=xy; f=font(size,bold);lines=[]
 for para in text.split('\n'):
  words=para.split();line=''
  for word in words:
   test=line+' '+word if line else word
   if d.textlength(test,font=f)>width and line:lines.append(line);line=word
   else:line=test
  lines.append(line)
 for line in lines:d.text((x,y),line,font=f,fill=color);y+=size+spacing
 return y

def tag(d,xy,text,kind='target',offset=(30,-30)):
 x,y=xy;x=max(15,min(1225,x));y=max(115,min(878,y+100));c=ORANGE if kind=='target' else CYAN if kind in ['robot','object'] else '#c0d9e3';size=15 if kind=='station' else 17;f=font(size,True);tw=min(365,d.textlength(text,font=f)+18);tx=max(12,min(1230-tw,x+offset[0]));ty=max(106,min(860,y+offset[1]));d.line((x,y,tx+7,ty+12),fill=c,width=2);d.ellipse((x-5,y-5,x+5,y+5),fill=c);d.rounded_rectangle((tx,ty,tx+tw,ty+29),radius=5,fill=BG,outline=c,width=1);d.text((tx+8,ty+4),text,font=f,fill=c)

def canvas(raw):
 im=Image.new('RGB',(1660,1000),BG);im.paste(Image.open(raw).convert('RGB'),(0,100));return im,ImageDraw.Draw(im)

def common(im,d,title,kicker):
 d.text((28,16),kicker,font=font(16,True),fill=CYAN);d.text((26,43),title,font=font(29,True),fill=FG)
 d.line((1240,101,1240,900),fill='#446071',width=2)
 writewrap(d,(27,925),'AUTHORED VISUAL TASK DEMONSTRATION  |  Blender CPU static poses  |  No physics, robot execution or contact validation',1600,18,DIM)
 d.text((27,961),'Apparatus: existing authored proxies, make/model unknown. Robot: licensed Unitree G1 visual meshes; authored pose.',font=font(14),fill=DIM)

def main():
 m=json.loads((OUT/'frame_manifest.json').read_text());raw=OUT/'raw/overview.png'
 if raw.exists():
  im,d=canvas(raw);common(im,d,'Chiral R01: one robot, one evolving specimen, the entire lab route','26 REFERENCE OPERATIONS  /  8 WORK ZONES  /  2 AUTHORED TASK CYCLES')
  off=[(-160,-55),(50,-50),(-100,-65),(40,-50),(-100,25),(20,-45),(-130,20),(40,-25)]
  anns=m.get('overview_annotations',[])
  for i,a in enumerate(anns):tag(d,a['xy'],a['label'],a['kind'],(-135,-90) if i==0 else (40,45) if i==1 else off[(i-2)%8])
  y=124;y=writewrap(d,(1265,y),'EPISODE START',355,19,CYAN,True);y+=12
  y=writewrap(d,(1265,y),'R01 raw-stock cassette and empty build tray only. No finished array exists yet.',355,21,FG);y+=22
  y=writewrap(d,(1265,y),'FOLLOW THE BLUE ROUTE',355,17,CYAN,True);y+=10
  y=writewrap(d,(1265,y),'1  Raw stock\n2  Fabrication handoff\n3  Release and sort\n4  18-half-unit assembly\n5  Mass + envelope\n6  Compression + observation\n    Repeat on the same object\n7  Used-specimen archive\n8  Cleanup and reset',355,18,FG,False,10)
  y+=22;writewrap(d,(1265,y),'All downstream sample copies from the original stage-prop scene are hidden. Each step exposes only its current lineage state.',355,17,DIM)
  im.save(OUT/'overview.jpg',quality=93)
 for f in m['frames']:
  raw=OUT/'raw'/f"{f['index']:02d}_{f['id']}.png"
  if not raw.exists():continue
  im,d=canvas(raw);common(im,d,f['title'],f"STEP {f['index']:02d} / 26  |  {f['id']}  |  {f['station'].replace('WS_','')}")
  # Labels are pinned to rendered object/world coordinates, not guessed screen positions.
  for a in f.get('projected_annotations',[]):
   label='MOBILE G1 / AUTHORED POSE' if a['kind']=='robot' else 'ACTIVE TARGET' if a['kind']=='target' else 'R01 CURRENT OBJECT STATE'
   tag(d,a['xy'],label,a['kind'],(-330,-130) if a['kind']=='robot' else (155,-65) if a['kind']=='target' else (160,85))
  y=119; detail=OUT/f.get('detail_image','missing')
  if detail.is_file():
   det=Image.open(detail).convert('RGB');det.thumbnail((360,230));im.paste(det,(1266,146));d.text((1265,117),'SAME OBJECT / INSPECTION VIEW',font=font(14,True),fill=CYAN);y=391
  else:
   y=writewrap(d,(1265,y),'OBJECT IN THIS STEP',365,17,CYAN,True);y+=13
   y=writewrap(d,(1265,y),f['objects'],365,23,FG,True);y+=25
  y=writewrap(d,(1265,y),'BEFORE',360,15,CYAN,True);y+=5;y=writewrap(d,(1265,y),f['sample_state_before'],360,19,FG);y+=20
  y=writewrap(d,(1265,y),'AFTER / INTENDED STATE',360,15,CYAN,True);y+=5;y=writewrap(d,(1265,y),f['sample_state_after'],360,19,FG);y+=22
  if detail.is_file():
   y=writewrap(d,(1265,y),'MANIPULATED / CARRIED',360,15,ORANGE,True);y+=5;y=writewrap(d,(1265,y),f['objects'],360,18,FG);y+=18
  note='Single lineage: obj.R01.001' if f['index']>=9 else 'Lineage: raw stock -> units R01.001-018'
  y=writewrap(d,(1265,y),note,360,16,DIM)
  if f['id'] in ['LOAD','UNLOAD','OBS_RESIDUAL','RELOAD']:
   y+=15;writewrap(d,(1265,y),'Shape is an authored illustration. No measured force, predicted twist, or perfect recovery is implied.',360,15,ORANGE)
  im.save(OUT/f['image'],quality=91)
 print('Annotated',len(list((OUT/'frames').glob('*.jpg'))),'frames')
if __name__=='__main__':main()
