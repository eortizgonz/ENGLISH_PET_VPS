from pathlib import Path
ROOT=Path(__file__).resolve().parent
api=(ROOT/'api_server.py').read_text(); js=(ROOT/'v44_mock_quality.js').read_text(); v43=(ROOT/'v43_full_mock_bank.js').read_text(); sw=(ROOT/'sw.js').read_text(); pg=(ROOT/'postgres_schema.sql').read_text()
checks={
 'version44': "APP_VERSION='" in api and float(api.split("APP_VERSION='",1)[1].split("'",1)[0])>=44,
 'attempt_table': 'CREATE TABLE IF NOT EXISTS mock_attempts' in api,
 'item_table': 'CREATE TABLE IF NOT EXISTS mock_item_responses' in api,
 'post_attempts': "p=='/api/mock-attempts'" in api,
 'get_quality': "p=='/api/mock-quality'" in api,
 'facility': "item['facility']" in api,
 'discrimination': "item['discrimination']" in api,
 'sample_gate10': 'n>=10' in api,
 'sample_gate20': 'len(attempts)>=20' in api,
 'form_equivalence': "'within_5_points'" in api,
 'frontend': 'Mock Quality & Difficulty V44' in js,
 'capture_from_mock': "'/mock-attempts'" in v43,
 'postgres': 'mock_item_responses' in pg,
 'pwa': 'v44_mock_quality.js' in sw,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
assert all(checks.values())
print(f"PET Quest V44 UI/Code QA: PASS {sum(checks.values())}/{len(checks)}")
