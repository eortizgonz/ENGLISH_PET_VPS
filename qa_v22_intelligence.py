from pathlib import Path
root=Path(__file__).parent
js=(root/'v22_adult_intelligence.js').read_text()
html=(root/'index.html').read_text()
css=(root/'styles.css').read_text()
sw=(root/'sw.js').read_text()
checks={
'V22 script loaded':'v22_adult_intelligence.js' in html,
'Adult only':'adult()' in js and "state.view!=='home'" in js,
'Five questions':'¿Qué hizo?' in js and '¿Qué aprendió?' in js and '¿Qué superó?' in js and '¿Qué sigue pendiente?' in js and '¿Cuánta ayuda necesitó?' in js,
'Autonomy score':'function autonomy' in js and 'helpRate' in js,
'Learning overcome detection':'overcome' in js and 'delta:n.pct-p.pct' in js,
'Pending focus':'pending' in js and 'focusStats' in js,
'Adult action plan':'adultActions' in js and 'Qué puede hacer el adulto' in js,
'No diagnostic claim':'Sin diagnósticos emocionales' in js,
'Export CSV':'exportCSV' in js and 'petquest_adult_intelligence.csv' in js,
'Copy summary':'data-v22-copy' in js and 'plainSummary' in js,
'Skill map':'v22-skill-grid' in js and 'Mapa de habilidades' in js,
'Readiness integration':'PETQUEST_V21' in js and 'confidence' in js,
'V20 journey integration':'PETQUEST_V20' in js,
'Responsive CSS':'@media(max-width:540px)' in css and '.v22-intelligence' in css,
'Offline cached':'v22_adult_intelligence.js' in sw,
'Cache V22':any(f'petquest-v{i}-shell' in sw for i in range(22,40)),
'Privacy-safe wording':'guía el proceso, no resuelvas por él' in js,
'Parent teacher title':'Parent & Teacher Intelligence Center' in js,
'Weekly comparison':'week(-1)' in js,
'Public API':'window.PETQUEST_V22' in js,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items():print(('PASS' if v else 'FAIL'),k)
print(f'PET Quest V22 Intelligence QA: {len(checks)-len(failed)}/{len(checks)} PASS')
if failed: raise SystemExit(1)
