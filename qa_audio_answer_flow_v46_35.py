#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parent
source = (ROOT / 'v46_18_audio_bank.js').read_text(encoding='utf-8')
index = (ROOT / 'index.html').read_text(encoding='utf-8')
worker = (ROOT / 'sw.js').read_text(encoding='utf-8')
bank = json.loads((ROOT / 'PET_AUDIO_BANK_V46_18.json').read_text(encoding='utf-8'))

def stable_answer_slot(item_id, count):
    value = 2166136261
    for char in 'v46.35:' + str(item_id):
        value = ((value ^ ord(char)) * 16777619) & 0xffffffff
    return value % count

balanced_counts = [0, 0, 0]
for item in bank['items']:
    balanced_counts[stable_answer_slot(item['id'], len(item['options']))] += 1

checks = [
    ('Comprobar button removed', 'data-pqab-check' not in source and '>Comprobar<' not in source),
    ('Next validates the selected answer', "[data-pqab-next]')?.addEventListener('click',validateAndAdvance)" in source),
    ('Next is disabled without a selection and after validation', "S.answer===null||S.checked?'disabled':''" in source),
    ('API string indexes are normalized before validation', "if(/^\\d+$/.test(value))return Number(value)" in source),
    ('Letter answer keys are supported', "value.toUpperCase().charCodeAt(0)-65" in source),
    ('Answer positions are balanced at load time', 'S.manifest=balanceAnswerPositions(S.manifest)' in source),
    ('A B C distribution is balanced across 500 items', min(balanced_counts) >= 150 and max(balanced_counts) <= 180),
    ('Wrong selected answer receives wrong class', "result=chosen&&S.checked?(correct?'correct':'wrong')" in source),
    ('Correct response shows success message', '¡Excelente! Respuesta correcta' in source),
    ('Correct response advances automatically', 'successTimer=setTimeout' in source and ')next()},900)' in source),
    ('Each validation tracks one audio answer event', 'S.checked=true;const ok=isCorrect(q);track(q,ok);renderPanel()' in source),
    ('Asset version updated in page', 'v46_18_audio_bank.js?v=46.35-answer-flow3' in index),
    ('Asset version updated in service worker', 'v46_18_audio_bank.js?v=46.35-answer-flow3' in worker),
]

for name, passed in checks:
    print(('PASS' if passed else 'FAIL'), name)

passed = sum(ok for _, ok in checks)
print(f'AUDIO ANSWER FLOW V46.35: {passed}/{len(checks)} PASS')
sys.exit(0 if passed == len(checks) else 1)
