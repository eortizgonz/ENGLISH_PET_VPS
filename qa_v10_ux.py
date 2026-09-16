from pathlib import Path
root=Path(__file__).parent
checks={
 'v10 script': 'v10_ux.js' in (root/'index.html').read_text(),
 'kid/adult mode': 'data-ux-mode' in (root/'v10_ux.js').read_text(),
 'guided tour': 'showTourV10' in (root/'v10_ux.js').read_text(),
 'mission engine': 'uxMission' in (root/'v10_ux.js').read_text(),
 'exercise stepper': 'uxStepper' in (root/'v10_ux.js').read_text(),
 'coach guide': 'Milo te guía' in (root/'v10_ux.js').read_text(),
 'mascot image': (root/'assets/mascot.svg').exists(),
 'reading image': (root/'assets/reading.svg').exists(),
 'listening image': (root/'assets/listening.svg').exists(),
 'writing image': (root/'assets/writing.svg').exists(),
 'speaking image': (root/'assets/speaking.svg').exists(),
 'offline assets': 'assets/mascot.svg' in (root/'sw.js').read_text() and 'v10_ux.js' in (root/'sw.js').read_text(),
}
for name,ok in checks.items(): print(('PASS' if ok else 'FAIL'), name)
if not all(checks.values()): raise SystemExit(1)
print('PET Quest V10 UX QA: PASS')
