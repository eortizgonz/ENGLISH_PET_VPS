#!/usr/bin/env python3
import argparse, sqlite3, tempfile, json
from pathlib import Path

def counts(db):
    c=sqlite3.connect(db)
    names=[r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    out={}
    for t in names:
        try: out[t]=c.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        except Exception: out[t]=None
    c.close(); return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source',default='petquest.db'); args=ap.parse_args()
    src=Path(args.source)
    if not src.exists(): raise SystemExit('BLOCKED: source database missing')
    with tempfile.TemporaryDirectory() as td:
        restored=Path(td)/'restored.db'
        a=sqlite3.connect(src); b=sqlite3.connect(restored); a.backup(b); a.close(); b.close()
        before,after=counts(src),counts(restored)
        ok=before==after
        print(json.dumps({'backup_restore_pass':ok,'source':str(src),'table_counts':after},indent=2))
        raise SystemExit(0 if ok else 2)
if __name__=='__main__': main()
