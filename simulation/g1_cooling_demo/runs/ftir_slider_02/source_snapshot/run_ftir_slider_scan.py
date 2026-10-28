"""Run the sensor-isolated G1 observation/torso preparation attempt."""
import argparse
from run_ftir_press import run

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True)
    p.add_argument('--duration',type=float,default=16.)
    p.add_argument('--initial-xy',nargs=2,type=float,default=None,
                   help='Authored standing XY; no walking credit')
    p.add_argument('--timestep',type=float,choices=[.001,.002],default=.002);a=p.parse_args()
    if run(a.out,a.duration,a.timestep,operation='slider_scan',initial_xy=a.initial_xy)['status']=='failed':raise SystemExit(1)
