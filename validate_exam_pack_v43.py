#!/usr/bin/env python3
import json,sys,re
from pathlib import Path
REQ={'reading':{1:('multiple_choice',5),2:('matching',5),3:('multiple_choice',5),4:('gapped_text',5),5:('multiple_choice_cloze',6),6:('open_cloze',6)},'listening':{1:('multiple_choice',7),2:('multiple_choice',6),3:('gap_fill',6),4:('multiple_choice',6)}}

def validate(pack):
    errors=[]; warnings=[]; ids=[]; prompts=[]
    for top in ('pack_id','title','license','status','authoring'):
        if top not in pack: errors.append(f'missing {top}')
    if pack.get('license')!='original-petquest-content': warnings.append('license is not the expected original-content label')
    for skill,parts in REQ.items():
        arr=pack.get(skill,[])
        expected_total=sum(v[1] for v in parts.values())
        if len(arr)!=expected_total: errors.append(f'{skill}: expected {expected_total}, got {len(arr)}')
        for item in arr:
            iid=str(item.get('id','')).strip(); prompt=str(item.get('prompt','')).strip()
            if not iid: errors.append(f'{skill}: item without id')
            if iid in ids: errors.append(f'duplicate id {iid}')
            ids.append(iid)
            if not prompt: errors.append(f'{iid}: empty prompt')
            prompts.append(re.sub(r'\s+',' ',prompt.lower()))
        for part,(kind,count) in parts.items():
            got=[x for x in arr if int(x.get('part',0))==part]
            if len(got)!=count: errors.append(f'{skill} part {part}: expected {count}, got {len(got)}')
            for x in got:
                iid=x.get('id','?')
                if x.get('interaction')!=kind: errors.append(f'{iid}: interaction must be {kind}')
                if kind in ('multiple_choice','multiple_choice_cloze'):
                    opts=x.get('options') or []
                    if len(opts)<3: errors.append(f'{iid}: at least 3 options required')
                    norm=[str(o).strip().casefold() for o in opts]
                    if len(set(norm))!=len(norm): errors.append(f'{iid}: duplicate options')
                    if not isinstance(x.get('answer'),int) or not (0<=x['answer']<len(opts)): errors.append(f'{iid}: invalid option answer index')
                if kind in ('matching','gapped_text'):
                    opts=x.get('options') or []
                    keys=[o.get('key') for o in opts if isinstance(o,dict)]
                    if len(keys)<8: errors.append(f'{iid}: expected at least 8 keyed options')
                    if x.get('answer') not in keys: errors.append(f'{iid}: answer not found in option keys')
                if skill=='reading' and part==6:
                    ans=str(x.get('answer','')).strip()
                    if not ans or len(ans.split())!=1 or not re.fullmatch(r"[A-Za-z]+(?:['-][A-Za-z]+)?",ans): errors.append(f'{iid}: open cloze answer must be one word')
                    if '___' not in str(x.get('prompt','')): errors.append(f'{iid}: open cloze prompt must contain ___')
                if skill=='listening':
                    if not str(x.get('audio_id','')).strip(): errors.append(f'{iid}: missing audio_id')
                    if not str(x.get('transcript','')).strip(): errors.append(f'{iid}: missing authoring transcript')
                    if part==3:
                        accepted=x.get('accepted_answers') or [x.get('answer')]
                        if not any(str(a or '').strip() for a in accepted): errors.append(f'{iid}: gap fill has no accepted answer')
    # content overlap within pack
    dup_prompts={p for p in prompts if prompts.count(p)>1}
    if dup_prompts: errors.append(f'duplicate prompts within pack: {len(dup_prompts)}')
    auth=pack.get('authoring') or {}
    if auth.get('external_academic_signoff') is not True: warnings.append('external academic sign-off pending')
    if auth.get('studio_audio_ready') is not True: warnings.append('studio audio pending; Listening must not be released as exact mock')
    return errors,warnings

if __name__=='__main__':
    targets=[Path(x) for x in sys.argv[1:]] or list(Path('exam_packs').glob('pq-mock-*.json'))
    failed=False
    for p in targets:
        pack=json.loads(p.read_text(encoding='utf-8')); errs,warns=validate(pack)
        print(f'{p.name}:', 'PASS' if not errs else 'FAIL', f'({len(warns)} warnings)')
        for e in errs: print(' ERROR:',e)
        for w in warns: print(' WARN :',w)
        failed=failed or bool(errs)
    raise SystemExit(1 if failed else 0)
