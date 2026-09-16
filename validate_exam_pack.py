#!/usr/bin/env python3
import json,sys
from pathlib import Path
REQ={'reading':{1:('multiple_choice',5),2:('matching',5),3:('multiple_choice',5),4:('gapped_text',5),5:('multiple_choice_cloze',6),6:('open_cloze',6)},'listening':{1:('multiple_choice',7),2:('multiple_choice',6),3:('gap_fill',6),4:('multiple_choice',6)}}
def validate(pack):
    errors=[]
    for skill,parts in REQ.items():
        arr=pack.get(skill,[])
        for part,(kind,count) in parts.items():
            got=[x for x in arr if int(x.get('part',0))==part]
            if len(got)!=count: errors.append(f'{skill} part {part}: expected {count}, got {len(got)}')
            for x in got:
                if x.get('interaction')!=kind: errors.append(f"{skill} part {part} {x.get('id')}: interaction must be {kind}")
                if skill=='reading' and part==6:
                    ans=str(x.get('answer','')).strip()
                    if not ans or ' ' in ans: errors.append(f"{x.get('id')}: open cloze answer must be one word")
        if len(arr)!=sum(v[1] for v in parts.values()): errors.append(f'{skill}: wrong total {len(arr)}')
    return errors
if __name__=='__main__':
    p=Path(sys.argv[1] if len(sys.argv)>1 else 'sample_item_pack_v42.json'); pack=json.loads(p.read_text()); errs=validate(pack)
    print('ITEM PACK VALIDATION:', 'PASS' if not errs else 'FAIL')
    for e in errs: print('-',e)
    raise SystemExit(1 if errs else 0)
