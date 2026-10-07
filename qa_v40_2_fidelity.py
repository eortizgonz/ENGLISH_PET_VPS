#!/usr/bin/env python3
from pathlib import Path
import json,re,subprocess,sys,wave
ROOT=Path(__file__).resolve().parent
js=(ROOT/'v40_2_exam_fidelity.js').read_text(encoding='utf-8')
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
ck('Listening learning continue', 'data-v402-lp3-next' in js and 'Continuar a la siguiente lección' in js)
ck('Listening learning persisted', "source:'v40.2-listening-gap-fill'" in js and 'F.listeningChecks[q.id]' in js)
ck('Listening gap fill shown once', 'firstPart3=qs.findIndex' in js and 'state.idx===firstPart3' in js)
ck('Reading and Listening exam back buttons', js.count('screen-head v402-exam-head') >= 2 and js.count('data-view="home"') >= 2)
ck('Exact exams update unified skill history', all(x in js for x in ['readingExamHistory(rec.at)','listeningExamHistory(rec.at)',"source:'v40.2-exact-reading-item'","source:'v40.2-exact-listening-item'",'PETQUEST_V468?.refresh']))
ck('Listening 25 marks', 'pctn(c,25)' in js and 'correct:c,total:25' in js)
ck('Packaged audio player', 'new Audio(path)' in js and 'speakText(' not in js)
ck('Unlimited replay + optional strict two-play', 'strictTwoPlay' in js and 'sin límite' in js and 'strict&&n>=2' in js)
ck('Automatic pronunciation best', 'automaticPronunciationAttempts' in js and 'mejor pronunciación' in js and 'Math.max' in js)
ck('No manual speaking review', 'data-v402-save-speaking' not in js and '<select id="v402_' not in js)
ck('SW fidelity layer', 'v40_2_exam_fidelity.js' in (ROOT/'sw.js').read_text(encoding='utf-8'))
ck('Current API version', "APP_VERSION='46.32-pg'" in (ROOT/'api_server.py').read_text(encoding='utf-8'))
manifest=json.loads((ROOT/'assets/audio/fidelity/audio_manifest.json').read_text(encoding='utf-8'))
active_audio=[ROOT/'assets/audio/fidelity'/name for name in manifest['files']]
ck('15 clean prerecorded WAV assets', len(active_audio)==15 and all(p.suffix=='.wav' and p.exists() for p in active_audio))
all_audio=True
for p in active_audio:
    try:
        with wave.open(str(p),'rb') as wav:
            all_audio &= wav.getnchannels()==1 and wav.getsampwidth()==2 and wav.getframerate()==24000 and wav.getnframes()>24000
    except Exception: all_audio=False
ck('Audio files decode', all_audio)
for name,ok in checks: print(('PASS' if ok else 'FAIL'),name)
print(f'{sum(ok for _,ok in checks)}/{len(checks)} PASS')
sys.exit(0 if all(ok for _,ok in checks) else 1)
