#!/usr/bin/env python3
import json, os, subprocess, sys, datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parent
EVIDENCE=ROOT/os.environ.get('PETQUEST_RELEASE_EVIDENCE_FILE','release_evidence.json')
MAX_EVIDENCE_AGE_DAYS=int(os.environ.get('PETQUEST_MAX_EVIDENCE_AGE_DAYS','120'))

REQUIRED=['ACADEMIC','DATABASE','SECURITY','MULTI_TENANT','PRIVACY','EMAIL','AUDIO','BACKUP_RESTORE','DEVICE_MATRIX','LOAD_TEST','PENTEST','PILOT']

def run(cmd,timeout=90):
    try:
        p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=timeout)
        return p.returncode==0,(p.stdout+p.stderr)[-3000:]
    except Exception as e:
        return False,str(e)

def fresh_pass(section, data):
    row=(data or {}).get(section,{})
    if str(row.get('status','')).upper()!='PASS': return False
    ds=str(row.get('evidence_date','')).strip()
    artifact=str(row.get('artifact','')).strip()
    if not ds or not artifact: return False
    try:
        d=datetime.date.fromisoformat(ds[:10])
        if (datetime.date.today()-d).days > MAX_EVIDENCE_AGE_DAYS: return False
    except Exception:return False
    ap=ROOT/artifact
    return ap.exists() and ap.is_file() and ap.stat().st_size>0

def load_evidence():
    if not EVIDENCE.exists(): return {}
    try:return json.loads(EVIDENCE.read_text())
    except Exception:return {}

def parse_runtime_gate():
    # Static/runtime truth only: PostgreSQL must be active in the production backend code path.
    api=(ROOT/'api_server.py').read_text(errors='ignore')
    prod=(ROOT/'production_fastapi.py').read_text(errors='ignore') if (ROOT/'production_fastapi.py').exists() else ''
    database=('DATABASE_ENGINE' in prod and 'postgres' in prod.lower() and 'psycopg' in prod.lower()) or ("DATABASE_ENGINE='postgres'" in api and 'psycopg' in api.lower())
    backend=(ROOT/'production_fastapi.py').exists() and 'FastAPI(' in prod
    return database,backend

def main():
    evidence=load_evidence()
    database,backend=parse_runtime_gate()
    academic=run([sys.executable,'qa_v41_academic.py'])[0] and run([sys.executable,'qa_v44_psychometrics.py'])[0]
    security=run([sys.executable,'qa_security_v46.py'])[0]
    multi=run([sys.executable,'tenant_isolation_check.py'])[0]
    privacy=run([sys.executable,'qa_v41_privacy.py'])[0]
    backup=run([sys.executable,'qa_backup_restore_v46.py'])[0]
    audio=run([sys.executable,'validate_studio_audio.py'])[0]
    email_configured=bool(os.environ.get('PETQUEST_SMTP_HOST','').strip() and os.environ.get('PETQUEST_SMTP_FROM','').strip())
    # Production backend is a mandatory subcontrol of DATABASE. If either is false, DATABASE remains blocked.
    checks={
      'ACADEMIC': academic and fresh_pass('academic_review', evidence),
      'DATABASE': database and backend,
      'SECURITY': security,
      'MULTI_TENANT': multi,
      'PRIVACY': privacy and fresh_pass('legal', evidence),
      'EMAIL': email_configured and fresh_pass('email', evidence),
      'AUDIO': audio,
      'BACKUP_RESTORE': backup and fresh_pass('backup_restore', evidence),
      'DEVICE_MATRIX': fresh_pass('device_matrix', evidence),
      'LOAD_TEST': fresh_pass('load_test', evidence),
      'PENTEST': fresh_pass('pentest', evidence),
      'PILOT': fresh_pass('pilot', evidence),
    }
    pent=evidence.get('pentest',{}) if isinstance(evidence,dict) else {}
    critical=int(pent.get('critical_issues', os.environ.get('PETQUEST_CRITICAL_ISSUES','0')) or 0)
    high=int(pent.get('high_issues', os.environ.get('PETQUEST_HIGH_ISSUES','0')) or 0)
    blocked=[k for k in REQUIRED if not checks.get(k,False)]
    approved=(not blocked and critical==0 and high==0)
    out={
      'version':'46.0',
      'criteria':REQUIRED,
      'checks':checks,
      'critical_issues':critical,
      'high_issues':high,
      'blocked':blocked,
      'internal_subcontrols':{'production_backend_fastapi':backend,'postgres_runtime':database},
      'COMMERCIAL_RELEASE':'APPROVED' if approved else 'BLOCKED'
    }
    (ROOT/'release_gate_snapshot.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(out,indent=2,ensure_ascii=False))
    return 0 if approved else 3
if __name__=='__main__': raise SystemExit(main())
