(()=>{
  const ORDER=['ACADEMIC','DATABASE','SECURITY','MULTI_TENANT','PRIVACY','EMAIL','AUDIO','BACKUP_RESTORE','DEVICE_MATRIX','LOAD_TEST','PENTEST','PILOT'];
  const $=s=>document.querySelector(s);
  function token(){try{return localStorage.getItem('petQuestToken')||''}catch{return ''}}
  function allowed(){return !!window.API?.user && ['school','admin'].includes(window.API.user.role)}
  function inReports(){return !!window.state && window.state.view==='reports'}
  function cleanup(){document.querySelector('#v46-operational-gate')?.remove()}
  async function mount(){
    cleanup();
    if(!inReports() || !allowed()) return false;
    const host=$('#releaseGateMount');
    if(!host) return false;
    const t=token();
    if(!t) return false;
    const box=document.createElement('section');
    box.id='v46-operational-gate'; box.className='card v46-gate';
    box.innerHTML='<h2>🚦 Production Release Gate</h2><p class="muted">Criterio único de liberación: 12 gates en PASS, CRITICAL ISSUES = 0 y HIGH ISSUES = 0. Si falta evidencia, el estado permanece BLOCKED.</p><div id="v46-gate-body">Cargando...</div>';
    host.replaceChildren(box);
    try{
      const r=await fetch('/api/production-gate',{headers:{Authorization:'Bearer '+t},cache:'no-store'});
      if(r.status===401){cleanup();return false}
      if(r.status===403){cleanup();return false}
      if(!r.ok)throw new Error('HTTP '+r.status);
      const d=await r.json();
      // Re-check state after async response so a navigation cannot leak the panel.
      if(!inReports() || !allowed()){cleanup();return false}
      const body=$('#v46-gate-body'); if(!body)return false;
      const c=d.checks||{};
      const rows=ORDER.map(k=>`<div class="v46-row"><span>${k.replaceAll('_',' ')}</span><b class="${c[k]?'pass':'blocked'}">${c[k]?'PASS':'BLOCKED'}</b></div>`).join('');
      const critical=Number(d.critical_issues||0), high=Number(d.high_issues||0), approved=d.commercial_release==='APPROVED';
      body.innerHTML=`<div class="v46-status ${approved?'pass':'blocked'}">COMMERCIAL_RELEASE = ${d.commercial_release}</div>${rows}<div class="v46-row"><span>CRITICAL ISSUES</span><b class="${critical===0?'pass':'blocked'}">${critical}</b></div><div class="v46-row"><span>HIGH ISSUES</span><b class="${high===0?'pass':'blocked'}">${high}</b></div><p><strong>Bloqueadores:</strong> ${(d.blocked||[]).join(', ')||'ninguno'}</p><p class="muted">Panel administrativo visible solo para School/Admin dentro de Reportes.</p>`;
      return true;
    }catch(e){
      const body=$('#v46-gate-body'); if(body) body.textContent='No fue posible consultar el release gate.';
      return false;
    }
  }
  const style=document.createElement('style');
  style.textContent='.v46-gate{margin:18px 0}.v46-row{display:flex;justify-content:space-between;gap:18px;padding:8px 0;border-bottom:1px solid #ddd}.v46-status{font-size:1.1rem;font-weight:800;padding:10px;border-radius:10px;margin:10px 0}.v46-gate .pass{color:#08783e}.v46-gate .blocked{color:#b42318}';
  document.head.appendChild(style);
  window.PETQuestReleaseGate={mount,cleanup};
})();
