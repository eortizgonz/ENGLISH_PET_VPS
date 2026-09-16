from pathlib import Path
root=Path(__file__).parent
js=(root/'v18_listening.js').read_text()
idx=(root/'index.html').read_text()
sw=(root/'sw.js').read_text()
checks={
'V18 script loaded':'v18_listening.js' in idx,
'Learning mode':'🌱 Aprender' in js,
'Exam mode':'🏁 Simular examen' in js,
'Vocabulary prelisten':'vocabFor' in js and 'v18-vocab' in js,
'Segmented audio':'splitAudio' in js and 'data-v18-play-segment' in js,
'Speed control':'v18Speed' in js,
'Accent variation':'en-AU' in js and 'en-US' in js and 'en-GB' in js,
'25 question exam':'slice(0,25)' in js,
'Unlimited replay + strict option':'strictTwoPlay' in js and 'Repetición libre' in js and 'n>=2' in js,
'No hints in exam':'sin vocabulario ni pistas' in js,
'Part analytics':'byPart' in js,
'Focus analytics':'byFocus' in js,
'Adult insight':'v18-adult-insight' in js,
'PWA cache V18':'v18_listening.js' in sw and 'petquest-v46-10' in sw,
'Non official wording':'contenido original' in js,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
print(f'PET Quest V18 Listening QA: {len(checks)-len(failed)}/{len(checks)}')
raise SystemExit(1 if failed else 0)
