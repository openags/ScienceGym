"""Colorize the recorded native head depth stream; values stay in meters."""
import argparse
from pathlib import Path
import numpy as np
import imageio.v2 as imageio
from PIL import Image,ImageDraw

def render(folder):
 folder=Path(folder);data=np.load(folder/'head_depth.npz');writer=imageio.get_writer(folder/'head_depth.mp4',fps=10,codec='libx264',quality=8,macro_block_size=4)
 for t,depth in zip(data['time'],data['depth']):
  # A fixed meter scale for every frame, never per-frame normalization.
  v=np.clip((depth-.2)/1.8,0,1);rgb=np.stack([255*(1-v),210*np.sin(np.pi*v),255*v],axis=-1).astype(np.uint8)
  rgb[~np.isfinite(depth)|(depth>2)]=[12,23,30]
  im=Image.fromarray(rgb).resize((640,360));draw=ImageDraw.Draw(im);draw.rectangle([0,0,640,24],fill='#10262d');draw.text((10,5),f'Native head depth | {t:.1f}s | red 0.2m - blue 2.0m',fill='white');writer.append_data(np.asarray(im))
 writer.close();print('Recorded depth video rendered')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('folder');a=p.parse_args();render(a.folder)
