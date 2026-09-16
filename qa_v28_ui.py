from pathlib import Path
r=Path(__file__).resolve().parent
js=(r/'v28_intervention_engine.js').read_text(); idx=(r/'index.html').read_text(); sw=(r/'sw.js').read_text(); api=(r/'api_server.py').read_text()
checks={
'V28 script loaded':'v28_intervention_engine.js' in idx,
'Intervention endpoint':"/api/intervention-plan" in api,
'Prioritized interventions':'Intervenciones priorizadas' in js,
'Advance candidates':'Pueden avanzar' in js,
'Follow up':'Requieren seguimiento' in js,
'Exit criteria':'Criterio de salida' in js,
'Create intervention':'Crear intervención' in js,
'Collective preserves individual':'complementa la ruta individual' in js,
'PWA V28':'v28_intervention_engine.js' in sw and 'petquest-v' in sw and './v28_intervention_engine.js' in sw,
'Responsive UI':'@media(max-width:800px)' in js,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
assert all(checks.values())
print(f'PET Quest V28 UI QA: PASS — {len(checks)}/{len(checks)}')
