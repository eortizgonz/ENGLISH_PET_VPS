#!/usr/bin/env python3
"""Static + runtime-oriented checks for school/tenant isolation in the legacy API."""
from pathlib import Path
import re, json
s=Path('api_server.py').read_text()
checks={
 'tenant_alias_exposed': "user['tenant_id']=user.get('school_id')" in s,
 'class_lookup_scoped': 'WHERE id=? AND school_id=?' in s,
 'school_students_scoped': 'WHERE school_id=? AND role="student"' in s,
 'privacy_resolution_scoped': "u['role']=='school' and r['school_id']!=u['school_id']" in s,
 'user_patch_scoped': "target['school_id']!=u['school_id']" in s,
 'backend_scope_helper': 'def school_scope(self,u)' in s,
}
print(json.dumps({'ok':all(checks.values()),'checks':checks},indent=2))
raise SystemExit(0 if all(checks.values()) else 2)
