from pathlib import Path
r=Path(__file__).resolve().parent
js=(r/'v27_classroom_intelligence.js').read_text(); idx=(r/'index.html').read_text(); sw=(r/'sw.js').read_text(); api=(r/'api_server.py').read_text()
checks={
'V27 script loaded':'v27_classroom_intelligence.js' in idx,
'Compare classes':'Comparación entre clases' in js,
'Temporary groups':'Grupo temporal sugerido' in js,
'Weekly plan':'Plan semanal colectivo' in js,
'Individual path preserved':'no cambia la matrícula ni reemplaza la prioridad personal' in js,
'School intelligence endpoint':"/api/school-intelligence" in api,
'Support groups endpoint':"/api/support-groups" in api,
'Weekly plan endpoint':"/api/weekly-class-plan" in api,
'PWA V27':any(f'petquest-v{i}-shell' in sw for i in range(27,40)) and './v27_classroom_intelligence.js' in sw,
'Responsive UI':'@media(max-width:900px)' in js,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
assert all(checks.values())
print(f'PET Quest V27 UI QA: PASS — {len(checks)}/{len(checks)}')
