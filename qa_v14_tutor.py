from pathlib import Path
root=Path(__file__).parent
js=(root/'v14_tutor.js').read_text()
html=(root/'index.html').read_text()
sw=(root/'sw.js').read_text()
css=(root/'styles.css').read_text()
checks={
 'V14 loaded':'v14_tutor.js' in html,
 'Tutor UI':'v14-tutor' in js and '.v14-tutor' in css,
 'No entendí':'No entendí' in js,
 'Hint':'Dame una pista' in js,
 'Easier':'Más fácil' in js,
 'Example':'Ponme un ejemplo' in js,
 'Similar':'Algo parecido' in js,
 'Why after check':'Explícame por qué' in js and "checked?" in js,
 'No direct answer promise':'no te dirá qué letra elegir' in js,
 'Micro practice':'V14_MICRO' in js and 'data-v14-micro-opt' in js,
 'Help analytics':'helpCounts' in js and 'preferredHelp' in js,
 'Adult insight':'Uso del Tutor Milo' in js,
 'Accessible live region':'aria-live' in js,
 'Offline cache V14':'petquest-v' in sw and './v14_tutor.js' in sw,
 'V13 preserved':'v13_adaptive.js' in html and './v13_adaptive.js' in sw,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items():print(f'{"PASS" if v else "FAIL"}: {k}')
if failed: raise SystemExit('FAILED: '+', '.join(failed))
print(f'PET Quest V14 Tutor QA: PASS ({len(checks)}/{len(checks)})')
