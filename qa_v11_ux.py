from pathlib import Path
root=Path(__file__).resolve().parent
checks={
 'index loads V11': 'v11_ux.js' in (root/'index.html').read_text(),
 'adventure map': 'Tu mapa de aventuras' in (root/'v11_ux.js').read_text(),
 'avatar choice': 'Elige tu compañero' in (root/'v11_ux.js').read_text(),
 'micro sessions': '¿Cuánto quieres practicar?' in (root/'v11_ux.js').read_text(),
 'rewards': 'Consigue 3 respuestas correctas' in (root/'v11_ux.js').read_text(),
 'celebration': 'v11-celebration' in (root/'v11_ux.js').read_text(),
 'skill worlds': all(x in (root/'v11_ux.js').read_text() for x in ['Bosque de las Historias','Bahía de los Sonidos','Taller de las Ideas','Isla de la Voz','Castillo PET']),
 'service worker includes V11': 'v11_ux.js' in (root/'sw.js').read_text(),
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
raise SystemExit(0 if all(checks.values()) else 1)
