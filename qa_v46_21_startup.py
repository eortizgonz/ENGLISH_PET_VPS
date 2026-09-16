from pathlib import Path
root=Path(__file__).parent
app=(root/'app.js').read_text()
gate=(root/'v46_operational_release_gate.js').read_text()
sw=(root/'sw.js').read_text()
manifest=(root/'manifest.webmanifest').read_text()
api=(root/'api_server.py').read_text()
checks={
 'startup_login_without_token': "view:API.token?'home':'login'" in app,
 'invalid_token_forces_login': "localStorage.removeItem('petQuestToken')" in app and "state.view='login'" in app,
 'gate_no_body_fallback': '||document.body' not in gate and "document.body" not in gate,
 'gate_reports_only': "window.state.view==='reports'" in gate,
 'gate_school_admin_only': "['school','admin'].includes(window.API.user.role)" in gate,
 'api_not_cached': "url.pathname.startsWith('/api/')" in sw and 'event.respondWith(fetch(event.request))' in sw,
 'new_sw_cache': "petquest-v46-21" in sw,
 'pwa_start_url': 'source=pwa' in manifest and 'index.html' in manifest,
 'backend_version': "APP_VERSION='46.21'" in api,
}
failed=[k for k,v in checks.items() if not v]
print('PET Quest V46.21 Startup QA:', 'PASS' if not failed else 'FAIL', f"{sum(checks.values())}/{len(checks)}", failed)
raise SystemExit(1 if failed else 0)
