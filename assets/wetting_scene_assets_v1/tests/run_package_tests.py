"""Execute package tests and write a compact reproducible public result receipt."""
from pathlib import Path
import unittest,json,sys,platform,hashlib
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
suite=unittest.defaultTestLoader.discover(str(P/'tests'),pattern='test_*.py')
r=unittest.TextTestRunner(verbosity=2).run(suite)
receipt={'status':'PASS' if r.wasSuccessful() else 'FAIL','tests_run':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skipped':len(r.skipped),'python_version':platform.python_version(),'scope':['all eleven preview states passive','safe-close review reachable','all forbidden actions blocked','unknown fields/invalid labels/replays of review transitions blocked','read-only physical flags','exact operation bindings and all-anchor use','actual render hashes and geometry check receipts'],'physical_device_execution':False,'scientific_verification':False,'tested_code_sha256':{n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in ['semantic_controls.py','tests/test_semantic_controls.py','tests/test_package.py']}}
(P/'review/guard_validation.json').write_text(json.dumps(receipt,indent=2)+'\n')
sys.exit(0 if r.wasSuccessful() else 1)
