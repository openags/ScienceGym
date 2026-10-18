"""Rebuild all authored task projections in dependency order (no mesh rendering)."""
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
if __name__=='__main__':
    for script in ['authoring.py','assemble_package.py','planner.py','selected_reconstruction.py','selected_solar_path.py','refresh_review.py']:
        subprocess.run([sys.executable,str(HERE/script)],check=True)
