from pathlib import Path
base=Path(__file__).parent
idx=(base/'index.html').read_text()
js=(base/'v16_speaking_writing.js').read_text()
sw=(base/'sw.js').read_text()
css=(base/'styles.css').read_text()
checks={
'v16 script loaded':'v16_speaking_writing.js' in idx,
'speaking adventure':'Speaking Adventure' in js,
'model audio':'speechSynthesis' in js,
'speech recognition':'SpeechRecognition' in js,
'pronunciation limitation':'no mide fonemas' in js,
'own answer':'Ahora dilo con tus propias palabras' in js,
'writing builder':'Writing Builder' in js,
'ideas stage':"stage==='ideas'" in js,
'sentences stage':"stage==='sentences'" in js,
'paragraph stage':"stage==='paragraph'" in js,
'final stage':'Tu texto PET' in js,
'draft persistence':'petquest_v16_learning' in js,
'adult insight':'Speaking & Writing V16' in js,
'v16 css':'.v16-two-col' in css,
'v16 sw compatibility':'v16_speaking_writing.js' in sw,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if failed: raise SystemExit('FAILED: '+', '.join(failed))
print(f'PET Quest V16 Learning QA: PASS — {len(checks)}/{len(checks)}')
