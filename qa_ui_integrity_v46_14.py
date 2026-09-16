from pathlib import Path
import re, subprocess
ROOT=Path(__file__).resolve().parent
idx=(ROOT/'index.html').read_text()
alljs='\n'.join(p.read_text(errors='ignore') for p in ROOT.glob('*.js'))
checks=[]
def ck(n,c,d=''):
    checks.append((n,bool(c),d))
    if not c: print('FAIL',n,d)
# Every indexed script exists and parses.
for s in re.findall(r'<script\s+src=["\']([^"\'?]+)',idx):
    p=ROOT/s; ck('exists:'+s,p.exists())
    if p.exists():
        r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True); ck('syntax:'+s,r.returncode==0,r.stderr[-300:])
# Literal buttons must be represented in JS and new examiner controls have handlers.
for a in ['hear','start','stop','analyse','history','retry']:
    ck('speaking_button:'+a,f'data-v4614-{a}' in alljs and f"[data-v4614-{a}]" in alljs)
for field in ['v4614Transcript','v4614Playback','v4614Live','v4614Meter','v4614Result']:
    ck('speaking_field:'+field,field in alljs)
for metric in ['fluency','wpm','long_pauses','hesitations','restarts','grammar','vocabulary_range','discourse_markers','pronunciation_proxy','intelligibility','stress_variation','intonation_variation','response_length','interaction']:
    ck('metric:'+metric,metric in alljs)
ck('warning','no equivale a una calificación oficial Cambridge' in alljs)
ck('version','v46_14_speaking_ai_examiner.js?v=46.14' in idx)
print(f'PET Quest V46.14 UI Integrity: {sum(c for _,c,_ in checks)}/{len(checks)} PASS')
if not all(c for _,c,_ in checks): raise SystemExit(1)
