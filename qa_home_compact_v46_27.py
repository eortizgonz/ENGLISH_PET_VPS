from pathlib import Path

root = Path(__file__).resolve().parent
js = (root / 'v46_27_mastery_orchestrator.js').read_text(encoding='utf-8')
app = (root / 'app.js').read_text(encoding='utf-8')

checks = {
    'primary readiness remains visible': 'PET Readiness:' in js and 'pq27-summary' in js,
    'next-step banner removed': 'La app decide tu siguiente paso' not in js and 'data-pq27-continue' not in js,
    'dashboard secondary panel removed': 'class="pq27-more"' not in js and 'Más opciones y detalles' not in js,
    'PET path and portal row removed': 'Tu camino PET' not in app and 'class="portal-row"' not in app,
    'home reduced to two fixed blocks': 'function compactHome()' in js and 'Explorar más herramientas' not in js,
    'late injected cards are collected': 'MutationObserver(()=>compactHome())' in js,
    'adventure map retained': "node.matches?.('.v11-adventure')" in js,
    'adventure map follows readiness': "dashboard.insertAdjacentElement('afterend',map)" in js,
    'old tools dropdown removed': "oldMore?.remove()" in js,
    'other home cards removed': "node.remove()" in js,
    'responsive compact styles': '.pq-home-compact' in js and '@media(max-width:800px)' in js,
}

for name, ok in checks.items():
    print(('PASS' if ok else 'FAIL'), name)

failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit('FAILED: ' + ', '.join(failed))

print(f'Compact home QA: PASS — {len(checks)}/{len(checks)}')
