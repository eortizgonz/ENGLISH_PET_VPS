#!/usr/bin/env python3
import json, sys
from pathlib import Path
root=Path(__file__).resolve().parent
manifest_path=Path(sys.argv[1]) if len(sys.argv)>1 else root/'assets/audio/fidelity/audio_manifest.json'
m=json.loads(manifest_path.read_text(encoding='utf-8'))
errors=[]
if m.get('recording_type')!='human_studio': errors.append('recording_type must be human_studio')
if not m.get('production_ready'): errors.append('production_ready must be true')
if not m.get('rights_cleared'): errors.append('rights_cleared must be true')
if not m.get('academic_qa_signed_off'): errors.append('academic_qa_signed_off must be true')
files=m.get('files') or []
if len(files)<15: errors.append('manifest must enumerate the production audio set')
for f in files:
    rel = f.get('path','') if isinstance(f,dict) else str(f)
    p = manifest_path.parent/rel
    if not p.is_file() or p.stat().st_size<1000: errors.append(f"missing/invalid audio: {rel}")
if errors:
    print('STUDIO AUDIO VALIDATION: NOT READY')
    for e in errors: print('- '+e)
    raise SystemExit(2)
print('STUDIO AUDIO VALIDATION: PASS')
