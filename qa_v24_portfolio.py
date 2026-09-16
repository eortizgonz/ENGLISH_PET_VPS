from pathlib import Path
root=Path(__file__).parent
js=(root/'v24_portfolio.js').read_text()
idx=(root/'index.html').read_text()
sw=(root/'sw.js').read_text()
checks={
 'script_loaded':'v24_portfolio.js' in idx,
 'cache_v24':any(f'petquest-v{i}-shell' in sw for i in range(24,40)),
 'offline_script':'./v24_portfolio.js' in sw,
 'offline_asset':'./assets/portfolio.svg' in sw,
 'portfolio_asset':(root/'assets/portfolio.svg').exists(),
 'mastered_words':'masteredWords' in js,
 'capture_mastered':'data-master-word' in js,
 'writing_evidence':'Mi Writing destacado' in js,
 'speaking_evidence':'Mi Speaking destacado' in js,
 'timeline':'Mi línea de crecimiento' in js,
 'worlds':'Mis mundos' in js,
 'badges':'Mi colección' in js,
 'kid_portfolio':'Mira todo lo que ya puedes hacer' in js,
 'adult_portfolio':'Evidencia de aprendizaje' in js,
 'csv':'Exportar CSV' in js,
 'copy':'Copiar resumen' in js,
 'local_storage':"petQuestV24Portfolio" in js,
 'responsive':'@media(max-width:720px)' in js,
 'aria_dialog':'aria-modal="true"' in js,
 'exposed_api':'window.PETQUEST_V24' in js,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if not all(checks.values()): raise SystemExit(1)
print(f'PET Quest V24 Portfolio QA: PASS — {len(checks)}/{len(checks)}')
