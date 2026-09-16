#!/usr/bin/env python3
import json, glob, os, hashlib, sys
from collections import Counter
ROOT=os.path.dirname(__file__)
idx=json.load(open(os.path.join(ROOT,'exam_packs','index.json'),encoding='utf-8'))
checks=[]
def ck(name,cond,detail=''):
    checks.append((name,bool(cond),detail)); print(('PASS' if cond else 'FAIL'),name,detail)
ck('index version 46.20',idx.get('version')=='46.20')
ck('20 mock packs',len(idx.get('packs',[]))==20,str(len(idx.get('packs',[]))))
ck('index totals',idx.get('counts')=={'reading_questions':640,'listening_questions':500,'writing_tasks':40,'speaking_parts':80},str(idx.get('counts')))
all_ids=[]; all_audio=[]; pack_hashes=[]; source_hashes=[]
for rec in idx['packs']:
    pid=rec['pack_id']; path=os.path.join(ROOT,'exam_packs',pid+'.json');
    ck(pid+' file exists',os.path.isfile(path))
    p=json.load(open(path,encoding='utf-8'))
    rc=Counter(int(q['part']) for q in p['reading']); lc=Counter(int(q['part']) for q in p['listening'])
    ck(pid+' reading 32',len(p['reading'])==32,str(rc))
    ck(pid+' reading contract',rc==Counter({1:5,2:5,3:5,4:5,5:6,6:6}),str(rc))
    ck(pid+' listening 25',len(p['listening'])==25,str(lc))
    ck(pid+' listening contract',lc==Counter({1:7,2:6,3:6,4:6}),str(lc))
    ck(pid+' writing 2',len(p.get('writing',[]))==2)
    ck(pid+' speaking 4',len(p.get('speaking',{}).get('parts',[]))==4)
    ck(pid+' external signoff false',p.get('authoring',{}).get('external_academic_signoff') is False)
    ck(pid+' psychometric equivalence false',p.get('authoring',{}).get('psychometric_equivalence_validated') is False)
    ids=[q['id'] for q in p['reading']+p['listening']]; all_ids+=ids
    aud=set(q['audio_id'] for q in p['listening']); all_audio += list(aud)
    ck(pid+' 15 unique recordings',len(aud)==15,str(len(aud)))
    missing=[q['audio_file'] for q in p['listening'] if not os.path.isfile(os.path.join(ROOT,q['audio_file']))]
    ck(pid+' audio files exist',not missing,str(len(missing)))
    pack_hashes.append(hashlib.sha256(json.dumps({'r':p['reading'],'l':p['listening'],'w':p['writing'],'s':p['speaking']},sort_keys=True).encode()).hexdigest())
    # source content hash ignores item ids; confirms forms are not byte clones
    source_hashes.append(hashlib.sha256(json.dumps({'r':[ {k:v for k,v in q.items() if k!='id'} for q in p['reading']], 'l':[q['transcript'] for q in p['listening']], 'w':p['writing'],'s':p['speaking']},sort_keys=True).encode()).hexdigest())
ck('1140 item IDs globally unique',len(all_ids)==1140 and len(set(all_ids))==1140,f'{len(all_ids)}/{len(set(all_ids))}')
ck('300 listening recordings globally unique',len(all_audio)==300 and len(set(all_audio))==300,f'{len(all_audio)}/{len(set(all_audio))}')
ck('20 full form payloads distinct',len(set(pack_hashes))==20,str(len(set(pack_hashes))))
ck('20 source-content forms distinct',len(set(source_hashes))==20,str(len(set(source_hashes))))
# Part 3 one recording / 6 questions and Part 4 one recording / 6 questions
for rec in idx['packs']:
    p=json.load(open(os.path.join(ROOT,'exam_packs',rec['pack_id']+'.json'),encoding='utf-8'))
    for part in (3,4):
        aud={q['audio_id'] for q in p['listening'] if int(q['part'])==part}
        ck(rec['pack_id']+f' L{part} shared recording',len(aud)==1,str(aud))
# UI integration
v43=open(os.path.join(ROOT,'v43_full_mock_bank.js'),encoding='utf-8').read(); v11=open(os.path.join(ROOT,'v46_11_mock_listening.js'),encoding='utf-8').read(); v20=open(os.path.join(ROOT,'v46_20_full_mock_mastery.js'),encoding='utf-8').read(); index=open(os.path.join(ROOT,'index.html'),encoding='utf-8').read()
ck('bank advertises 20 Full Mocks','20 Full Mocks' in v43)
ck('generic listening buttons','data-v4611-start-listening' in v43 and 'data-v4611-start-listening' in v11)
ck('writing paper integrated','openWriting' in v20 and '45 minutes' in v20)
ck('speaking paper integrated','openSpeaking' in v20 and 'Speaking AI' in v20)
ck('v46.20 script loaded','v46_20_full_mock_mastery.js?v=46.27' in index)
passed=sum(x[1] for x in checks); total=len(checks)
print(f'RESULT {passed}/{total} PASS')
sys.exit(0 if passed==total else 1)
