// PET Quest V8 Release Candidate: observability, learning analytics and privacy self-service.
API.observability=null; API.learningAnalytics=null; API.privacyRequests=[];

async function trackV8(event_type, detail={}){
  if(!API.token) return;
  try{await apiRequest('/events',{method:'POST',body:{event_type,...detail}})}catch(e){}
}

const v8LoadAdminData=loadAdminData;
loadAdminData=async function(){
  await v8LoadAdminData();
  if(!API.user||!['school','admin'].includes(API.user.role))return;
  try{
    const jobs=[apiRequest('/observability'),apiRequest('/analytics'),apiRequest('/privacy/requests')];
    const [o,a,p]=await Promise.all(jobs);
    API.observability=o; API.learningAnalytics=a; API.privacyRequests=p.requests||[];
    render();
  }catch(e){toast('Administración V8: algunos indicadores no pudieron cargarse')}
};

function privacyCenter(){
  if(!API.token)return el(`<div class="app-shell">${topBar()}<main class="container">${screenHead('Privacidad','Inicia sesión para administrar tus datos.')}<div class="card empty"><button class="btn btn-primary" data-view="login">Iniciar sesión</button></div></main></div>`);
  el(`<div class="app-shell">${topBar()}<main class="container">${screenHead('Centro de privacidad','Consulta tus derechos y controla los datos sincronizados con PET Quest.')}
  <div class="dashboard-grid">
    <div class="card"><div class="label">Cuenta</div><div class="big-number small-number">${esc(API.user?.email||'')}</div><p>${esc(API.user?.name||'')}</p></div>
    <div class="card"><div class="label">Rol</div><div class="big-number small-number">${esc(API.user?.role||'')}</div><p>Los datos locales del navegador se controlan por separado.</p></div>
    <div class="card"><div class="label">Exportación</div><div class="big-number">JSON</div><p>Cuenta, progreso, consentimientos, eventos y auditoría propia.</p></div>
  </div>
  <div class="card settings">
    <h2>Tus datos</h2><p>Puedes descargar una copia de los datos asociados a tu cuenta en el servidor.</p>
    <div class="row"><button class="btn btn-primary" data-privacy-export>Descargar mis datos</button><button class="btn btn-soft" data-clear-local>Borrar progreso local de este navegador</button></div>
    <div id="privacyMsg"></div>
  </div>
  <div class="card settings">
    <h2>Solicitar eliminación</h2><p>La solicitud se registra para revisión. No se ejecuta un borrado irreversible automático para evitar pérdidas accidentales y porque un colegio puede necesitar validar obligaciones de retención.</p>
    <label><span>Motivo o comentario opcional</span><textarea id="deleteNote" class="textarea" placeholder="Describe tu solicitud..."></textarea></label>
    <button class="btn btn-dark" data-delete-request>Registrar solicitud de eliminación</button><div id="deleteMsg"></div>
  </div></main></div>`);
}

const v8Account=account;
account=function(){
  v8Account();
  const card=document.querySelector('.card.settings');
  if(card&&API.token){card.insertAdjacentHTML('beforeend','<div class="row"><button class="btn btn-soft" data-view="privacy">Centro de privacidad</button></div>');bind();}
};

const v8Admin=admin;
admin=function(){
  v8Admin();
  if(!['school','admin'].includes(API.user?.role))return;
  const main=document.querySelector('main.container');if(!main)return;
  const obs=API.observability?.metrics||{}, ana=API.learningAnalytics||{}, req=API.privacyRequests||[], skill=ana.by_skill||{};
  const rows=Object.entries(skill).map(([k,v])=>`<tr><td>${esc(SKILLS[k]||k)}</td><td>${v.events||0}</td><td>${v.answers||0}</td><td>${v.accuracy||0}%</td><td>${v.minutes||0}</td></tr>`).join('');
  main.insertAdjacentHTML('beforeend',`<div class="card settings">
    <div class="row between"><div><h2>Observabilidad V8</h2><p>Latencia y errores de las últimas ${API.observability?.window||0} solicitudes API del proceso actual.</p></div><button class="btn btn-soft" data-load-admin>Actualizar</button></div>
    <div class="dashboard-grid four"><div class="card"><div class="label">Solicitudes</div><div class="big-number">${obs.requests||0}</div></div><div class="card"><div class="label">Errores</div><div class="big-number">${obs.errors||0}</div></div><div class="card"><div class="label">P50</div><div class="big-number">${obs.p50_ms||0}<small> ms</small></div></div><div class="card"><div class="label">P95</div><div class="big-number">${obs.p95_ms||0}<small> ms</small></div></div></div>
  </div>
  <div class="card settings"><h2>Learning Analytics</h2><p>${ana.active_students||0} alumnos activos · ${ana.events||0} eventos educativos registrados.</p>${rows?`<div class="table-wrap"><table><thead><tr><th>Habilidad</th><th>Eventos</th><th>Respuestas</th><th>Precisión</th><th>Minutos</th></tr></thead><tbody>${rows}</tbody></table></div>`:'<div class="notice">Aún no hay eventos V8. Se registrarán a medida que los alumnos practiquen conectados.</div>'}</div>
  <div class="card settings"><h2>Solicitudes de privacidad</h2>${req.length?`<div class="table-wrap"><table><thead><tr><th>Usuario</th><th>Tipo</th><th>Estado</th><th>Fecha</th></tr></thead><tbody>${req.slice(0,50).map(r=>`<tr><td>${esc(r.name)}<div class="small">${esc(r.email)}</div></td><td>${esc(r.request_type)}</td><td>${esc(r.status)}</td><td>${esc((r.requested_at||'').slice(0,16))}</td></tr>`).join('')}</tbody></table></div>`:'<div class="notice">Sin solicitudes pendientes.</div>'}</div>`);
  const consentCard=[...document.querySelectorAll('.card.settings')].find(x=>x.textContent.includes('Privacidad infantil y producción V7'));
  if(consentCard){consentCard.querySelectorAll('tbody tr').forEach((tr,i)=>{const c=(API.consents||[]).filter(x=>!x.revoked_at)[i];if(c){const td=document.createElement('td');td.innerHTML=`<button class="btn btn-soft mini" data-revoke-consent="${c.student_id}">Revocar</button>`;tr.appendChild(td)}})}
  bind();
};

render=function(){
  clearInterval(timerId);timerId=null;
  ({home,dashboard,practice,answers,writing,speaking,plan,wordbook,mock,settings,parent,teacher,school,account,review,achievements,login,assignments,reports,cms,security,recover,resetPassword,admin,privacy:privacyCenter}[state.view]||home)();
};

const v8Bind=bind;
bind=function(){
  v8Bind();
  const pe=document.querySelector('[data-privacy-export]'); if(pe)pe.onclick=async()=>{const m=document.getElementById('privacyMsg');try{const j=await apiRequest('/privacy/export');const blob=new Blob([JSON.stringify(j,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='petquest-my-data.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);m.innerHTML='<div class="feedback ok">Copia de datos generada.</div>'}catch(e){m.innerHTML='<div class="feedback bad">No se pudo generar la exportación.</div>'}};
  const dr=document.querySelector('[data-delete-request]');if(dr)dr.onclick=async()=>{const m=document.getElementById('deleteMsg');try{const r=await apiRequest('/privacy/delete-request',{method:'POST',body:{note:document.getElementById('deleteNote').value}});m.innerHTML=`<div class="feedback ok">Solicitud registrada #${r.id}${r.already_open?' (ya estaba abierta)':''}.</div>`}catch(e){m.innerHTML='<div class="feedback bad">No se pudo registrar la solicitud.</div>'}};
  const cl=document.querySelector('[data-clear-local]');if(cl)cl.onclick=()=>{if(confirm('¿Borrar el progreso guardado únicamente en este navegador?')){localStorage.removeItem(STORAGE);location.reload()}};
  document.querySelectorAll('[data-revoke-consent]').forEach(b=>b.onclick=async()=>{try{await apiRequest('/consents/revoke',{method:'POST',body:{student_id:+b.dataset.revokeConsent}});toast('Consentimiento revocado');await loadAdminData()}catch(e){toast('No se pudo revocar el consentimiento')}});

  const check=document.querySelector('[data-check]');if(check)check.addEventListener('click',()=>setTimeout(()=>{const h=data.history[data.history.length-1];if(h)trackV8('practice_answer',{skill:h.skill,item_id:h.qid,success:!!h.correct,meta:{focus:h.focus,level:h.level}})},0));
  const mockNext=document.querySelector('[data-mock-next]');if(mockNext)mockNext.addEventListener('click',()=>setTimeout(()=>{const h=data.history[data.history.length-1];if(h?.source==='mock')trackV8('mock_answer',{skill:h.skill,item_id:h.qid,success:!!h.correct,meta:{focus:h.focus,level:h.level}})},0));
  const ew=document.querySelector('[data-eval-writing]');if(ew)ew.addEventListener('click',()=>setTimeout(()=>{const w=data.writing[data.writing.length-1];if(w)trackV8('writing_evaluated',{skill:'writing',item_id:'part-'+w.part,success:(w.score||0)>=14,meta:{score:w.score,words:w.words}})},0));
  const es=document.querySelector('[data-eval-speaking]');if(es)es.addEventListener('click',()=>setTimeout(()=>{const s=data.speaking[data.speaking.length-1];if(s?.score)trackV8('speaking_evaluated',{skill:'speaking',item_id:'part-'+s.part,success:(s.score||0)>=14,meta:{score:s.score,words:s.words||0}})},0));
};

render();
