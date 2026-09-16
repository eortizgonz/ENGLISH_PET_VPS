#!/usr/bin/env python3
from pathlib import Path
import json, glob, re, hashlib, sys
ROOT=Path(__file__).resolve().parent
checks=[]
def ck(name,cond,detail=''): checks.append((name,bool(cond),detail))

school=json.loads((ROOT/'PRACTICE_BANK_V46_21.json').read_text(encoding='utf-8'))
adult=json.loads((ROOT/'PRACTICE_BANK_ADULT_V46_26.json').read_text(encoding='utf-8'))
curr=json.loads((ROOT/'PET_LEARN_CURRICULUM_V46_27.json').read_text(encoding='utf-8'))
audio=json.loads((ROOT/'PET_AUDIO_BANK_V46_18.json').read_text(encoding='utf-8'))
ck('practice_schools_5000',len(school.get('items',[]))==5000,len(school.get('items',[])))
ck('practice_adult_3000',len(adult.get('items',[]))==3000,len(adult.get('items',[])))
ck('curriculum_100',len(curr.get('items',[]))==100,len(curr.get('items',[])))
ck('school_audio_manifest_500',len(audio.get('items',[]))==500,len(audio.get('items',[])))

packs=list((ROOT/'exam_packs').glob('pq-*.json')); item_count=0
for p in packs:
 d=json.loads(p.read_text(encoding='utf-8')); item_count += sum(len(d.get(k) or []) for k in ('reading','listening','writing','speaking'))
ck('exam_packs_40',len(packs)==40,len(packs)); ck('exam_items_2500',item_count==2500,item_count)

audio_files=[p for p in (ROOT/'assets'/'audio').rglob('*') if p.is_file() and p.suffix.lower() in {'.mp3','.wav','.m4a','.ogg'}]
ck('audio_files_877',len(audio_files)==877,len(audio_files))
missing=[x.get('audio_file') for x in audio.get('items',[]) if not (ROOT/str(x.get('audio_file'))).is_file()]
ck('school_audio_paths_present',not missing,len(missing))

schema=(ROOT/'postgres_full_schema.sql').read_text(encoding='utf-8')
tables=set(re.findall(r'CREATE TABLE IF NOT EXISTS public\.([a-zA-Z0-9_]+)',schema,re.I))
for t in ('content_packages','practice_bank_items','curriculum_lessons','audio_assets','exam_packs','exam_items','content_seed_runs'):
 ck('schema_'+t,t in tables)
ck('schema_total_at_least_49',len(tables)>=49,len(tables))

pc=(ROOT/'postgres_content.py').read_text(encoding='utf-8')
for token in ('_seed_practice','_seed_curriculum','_seed_audio','_seed_exam','practice_bank','audio_bank','curriculum','exam_index','exam_pack'):
 ck('content_module_'+token,token in pc)
setup=(ROOT/'setup_postgres_pet.py').read_text(encoding='utf-8')
ck('setup_runs_content_seed','postgres_content.seed_all()' in setup)
check=(ROOT/'postgres_check.py').read_text(encoding='utf-8')
ck('postgres_check_content_health','postgres_content.health()' in check)
api=(ROOT/'api_server.py').read_text(encoding='utf-8')
for route in ('/api/content/status','/api/content/practice-bank','/api/content/audio-bank','/api/content/curriculum','/api/content/exam-index','/api/content/exam-pack/'):
 ck('api_'+route,route in api)
for fn in ('v46_21_practice_bank.js','v46_22_practice_diagnostic.js','v46_18_audio_bank.js','v43_full_mock_bank.js','v46_20_full_mock_mastery.js','v46_11_mock_listening.js','v46_27_mastery_orchestrator.js'):
 txt=(ROOT/fn).read_text(encoding='utf-8'); ck('db_first_'+fn,'/content/' in txt)

passed=sum(1 for _,ok,_ in checks if ok); total=len(checks)
for name,ok,detail in checks: print(('PASS' if ok else 'FAIL'),name,detail)
print(f'RESULT {passed}/{total}')
raise SystemExit(0 if passed==total else 2)
