from pathlib import Path
import subprocess, json, sys
root=Path(__file__).parent
files=sorted((root/'assets/audio/fidelity').glob('*.mp3'))
checks=[]
checks.append(('15 audio files',len(files)==15))
for f in files:
    p=subprocess.run(['ffprobe','-v','error','-select_streams','a:0','-show_entries','stream=sample_rate,channels,bit_rate','-of','json',str(f)],capture_output=True,text=True)
    ok=p.returncode==0
    if ok:
        d=json.loads(p.stdout)['streams'][0]
        ok=int(d['sample_rate'])==44100 and int(d['channels'])==1 and int(d['bit_rate'])>=120000
    checks.append((f.name,ok))
js=(root/'v40_2_exam_fidelity.js').read_text()
v18=(root/'v18_listening.js').read_text()
checks += [
 ('unlimited v40 default','strictTwoPlay:false' in js and 'sin límite' in js),
 ('optional strict v40','strictTwoPlay' in js and 'strict&&n>=2' in js),
 ('pause restart volume','data-v402-audio-pause' in js and 'data-v402-audio-restart' in js and 'data-v402-audio-volume' in js),
 ('unlimited v18 default','V18.strictTwoPlay=!!V18.strictTwoPlay' in v18 and 'Repetición libre' in v18),
]
for k,v in checks: print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks if not v]
print(f'AUDIO V46.10: {len(checks)-len(failed)}/{len(checks)} PASS')
sys.exit(1 if failed else 0)
