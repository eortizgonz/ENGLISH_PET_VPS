from pathlib import Path
import json, sys
R=Path(__file__).resolve().parent
A=json.loads((R/'THREE_MOCK_ITEM_AUDIT_V46_28.json').read_text(encoding='utf-8'))
checks=[]
def ck(name,ok): checks.append((name,bool(ok))); print(('PASS' if ok else 'FAIL'),name)
ck('189 audit records',A.get('total_records')==189)
for m in 'ABC':
 s=A['summary'][m]
 ck(f'{m} 63 records',s['total']==63)
 ck(f'{m} Reading 32',s['by_skill']['Reading']['total']==32)
 ck(f'{m} Listening 25',s['by_skill']['Listening']['total']==25)
 ck(f'{m} Writing 2',s['by_skill']['Writing']['total']==2)
 ck(f'{m} Speaking 4',s['by_skill']['Speaking']['total']==4)
 p=json.loads((R/'exam_packs'/f'pq-mock-{m.lower()}.json').read_text(encoding='utf-8'))
 ck(f'{m} pack audit 63',p['audit_v46_28']['records']==63)
 ck(f'{m} production blocked',p['audit_v46_28']['production_gate']['allowed'] is False)
# Every record has required audit fields
required=['mock','skill','part','item','cefr_target','target_skill','ambiguity','grammar_level','vocabulary_level','cultural_dependency','reviewer_1','reviewer_2','final_status','production_eligible','reasons']
ck('all records required fields',all(all(k in r for k in required) for r in A['records']))
ck('only valid final statuses',all(r['final_status'] in ('APPROVED_INTERNAL_QA','REJECTED_FOR_REVISION') for r in A['records']))
ck('rejected never production eligible',all(not r['production_eligible'] for r in A['records'] if r['final_status']=='REJECTED_FOR_REVISION'))
ck('reviewers disclosed automated',A.get('external_academic_signoff') is False and 'automated' in A.get('note','').lower())
# Confirm known defects are rejected
ids={r['item']:r for r in A['records']}
for iid in ['pq-mock-a-r5-6','pq-mock-a-l2-2','pq-mock-a-l4-1','pq-mock-a-w1','pq-mock-a-s2','pq-mock-a-s3','pq-mock-b-r1-1','pq-mock-c-r4-1']:
 ck(iid+' rejected',ids[iid]['final_status']=='REJECTED_FOR_REVISION')
# Index contains product block
idx=json.loads((R/'exam_packs/index.json').read_text(encoding='utf-8'))
for m in 'abc':
 rec=next(x for x in idx['packs'] if x['pack_id']==f'pq-mock-{m}')
 ck(f'index {m} blocked',rec['item_audit_v46_28']['production_allowed'] is False)
# UI gates are present
for f,tok in [('v43_full_mock_bank.js','audit_v46_28?.production_gate?.allowed===false'),('v46_11_mock_listening.js','audit_v46_28?.production_gate?.allowed===false'),('v46_20_full_mock_mastery.js','audit_v46_28?.production_gate?.allowed===false')]:
 ck(f+' gate',tok in (R/f).read_text(encoding='utf-8'))
print(f'RESULT {sum(ok for _,ok in checks)}/{len(checks)} PASS')
sys.exit(0 if all(ok for _,ok in checks) else 1)
