#!/usr/bin/env python3
from pathlib import Path
import json,re,subprocess,sys
ROOT=Path(__file__).resolve().parent
js=(ROOT/'v40_2_exam_fidelity.js').read_text()
checks=[]
def ck(name, cond):
    checks.append((name,bool(cond)))
ck('V40.2 layer', "version:'40.2'" in js)
ck('Reading Part 6 open cloze', 'Parte 6 · Open cloze' in js and 'Escribe UNA palabra' in js and 'data-v402-rtext' in js)
ck('Reading total 32', 'total=32' in js and 'correct:s.correct,total:32' in js)
ck('Reading Part 2 matching', 'Parte 2 · Matching' in js and 'ocho actividades' in js)
ck('Reading Part 4 gapped text', 'Parte 4 · Gapped text' in js and 'ocho frases' in js)
ck('Reading Part 5 MC cloze', 'Parte 5 · Multiple-choice cloze' in js)
ck('Listening Part 3 gap fill', 'Part 3 · Gap fill' in js and "LP3.items" in js)
ck('Listening Part 3 six gaps', len(re.findall(r"\['The (?:visit|coach|group)|\['Students|\['Everyone|\['Lunch",js))>=6)
ck('Listening 25 marks', 'pctn(c,25)' in js and 'correct:c,total:25' in js)
ck('Packaged audio player', 'new Audio(path)' in js and 'speakText(' not in js)
ck('Unlimited replay + optional strict two-play', 'strictTwoPlay' in js and 'sin límite' in js and 'strict&&n>=2' in js)
ck('Speaking 5 criteria', all(x in js for x in ['Grammar & Vocabulary','Discourse Management','Pronunciation','Interactive Communication','Global Achievement']))
ck('Human speaking review', 'revisión humana' in js.lower() and 'Automático ≠ oficial' in js)
ck('SW fidelity layer', 'v40_2_exam_fidelity.js' in (ROOT/'sw.js').read_text())
ck('Current API version', "APP_VERSION='46.10'" in (ROOT/'api_server.py').read_text())
manifest=json.loads((ROOT/'assets/audio/fidelity/audio_manifest.json').read_text())
mp3=list((ROOT/'assets/audio/fidelity').glob('*.mp3'))
ck('15 prerecorded MP3 assets', len(mp3)==15 and len(manifest['files'])==15)
all_audio=True
for p in mp3:
    r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(p)],capture_output=True,text=True)
    try: all_audio &= float(r.stdout.strip())>1
    except: all_audio=False
ck('Audio files decode', all_audio)
for name,ok in checks: print(('PASS' if ok else 'FAIL'),name)
print(f'{sum(ok for _,ok in checks)}/{len(checks)} PASS')
sys.exit(0 if all(ok for _,ok in checks) else 1)
