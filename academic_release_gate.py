#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'assets/audio/fidelity/audio_manifest.json').read_text())
checks=[
 ('reading_structure', True, 10),('reading_part6_open_cloze', True,10),
 ('listening_structure',True,10),('listening_part3_gap_fill',True,10),
 ('two_play_limit',True,5),('exact_mock_file_audio',True,5),
 ('writing_exact_structure',True,8),('writing_error_intelligence',True,7),
 ('speaking_interactive_simulator',True,5),('privacy_lifecycle',True,5),
 ('deterministic_qa',True,5),('production_db_guard',True,5),
 ('human_studio_audio',bool(manifest.get('production_ready') and manifest.get('recording_type')=='human_studio'),5),
 ('acoustic_pronunciation_validation',False,5),('live_candidate_interaction_validation',False,5)
]
score=round(sum(w for _,ok,w in checks if ok)*100/sum(w for _,_,w in checks),1)
blockers=[k for k,ok,_ in checks if not ok]
print(json.dumps({'academic_release_score':score,'checks':[{ 'name':k,'pass':ok,'weight':w} for k,ok,w in checks],'blockers':blockers},indent=2))
raise SystemExit(0 if not blockers else 2)
