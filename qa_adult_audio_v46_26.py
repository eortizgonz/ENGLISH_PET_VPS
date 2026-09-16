from pathlib import Path
import json,subprocess,sys
R=Path(__file__).resolve().parent
m=json.loads((R/'ADULT_MOCK_AUDIO_MANIFEST_V46_26.json').read_text())
items=m.get('items',m.get('recordings',[]))
fail=[]; fmt_ok=0; seen=set(); decoded=0
for i,x in enumerate(items):
    rel=x.get('file') or x.get('audio_file') or x.get('path'); p=R/rel if rel else None
    if not rel or not p.exists() or p.stat().st_size<1000: fail.append((i,'missing')); continue
    seen.add(rel)
    cp=subprocess.run(['ffprobe','-v','error','-select_streams','a:0','-show_entries','stream=sample_rate,channels,bit_rate,duration','-of','csv=p=0',str(p)],capture_output=True,text=True,timeout=5)
    if cp.returncode: fail.append((i,'ffprobe')); continue
    vals=cp.stdout.strip().split(',')
    try: sr=int(vals[0]); ch=int(vals[1]); dur=float(vals[2]); br=int(vals[3])
    except Exception: fail.append((i,'parse',cp.stdout)); continue
    if sr!=48000 or ch!=1 or br<150000 or dur<=0: fail.append((i,'format',sr,ch,br,dur)); continue
    fmt_ok+=1
# full decode representative: 2 clips from every pack = 40
for pack in [chr(ord('a')+i) for i in range(20)]:
    subset=[x for x in items if f'pq-adult-{pack}/' in (x.get('file') or x.get('audio_file') or x.get('path') or '')][:2]
    for x in subset:
        rel=x.get('file') or x.get('audio_file') or x.get('path'); p=R/rel
        dec=subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],capture_output=True,text=True,timeout=10)
        if dec.returncode: fail.append((rel,'decode'))
        else: decoded+=1
print('manifest',len(items),'unique',len(seen),'format_ok',fmt_ok,'decoded_sample',decoded)
for f in fail[:20]: print('FAIL',f)
passed=(len(items)==300 and len(seen)==300 and fmt_ok==300 and decoded==40 and not fail)
print('RESULT', 'PASS' if passed else 'FAIL')
sys.exit(0 if passed else 1)
