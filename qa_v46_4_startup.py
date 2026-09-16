from pathlib import Path
import json,re
R=Path(__file__).resolve().parent
app=(R/'app.js').read_text()
gate=(R/'v46_operational_release_gate.js').read_text()
idx=(R/'index.html').read_text()
sw=(R/'sw.js').read_text()
man=json.loads((R/'manifest.webmanifest').read_text())
server=(R/'api_server.py').read_text()
checks={
 'version_46_4': "APP_VERSION='46.4'" in server,
 'manifest_46_4': man.get('id')=='./petquest-v46-4' and 'v=46.4' in man.get('start_url',''),
 'no_auto_mount_observer': 'MutationObserver' not in gate and "addEventListener('load'" not in gate,
 'no_body_fallback': 'document.body' not in gate,
 'explicit_reports_mount': 'releaseGateMount' in app and 'PETQuestReleaseGate?.mount' in app,
 'school_admin_only': "['school','admin']" in gate,
 'api_not_cached': "url.pathname.startsWith('/api/')" in sw,
 'navigation_network_first': "event.request.mode==='navigate'" in sw and "fetch(event.request,{cache:'no-store'})" in sw,
 'cache_v46_4': "petquest-v46-4" in sw,
 'versioned_app_script': 'app.js?v=46.4' in idx,
 'versioned_gate_script': 'v46_operational_release_gate.js?v=46.4' in idx,
 'sw_update_cache_none': "updateViaCache:'none'" in idx,
 'static_no_store': "Cache-Control','no-store, max-age=0, must-revalidate" in server,
 'legacy_v45_disabled': 'legacy auto-mount disabled' in (R/'v45_production_saas.js').read_text(),
}
failed=[k for k,v in checks.items() if not v]
print('PET Quest V46.4 Startup QA:', 'PASS' if not failed else 'FAIL', f"{sum(checks.values())}/{len(checks)}")
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if failed: raise SystemExit(1)
