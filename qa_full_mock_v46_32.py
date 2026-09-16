#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parent
checks=[]
def ck(n,c,d=''):
 checks.append(bool(c)); print(('PASS ' if c else 'FAIL ')+n+((' '+str(d)) if d else ''))
idx=json.loads((R/'exam_packs/index.json').read_text())
packs=idx.get('packs',[]); ck('20_school_packs',len(packs)==20,len(packs))
all_ids=set(); recs=set(); missing=[]
for meta in packs:
 pid=meta['pack_id']; p=R/'exam_packs'/f'{pid}.json'; ck(pid+'_exists',p.exists())
 if not p.exists(): continue
 d=json.loads(p.read_text()); rd=d.get('reading',[]); ls=d.get('listening',[]); wr=d.get('writing',[]); sp=d.get('speaking',{}).get('parts',[]) if isinstance(d.get('speaking'),dict) else d.get('speaking',[])
 ck(pid+'_structure',len(rd)==32 and len(ls)==25 and len(wr)==2 and len(sp)==4,(len(rd),len(ls),len(wr),len(sp)))
 for q in rd+ls:
  qid=q.get('id');
  if qid in all_ids: ck(pid+'_unique_item_'+str(qid),False)
  all_ids.add(qid)
 for q in ls:
  aid=q.get('audio_id'); rel=q.get('audio_file');
  if aid: recs.add(aid)
  if rel and not (R/rel).exists(): missing.append(rel)
ck('1140_unique_items',len(all_ids)==1140,len(all_ids))
ck('300_unique_recordings',len(recs)==300,len(recs))
ck('all_mock_audio_files_exist',not missing,len(missing))
html=(R/'index.html').read_text(); ck('mastery_script_loaded','v46_20_full_mock_mastery.js' in html); ck('listening_script_loaded','v46_11_mock_listening.js' in html)
print(f'RESULT {sum(checks)}/{len(checks)}')
if not all(checks): raise SystemExit(1)
