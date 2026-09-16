from pathlib import Path
root=Path(__file__).parent
index=(root/'index.html').read_text()
js=(root/'v12_ux.js').read_text()
css=(root/'styles.css').read_text()
sw=(root/'sw.js').read_text()
checks={
 'v12 loaded':'v12_ux.js' in index,
 'age adaptation':'V12_AGES' in js and '7-9' in js and '13+' in js,
 'badges':'V12_BADGES' in js and 'Mis insignias' in js,
 'avatar accessories':'V12_ACCESSORIES' in js,
 'context scenes':'function v12Scene' in js and 'assets/scene_' in js,
 'guided start':'data-v12-start' in js,
 'adult age config':'Modo Adulto' in js,
 'responsive css':'.v12-hero-scene' in css and '@media(max-width:760px)' in css,
 'offline v12':'v12_ux.js' in sw and any(f'petquest-v{i}' in sw for i in range(12,40)),
}
for asset in ['scene_home.svg','scene_reading.svg','scene_listening.svg','scene_writing.svg','scene_speaking.svg','scene_mock.svg']:
    checks[f'asset {asset}']=(root/'assets'/asset).exists()
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if failed: raise SystemExit('V12 UX QA failed: '+', '.join(failed))
print('PET Quest V12 UX QA: PASS')
