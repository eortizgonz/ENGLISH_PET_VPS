// PET Quest V46.30 - child-friendly self-registration and password recovery UX.
(function(){
  function passwordRules(value){
    const v=String(value||'');
    return {
      length:v.length>=10,
      upper:/[A-Z]/.test(v),
      lower:/[a-z]/.test(v),
      number:/\d/.test(v)
    };
  }
  function passwordRulesHtml(value){
    const r=passwordRules(value);
    const item=(ok,text)=>`<div class="pq-rule ${ok?'ok':''}">${ok?'✓':'○'} ${text}</div>`;
    return `<div class="pq-password-rules">${item(r.length,'10 o más caracteres')}${item(r.upper,'1 letra mayúscula')}${item(r.lower,'1 letra minúscula')}${item(r.number,'1 número')}</div>`;
  }
  function strongLocal(value){const r=passwordRules(value);return Object.values(r).every(Boolean)}
  function randomPassword(){
    const upper='ABCDEFGHJKLMNPQRSTUVWXYZ', lower='abcdefghijkmnopqrstuvwxyz', digits='23456789';
    const all=upper+lower+digits+'!@#$%';
    const pick=s=>s[Math.floor(Math.random()*s.length)];
    let out=pick(upper)+pick(lower)+pick(digits)+'!';
    while(out.length<14)out+=pick(all);
    return out.split('').sort(()=>Math.random()-.5).join('');
  }
  function setPasswordValue(id,value){
    const input=document.getElementById(id); if(!input)return;
    input.value=value; input.dispatchEvent(new Event('input',{bubbles:true})); input.focus();
  }
  function authHeader(title,subtitle){
    return `<div class="pq-auth-brand"><div class="pq-auth-logo">PET</div><div><div class="pq-auth-title">${title}</div><div class="pq-auth-subtitle">${subtitle}</div></div></div>`;
  }

  window.register=function(){
    el(`<div class="app-shell pq-auth-page"><main class="container pq-auth-wrap"><div class="card settings narrow pq-auth-card">
      ${authHeader('Crear mi cuenta','Tu progreso quedará guardado de forma personal.')}
      <div class="pq-step">Paso 1 de 1 · Datos de acceso</div>
      <label><span>Nombre del estudiante</span><input id="registerName" autocomplete="name" maxlength="120" placeholder="Ej.: Sofia"></label>
      <label><span>Usuario</span><input id="registerUsername" autocomplete="username" maxlength="32" placeholder="Ej.: sofia10"><small class="muted">3–32 caracteres: letras, números, punto, guion o _.</small></label><label><span>Correo</span><input id="registerEmail" type="email" autocomplete="email" maxlength="180" placeholder="nombre@correo.com"></label>
      <label><span>Crear contraseña</span><div class="pq-password-row"><input id="registerPassword" type="password" autocomplete="new-password" maxlength="128" placeholder="Crea una contraseña segura"><button type="button" class="btn btn-ghost mini" data-toggle-password="registerPassword" aria-label="Mostrar u ocultar contraseña">Mostrar</button></div></label>
      <div id="registerRules">${passwordRulesHtml('')}</div>
      <button type="button" class="btn btn-soft" data-generate-password="registerPassword">Generar contraseña segura</button>
      <label><span>Repetir contraseña</span><div class="pq-password-row"><input id="registerPassword2" type="password" autocomplete="new-password" maxlength="128" placeholder="Repítela para confirmar"><button type="button" class="btn btn-ghost mini" data-toggle-password="registerPassword2">Mostrar</button></div></label>
      <label class="pq-check"><input id="registerPermission" type="checkbox"><span>Confirmo que esta cuenta se crea con autorización de mi padre, madre, tutor o colegio.</span></label>
      <button class="btn btn-primary pq-auth-primary" data-register>Crear cuenta</button>
      <div id="registerMsg" aria-live="polite"></div>
      <div class="pq-auth-divider"><span>¿Ya tienes una cuenta?</span></div>
      <button class="btn btn-ghost" data-view="login">Iniciar sesión</button>
    </div></main></div>`);
  };

  window.login=function(){
    const demo=['development','test'].includes(API.environment||'')&&API.demoSeedEnabled&&API.demoAccountsAvailable;
    const email=demo?'student@petquest.local':''; const pw=demo?'Student123!':'';
    const demoBox=demo?'<div class="notice"><b>Demo local:</b> student@petquest.local / Student123!</div>':'';
    el(`<div class="app-shell pq-auth-page"><main class="container pq-auth-wrap"><div class="card settings narrow pq-auth-card">
      ${authHeader('Bienvenido a PET Quest','Entra y continúa exactamente donde quedaste.')}
      <label><span>Usuario o correo</span><input id="loginEmail" type="text" value="${email}" autocomplete="username" placeholder="usuario o nombre@correo.com"></label>
      <label><span>Contraseña</span><div class="pq-password-row"><input id="loginPassword" type="password" value="${pw}" autocomplete="current-password"><button type="button" class="btn btn-ghost mini" data-toggle-password="loginPassword">Mostrar</button></div></label>
      <div class="pq-login-actions"><label class="pq-check compact"><input id="rememberEmail" type="checkbox"><span>Recordar mi correo</span></label><button class="pq-link" type="button" data-view="recover">¿Olvidaste tu contraseña?</button></div>
      <button class="btn btn-primary pq-auth-primary" data-login>Entrar</button>
      <div id="loginMsg" aria-live="polite"></div>${demoBox}
      <div class="pq-auth-divider"><span>¿Es tu primera vez?</span></div>
      <button class="btn btn-soft" data-view="register">Crear una cuenta</button>
    </div></main></div>`);
    const remembered=localStorage.getItem('petQuestRememberedEmail');
    if(remembered&&!demo){const e=document.getElementById('loginEmail');if(e)e.value=remembered;const r=document.getElementById('rememberEmail');if(r)r.checked=true}
  };

  window.recover=function(){
    el(`<div class="app-shell pq-auth-page"><main class="container pq-auth-wrap"><div class="card settings narrow pq-auth-card">
      ${authHeader('Recuperar contraseña','Te ayudaremos a crear una nueva contraseña.')}
      <div class="notice">Escribe el correo de tu cuenta. Por seguridad, la respuesta será la misma aunque el correo no exista.</div>
      <label><span>Correo</span><input id="recoverEmail" type="email" autocomplete="email" placeholder="nombre@correo.com"></label>
      <button class="btn btn-primary pq-auth-primary" data-recover>Continuar</button>
      <div id="recoverMsg" aria-live="polite"></div>
      <button class="btn btn-ghost" data-view="login">Volver a iniciar sesión</button>
    </div></main></div>`);
  };

  window.resetPassword=function(){
    const q=new URLSearchParams(location.search); const token=q.get('reset_token')||sessionStorage.getItem('petQuestResetToken')||'';
    el(`<div class="app-shell pq-auth-page"><main class="container pq-auth-wrap"><div class="card settings narrow pq-auth-card">
      ${authHeader('Crear nueva contraseña','Elige una contraseña nueva para proteger tu progreso.')}
      <input id="resetToken" type="hidden" value="${esc(token)}">
      <label><span>Nueva contraseña</span><div class="pq-password-row"><input id="resetPassword" type="password" autocomplete="new-password" maxlength="128"><button type="button" class="btn btn-ghost mini" data-toggle-password="resetPassword">Mostrar</button></div></label>
      <div id="resetRules">${passwordRulesHtml('')}</div>
      <button type="button" class="btn btn-soft" data-generate-password="resetPassword">Generar contraseña segura</button>
      <label><span>Repetir nueva contraseña</span><div class="pq-password-row"><input id="resetPassword2" type="password" autocomplete="new-password" maxlength="128"><button type="button" class="btn btn-ghost mini" data-toggle-password="resetPassword2">Mostrar</button></div></label>
      <button class="btn btn-primary pq-auth-primary" data-reset-password>Guardar nueva contraseña</button>
      <div id="resetMsg" aria-live="polite"></div>
      <button class="btn btn-ghost" data-view="login">Volver</button>
    </div></main></div>`);
  };

  const previousRender=window.render;
  window.render=function(){
    if(state.view==='register')window.register();
    else if(state.view==='recover')window.recover();
    else if(state.view==='resetPassword')window.resetPassword();
    else previousRender();
    window.bind();
  };

  const previousBind=window.bind;
  window.bind=function(){
    previousBind();
    document.querySelectorAll('[data-toggle-password]').forEach(btn=>btn.onclick=()=>{
      const input=document.getElementById(btn.dataset.togglePassword);if(!input)return;
      const show=input.type==='password';input.type=show?'text':'password';btn.textContent=show?'Ocultar':'Mostrar';
    });
    document.querySelectorAll('[data-generate-password]').forEach(btn=>btn.onclick=()=>setPasswordValue(btn.dataset.generatePassword,randomPassword()));
    const rp=document.getElementById('registerPassword');if(rp)rp.oninput=()=>{const box=document.getElementById('registerRules');if(box)box.innerHTML=passwordRulesHtml(rp.value)};
    const reset=document.getElementById('resetPassword');if(reset)reset.oninput=()=>{const box=document.getElementById('resetRules');if(box)box.innerHTML=passwordRulesHtml(reset.value)};
    const reg=document.querySelector('[data-register]');if(reg)reg.onclick=async()=>{
      const m=document.getElementById('registerMsg');const name=document.getElementById('registerName').value.trim();const username=document.getElementById('registerUsername').value.trim();const email=document.getElementById('registerEmail').value.trim();const p1=document.getElementById('registerPassword').value;const p2=document.getElementById('registerPassword2').value;
      if(name.length<2){m.innerHTML='<div class="feedback bad">Escribe el nombre del estudiante.</div>';return}
      if(!/^[A-Za-z0-9][A-Za-z0-9._-]{2,31}$/.test(username)){m.innerHTML='<div class="feedback bad">Crea un usuario de 3 a 32 caracteres usando letras, números, punto, guion o _.</div>';return}
      if(!/^\S+@\S+\.\S+$/.test(email)){m.innerHTML='<div class="feedback bad">Escribe un correo válido.</div>';return}
      if(!strongLocal(p1)){m.innerHTML='<div class="feedback bad">La contraseña todavía no cumple los 4 requisitos.</div>';return}
      if(p1!==p2){m.innerHTML='<div class="feedback bad">Las contraseñas no coinciden. Revísalas e intenta nuevamente.</div>';return}
      if(!document.getElementById('registerPermission').checked){m.innerHTML='<div class="feedback bad">Confirma la autorización de un adulto responsable o del colegio.</div>';return}
      reg.disabled=true;reg.textContent='Creando cuenta…';
      try{
        const r=await apiRequest('/register',{method:'POST',body:{name,username,email,password:p1,confirm_password:p2,profile_mode:'schools',permission_confirmed:true}});
        if(r.token){API.token=r.token;API.user=r.user;API.sessionExpiresAt=r.expires_at||'';localStorage.setItem('petQuestToken',r.token);if(r.expires_at)localStorage.setItem('petQuestSessionExpiresAt',r.expires_at);await apiBootstrap();state.view='home';render();return}
        m.innerHTML='<div class="feedback ok"><b>Cuenta creada.</b> Ya puedes iniciar sesión.</div>';
        setTimeout(()=>{state.view='login';render();const e=document.getElementById('loginEmail');if(e)e.value=email},500);
      }catch(e){const map={email_exists:'Ese correo ya tiene una cuenta. Inicia sesión o recupera la contraseña.',username_or_email_exists:'Ese usuario o correo ya está registrado.',invalid_username:'El usuario no tiene un formato válido.',weak_password:'La contraseña no cumple los requisitos.',permission_required:'Necesitamos confirmar la autorización.'};m.innerHTML=`<div class="feedback bad">${esc(map[e.message]||'No pudimos crear la cuenta. Intenta nuevamente.')}</div>`}
      finally{if(document.body.contains(reg)){reg.disabled=false;reg.textContent='Crear cuenta'}}
    };
    const lg=document.querySelector('[data-login]');if(lg){const inherited=lg.onclick;lg.onclick=async()=>{const remember=document.getElementById('rememberEmail');const email=document.getElementById('loginEmail')?.value.trim()||'';if(remember?.checked)localStorage.setItem('petQuestRememberedEmail',email);else localStorage.removeItem('petQuestRememberedEmail');return inherited?.()}}
    const rc=document.querySelector('[data-recover]');if(rc)rc.onclick=async()=>{
      const m=document.getElementById('recoverMsg');const email=document.getElementById('recoverEmail').value.trim();if(!/^\S+@\S+\.\S+$/.test(email)){m.innerHTML='<div class="feedback bad">Escribe un correo válido.</div>';return}
      rc.disabled=true;try{const r=await apiRequest('/forgot-password',{method:'POST',body:{email}});m.innerHTML='<div class="feedback ok"><b>Solicitud procesada.</b> Revisa tu correo para crear una contraseña nueva.</div>';
        if(r.dev_reset_token){sessionStorage.setItem('petQuestResetToken',r.dev_reset_token);m.innerHTML+='<button class="btn btn-soft" data-open-reset>Continuar en modo local</button>';document.querySelector('[data-open-reset]').onclick=()=>{state.view='resetPassword';render()}}
      }catch(e){
        const msg=e?.message==='api_html_response'
          ? 'La aplicación estaba usando una copia antigua o un servidor incorrecto. Actualiza la página con Ctrl+F5 y vuelve a intentarlo.'
          : (e?.message==='api_timeout' ? 'El servidor tardó demasiado en responder. Verifica que PET Quest siga abierto e intenta nuevamente.' : 'No pudimos procesar la solicitud. Intenta nuevamente.');
        m.innerHTML=`<div class="feedback bad">${esc(msg)}</div>`
      }finally{rc.disabled=false}
    };
    const resetBtn=document.querySelector('[data-reset-password]');if(resetBtn)resetBtn.onclick=async()=>{
      const m=document.getElementById('resetMsg'),token=document.getElementById('resetToken').value,p1=document.getElementById('resetPassword').value,p2=document.getElementById('resetPassword2').value;
      if(!token){m.innerHTML='<div class="feedback bad">El enlace de recuperación no es válido. Solicita uno nuevo.</div>';return}
      if(!strongLocal(p1)){m.innerHTML='<div class="feedback bad">La contraseña todavía no cumple los 4 requisitos.</div>';return}
      if(p1!==p2){m.innerHTML='<div class="feedback bad">Las contraseñas no coinciden.</div>';return}
      resetBtn.disabled=true;try{await apiRequest('/reset-password',{method:'POST',body:{token,password:p1}});sessionStorage.removeItem('petQuestResetToken');history.replaceState({},'',location.pathname);m.innerHTML='<div class="feedback ok"><b>Contraseña actualizada.</b> Ya puedes entrar con tu nueva contraseña.</div><button class="btn btn-primary" data-back-login>Iniciar sesión</button>';document.querySelector('[data-back-login]').onclick=()=>{state.view='login';render()}}catch(e){m.innerHTML='<div class="feedback bad">El enlace venció o ya fue utilizado. Solicita una recuperación nueva.</div>'}finally{resetBtn.disabled=false}
    };
  };

  const params=new URLSearchParams(location.search);if(params.get('reset_token'))state.view='resetPassword';
  window.render();
})();
