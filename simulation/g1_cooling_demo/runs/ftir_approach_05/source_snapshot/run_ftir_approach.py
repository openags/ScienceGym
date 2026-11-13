"""Execute an aisle approach and FTIR window operation on one physics clock."""
import argparse

from run_ftir_press import run


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--out', required=True)
    p.add_argument('--duration', type=float, default=180.)
    p.add_argument('--initial-xy', nargs=2, type=float, default=[4.95, -5.20])
    p.add_argument('--station-xy', nargs=2, type=float, default=[5.95, -5.20])
    p.add_argument('--prior')
    args = p.parse_args()
    result = run(args.out, args.duration, operation='slider', initial_xy=args.station_xy,
                 slider_prior=args.prior, observe_slider_outcome=True, approach_from=args.initial_xy)
    if result['status'] == 'failed':
        raise SystemExit(1)
