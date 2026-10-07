from pathlib import Path
base=Path(__file__).parent
idx=(base/'index.html').read_text()
js=(base/'v17_conversation.js').read_text()
sw=(base/'sw.js').read_text()
css=(base/'styles.css').read_text()
checks={
'v17 script loaded':'v17_conversation.js' in idx,
'learn mode':'data-v17-mode="learn"' in js,
'conversation mode':'data-v17-mode="conversation"' in js,
'exam mode':'data-v17-mode="exam"' in js,
'five scenarios':'New school club' in js and 'At the shop' in js and 'Holiday plans' in js and 'Free-time hobbies' in js and 'Plan a celebration' in js,
'voice output':'speechSynthesis' in js,
'voice recognition':'SpeechRecognition' in js,
'free answer':'v17FreeAnswer' in js,
'conversation persistence':'petquest_v17_conversation' in js,
'no hints exam':'sin pistas' in js.lower(),
'official limitation':'otro candidato' in js,
'exam review':'Speaking Exam Review' in js,
'exam unified progress':all(x in js for x in ["source:'v17-speaking-exam'",'data.speaking.push','data.mockAttempts.push','PETQUEST_V468?.refresh']),
'adult insight':'Conversation V17' in js,
'v17 css':'.v17-modebar' in css and '.v17-dialog-card' in css,
'v17 sw':any(f'petquest-v{i}-shell' in sw for i in range(17,40)) and 'v17_conversation.js' in sw,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if failed: raise SystemExit('FAILED: '+', '.join(failed))
print(f'PET Quest V17 Conversation QA: PASS — {len(checks)}/{len(checks)}')
