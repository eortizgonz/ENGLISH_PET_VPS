from pathlib import Path
p=Path(__file__).resolve().parent
api=(p/"api_server.py").read_text(); js=(p/"v33_strategy_forecast.js").read_text(); idx=(p/"index.html").read_text(); sw=(p/"sw.js").read_text()
checks={
"forecast GET":"/api/strategy-forecast" in api,
"target POST":"/api/strategy-targets" in api,
"30 60 90":all(x in api for x in ["30:1","60:2","90:3"]),
"confidence":"confidence" in api and "Confianza" in js,
"no promise":"no garantiza resultados futuros" in api,
"capacity":"teacher_hours_week" in api and "Capacidad orientativa" in js,
"annual targets":"strategic_targets" in api and "Meta anual" in js,
"historic impact":"historic_intervention_gain" in api,
"frontend loaded":"v33_strategy_forecast.js" in idx,
"pwa v33":"v33_strategy_forecast.js" in sw and "petquest-v" in sw,
"no student ranking":"ranking" not in js.lower(),
"version":"33.0" in js and "PETQuest/" in api,
}
for k,v in checks.items(): print(("PASS" if v else "FAIL"),k)
assert all(checks.values())
print(f"PET Quest V33 Strategy QA: PASS - {len(checks)}/{len(checks)}")
