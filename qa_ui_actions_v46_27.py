import re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
html=(ROOT/'index.html').read_text()
scripts=[s.split('?')[0] for s in re.findall(r'<script[^>]+src="([^"]+)"',html)]
missing=[s for s in scripts if not (ROOT/s).exists()]
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
# Every field must at least expose id/name/data-* so code can read it.
unaddressed=[]
for f in fields:
    if 'readonly' in f: continue
    if not (re.search(r'\bid=',f) or re.search(r'\bname=',f) or re.search(r'\bdata-[\w-]+',f)): unaddressed.append(f)
checks={
 'loaded_scripts_exist':not missing,
 'buttons_found':len(buttons)>=300,
 'all_active_buttons_addressable':not orph,
 'fields_found':len(fields)>=100,
 'all_fields_addressable':not unaddressed,
 'per_user_listening_state':'stateKey=()=>`${BASE_KEY}_${examProfile()}_u_${window.API?.user?.id||\'anon\'}`' in (ROOT/'v46_11_mock_listening.js').read_text(),
 'progress_badge':'v4612ProgressBadge' in (ROOT/'v46_8_user_progress.js').read_text(),
 'progress_api':'/my-preparation' in (ROOT/'v46_8_user_progress.js').read_text(),
}
# Syntax all loaded JS.
syntax=[]
for s in scripts:
 if (ROOT/s).exists():
  r=subprocess.run(['node','--check',str(ROOT/s)],capture_output=True,text=True)
  if r.returncode: syntax.append((s,r.stderr[:200]))
checks['all_loaded_js_syntax']=not syntax
print('UI ACTION INTEGRITY V46.12')
print('scripts',len(scripts),'buttons',len(buttons),'fields',len(fields),'orphan_buttons',len(orph),'unaddressed_fields',len(unaddressed))
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if missing: print('missing',missing)
if orph: print('orphans',orph[:10])
if unaddressed: print('fields',unaddressed[:10])
if syntax: print('syntax',syntax[:5])
assert all(checks.values())
