from pathlib import Path
idx=Path('index.html').read_text(); js=Path('v31_executive_review.js').read_text(); sw=Path('sw.js').read_text()
checks={
 'script':'v31_executive_review.js' in idx,
 'monthly':'monthly' in js and 'Mensual' in js,
 'quarterly':'quarterly' in js and 'Trimestral' in js,
 'chart':'<svg' in js and 'Tendencia' in js,
 'no_child_rank':'rankings públicos de estudiantes' in js,
 'print_pdf':'window.print()' in js and 'Guardar PDF' in js,
 'csv':'executive-review.csv' in js,
 'class_teacher':'Cursos y docentes' in js,
 'priorities':'Prioridades para dirección' in js,
 'pwa':"petquest-v" in sw and "./v31_executive_review.js" in sw,
}
for k,v in checks.items():assert v,k
print(f"PET Quest V31 UI QA: {sum(checks.values())}/{len(checks)} PASS")
