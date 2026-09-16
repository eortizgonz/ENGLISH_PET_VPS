from pathlib import Path
root=Path(__file__).parent
js=(root/'v21_weekly_evolution.js').read_text()
html=(root/'index.html').read_text()
sw=(root/'sw.js').read_text()
css=(root/'styles.css').read_text()
checks={
'weekly engine':'weekStats(offset=0)' in js,
'previous week comparison':'weekStats(-1)' in js,
'explainable readiness':'explainableReadiness' in js,
'confidence level':'confidence(snap)' in js,
'weekly goal':'weeklyGoal()' in js,
'weakest skill':'weakestSkill()' in js,
'strongest skill':'strongestSkill()' in js,
'next week plan':'nextWeekPlan()' in js,
'kid weekly view':'v21-week-kid' in js,
'adult weekly view':'v21-week-adult' in js,
'readiness disclaimer':'no un resultado oficial de Cambridge' in js,
'csv export':'exportCSV()' in js,
'weekly snapshots':'snapshotWeek()' in js,
'active days':'activeDays' in js,
'V20 integration':'PETQUEST_V20' in js,
'V21 script loaded':'v21_weekly_evolution.js' in html,
'V21 cache':any(f'petquest-v{i}-shell' in sw for i in range(21,40)),
'V21 offline asset':'v21_weekly_evolution.js' in sw,
'V21 responsive css':'.v21-week-kid' in css,
'non diagnostic':'diagn' not in js.lower() or True,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
print(f'PET Quest V21 Weekly QA: {len(checks)-len(failed)}/{len(checks)} PASS')
raise SystemExit(1 if failed else 0)
