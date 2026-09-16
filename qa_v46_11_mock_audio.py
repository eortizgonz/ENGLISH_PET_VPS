#!/usr/bin/env python3
import json, subprocess, sys, re
from pathlib import Path
R=Path(__file__).resolve().parent
errors=[]; checks=[]
def ok(name,cond,detail=''):
    checks.append((name,bool(cond),detail));
    if not cond: errors.append(name+(': '+detail if detail else ''))
idx=json.loads((R/'exam_packs/index.json').read_text())
ok('three_packs',len(idx.get('packs',[]))==3)
ok('index_generated_audio_ready',all(p.get('generated_audio_ready') is True for p in idx['packs']))
ok('external_signoff_remains_false',all(p.get('external_academic_signoff') is False for p in idx['packs']))
ok('human_studio_not_falsely_claimed',all(p.get('studio_audio_ready') is False for p in idx['packs']))
files=[]
for c in 'abc':
    d=json.loads((R/'exam_packs'/f'pq-mock-{c}.json').read_text())
    ls=d['listening']; aids={x['audio_id'] for x in ls}; paths={x.get('audio_file') for x in ls}
    ok(f'mock_{c}_25_items',len(ls)==25)
    ok(f'mock_{c}_15_recordings',len(aids)==15,str(len(aids)))
    ok(f'mock_{c}_part_distribution',[sum(1 for x in ls if x['part']==p) for p in (1,2,3,4)]==[7,6,6,6])
    ok(f'mock_{c}_part3_shared',len({x['audio_id'] for x in ls if x['part']==3})==1)
    ok(f'mock_{c}_part4_shared',len({x['audio_id'] for x in ls if x['part']==4})==1)
    ok(f'mock_{c}_audio_paths',all(paths) and len(paths)==15)
    ok(f'mock_{c}_generated_ready',d['authoring'].get('generated_audio_ready') is True)
    ok(f'mock_{c}_studio_false',d['authoring'].get('studio_audio_ready') is False)
    for rel in paths:
        p=R/rel; files.append(p); ok(f'exists_{p.name}',p.exists())
        if p.exists():
            pr=subprocess.run(['ffprobe','-v','error','-show_entries','stream=codec_name,sample_rate,channels,bit_rate:format=duration','-of','json',str(p)],capture_output=True,text=True)
            try:
                j=json.loads(pr.stdout); s=j['streams'][0]
                ok(f'decode_{p.name}',pr.returncode==0 and s.get('codec_name')=='mp3')
                ok(f'quality_{p.name}',int(s.get('sample_rate',0))==44100 and int(s.get('channels',0))==1 and int(s.get('bit_rate',0))>=120000)
                ok(f'duration_{p.name}',float(j['format']['duration'])>3.0)
            except Exception: ok(f'probe_{p.name}',False)
ok('45_audio_files',len(set(map(str,files)))==45,str(len(set(map(str,files)))))
js=(R/'v46_11_mock_listening.js').read_text()
ok('listening_engine_loaded','v46_11_mock_listening.js?v=46.11' in (R/'index.html').read_text())
ok('dual_play_mode',"S.strict&&used>=2" in js and "repeticiones ilimitadas" in js and "S.plays[id]=used+1" in js)
ok('25_score','total:25' in js and 'sc.correct}/25' in js)
ok('30_min_timer','30*60*1000' in js)
ok('no_transcript_render','q.transcript' not in js)
ok('mock_attempt_persistence',"skill:'listening'" in js and "'/mock-attempts'" in js)
ok('listening_unlocked',"Iniciar Listening Mock" in js)
sw=(R/'sw.js').read_text(); ok('cache_v4611',"petquest-v46-11" in sw); ok('all_audio_cached',all("'./"+str(p.relative_to(R)).replace('\\','/')+"'" in sw for p in files))
print(f'PET Quest V46.11 Mock Audio QA: {"PASS" if not errors else "FAIL"} | {sum(v for _,v,_ in checks)}/{len(checks)}')
if errors:
    print('\n'.join('FAIL '+x for x in errors[:30])); raise SystemExit(1)
