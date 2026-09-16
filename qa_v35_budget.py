from pathlib import Path
import re, py_compile
ROOT=Path(__file__).resolve().parent
checks={
'frontend file':(ROOT/'v35_budget_optimizer.js').exists(),
'index loads v35':'v35_budget_optimizer.js' in (ROOT/'index.html').read_text(),
'cache current':bool(re.search(r"petquest-v\d+-shell",(ROOT/'sw.js').read_text())),
'cache includes v35':'./v35_budget_optimizer.js' in (ROOT/'sw.js').read_text(),
'optimizer get':"/api/budget-optimizer'" in (ROOT/'api_server.py').read_text(),
'optimizer run':"/api/budget-optimizer/run'" in (ROOT/'api_server.py').read_text(),
'budget constraint':'budget' in (ROOT/'v35_budget_optimizer.js').read_text(),
'cost constraint':'cost_per_hour' in (ROOT/'api_server.py').read_text(),
'hours constraint':'max_hours_week' in (ROOT/'api_server.py').read_text(),
'weeks constraint':'weeks' in (ROOT/'v35_budget_optimizer.js').read_text(),
'impact range':'skill_delta_range' in (ROOT/'api_server.py').read_text() or "'range'" in (ROOT/'api_server.py').read_text(),
'no guarantee':'no garantiza' in (ROOT/'api_server.py').read_text().lower(),
'empty state':'No hay escenarios factibles' in (ROOT/'v35_budget_optimizer.js').read_text(),
'version current':bool(re.search(r"'version':'(?:3[5-9]|[4-9]\d)\.0'",(ROOT/'api_server.py').read_text())),
'responsive':'@media' in (ROOT/'v35_budget_optimizer.js').read_text(),
}
for k,v in checks.items():print(('PASS' if v else 'FAIL'),k)
assert all(checks.values())
py_compile.compile(str(ROOT/'api_server.py'),doraise=True)
print(f'PET Quest V35 Compatibility QA: {len(checks)}/{len(checks)} PASS')
