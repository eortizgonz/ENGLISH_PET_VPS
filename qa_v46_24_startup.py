from pathlib import Path
R=Path(__file__).parent
app=(R/'app.js').read_text(); gate=(R/'v46_operational_release_gate.js').read_text(); sw=(R/'sw.js').read_text(); manifest=(R/'manifest.webmanifest').read_text(); api=(R/'api_server.py').read_text(); idx=(R/'index.html').read_text()
checks={
 'startup_login_without_token':"view:API.token?'home':'login'" in app,
 'invalid_token_forces_login':"localStorage.removeItem('petQuestToken')" in app and "state.view='login'" in app,
 'api_not_cached':"url.pathname.startsWith('/api/')" in sw and 'event.respondWith(fetch(event.request))' in sw,
 'new_sw_cache':"petquest-v46-24" in sw,
 'pwa_start_url':'source=pwa' in manifest and 'index.html' in manifest,
 'backend_version':"APP_VERSION='46.24'" in api and "server_version='PETQuest/46.24'" in api,
 'error_dna_loaded':'v46_24_error_dna.js?v=46.24' in idx,
 'child_experience_preserved':'v46_23_child_experience.js?v=46.24' in idx,
 'practice_diagnostic_preserved':'v46_22_practice_diagnostic.js?v=46.24' in idx,
 'gate_reports_only':"window.state.view==='reports'" in gate,
}
failed=[k for k,v in checks.items() if not v]
print('PET Quest V46.24 Startup QA:', 'PASS' if not failed else 'FAIL', f"{sum(checks.values())}/{len(checks)}", failed)
raise SystemExit(1 if failed else 0)
