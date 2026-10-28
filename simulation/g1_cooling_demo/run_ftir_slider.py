"""Run an isolated G1 observation, window push and return attempt."""
import argparse
from run_ftir_press import run

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True)
    p.add_argument('--duration',type=float,default=140.)
    p.add_argument('--initial-xy',nargs=2,type=float,default=None)
    p.add_argument('--prior',help='Public object-local hand-affordance JSON; copied and pinned in the isolated bundle')
    p.add_argument('--observe-outcome',action='store_true',help='Turn back to the instrument and require fresh RGB-D confirmation before completion')
    p.add_argument('--timestep',type=float,choices=[.001,.002],default=.002);a=p.parse_args()
    if run(a.out,a.duration,a.timestep,operation='slider',initial_xy=a.initial_xy,slider_prior=a.prior,observe_slider_outcome=a.observe_outcome)['status']=='failed':raise SystemExit(1)
