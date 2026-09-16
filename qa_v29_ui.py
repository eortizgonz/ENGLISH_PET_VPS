from pathlib import Path
r=Path(__file__).resolve().parent
js=(r/'v29_intervention_outcomes.js').read_text(); idx=(r/'index.html').read_text(); sw=(r/'sw.js').read_text(); api=(r/'api_server.py').read_text()
checks={
'V29 loaded':'v29_intervention_outcomes.js' in idx,
'outcomes endpoint':'/api/intervention-outcomes' in api,
'evaluate endpoint':'/api/interventions/evaluate' in api,
'effectiveness endpoint':'/api/intervention-effectiveness' in api,
'before after':'Antes' in js and 'Ahora' in js,
'decisions':'Cambiar estrategia' in js and 'Extender' in js and 'Cerrar' in js,
'PWA V29':'./v29_intervention_outcomes.js' in sw,
'responsive':'@media(max-width:850px)' in js,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
assert all(checks.values())
print(f'PET Quest V29 UI QA: PASS — {len(checks)}/{len(checks)}')
