from pathlib import Path
import re
root=Path(__file__).resolve().parent
s=(root/'v46_18_audio_bank.js').read_text()
checks=[]
def ck(name,cond):
    checks.append((name,bool(cond)))
ck('LEARN MODE visible','♾️ LEARN MODE' in s)
ck('REAL EXAM MODE visible','🎓 REAL EXAM MODE' in s)
ck('learn mode default',"mode:'learn'" in s)
ck('separate learn counter','learnPlays:{}' in s and 'S.learnPlays' in s)
ck('separate exam counter','examPlays:{}' in s and 'S.examPlays' in s)
ck('new exam session resets plays','S.examPlays={}' in s and 'S.examSession+=1' in s)
ck('exam exactly two guard',"S.mode==='exam'&&n>=2" in s)
ck('exam fixed 1x',"a.playbackRate=S.mode==='exam'?1:S.speed" in s)
ck('learn speeds .75',"[.75,.85,1,1.10]" in s)
ck('learn unlimited display',"`${n} · ♾`" in s)
ck('exam counter display',"`${n} / 2`" in s)
ck('exam transcript hidden',"S.mode==='exam'?'style=\"display:none\"':''" in s)
ck('learn does not consume exam plays',"const map=S.mode==='exam'?S.examPlays:S.learnPlays" in s)
ck('tracking reports active counter',"S.mode==='exam'?S.examPlays:S.learnPlays" in s)
ck('user scoped storage','petquest_v4619_audio_bank_u_' in s)
ck('version 46.19',"version:'46.19'" in s)
for n,ok in checks: print(('PASS' if ok else 'FAIL'),n)
print(f'LEARN/REAL EXAM V46.19: {sum(x[1] for x in checks)}/{len(checks)} PASS')
raise SystemExit(0 if all(x[1] for x in checks) else 1)
