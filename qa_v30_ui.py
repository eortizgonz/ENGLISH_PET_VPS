from pathlib import Path
r=Path(__file__).resolve().parent
js=(r/'v30_school_impact.js').read_text();idx=(r/'index.html').read_text();sw=(r/'sw.js').read_text();api=(r/'api_server.py').read_text()
checks={'loaded':'v30_school_impact.js' in idx,'impact endpoint':"/api/school-impact'" in api,'snapshot endpoint':'/api/school-impact/snapshot' in api,'csv':'/api/school-impact.csv' in api,'growth':'Crecimiento vs. último corte' in js,'risk':'Riesgo' in js,'interventions':'Efectividad de intervenciones' in js,'priorities':'Prioridades ejecutivas' in js,'PWA':'petquest-v' in sw and './v30_school_impact.js' in sw,'responsive':'@media(max-width:850px)' in js}
for k,v in checks.items():print(('PASS' if v else 'FAIL'),k)
assert all(checks.values());print('PET Quest V30 UI QA: PASS — 10/10')
