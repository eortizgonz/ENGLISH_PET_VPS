from pathlib import Path
import re
root=Path(__file__).parent
js=(root/'v19_reading.js').read_text()
html=(root/'index.html').read_text()
sw=(root/'sw.js').read_text()
app=(root/'app.js').read_text(); v5=(root/'v5_enhancements.js').read_text()
checks={
'V19 script loaded':'v19_reading.js' in html,
'Learning mode':'data-v19-mode="learn"' in js,
'Exam mode':'data-v19-mode="exam"' in js,
'Chunked reading':'chunksFor' in js and 'data-v19-next-chunk' in js,
'Context vocabulary':'vocabFor' in js and 'Vocabulario contextual' in js,
'Clue strategy':'data-v19-clues' in js and 'Busca estas pistas' in js,
'Option elimination':'data-v19-eliminate' in js and 'descartar' in js,
'No immediate explanations in exam':'sin pistas, traducción, descarte guiado ni explicación inmediata' in js,
'32 question exam':'32 preguntas' in js and 'idx<31' in js,
'45 minute timer':'45*60*1000' in js,
'Part analytics':'byPart=[1,2,3,4,5,6]' in js,
'Focus analytics':'byFocus' in js,
'Adult insight':'Reading V19' in js,
'PWA V19':any(f'petquest-v{i}-shell' in sw for i in range(19,40)) and "'./v19_reading.js'" in sw,
'Original content disclaimer':'contenido original' in js.lower(),
}
# Count static reading items in base + V5 should equal 32.
count=len(re.findall(r"\{id:'r\d+'",app))+len(re.findall(r"\{id:'r\d+'",v5))
checks['Reading bank = 32']=count==32
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
print('Reading bank count:',count)
if failed: raise SystemExit('FAILED: '+', '.join(failed))
print(f'PET Quest V19 Reading QA: PASS — {len(checks)}/{len(checks)}')
