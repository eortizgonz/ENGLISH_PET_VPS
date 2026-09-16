from pathlib import Path
import re
root=Path(__file__).resolve().parent
app=(root/'app.js').read_text()
v6=(root/'v6_enhancements.js').read_text()
api=(root/'api_server.py').read_text()
checks={
 'initial view requires login': "view:API.token?'home':'login'" in app,
 'render protects unauthenticated routes': "if(!API.token&&state.view!=='login'){state.view='login'}" in app,
 'global logout visible': 'data-logout>Cerrar sesión' in app,
 'clear auth helper': 'function clearAuthSession()' in app,
 '401 returns to login': "r.status===401&&path!='/login'" in app,
 'session expiry persisted': 'petQuestSessionExpiresAt' in app,
 'session expiry checked on startup': 'exp<=Date.now()' in app,
 'login saves expiry': 'API.sessionExpiresAt=r.expires_at' in app,
 'logout calls backend': "apiRequest('/logout',{method:'POST'})" in v6,
 'logout clears session': 'clearAuthSession();state.view=\'login\'' in v6,
 'enter submits login': "e.key==='Enter'" in v6,
 'backend login route': "if p=='/api/login':" in api,
 'backend logout route': "if p=='/api/logout':" in api,
 'backend invalidates token': "DELETE FROM sessions WHERE token=?" in api,
 'backend version 46.23': "APP_VERSION='46.23'" in api,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
assert all(checks.values()), [k for k,v in checks.items() if not v]
print(f'AUTH SESSION V46.12: {len(checks)}/{len(checks)} PASS')
