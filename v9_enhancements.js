// PET Quest V9 — mastery, risk alerts and verified recovery center.
API.mastery=null; API.schoolMastery=null; API.recoveryChecks=[];

async function loadV9Data(){
  if(!API.token)return;
  try{API.mastery=await apiRequest('/mastery/me')}catch(e){}
  if(['teacher','school','admin'].includes(API.user?.role)){try{API.schoolMastery=await apiRequest('/mastery/school')}catch(e){}}
  if(API.user?.role==='admin'){try{API.recoveryChecks=(await apiRequest('/recovery/checks')).checks||[]}catch(e){}}
}

const v9LoadAdminData=loadAdminData;
loadAdminData=async function(){await v9LoadAdminData();await loadV9Data();render();};

const v9Dashboard=dashboard;
dashboard=function(){
  v9Dashboard(); if(!API.mastery)return;
  const main=document.querySelector('main.container');if(!main)return;
  const m=API.mastery, skill=Object.entries(m.skills||{}).map(([k,v])=>`<div class="skill-row"><strong>${esc(SKILLS[k]||k)}</strong><span>${v.accuracy||0}% · dominio ${v.mastery||0}</span></div>`).join('');
  main.insertAdjacentHTML('beforeend',`<div class="card settings"><div class="row between"><div><h2>Mastery V9</h2><p>Tu historial conectado se transforma en señales de dominio y focos de refuerzo.</p></div><div class="score-orb ${m.risk?'risk':''}">${m.accuracy||0}%</div></div>${skill||'<div class="notice">Aún faltan respuestas conectadas para calcular dominio.</div>'}${(m.weak_focus||[]).length?`<h3>Refuerzo prioritario</h3><div class="chips">${m.weak_focus.map(x=>`<span class="chip">${esc(x.focus)} · ${x.mastery}%</span>`).join('')}</div>`:''}</div>`);
};

const v9Admin=admin;
admin=function(){
  v9Admin(); if(!['teacher','school','admin'].includes(API.user?.role))return;
  const main=document.querySelector('main.container');if(!main)return; const sm=API.schoolMastery||{};
  const students=(sm.students||[]).sort((a,b)=>(b.risk-a.risk)||(a.accuracy-b.accuracy));
  main.insertAdjacentHTML('beforeend',`<div class="card settings"><h2>Riesgo académico V9</h2><p>${sm.at_risk||0} alumnos en riesgo entre ${sm.evaluated||0} con evidencia suficiente.</p>${students.length?`<div class="table-wrap"><table><thead><tr><th>Alumno</th><th>Respuestas</th><th>Precisión</th><th>Estado</th><th>Foco prioritario</th></tr></thead><tbody>${students.slice(0,100).map(s=>`<tr><td>${esc(s.name)}</td><td>${s.answers}</td><td>${s.accuracy}%</td><td>${s.risk?'<span class="badge danger">Riesgo</span>':'<span class="badge success">Seguimiento</span>'}</td><td>${esc(s.weak_focus?.[0]?.focus||'—')}</td></tr>`).join('')}</tbody></table></div>`:'<div class="notice">Aún no hay evidencia suficiente.</div>'}</div>`);
  if(API.user?.role==='admin') main.insertAdjacentHTML('beforeend',`<div class="card settings"><h2>Recovery Center V9</h2><p>Un backup no se considera recuperable hasta pasar <code>PRAGMA integrity_check</code>.</p><div class="row"><input id="backupToVerify" class="input" placeholder="Nombre exacto del backup .db"><button class="btn btn-primary" data-verify-backup>Verificar backup</button></div><div id="recoveryMsg"></div>${API.recoveryChecks.length?`<div class="table-wrap"><table><thead><tr><th>Backup</th><th>Integridad</th><th>Resultado</th><th>Fecha</th></tr></thead><tbody>${API.recoveryChecks.slice(0,30).map(x=>`<tr><td>${esc(x.backup_name)}</td><td>${x.ok?'OK':'FALLA'}</td><td>${esc(x.integrity_result||'')}</td><td>${esc((x.checked_at||'').slice(0,16))}</td></tr>`).join('')}</tbody></table></div>`:''}</div>`);
  const privacy=[...document.querySelectorAll('.card.settings')].find(x=>x.textContent.includes('Solicitudes de privacidad'));
  if(privacy){privacy.querySelectorAll('tbody tr').forEach((tr,i)=>{const r=(API.privacyRequests||[])[i];if(r&&r.status==='open'&&r.request_type==='delete'){const td=document.createElement('td');td.innerHTML=`<button class="btn btn-soft mini" data-privacy-resolve="${r.id}" data-action="reject">Rechazar</button> <button class="btn btn-dark mini" data-privacy-resolve="${r.id}" data-action="approve_delete">Anonimizar</button>`;tr.appendChild(td)}})}
  bind();
};

const v9Login=login;
login=function(){v9Login();};

const v9Bind=bind;
bind=function(){
  v9Bind();
  const vb=document.querySelector('[data-verify-backup]');if(vb)vb.onclick=async()=>{const m=document.getElementById('recoveryMsg'),name=document.getElementById('backupToVerify').value.trim();if(!name)return toast('Ingresa el nombre del backup');try{const r=await apiRequest('/recovery/verify',{method:'POST',body:{name}});m.innerHTML=`<div class="feedback ok">Backup verificado: ${esc(r.integrity)}</div>`;await loadAdminData()}catch(e){m.innerHTML='<div class="feedback bad">El backup no pasó la verificación.</div>'}};
  document.querySelectorAll('[data-privacy-resolve]').forEach(b=>b.onclick=async()=>{const destructive=b.dataset.action==='approve_delete';if(destructive&&!confirm('Esto anonimizará la cuenta y eliminará progreso/eventos sincronizados. ¿Continuar?'))return;try{await apiRequest('/privacy/resolve',{method:'POST',body:{request_id:+b.dataset.privacyResolve,action:b.dataset.action}});toast('Solicitud procesada');await loadAdminData()}catch(e){toast('No se pudo procesar la solicitud')}});
};

(async()=>{if(API.token){await loadV9Data();render()}})();
