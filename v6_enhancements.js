// PET Quest V6: account security, school administration and operational controls.
API.users=[]; API.schools=[]; API.metrics=null; API.backups=[];

const v6Top=topBar;
topBar=function(){
  const base=v6Top();
  if(!API.user||!['school','admin'].includes(API.user.role)) return base;
  return base.replace('<button class="role-pill" data-view="account">',`<button class="navlink hide-md" data-view="admin">Administración</button><button class="role-pill" data-view="account">`);
};

function security(){
  el(`<div class="app-shell">${topBar()}<main class="container">${screenHead('Seguridad de cuenta','Cambia tu contraseña y controla tu sesión.')}
  <div class="card settings narrow">
    <label><span>Contraseña actual</span><input id="currentPassword" type="password" autocomplete="current-password"></label>
    <label><span>Nueva contraseña</span><input id="newPassword" type="password" autocomplete="new-password" placeholder="10+ caracteres, mayúscula, minúscula y número"></label>
    <label><span>Repite la nueva contraseña</span><input id="newPassword2" type="password" autocomplete="new-password"></label>
    <button class="btn btn-primary" data-change-password>Actualizar contraseña</button>
    <button class="btn btn-ghost" data-logout>Cerrar sesión</button>
    <div id="securityMsg"></div>
  </div></main></div>`);
}

function recover(){
  el(`<div class="app-shell">${topBar()}<main class="container">${screenHead('Recuperar acceso','Genera un proceso de restablecimiento seguro.')}
  <div class="card settings narrow">
    <label><span>Correo</span><input id="recoverEmail" type="email" placeholder="nombre@colegio.com"></label>
    <button class="btn btn-primary" data-recover>Solicitar recuperación</button>
    <div id="recoverMsg"></div>
    <div class="small">En desarrollo local, el servidor puede mostrar un token de prueba. En producción debe enviarse mediante un proveedor de correo.</div>
  </div></main></div>`);
}

function resetPassword(){
  el(`<div class="app-shell">${topBar()}<main class="container">${screenHead('Restablecer contraseña','Usa el token de recuperación recibido.')}
  <div class="card settings narrow">
    <label><span>Token</span><input id="resetToken" autocomplete="off"></label>
    <label><span>Nueva contraseña</span><input id="resetPassword" type="password" placeholder="10+ caracteres, mayúscula, minúscula y número"></label>
    <button class="btn btn-primary" data-reset-password>Restablecer</button><div id="resetMsg"></div>
  </div></main></div>`);
}

async function loadAdminData(){
  try{
    const [u,s,m]=await Promise.all([apiRequest('/users'),apiRequest('/schools'),apiRequest('/metrics')]);
    API.users=u.users||[]; API.schools=s.schools||[]; API.metrics=m;
    if(API.user?.role==='admin'){try{API.backups=(await apiRequest('/backups')).backups||[]}catch(e){API.backups=[]}}
    render();
  }catch(e){toast('No se pudo cargar la administración')}
}

function admin(){
  const allowed=['school','admin'].includes(API.user?.role);
  if(!allowed) return el(`<div class="app-shell">${topBar()}<main class="container">${screenHead('Administración','Acceso restringido')}<div class="card empty">Inicia sesión como Colegio o Admin.</div></main></div>`);
  const users=API.users||[], schools=API.schools||[], stats=API.metrics?.stats||{};
  el(`<div class="app-shell">${topBar()}<main class="container">${screenHead('Administración V6','Usuarios, colegios, seguridad operacional y respaldo.')}
  <div class="dashboard-grid four">
    <div class="card"><div class="label">Usuarios</div><div class="big-number">${stats.users??users.length}</div></div>
    <div class="card"><div class="label">Estudiantes</div><div class="big-number">${users.filter(x=>x.role==='student').length}</div></div>
    <div class="card"><div class="label">Sesiones activas</div><div class="big-number">${stats.active_sessions??0}</div></div>
    <div class="card"><div class="label">Backups</div><div class="big-number">${API.metrics?.backup_count??0}</div></div>
  </div>
  <div class="card settings">
    <div class="row between"><div><h2>Usuarios</h2><p>Crea cuentas y desactiva accesos sin borrar historial.</p></div><button class="btn btn-soft" data-load-admin>Actualizar</button></div>
    <div class="form-grid"><label><span>Nombre</span><input id="adminName"></label><label><span>Correo</span><input id="adminEmail" type="email"></label><label><span>Rol</span><select id="adminRole"><option value="student">Alumno</option><option value="teacher">Profesor</option><option value="school">Colegio</option>${API.user?.role==='admin'?'<option value="admin">Admin</option>':''}</select></label><label><span>Contraseña temporal</span><input id="adminPassword" type="password" value="Temporary123!"></label></div>
    ${API.user?.role==='admin'?`<label><span>Colegio</span><select id="adminSchool">${schools.map(s=>`<option value="${s.id}">${esc(s.name)}</option>`).join('')}</select></label>`:''}
    <button class="btn btn-primary" data-create-user>Crear usuario</button><div id="adminMsg"></div>
    <div class="table-wrap"><table><thead><tr><th>Nombre</th><th>Rol</th><th>Correo</th><th>Verificado</th><th>Estado</th><th>Acción</th></tr></thead><tbody>${users.map(u=>`<tr><td>${esc(u.name)}</td><td>${esc(u.role)}</td><td>${esc(u.email)}</td><td>${u.verified_at?'Sí':'Pendiente'}</td><td>${u.disabled?'Desactivado':'Activo'}</td><td><button class="btn btn-soft mini" data-toggle-user="${u.id}" data-disabled="${u.disabled?0:1}">${u.disabled?'Activar':'Desactivar'}</button></td></tr>`).join('')}</tbody></table></div>
  </div>
  ${API.user?.role==='admin'?`<div class="card settings"><h2>Colegios y respaldos</h2><div class="form-grid"><label><span>Nuevo colegio</span><input id="schoolName" placeholder="Nombre del colegio"></label><div><span>&nbsp;</span><button class="btn btn-primary" data-create-school>Crear colegio</button></div></div><div class="row"><button class="btn btn-dark" data-backup>Crear backup ahora</button></div><div id="opsMsg"></div>${API.backups.length?`<div class="small">Últimos backups: ${API.backups.slice(0,5).map(x=>esc(x.name)).join(' · ')}</div>`:''}</div>`:''}
  </main></div>`);
}

const v6Account=account;
account=function(){
  v6Account();
  const card=document.querySelector('.card.settings');
  if(card&&API.token){card.insertAdjacentHTML('beforeend','<div class="row"><button class="btn btn-soft" data-view="security">Seguridad de cuenta</button><button class="btn btn-ghost" data-logout>Cerrar sesión</button></div>');bind();}
};

login=function(){const demo=['development','test'].includes(API.environment||'');const email=demo?'student@petquest.local':'';const pw=demo?'Student123!':'';const demoBox=demo?'<div class="notice"><b>Demo local:</b> student@petquest.local / Student123!<br>teacher@petquest.local / Teacher123!<br>school@petquest.local / School123!<br>admin@petquest.local / Admin123!</div>':'';el(`<div class="app-shell">${topBar()}<main class="container">${screenHead('Iniciar sesión','Conecta progreso, colegio, profesor y asignaciones.')}<div class="card settings narrow"><label><span>Correo</span><input id="loginEmail" type="email" value="${email}" autocomplete="username"></label><label><span>Contraseña</span><input id="loginPassword" type="password" value="${pw}" autocomplete="current-password"></label><button class="btn btn-primary" data-login>Entrar</button><button class="btn btn-ghost" data-view="recover">Olvidé mi contraseña</button>${demoBox}<div id="loginMsg"></div></div></main></div>`)};

render=function(){
  clearInterval(timerId);timerId=null;
  ({home,dashboard,practice,answers,writing,speaking,plan,wordbook,mock,settings,parent,teacher,school,account,review,achievements,login,assignments,reports,cms,security,recover,resetPassword,admin}[state.view]||home)();
};

const v6Bind=bind;
bind=function(){
  v6Bind();
  const cp=document.querySelector('[data-change-password]'); if(cp)cp.onclick=async()=>{const m=document.getElementById('securityMsg'),a=document.getElementById('newPassword').value,b=document.getElementById('newPassword2').value;if(a!==b){m.innerHTML='<div class="feedback bad">Las contraseñas no coinciden.</div>';return}try{await apiRequest('/change-password',{method:'POST',body:{current_password:document.getElementById('currentPassword').value,new_password:a}});m.innerHTML='<div class="feedback ok">Contraseña actualizada. Las otras sesiones fueron cerradas.</div>'}catch(e){m.innerHTML=`<div class="feedback bad">No se pudo actualizar: ${esc(e.message)}</div>`}};
  const lo=document.querySelectorAll('[data-logout]');lo.forEach(x=>x.onclick=async()=>{x.disabled=true;try{if(API.token)await apiRequest('/logout',{method:'POST'})}catch(e){}clearAuthSession();state.view='login';render()});const lp=document.getElementById('loginPassword');if(lp)lp.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();document.querySelector('[data-login]')?.click()}};
  const rc=document.querySelector('[data-recover]');if(rc)rc.onclick=async()=>{const m=document.getElementById('recoverMsg');try{const r=await apiRequest('/forgot-password',{method:'POST',body:{email:document.getElementById('recoverEmail').value}});m.innerHTML=`<div class="feedback ok">Solicitud procesada.${r.dev_reset_token?`<br><b>Token local:</b> <code>${esc(r.dev_reset_token)}</code><br><button class="btn btn-soft mini" data-view="resetPassword">Usar token</button>`:''}</div>`;bind()}catch(e){m.innerHTML='<div class="feedback bad">No se pudo procesar.</div>'}};
  const rp=document.querySelector('[data-reset-password]');if(rp)rp.onclick=async()=>{const m=document.getElementById('resetMsg');try{await apiRequest('/reset-password',{method:'POST',body:{token:document.getElementById('resetToken').value,password:document.getElementById('resetPassword').value}});m.innerHTML='<div class="feedback ok">Contraseña restablecida. Ya puedes iniciar sesión.</div>'}catch(e){m.innerHTML=`<div class="feedback bad">No se pudo restablecer: ${esc(e.message)}</div>`}};
  const la=document.querySelector('[data-load-admin]');if(la)la.onclick=loadAdminData;
  const cu=document.querySelector('[data-create-user]');if(cu)cu.onclick=async()=>{const m=document.getElementById('adminMsg');try{const body={name:document.getElementById('adminName').value,email:document.getElementById('adminEmail').value,role:document.getElementById('adminRole').value,password:document.getElementById('adminPassword').value};const school=document.getElementById('adminSchool');if(school)body.school_id=+school.value;const r=await apiRequest('/users',{method:'POST',body});m.innerHTML=`<div class="feedback ok">Usuario creado.${r.dev_verification_token?` Token local de verificación: <code>${esc(r.dev_verification_token)}</code>`:''}</div>`;await loadAdminData()}catch(e){m.innerHTML=`<div class="feedback bad">No se pudo crear: ${esc(e.message)}</div>`}};
  document.querySelectorAll('[data-toggle-user]').forEach(btn=>btn.onclick=async()=>{try{await apiRequest('/users/'+btn.dataset.toggleUser,{method:'PATCH',body:{disabled:+btn.dataset.disabled===1}});await loadAdminData()}catch(e){toast('No se pudo cambiar el estado')}});
  const cs=document.querySelector('[data-create-school]');if(cs)cs.onclick=async()=>{const m=document.getElementById('opsMsg');try{await apiRequest('/schools',{method:'POST',body:{name:document.getElementById('schoolName').value}});m.innerHTML='<div class="feedback ok">Colegio creado.</div>';await loadAdminData()}catch(e){m.innerHTML='<div class="feedback bad">No se pudo crear el colegio.</div>'}};
  const bk=document.querySelector('[data-backup]');if(bk)bk.onclick=async()=>{const m=document.getElementById('opsMsg');try{const r=await apiRequest('/backup',{method:'POST'});m.innerHTML=`<div class="feedback ok">Backup creado: ${esc(r.name)} (${Math.round(r.bytes/1024)} KB)</div>`;await loadAdminData()}catch(e){m.innerHTML='<div class="feedback bad">No se pudo crear el backup.</div>'}};
};

const oldBootstrap=apiBootstrap;
apiBootstrap=async function(){await oldBootstrap();if(API.user&&['school','admin'].includes(API.user.role)&&state.view==='admin')await loadAdminData()};

render();
