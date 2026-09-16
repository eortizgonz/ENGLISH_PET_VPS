from pathlib import Path
import json,sys,collections,re
R=Path(__file__).parent; d=json.loads((R/'PRACTICE_BANK_V46_21.json').read_text()); I=d['items']; checks=[]
def C(n,x):checks.append((n,bool(x)))
C('total_5000',len(I)==5000)
C('all_have_patterns',all(isinstance(x.get('diagnostic_patterns'),list) and x['diagnostic_patterns'] for x in I))
c=collections.Counter(p for x in I for p in x['diagnostic_patterns'])
for p in ['gist','numbers','times','opinion','corrected_information','spelling','detail','inference','cohesion','pronunciation']:
    C('pattern_'+p,c[p]>=10)
js=(R/'v46_22_practice_diagnostic.js').read_text()
for token in ['Diagnóstico pedagógico','Problema principal','Generar 10 ejercicios','corrected_information','min_evidence','practice_remediation_answer','practice_remediation_complete','diagnostic_patterns']:
    C('js_'+re.sub(r'\W+','_',token).strip('_'),token in js)
api=(R/'api_server.py').read_text(); C('api_endpoint',"p=='/api/practice-diagnostic'" in api); C('api_min_evidence',"x['n']>=3" in api); C('api_user_scope',"WHERE user_id=? AND event_type IN ('practice_bank_answer','practice_remediation_answer')" in api); C('version',"APP_VERSION='46.25'" in api and "server_version='PETQuest/46.25'" in api)
idx=(R/'index.html').read_text(); C('index_module','v46_22_practice_diagnostic.js?v=46.25' in idx and 'v46_23_child_experience.js?v=46.25' in idx)
for n,v in checks:print(('PASS' if v else 'FAIL'),n)
print(f'{sum(v for _,v in checks)}/{len(checks)} PASS');sys.exit(0 if all(v for _,v in checks) else 1)
