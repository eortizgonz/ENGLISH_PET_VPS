import json, subprocess, hashlib, re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from mutagen.mp3 import MP3
ROOT=Path(__file__).resolve().parent
m=json.loads((ROOT/'PET_AUDIO_BANK_V46_18.json').read_text())
items=m['items']; failures=[]
print('Auditing',len(items),'PET Audio Bank files')
paths=[]
for x in items:
    p=ROOT/x['audio_file']; paths.append((x,p))
    if not p.exists(): failures.append((x['id'],'missing')); continue
    if hashlib.sha256(p.read_bytes()).hexdigest()!=x['sha256']: failures.append((x['id'],'sha256'))
    try:
        a=MP3(p); info=a.info
        if int(info.sample_rate)!=48000: failures.append((x['id'],'sample_rate'))
        if int(info.channels)!=1: failures.append((x['id'],'channels'))
        if int(info.bitrate)<150000: failures.append((x['id'],'bitrate'))
        if info.length<=1: failures.append((x['id'],'duration'))
    except Exception as e: failures.append((x['id'],'mp3_parse'))

def decode(pair):
    x,p=pair
    if not p.exists(): return (x['id'],False,'missing')
    r=subprocess.run(['ffmpeg','-hide_banner','-nostats','-v','error','-i',str(p),'-f','null','-'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True,timeout=30)
    return (x['id'],r.returncode==0,r.stderr[:120])
with ThreadPoolExecutor(max_workers=16) as ex:
    futs=[ex.submit(decode,p) for p in paths]
    for f in as_completed(futs):
        iid,ok,msg=f.result()
        if not ok: failures.append((iid,'decode:'+msg))
# Peak sample across 80 evenly distributed files.
peaks=[]
for idx in [round(i*(len(items)-1)/79) for i in range(80)]:
    x,p=paths[idx]
    r=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(p),'-af','volumedetect','-f','null','-'],capture_output=True,text=True,timeout=20)
    mm=re.findall(r'max_volume:\s*(-?[0-9.]+) dB',r.stderr)
    if mm: peaks.append(float(mm[-1]))
    else: failures.append((x['id'],'peak_missing'))
if peaks and max(peaks)>-0.5: failures.append(('PEAK_SAMPLE',max(peaks)))
voices={v for x in items for v in x.get('voice_profiles',[])}
disclosure=all(x.get('synthetic') and not x.get('human_recording') for x in items)
if len(voices)<15: failures.append(('ALL','voice_diversity'))
if not disclosure: failures.append(('ALL','disclosure'))
print('files parsed+hash',len(items))
print('full decode','PASS' if not any('decode' in str(y[1]) for y in failures) else 'FAIL')
print('peak sample',len(peaks),'max',max(peaks) if peaks else None)
print('voice profiles',len(voices),'synthetic disclosure',disclosure)
print('AUDIO 500 FULL V46.25:', 'PASS' if not failures else 'FAIL', failures[:12])
assert not failures
