#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent
api=(ROOT/'api_server.py').read_text(encoding='utf-8')
ux=(ROOT/'v46_30_registration_ux.js').read_text(encoding='utf-8')
index=(ROOT/'index.html').read_text(encoding='utf-8')
checks={
 'register_endpoint':"p=='/api/register'" in api,
 'student_only_registration':"'student',sid" in api,
 'password_hashing':'hash_pw(password)' in api,
 'duplicate_email':'email_exists' in api,
 'permission_gate':'permission_required' in api,
 'forgot_password':"p=='/api/forgot-password'" in api,
 'reset_password':"p=='/api/reset-password'" in api,
 'registration_screen':'Crear mi cuenta' in ux,
 'password_confirmation':'registerPassword2' in ux and 'resetPassword2' in ux,
 'show_hide_password':'data-toggle-password' in ux,
 'password_generator':'data-generate-password' in ux,
 'remember_email':'petQuestRememberedEmail' in ux,
 'script_loaded':'v46_30_registration_ux.js' in index,
}
failed=[k for k,v in checks.items() if not v]
print('PET Quest V46.30 registration/recovery QA')
for k,v in checks.items():print(('PASS' if v else 'FAIL'),k)
if failed:raise SystemExit('FAILED: '+', '.join(failed))
print('ALL STATIC CHECKS PASSED')
