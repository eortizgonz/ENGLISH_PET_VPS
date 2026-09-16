#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
EXPECTED=['ACADEMIC','DATABASE','SECURITY','MULTI_TENANT','PRIVACY','EMAIL','AUDIO','BACKUP_RESTORE','DEVICE_MATRIX','LOAD_TEST','PENTEST','PILOT']
p=subprocess.run([sys.executable,str(ROOT/'PETQUEST_RELEASE_GATE.py')],cwd=ROOT,capture_output=True,text=True,timeout=180)
try:d=json.loads(p.stdout[p.stdout.find('{'):])
except Exception as e: raise SystemExit('invalid gate json: '+repr(e)+'\n'+p.stdout+'\n'+p.stderr)
assert d['criteria']==EXPECTED,d['criteria']
assert list(d['checks'].keys())==EXPECTED,d['checks'].keys()
assert d['COMMERCIAL_RELEASE']=='BLOCKED' if d['blocked'] else d['COMMERCIAL_RELEASE']=='APPROVED'
assert d['critical_issues']>=0 and d['high_issues']>=0
assert (ROOT/'release_gate_snapshot.json').exists()
print('PET Quest V46 Unified Release Gate QA: PASS',json.dumps({'blocked':d['blocked'],'critical':d['critical_issues'],'high':d['high_issues']}))
