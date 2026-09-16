#!/usr/bin/env python3
from pathlib import Path
import json,re
R=Path(__file__).resolve().parent
js=(R/'v43_full_mock_bank.js').read_text(); bridge=(R/'v46_11_mock_listening.js').read_text() if (R/'v46_11_mock_listening.js').exists() else ''; html=(R/'index.html').read_text(); sw=(R/'sw.js').read_text()
checks={
 'script_loaded':'v43_full_mock_bank.js' in html,
 'cache_v43':'v43_full_mock_bank.js' in sw,
 'three_packs':all(f'pq-mock-{x}.json' in sw for x in 'abc'),
 'open_cloze':'open_cloze' in ''.join((R/f'exam_packs/pq-mock-{x}.json').read_text() for x in 'abc'),
 'reading_45min':'45*60*1000' in js,
 'no_hints':'No se muestran respuestas ni pistas' in js,
 'listening_audio_bridge':('Iniciar Listening Mock' in bridge and 'v46_11_mock_listening.js' in html),
 'remediation':'Remediation to Mastery V43' in js,
 'mastery_rule':'at least three recent correct attempts' in (R/'README.md').read_text(),
 'version':'43.0' in js,
}
failed=[k for k,v in checks.items() if not v]
print('PET Quest V43 UI QA:', 'PASS' if not failed else 'FAIL', f"{sum(checks.values())}/{len(checks)}")
if failed: print('failed:',failed); raise SystemExit(1)
