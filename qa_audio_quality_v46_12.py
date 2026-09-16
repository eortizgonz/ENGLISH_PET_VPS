import json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
mock=json.loads((ROOT/'VOICE_SIMULATION_MANIFEST_V46_12.json').read_text())
fid=json.loads((ROOT/'FIDELITY_VOICE_SIMULATION_MANIFEST_V46_12.json').read_text())
targets=mock['targets']+fid['targets']; checks=[]
def ck(n,c): checks.append((n,bool(c))); print(('PASS' if c else 'FAIL'),n); assert c
ck('60 voice-simulated recordings',len(targets)==60)
seen=set()
for x in targets:
 p=ROOT/x['file']; ck(x['audio_id']+' exists',p.exists() and p.stat().st_size>1000)
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration,bit_rate','-show_entries','stream=codec_name,sample_rate,channels,bit_rate','-of','json',str(p)],text=True))
 st=probe['streams'][0]; fmt=probe['format']; dur=float(fmt.get('duration') or 0); br=int(st.get('bit_rate') or fmt.get('bit_rate') or 0)
 ck(x['audio_id']+' mp3',st.get('codec_name')=='mp3'); ck(x['audio_id']+' 48k',int(st.get('sample_rate') or 0)==48000); ck(x['audio_id']+' mono',int(st.get('channels') or 0)==1); ck(x['audio_id']+' bitrate',br>=160000); ck(x['audio_id']+' duration',dur>1.0)
 r=subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],capture_output=True,text=True); ck(x['audio_id']+' decodes',r.returncode==0)
 seen.add(x['audio_id'])
# Multi-speaker recordings must map to >=2 voice profiles in the mock manifest.
for x in mock['targets']:
 if x.get('segments',1)>1: ck(x['audio_id']+' distinct dialogue voices',len({v.get('profile') for v in x.get('voices',[])})>=2)
ck('mock synthetic disclosure',mock.get('synthetic') is True and mock.get('human_recording') is False)
print(f'AUDIO QUALITY V46.12: {sum(v for _,v in checks)}/{len(checks)} PASS')
