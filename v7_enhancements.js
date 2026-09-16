// PET Quest V7 Production Candidate: privacy controls and operational readiness.
API.consents=[]; API.readiness=null;

const v7LoadAdminData=loadAdminData;
loadAdminData=async function(){
  try{
    const [u,s,m,c,r]=await Promise.all([
      apiRequest('/users'),apiRequest('/schools'),apiRequest('/metrics'),apiRequest('/consents'),fetch('/api/ready').then(x=>x.json())
    ]);
    API.users=u.users||[]; API.schools=s.schools||[]; API.metrics=m; API.consents=c.consents||[]; API.readiness=r;
    if(API.user?.role==='admin'){try{API.backups=(await apiRequest('/backups')).backups||[]}catch(e){API.backups=[]}}
    render();
  }catch(e){toast('No se pudo cargar la administración V7')}
};

const v7Admin=admin;
admin=function(){
  v7Admin();
  if(!['school','admin'].includes(API.user?.role))return;
  const main=document.querySelector('main.container'); if(!main)return;
  const students=(API.users||[]).filter(x=>x.role==='student');
  const active=(API.consents||[]).filter(x=>!x.revoked_at);
  const ready=API.readiness||{};
  main.insertAdjacentHTML('beforeend',`<div class="card settings">
    <div class="row between"><div><h2>Privacidad infantil y producción V7</h2><p>Consentimiento de tutor, readiness operacional y controles previos a sincronización.</p></div><span class="badge ${ready.ok?'ok':'bad'}">${ready.ok?'Sistema listo':'Revisar sistema'}</span></div>
    <div class="dashboard-grid four">
      <div class="card"><div class="label">Consentimientos activos</div><div class="big-number">${active.length}</div></div>
      <div class="card"><div class="label">Alumnos</div><div class="big-number">${students.length}</div></div>
      <div class="card"><div class="label">Entorno</div><div class="big-number small-number">${esc(ready.environment||'local')}</div></div>
      <div class="card"><div class="label">DB lista</div><div class="big-number">${ready.database?'Sí':'No'}</div></div>
    </div>
    <h3>Registrar consentimiento del tutor</h3>
    <div class="form-grid">
      <label><span>Alumno</span><select id="consentStudent">${students.map(s=>`<option value="${s.id}">${esc(s.name)} · ${esc(s.email)}</option>`).join('')}</select></label>
      <label><span>Nombre tutor</span><input id="guardianName" placeholder="Nombre y apellido"></label>
      <label><span>Correo tutor</span><input id="guardianEmail" type="email" placeholder="tutor@correo.com"></label>
      <label><span>Versión consentimiento</span><input id="consentVersion" value="2026-08"></label>
    </div>
    <button class="btn btn-primary" data-save-consent>Registrar consentimiento</button><div id="consentMsg"></div>
    ${active.length?`<div class="table-wrap"><table><thead><tr><th>Alumno</th><th>Tutor</th><th>Correo</th><th>Versión</th><th>Fecha</th></tr></thead><tbody>${active.slice(0,20).map(x=>`<tr><td>${esc(x.student_name)}</td><td>${esc(x.guardian_name)}</td><td>${esc(x.guardian_email)}</td><td>${esc(x.consent_version)}</td><td>${esc((x.accepted_at||'').slice(0,10))}</td></tr>`).join('')}</tbody></table></div>`:'<div class="notice">Aún no hay consentimientos registrados. Con el control activo, un alumno no puede sincronizar progreso hasta tener consentimiento vigente.</div>'}
    <div class="notice"><b>Readiness:</b> entorno ${esc(ready.environment||'n/a')} · dev mode ${ready.dev_mode?'activo':'inactivo'} · backup writable ${ready.backup_dir_writable?'sí':'no'}.</div>
  </div>`);
  bind();
};

const v7Bind=bind;
bind=function(){
  v7Bind();
  const sc=document.querySelector('[data-save-consent]');
  if(sc)sc.onclick=async()=>{
    const m=document.getElementById('consentMsg');
    try{
      await apiRequest('/consents',{method:'POST',body:{student_id:+document.getElementById('consentStudent').value,guardian_name:document.getElementById('guardianName').value,guardian_email:document.getElementById('guardianEmail').value,consent_version:document.getElementById('consentVersion').value}});
      m.innerHTML='<div class="feedback ok">Consentimiento registrado y auditado.</div>'; await loadAdminData();
    }catch(e){m.innerHTML=`<div class="feedback bad">No se pudo registrar: ${esc(e.message)}</div>`}
  };
};

render();

// Deep links from transactional email.
(function(){
  const q=new URLSearchParams(location.search);
  const reset=q.get('reset_token'); const verify=q.get('verify_token');
  if(reset){state.view='resetPassword';render();setTimeout(()=>{const i=document.getElementById('resetToken');if(i)i.value=reset},0)}
  if(verify){
    apiRequest('/verify-email',{method:'POST',body:{token:verify}}).then(()=>{toast('Correo verificado correctamente');history.replaceState({},'',location.pathname);}).catch(()=>toast('El enlace de verificación no es válido o expiró'));
  }
})();
