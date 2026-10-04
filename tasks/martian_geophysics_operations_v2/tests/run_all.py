"""One read-only entry point for static, author-test and exact-export checks."""
import json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
commands=[['verify_package.py'],['-m','unittest','discover','-s',str(HERE),'-p','test_*.py','-v'],['verify_export.py']]
results=[]
for command in commands:
 args=[sys.executable]+([str(HERE/command[0])] if len(command)==1 else command)
 result=subprocess.run(args,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},text=True,capture_output=True)
 print(result.stdout,end='');print(result.stderr,end='')
 results.append({'check':command[0],'exit_code':result.returncode})
print(json.dumps({'checks':results,'passed':all(r['exit_code']==0 for r in results),'physical_execution':False},indent=2))
raise SystemExit(not all(r['exit_code']==0 for r in results))
