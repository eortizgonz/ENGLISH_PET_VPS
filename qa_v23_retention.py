from pathlib import Path
root=Path(__file__).parent
js=(root/'v23_retention.js').read_text()
html=(root/'index.html').read_text()
sw=(root/'sw.js').read_text()
checks={
'V23 loaded':'v23_retention.js' in html,
'Healthy rhythm':'function healthyRhythm' in js,
'No streak punishment':'sin castigo por descansar' in js and 'No perdiste nada' in js,
'Friendly return':'Bienvenido de vuelta' in js and 'Qué bueno verte otra vez' in js,
'Weekly goal':'weeklyGoal' in js and 'Mi meta semanal' in js,
'Flexible goal 2-5':'Math.max(2,Math.min(5' in js,
'Visual calendar':'function calendarDays' in js and 'v23-calendar' in js,
'Chosen goals':'balanced' in js and 'confidence' in js and 'repair' in js and 'speak' in js,
'Retention signal':'function retentionSignal' in js,
'Non diagnostic':'no diagnóstica' in js,
'Rest allowed':'Hoy quiero descansar' in js and 'Descansar no borra progreso' in js,
'Short comeback':'Hacer 5 min' in js and 'dailyGoal=5' in js,
'Reward consistency':'rewardPoints' in js and '+10 semillas' in js,
'Adult view':'Motivación y retención saludable' in js,
'No backlog recovery':'sin recuperar tareas atrasadas' in js,
'V20 integration':'PETQUEST_V20' in js and 'resumeJourney' in js,
'Responsive':'@media(max-width:700px)' in js,
'Offline V23':any(f'petquest-v{i}-shell' in sw for i in range(23,40)) and "'./v23_retention.js'" in sw,
'Window API':'window.PETQUEST_V23' in js,
'Version':'version:\'23.0\'' in js,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
print(f"RESULT {len(checks)-len(failed)}/{len(checks)}")
raise SystemExit(1 if failed else 0)
