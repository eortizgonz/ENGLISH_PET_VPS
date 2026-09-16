# PET Quest 40.2 - Staging Validation

## Purpose
Validate the Commercial Release Candidate in an environment that behaves like production before public launch.

## Required
- Public DNS name
- HTTPS certificate
- Transactional SMTP account
- Persistent disk/volume
- Backups copied off-host
- A pilot school account

## Required validation sequence
1. Set PETQUEST_ENV=production and PETQUEST_DEV_MODE=0.
2. Set PETQUEST_PUBLIC_BASE_URL to the HTTPS public URL.
3. Configure SMTP credentials.
4. Start the service behind HTTPS.
5. Run `python3 qa_release_stack.py --base-url https://your-domain`.
6. Run `python3 security_smoke.py --base-url https://your-domain`.
7. Run `python3 load_profile.py --base-url https://your-domain --requests 500 --workers 25`.
8. Create a backup and restore it in a separate validation instance.
9. Run the pilot protocol with real children, parents and teachers.
10. Obtain independent legal/privacy and penetration-test sign-off.

## Production acceptance
The product is commercially deployable only when release readiness has no blockers, critical security findings are zero, backup restore succeeds, and pilot acceptance thresholds are met.
