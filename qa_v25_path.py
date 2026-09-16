from pathlib import Path
root=Path(__file__).parent
js=(root/'v25_personal_path.js').read_text()
idx=(root/'index.html').read_text()
sw=(root/'sw.js').read_text()
checks={
'V25 script loaded':'v25_personal_path.js' in idx,
'PWA V25 cache':any(f'petquest-v{i}-shell' in sw for i in range(25,40)) and 'v25_personal_path.js' in sw,
'Roadmap asset':'assets/roadmap.svg' in sw and (root/'assets/roadmap.svg').exists(),
'Four skills':all(x in js for x in ['reading','listening','writing','speaking']),
'Flexible preference':"preference:'mixed'" in js and 'preferencia flexible' in js.lower(),
'No fixed learning style':'no usa etiquetas fijas' in js.lower(),
'Visual preference':"['visual'" in js,
'Audio preference':"['audio'" in js,
'Practice preference':"['practice'" in js,
'Mixed preference':"['mixed'" in js,
'Future milestones':'Construir base' in js and 'Preparar examen' in js and 'Mantener dominio' in js,
'Castle PET':'Castillo PET' in js,
'Weakness priority':'principal oportunidad' in js,
'Strength visible':'fortaleza' in js.lower(),
'Weekly pace':'weeklyMinutes' in js and 'Meta semanal' in js,
'Evidence aware':'evidence' in js,
'Kid view':'Mi camino personal' in js,
'Adult view':'Personal Learning Path' in js,
'CSV export':'petquest_personal_learning_path.csv' in js,
'Responsive':'@media(max-width:760px)' in js,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
print(f"PET Quest V25 Path QA: {sum(checks.values())}/{len(checks)}", 'PASS' if all(checks.values()) else 'FAIL')
raise SystemExit(0 if all(checks.values()) else 1)
