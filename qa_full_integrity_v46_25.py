import re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
html=(ROOT/'index.html').read_text(errors='ignore')
scripts=[s.split('?')[0] for s in re.findall(r'<script[^>]+src="([^"]+)"',html)]
text='\n'.join((ROOT/s).read_text(errors='ignore') for s in scripts if (ROOT/s).exists())
buttons=re.findall(r'<button\b[^>]*>',text,re.I)
fields=re.findall(r'<(?:input|select|textarea)\b[^>]*>',text,re.I)
orph=[]
for b in buttons:
    if re.search(r'\bdisabled\b',b): continue
    ok='onclick=' in b or 'type="submit"' in b or "type='submit'" in b
    bid=re.search(r'id="([^"]+)"',b)
    if bid and text.count(bid.group(1))>=2: ok=True
    ds=re.findall(r'\b(data-[\w-]+)(?:=|\s|>)',b)
    for d in ds:
        parts=d[5:].split('-'); camel=parts[0]+''.join(x.title() for x in parts[1:])
        if text.count(d)>=2 or f'dataset.{camel}' in text or f"dataset['{camel}']" in text or f'getAttribute("{d}")' in text or f"getAttribute('{d}')" in text: ok=True
    if not ok: orph.append(b)
unaddressed=[]
for f in fields:
    if 'readonly' in f: continue
    if not (re.search(r'\bid=',f) or re.search(r'\bname=',f) or re.search(r'\bdata-[\w-]+',f)): unaddressed.append(f)
checks=[]
def C(name,ok,detail=''):
    checks.append((name,bool(ok),detail)); print(('PASS' if ok else 'FAIL'),name,detail)
C('version_46_25',"APP_VERSION='46.25'" in (ROOT/'api_server.py').read_text())
C('loaded_scripts_exist',all((ROOT/s).exists() for s in scripts),str(len(scripts)))
C('buttons_addressable',len(buttons)>=390 and not orph,f'{len(buttons)} buttons; orphans={len(orph)}')
C('fields_addressable',len(fields)>=120 and not unaddressed,f'{len(fields)} fields; unaddressed={len(unaddressed)}')
app=(ROOT/'app.js').read_text()
C('main_local_store_user_scoped','function userStoreKey()' in app and 'localStorage.setItem(userStoreKey()' in app)
C('writing_draft_user_scoped','petquest_v4625_writing_draft_u_' in app and 'data-save-writing-draft' in app)
for f,needle in [
 ('v43_full_mock_bank.js','_u_${window.API?.user?.id'),
 ('v46_11_mock_listening.js','_u_${window.API?.user?.id'),
 ('v46_18_audio_bank.js','_u_'+"'"),
 ('v46_20_full_mock_mastery.js','_u_${window.API?.user?.id'),
 ('v46_22_practice_diagnostic.js','_u_'+"'"),
 ('v46_23_child_experience.js','_u_'+"'"),
]:
    s=(ROOT/f).read_text()
    C('user_scoped_'+f,('_u_' in s and ('user?.id' in s or 'uid()' in s or 'userId()' in s)))
prog=(ROOT/'v46_8_user_progress.js').read_text()
C('progress_badge_visible','v4612ProgressBadge' in prog and 'Avance ${fmt(p.score)}%' in prog)
C('progress_auto_refresh',"petquest:server-mutated" in prog and 'setInterval' in prog and "version:'46.25'" in prog)
C('mutation_event_from_api',"petquest:server-mutated" in app)
C('anonymous_calibration_button_explicit','id="v4617Save"' in (ROOT/'v46_17_scale_equivalence.js').read_text())
# Every loaded JS syntax-valid.
syntax=[]
for s in scripts:
    if (ROOT/s).exists():
        r=subprocess.run(['node','--check',str(ROOT/s)],capture_output=True,text=True)
        if r.returncode: syntax.append(s)
C('all_loaded_js_syntax',not syntax,str(syntax[:5]))
print(f'FULL INTEGRITY V46.25: {sum(x[1] for x in checks)}/{len(checks)} PASS')
if orph: print('orphans',orph[:10])
if unaddressed: print('unaddressed',unaddressed[:10])
assert all(x[1] for x in checks)
