from pathlib import Path
root=Path(__file__).resolve().parent
api=(root/'api_server.py').read_text()
app=(root/'app.js').read_text()
ui=(root/'v46_8_user_progress.js').read_text()
idx=(root/'index.html').read_text()
sw=(root/'sw.js').read_text()
checks={
 'backend version 46.8': "APP_VERSION='46.8'" in api,
 'preparation endpoint': "p=='/api/my-preparation'" in api,
 'per user snapshot': "SELECT payload,updated_at FROM snapshots WHERE user_id=?" in api,
 'question error corrections': 'corrected_qids' in api and 'pending_qids' in api,
 'academic remediation corrections': 'corrected_codes' in api and 'pending_codes' in api,
 'four skill score': "skill_scores={'reading':reading,'writing':wscore,'listening':listening,'speaking':sscore}" in api,
 'remaining percentage': "100-preparation" in api,
 'internal not official': "official_cambridge_score':False" in api,
 'user isolation bootstrap': "const sr=await apiRequest('/snapshot')" in app,
 'login no stale save': "await apiBootstrap();state.view='home';render()" in app,
 'progress ui layer': 'REGISTRO INDIVIDUAL' in ui,
 'errors ui': 'Errores' in ui and 'Correcciones' in ui,
 'per exam table': 'Preparación por examen' in ui,
 'script loaded': 'v46_8_user_progress.js?v=46.8' in idx,
 'pwa cache 46.8': "petquest-v46-8" in sw and 'v46_8_user_progress.js?v=46.8' in sw,
 'teacher report metrics': 'pending_errors' in app and 'preparation_score' in app,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
assert all(checks.values()), [k for k,v in checks.items() if not v]
print(f'PASS {sum(checks.values())}/{len(checks)} V46.8 user progress')
