#!/usr/bin/env python3
from pathlib import Path
import os, re, sys
ROOT=Path(__file__).resolve().parent
SW=ROOT/'sw.js'
RECOMMENDED_LIMIT=245

def assets_from_sw():
    text=SW.read_text(encoding='utf-8')
    block=text.split('const ASSETS=[',1)[1].split('];',1)[0]
    vals=re.findall(r"['\"]([^'\"]+)['\"]",block)
    out=[]
    for value in vals:
        rel=value.split('?',1)[0]
        if rel.startswith('./'): rel=rel[2:]
        out.append(rel)
    return list(dict.fromkeys(out))

assets=assets_from_sw()
missing=[x for x in assets if not (ROOT/x).is_file()]
longest_rel=max(assets,key=len) if assets else ''
projected=len(str(ROOT))+1+len(longest_rel)
print(f'[PET Quest] Runtime folder: {ROOT}')
print(f'[PET Quest] Projected longest Windows path: {projected} characters')
if os.name=='nt' and projected>=RECOMMENDED_LIMIT:
    print('\nERROR: La ruta de Windows es demasiado larga para una ejecucion confiable.')
    print('Mueve o extrae la carpeta PET directamente en una ruta corta, por ejemplo:')
    print(r'  C:\PET')
    print(r'  C:\Users\TU_USUARIO\Desktop\PET')
    print('Luego ejecuta START_PET_QUEST_POSTGRES_WINDOWS.bat desde esa carpeta.')
    sys.exit(3)
if missing:
    print('\nERROR: El paquete esta incompleto. Faltan archivos requeridos:')
    for x in missing[:40]: print(' -',x)
    if len(missing)>40: print(f' ... y {len(missing)-40} mas')
    print('\nVuelve a extraer el ZIP completo en una ruta corta (recomendado C:\\PET).')
    sys.exit(4)
print(f'[PET Quest] Package integrity: PASS ({len(assets)} runtime assets present)')
sys.exit(0)
