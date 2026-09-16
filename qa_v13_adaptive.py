from pathlib import Path
base=Path(__file__).resolve().parent
js=(base/'v13_adaptive.js').read_text(encoding='utf-8')
idx=(base/'index.html').read_text(encoding='utf-8')
sw=(base/'sw.js').read_text(encoding='utf-8')
checks={
'adaptive signal engine':'function v13Signal' in js,
'challenge adaptation':"id:'challenge'" in js,
'support adaptation':"id:'support'" in js,
'rush signal':"id:'rush'" in js and 'responseMs' in js,
'repeated focus': 'v13RepeatedFocus' in js,
'response timing': 'responseMs' in js,
'non-diagnostic wording':'no son diagnósticos emocionales' in js,
'kid coach':'v13Practice' in js,
'adult insight':'v13Adult' in js,
'next mission adaptation':'v13Apply' in js,
'V13 loaded':'v13_adaptive.js' in idx,
'V13 cached':'v13_adaptive.js' in sw,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if failed: raise SystemExit('V13 QA failed: '+', '.join(failed))
print('PET Quest V13 Adaptive QA: PASS')
