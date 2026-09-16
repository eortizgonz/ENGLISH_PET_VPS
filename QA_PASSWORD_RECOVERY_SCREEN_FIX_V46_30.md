# QA Password Recovery Screen Fix V46.30

## Issue observed
Password recovery screen displayed:
`Unexpected token '<', "<!DOCTYPE "... is not valid JSON`

## Root cause
The UI attempted to parse an HTML response as JSON. This can occur when a stale cached frontend/service worker calls an outdated route or when the wrong server serves a static HTML fallback for an API request.

## Corrections
- Hardened `apiRequest()` to read the response as text first and only parse JSON safely.
- Detects HTML API responses explicitly as `api_html_response` instead of surfacing a raw JSON parser error.
- Password recovery UX now displays a user-friendly recovery instruction on stale/wrong-server responses.
- Bumped frontend build token to `46.30-authfix2`.
- Bumped PWA cache to `petquest-v46-30-authfix-2` to invalidate stale cached JS.
- Service worker remains network-only for `/api/*` requests.

## Validation
- `app.js`: JavaScript syntax PASS.
- `v46_30_registration_ux.js`: JavaScript syntax PASS.
- `sw.js`: JavaScript syntax PASS.
- `POST /api/forgot-password`: HTTP 200.
- Response Content-Type: `application/json; charset=utf-8`.
- Response body: valid JSON.

## User action after installing this build
Use the new ZIP, start PET Quest normally, then refresh with Ctrl+F5 once if an older browser tab is still open.
