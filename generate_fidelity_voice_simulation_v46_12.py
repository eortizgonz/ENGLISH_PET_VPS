#!/usr/bin/env python3
from pathlib import Path
import json, subprocess, hashlib
import generate_voice_simulation_v46_12 as g
ROOT=Path(__file__).resolve().parent
# Exact V40.2 Part 1/2 ordering: first app.js items, then V5 additions.
rows=[
('lp1_1','Girl','Hi Ben. The football match starts at half past four, not four o’clock. Meet me outside the sports centre at quarter past four.'),
('lp1_2','Woman','The art club is not in room twelve today. Please go to the library on the first floor instead.'),
('lp1_3','Girl','The blue notebook costs three pounds fifty, but the green one is only two pounds ninety.'),
('lp1_4','Boy','The bus leaves at twenty past eight. Please be at the stop ten minutes earlier.'),
('lp1_5','Girl','We planned to meet outside the cinema, but it is raining, so wait for me inside the café next door.'),
('lp1_6','Boy','There are fourteen students in my art class and sixteen in the music class.'),
('lp1_7','Girl','I forgot my water bottle, but I remembered my lunch box and my blue cap.'),
('lp2_1','Boy','I thought the film would be scary, but it was actually very funny. My sister loved it too, especially the ending.'),
('lp2_2','Girl','I usually walk to school, but today my dad drove me because the rain was really heavy.'),
('lp2_3','Boy','We chose the earlier train because the later one arrives after the museum closes.'),
('lp2_4','Girl','The book started slowly, but after chapter three I could not stop reading.'),
('lp2_5','Boy','I was nervous about performing, yet once the music began I forgot about the audience and really enjoyed it.'),
('lp2_6','Girl','I keep a small notebook beside my bed so I can write down new story ideas before I forget them.'),
('lp3_monologue','Teacher','Teacher: Here is the information for Friday’s school visit. Please meet at eight thirty in the school car park. The coach will leave from there shortly afterwards. Everyone should bring a light jacket. Lunch will be provided in the café, and we expect to return at about five fifteen.'),
('lp4_interview','Interviewer | Olivia','Interviewer: Olivia, how did you first start volunteering at the community garden? Olivia: A friend invited me, and I decided to try it. Interviewer: What was difficult at first? Olivia: Remembering all the plant names was the hardest part. Interviewer: What do you enjoy most now? Olivia: Working with different people. I learn something from everyone. Interviewer: Has the garden changed recently? Olivia: Yes. We now run activities for younger children. Interviewer: What happens when the weather is bad? Olivia: We still work, although bad weather can make some jobs harder. Interviewer: And what would you like to do next? Olivia: I would like to help design a new garden area.'),
]

def main():
 out=[]
 for i,(aid,speakers,text) in enumerate(rows,1):
  row={'pack_id':'fidelity','part':1 if aid.startswith('lp1') else 2 if aid.startswith('lp2') else 3 if aid.startswith('lp3') else 4,'audio_id':aid,'target_file':f'assets/audio/fidelity/{aid}.mp3','speakers':speakers,'transcript':text,'questions_covered':'6' if 'monologue' in aid or 'interview' in aid else '1'}
  print(f'[{i}/{len(rows)}] {aid}',flush=True); meta=g.synth(row); out.append(meta)
 (ROOT/'FIDELITY_VOICE_SIMULATION_MANIFEST_V46_12.json').write_text(json.dumps({'version':'46.12','synthetic':True,'human_recording':False,'targets':out},indent=2),encoding='utf-8')
 print('generated',len(out))
if __name__=='__main__':main()
