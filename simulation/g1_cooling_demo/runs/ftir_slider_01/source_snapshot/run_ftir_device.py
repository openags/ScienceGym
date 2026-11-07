"""Build the complete lab's passive FTIR candidate and run device diagnostics."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from world import build, HERE
from check_ftir_device import inspect


def run(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()):raise ValueError('Use a new empty device run directory')
    snapshot=out/'source_snapshot';snapshot.mkdir()
    for name in ['world.py','laboratory.py','ftir_device.py','convex_cells.py','robot_state.py',
                 'requirements.txt','check_ftir_device.py','run_ftir_device.py']:
        shutil.copyfile(HERE/name,snapshot/name)
    (out/'build_sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in snapshot.iterdir()},indent=2)+'\n')
    build(out,tray=False,laboratory=True,articulated_ftir=True)
    return inspect(out)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args()
    if not run(args.out)['passed']:raise SystemExit(1)
