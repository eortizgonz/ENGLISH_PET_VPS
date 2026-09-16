from pathlib import Path
r=Path(__file__).resolve().parent
idx=(r/'index.html').read_text(); js=(r/'v32_governance.js').read_text(); sw=(r/'sw.js').read_text(); api=(r/'api_server.py').read_text(); pg=(r/'postgres_schema.sql').read_text()
checks={
'V32 script':'v32_governance.js' in idx,
'governance GET':"/api/governance'" in api,
'goals POST':'/api/governance/goals' in api,
'actions POST':'/api/governance/actions' in api,
'review POST':'/api/governance/review' in api,
'action status':'/api/governance/actions/status' in api,
'goal tables':'governance_goals' in api,
'alerts':'off_track' in api and 'overdue_action' in api,
'baseline':'baseline_value' in api,
'roles':"'school','admin'" in api,
'frontend goals':'Objetivos académicos' in js,
'frontend actions':'Acciones y compromisos' in js,
'PWA':"petquest-v" in sw and './v32_governance.js' in sw,
'PostgreSQL':'governance_reviews' in pg,
'responsive':'@media(max-width:760px)' in js,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
assert all(checks.values())
print(f'PET Quest V32 Governance QA: {sum(checks.values())}/{len(checks)} PASS')
