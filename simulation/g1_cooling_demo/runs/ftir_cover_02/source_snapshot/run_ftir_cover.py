"""Run the sensor-isolated G1 cover-opening attempt in the complete laboratory."""
import argparse
from run_ftir_press import run

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True)
    p.add_argument('--duration',type=float,default=55)
    p.add_argument('--timestep',type=float,choices=[.001,.002],default=.002);a=p.parse_args()
    if run(a.out,a.duration,a.timestep,operation='cover')['status']=='failed':raise SystemExit(1)
