from pathlib import Path
import json,re,sys
R=Path(__file__).resolve().parent
checks=[]
def ck(name, cond, detail=''):
    checks.append((name,bool(cond),detail)); print(('PASS' if cond else 'FAIL'),name,detail)
idx=json.loads((R/'exam_packs/adult_index.json').read_text())
profiles=json.loads((R/'EXAM_PROFILES_V46_26.json').read_text())
bank=json.loads((R/'PRACTICE_BANK_ADULT_V46_26.json').read_text())
js=(R/'v46_26_exam_profiles.js').read_text()
app=(R/'app.js').read_text()
mockjs=(R/'v43_full_mock_bank.js').read_text()
pbjs=(R/'v46_21_practice_bank.js').read_text()
diagjs=(R/'v46_22_practice_diagnostic.js').read_text()
child=(R/'v46_23_child_experience.js').read_text()
# Core profile contract
ck('two_profiles', set(profiles['profiles'])=={'schools','adult'})
ck('default_schools', "examProfile:'schools'" in app or 'examProfile: \'schools\'' in app)
ck('adult_selector_label', 'B1 PRELIMINARY – ADULT' in js)
ck('schools_selector_label', 'B1 PRELIMINARY FOR SCHOOLS' in js)
ck('profile_persists_via_save', 'save()' in js and 'examProfile' in js)
ck('profile_change_event', 'exam_profile_changed' in js)
ck('adult_mock_index_routed', 'adult_index.json' in mockjs)
ck('adult_practice_bank_routed', 'PRACTICE_BANK_ADULT_V46_26.json' in pbjs and 'PRACTICE_BANK_ADULT_V46_26.json' in diagjs)
ck('child_ux_excluded_for_adult', "examProfile!=='adult'" in child or 'examProfile !== \'adult\'' in child)
# Adult pack structure
packs=idx['packs']; ck('adult_pack_count_20',len(packs)==20)
counts={'reading':0,'listening':0,'writing':0,'speaking':0}; all_ids=[]; texts=[]; themes=set()
for meta in packs:
    p=json.loads((R/'exam_packs'/f"{meta['pack_id']}.json").read_text())
    counts['reading']+=len(p['reading']); counts['listening']+=len(p['listening']); counts['writing']+=len(p['writing']); counts['speaking']+=len(p['speaking']['parts'])
    all_ids += [q['id'] for q in p['reading']+p['listening']]
    texts.append(json.dumps(p,ensure_ascii=False).lower()); themes.add(p['theme'].lower())
    ck(f"{p['pack_id']}_structure", len(p['reading'])==32 and len(p['listening'])==25 and len(p['writing'])==2 and len(p['speaking']['parts'])==4)
    ck(f"{p['pack_id']}_profile", p.get('exam_profile')=='adult' and all(x.get('profile')=='adult' for x in p['reading']+p['listening']+p['writing']))
ck('adult_totals',counts=={'reading':640,'listening':500,'writing':40,'speaking':80},str(counts))
ck('question_ids_unique',len(all_ids)==len(set(all_ids))==1140)
# School contamination - conservative school-specific tokens
blob='\n'.join(texts)
banned=[r'\bschool trip\b',r'\bschool courtyard\b',r'\bscience club\b',r'\bteenagers?\b',r'\bclassroom\b',r'\bhomework\b',r'\bstudents?\b']
hits={pat:len(re.findall(pat,blob,re.I)) for pat in banned}
ck('no_school_age_contamination',sum(hits.values())==0,str(hits))
# Requested topic universe represented across mock + practice metadata
requested={'work','travel','banking','housing','shopping','transport','appointments','technology','healthcare','restaurants','relationships','community','holidays','services','employment'}
practice_topics={str(x.get('topic','')).lower() for x in bank['items']}
profile_topics=set(profiles['profiles']['adult']['topics'])
ck('all_requested_adult_topics',requested.issubset(practice_topics|profile_topics),str(sorted(requested-(practice_topics|profile_topics))))
# Practice bank
items=bank['items']; ck('adult_practice_3000',len(items)==3000)
ck('adult_practice_unique_ids',len({x['id'] for x in items})==3000)
levels={'A2','A2+','B1-','B1','B1+','B2 bridge'}
ck('adult_levels_complete',levels.issubset({x['cefr'] for x in items}))
competencies={'grammar','vocabulary','reading inference','gist','detail','attitude','listening distractor','spelling','sentence cohesion','phrasal verbs','prepositions','linkers','pronunciation'}
ck('adult_competencies_complete',competencies.issubset({x['competency'] for x in items}))
required=['profile','topic','skill','part','cefr','difficulty','grammar','vocabulary','cognitive_skill','distractor_type','accent','audio_speed','target','estimated_time','competency','diagnostic_patterns']
ck('matrix_complete_3000',all(all(k in x and x[k] not in (None,'') for k in required) for x in items))
practice_blob=json.dumps(items,ensure_ascii=False).lower()
phits={pat:len(re.findall(pat,practice_blob,re.I)) for pat in banned}
ck('adult_practice_no_school_age_contamination',sum(phits.values())==0,str(phits))
# Scientific honesty
ck('external_equivalence_pending',all(not x.get('psychometric_equivalence_validated') and not x.get('external_academic_signoff') for x in packs))
manifest=json.loads((R/'ADULT_MOCK_AUDIO_MANIFEST_V46_26.json').read_text())
recs=manifest.get('items',manifest.get('recordings',[]))
ck('adult_audio_300_manifest',len(recs)==300)
ck('adult_audio_honesty',all(x.get('synthetic') is True and x.get('human_recording') is False for x in recs))
ck('adult_audio_voice_metadata',all(x.get('voice_profile') and x.get('speed_wpm') for x in recs))
# Separate state keys/profile-aware cache
ck('profile_separate_mock_state','examProfile()' in mockjs and 'adult' in mockjs)
ck('profile_separate_practice_state','examProfile()' in pbjs and 'adult' in pbjs)
passed=sum(x[1] for x in checks)
print(f'RESULT {passed}/{len(checks)} PASS')
sys.exit(0 if passed==len(checks) else 1)
