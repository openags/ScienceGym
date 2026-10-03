from pathlib import Path
import json
from contract import load_package,validate_package,validate_export
root=Path(__file__).resolve().parents[1]
p=load_package(root)
print(json.dumps(validate_package(p),indent=2))
if 'EXPORT_ALLOWLIST.json' in p:validate_export(root,p);print('Exact export boundary and hashes passed')
print('Static design and synthetic bookkeeping only; no physical validation')
