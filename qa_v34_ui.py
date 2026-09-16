from pathlib import Path
p=Path(__file__).resolve().parent
js=(p/'v34_decision_simulator.js').read_text(); api=(p/'api_server.py').read_text(); idx=(p/'index.html').read_text(); sw=(p/'sw.js').read_text()
checks={
 'V34 loaded':'PETQUEST_V34' in js,
 'GET simulator':"/api/decision-simulator'" in api,
 'POST simulator run':"/api/decision-simulator/run'" in api,
 'hours control':'data-v34-hours' in js,
 'weeks control':'data-v34-weeks' in js,
 'coverage control':'data-v34-coverage' in js,
 'confidence visible':'confidence' in js,
 'range visible':'skill_delta_range' in js,
 'efficiency visible':'efficiency_index' in js,
 'no guarantee wording':'no garantía' in js.lower() or 'no garantiza' in api.lower(),
 'script linked':'v34_decision_simulator.js' in idx,
 'PWA V34':'petquest-v3' in sw and 'v34_decision_simulator.js' in sw,
 'server V34':'PETQuest/' in api and "'version':'" in api,
 'zero when no coverage':'if covered==0 or current_skill<=0: expected=0.0' in api,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items():print(('PASS' if v else 'FAIL'),k)
print(f'PET Quest V34 QA: {len(checks)-len(failed)}/{len(checks)} PASS')
raise SystemExit(1 if failed else 0)
