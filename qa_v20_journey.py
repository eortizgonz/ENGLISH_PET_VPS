from pathlib import Path
root=Path(__file__).parent
js=(root/'v20_full_journey.js').read_text()
html=(root/'index.html').read_text()
sw=(root/'sw.js').read_text()
css=(root/'styles.css').read_text()
checks={
'V20 loaded':'v20_full_journey.js' in html,
'PWA V20':any(f'petquest-v{i}-shell' in sw for i in range(20,40)) and "'./v20_full_journey.js'" in sw,
'Four skills':all(x in js for x in ["reading","listening","writing","speaking"]),
'Daily planner':'function buildPlan()' in js and 'rankSkills()' in js,
'Balanced route':'priority' in js and 'Producción activa' in js,
'Five minute route':'target<=5' in js,
'Eight minute route':'target<=8' in js,
'Ten minute route':'target<=10' in js,
'Fifteen minute route':"mkStep('review',3" in js,
'Kid route':'Tu ruta completa de hoy' in js and 'Empezar mi ruta' in js,
'Adult insight':'Orquestación diaria de 4 habilidades' in js,
'User control':'data-v20-next' in js and 'data-v20-pause' in js,
'Learning modes forced':"V19.mode='learn'" in js and "V18.mode='learn'" in js and "V17.mode='conversation'" in js,
'V15 conflict disabled':"V15.active=false" in js,
'Journey summary':'lastJourney' in js and 'journeysCompleted' in js,
'Resume same route':'resumeJourney' in js and 'data-v20-resume' in js and 'paused' in js,
'One primary child session':'v20-superseded' in js and '.v20-superseded' in css,
'Why this route':'¿Por qué elegiste esta ruta, Milo?' in js,
'Responsive CSS':'.v20-active-bar' in css and '@media(max-width:820px)' in css,
'No diagnosis wording':'diagnost' not in js.lower(),
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if failed: raise SystemExit('FAILED: '+', '.join(failed))
print(f'PET Quest V20 Journey QA: PASS — {len(checks)}/{len(checks)}')
