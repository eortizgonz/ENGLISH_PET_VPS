from pathlib import Path
root=Path(__file__).parent
js=(root/'v15_autonomy.js').read_text()
html=(root/'index.html').read_text()
sw=(root/'sw.js').read_text()
css=(root/'styles.css').read_text()
checks={
 'V15 loaded':'v15_autonomy.js' in html,
 'Autonomous plan':'function v15Plan' in js and 'Calentamiento' in js and 'Misión principal' in js,
 'Short session':'targetMinutes' in js and 'sessionMinutes' in js,
 'User controlled navigation':'navigation remains user-controlled' in js and 'data-v15-nudge' in js,
 'Break recommendation':'Pausa corta recomendada' in js,
 'Support nudge':'Milo propone más ayuda' in js,
 'Independent attempt':'Probemos una sin ayuda' in js,
 'Step completion':'Paso completado' in js,
 'Level readiness':'function v15LevelReady' in js and 'Listo para subir' in js,
 'Adult summary':'Resumen de autonomía' in js,
 'Kid summary':'Tu última misión' in js,
 'Session persistence':'petQuestV15Autonomy' in js,
 'Tutor reuse':'v14Show' in js,
 'Adaptive reuse':'v13Overall' in js,
 'Accessible session':'aria-label="Sesión guiada por Milo"' in js and 'aria-live="polite"' in js,
 'Responsive UI':'.v15-session-bar' in css and '@media(max-width:760px)' in css,
 'Offline cache V15':any(f'petquest-v{i}-shell' in sw for i in range(15,40)) and './v15_autonomy.js' in sw,
 'V14 preserved':'v14_tutor.js' in html and './v14_tutor.js' in sw,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(f'{"PASS" if v else "FAIL"}: {k}')
if failed: raise SystemExit('FAILED: '+', '.join(failed))
print(f'PET Quest V15 Autonomy QA: PASS ({len(checks)}/{len(checks)})')
