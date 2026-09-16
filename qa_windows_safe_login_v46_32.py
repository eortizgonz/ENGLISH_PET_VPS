from pathlib import Path
import re, sys
R=Path(__file__).resolve().parent
checks=[]
def ck(name, ok, detail=''):
    checks.append((name,bool(ok),detail))
app=(R/'app.js').read_text()
idx=(R/'index.html').read_text()
sw=(R/'sw.js').read_text()
ck('anonymous_401_does_not_render_loop', "r.status===401&&path!='/login'&&hadToken" in app)
ck('get_request_dedup', 'const _apiInflight=new Map()' in app and '_apiInflight.has(key)' in app)
ck('request_timeout', 'AbortController' in app and '12000' in app)
ck('bootstrap_single_flight', 'let _bootstrapPromise=null' in app and 'if(_bootstrapPromise)return _bootstrapPromise' in app)
ck('circuit_breaker_loaded', 'v46_30_windows_runtime_guard.js?v=46.32-audiofix1' in idx)
guard=(R/'v46_30_windows_runtime_guard.js').read_text()
ck('api_circuit_breaker', 'count>24' in guard and 'api_circuit_breaker' in guard)
ck('student_admin_client_guard', 'client_role_guard' in guard and '/release-readiness' in guard)
ck('no_global_top_helper', not any(re.search(r'^\s*(?:function|const|let|var)\s+top\b', p.read_text(), re.M) for p in R.glob('*.js')))
prog=(R/'v46_8_user_progress.js').read_text()
ck('no_perpetual_progress_poll', 'setInterval(' not in prog)
for fn, auth_token in [
 ('v34_decision_simulator.js','allowed()'),('v35_budget_optimizer.js','ok()'),('v36_portfolio_optimizer.js','ok()'),
 ('v37_schedule_capacity.js','ok()'),('v38_production_hardening.js','ok()'),('v39_commercial_onboarding.js','ok()'),('v40_release_readiness.js','ok()')]:
    t=(R/fn).read_text()
    ck(fn+'_token_guard', 'if(!API?.token' in t)
    ck(fn+'_role_guard', auth_token in t)
ck('localhost_cache_hygiene', 'petquestLocalBuild' in idx and 'getRegistrations' in idx and "startsWith('petquest-')" in idx)
ck('sw_network_first_dynamic', "const dynamic=/\\.(?:js|json|css)$/" in sw and "cache:'no-store'" in sw)
ck('sw_new_cache', "petquest-v46-32-audiofix-1" in sw)
ck('version_46_32', '46.32-audiofix1' in idx and '46.30' in app)
for n,o,d in checks: print(('PASS' if o else 'FAIL'), n, d)
print(f'RESULT {sum(o for _,o,_ in checks)}/{len(checks)}')
sys.exit(0 if all(o for _,o,_ in checks) else 1)
