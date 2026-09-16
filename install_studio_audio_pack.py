#!/usr/bin/env python3
"""Validate and install a licensed human-studio audio pack into PET Quest.
The package directory must contain audio_manifest.json plus all listed files.
Nothing is installed unless the production validator passes first.
"""
import sys, subprocess, shutil, tempfile
from pathlib import Path
root=Path(__file__).resolve().parent
if len(sys.argv)!=2:
    print('Usage: python install_studio_audio_pack.py /path/to/audio-pack-directory'); raise SystemExit(2)
src=Path(sys.argv[1]).resolve(); manifest=src/'audio_manifest.json'
if not manifest.is_file(): print('Missing audio_manifest.json'); raise SystemExit(2)
validator=root/'validate_studio_audio.py'
r=subprocess.run([sys.executable,str(validator),str(manifest)])
if r.returncode: print('Audio pack NOT installed.'); raise SystemExit(r.returncode)
dst=root/'assets'/'audio'/'fidelity'; backup=root/'assets'/'audio'/'fidelity_reference_backup'
if backup.exists(): shutil.rmtree(backup)
if dst.exists(): shutil.copytree(dst,backup)
tmp=Path(tempfile.mkdtemp(prefix='petquest-audio-',dir=str(root/'assets'/'audio')))
try:
    for p in src.iterdir():
        if p.is_file(): shutil.copy2(p,tmp/p.name)
    if dst.exists(): shutil.rmtree(dst)
    tmp.rename(dst)
finally:
    if tmp.exists(): shutil.rmtree(tmp)
print('STUDIO AUDIO PACK INSTALLED:',dst)
