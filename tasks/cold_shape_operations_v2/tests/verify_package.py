import json,pathlib
from contract import load,validate_package
root=pathlib.Path(__file__).resolve().parents[1]
print(json.dumps({'status':'PASS','scope':'static contracts only',**validate_package(load(root))},indent=2))
