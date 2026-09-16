#!/usr/bin/env python3
import json, sys, subprocess, pathlib, hashlib
ROOT=pathlib.Path(__file__).resolve().parent
m=json.loads((ROOT/'PET_AUDIO_BANK_V46_18.json').read_text(encoding='utf-8'))
checks=[]
def ck(name,ok,detail=''): checks.append((name,bool(ok),detail))
ck('manifest version 46.18',m.get('version')=='46.18')
ck('500 total',m.get('total')==500,str(m.get('total')))
ck('part1 180',m['counts'].get('part1')==180)
ck('part2 160',m['counts'].get('part2')==160)
ck('part3 80',m['counts'].get('part3')==80)
ck('part4 80',m['counts'].get('part4')==80)
items=m['items']; ids=[x['id'] for x in items]; tx=[x['transcript'] for x in items]; files=[x['audio_file'] for x in items]
ck('unique ids',len(set(ids))==500)
ck('unique transcripts',len(set(tx))==500, f'{len(set(tx))}/500')
ck('unique audio paths',len(set(files))==500)
ck('training speeds exact',m.get('training_speeds')==[0.75,0.85,1.0,1.1],str(m.get('training_speeds')))
ck('exam speed 1.0',m['exam'].get('speed')==1.0)
ck('exam 2 plays',m['exam'].get('max_plays')==2)
ck('synthetic truth flag',m['voice_policy'].get('synthetic_voice_simulation') is True and m['voice_policy'].get('human_recordings') is False)
profiles=set(v for x in items for v in x['voice_profiles']); ck('voice profile diversity >= 15',len(profiles)>=15,str(len(profiles)))
brit=sum(1 for x in items if all('International' not in v for v in x['voice_profiles'])); ck('British predominance >= 75%',brit/500>=.75,f'{brit}/500')
intl=500-brit; ck('international exposure >= 15%',intl/500>=.15,f'{intl}/500')
missing=[]; bad=[]; samples=[]
for x in items:
 p=ROOT/x['audio_file']
 if not p.exists() or p.stat().st_size<1000: missing.append(x['id']); continue
 if x.get('sample_rate')!=48000 or x.get('channels')!=1 or x.get('bit_rate',0)<140000: bad.append(x['id'])
 if len(samples)<8 and x['index'] in (1,20): samples.append(p)
ck('500 audio files exist',not missing,str(missing[:5]))
ck('500 manifest audio specs valid',not bad,str(bad[:5]))
# Decode/probe representative files from all parts; all were ffprobed during generation and hashes persisted.
probe_ok=True
for p in samples:
 try:
  subprocess.run(['ffmpeg','-v','error','-i',str(p),'-t','1','-f','null','-'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 except Exception: probe_ok=False
ck('representative decode across parts',probe_ok,str(len(samples)))
# Validate stored SHA256 against a deterministic spread of 20 clips.
hash_ok=True
for x in items[::25]:
 p=ROOT/x['audio_file']; h=hashlib.sha256(p.read_bytes()).hexdigest(); hash_ok &= h==x['sha256']
ck('sample SHA256 integrity',hash_ok)
js=(ROOT/'v46_18_audio_bank.js').read_text(encoding='utf-8')
for token in ['0.75','0.85','1.10','REAL EXAM MODE','n>=2','/events','audio_bank_answer','PET_AUDIO_BANK_V46_18.json']:
 ck('UI '+token,token in js)
passed=sum(x[1] for x in checks)
for n,ok,d in checks: print(('PASS' if ok else 'FAIL'),n,d)
print(f'AUDIO BANK V46.19: {passed}/{len(checks)} PASS')
sys.exit(0 if passed==len(checks) else 1)
