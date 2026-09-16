from pathlib import Path
r=Path(__file__).resolve().parent
js=(r/'v26_school_ops.js').read_text(); html=(r/'index.html').read_text(); sw=(r/'sw.js').read_text(); api=(r/'api_server.py').read_text()
checks={
'V26 loaded':'v26_school_ops.js' in html,
'PWA V26':any(f'petquest-v{i}-shell' in sw for i in range(26,40)) and './v26_school_ops.js' in sw,
'create class':'/courses' in js and "p=='/api/courses'" in api,
'enroll':'/enrollments' in js and "p=='/api/enrollments'" in api,
'class intelligence':'/class-intelligence' in js and "p=='/api/class-intelligence'" in api,
'school students':'/school-students' in js and "p=='/api/school-students'" in api,
'group reinforcement':'data-v26-group' in js,
'individual priority':'Prioridad individual' in js,
'common weakness':'debilidad común' in js,
'responsive':'@media(max-width:850px)' in js,
}
bad=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if bad: raise SystemExit('FAILED: '+','.join(bad))
print(f'PET Quest V26 UI QA: PASS — {len(checks)}/{len(checks)}')
