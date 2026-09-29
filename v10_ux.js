// PET Quest V10 — child-first guided UX layer.
const V10UX={
  mode:localStorage.getItem('petQuestUxMode') || ((API.user?.role && API.user.role!=='student')?'adult':'kid'),
  tourStep:0,
  tourOpen:false
};
const UX_SKILL_IMAGES={reading:'assets/reading.svg',listening:'assets/listening.svg',writing:'assets/writing.svg',speaking:'assets/speaking.svg'};
const UX_TOURS={
  kid:[
    ['¡Hola! Soy Milo 👋','Voy contigo paso a paso. No tienes que saber dónde empezar: yo te mostraré una misión cada vez.','assets/mascot.svg'],
    ['1. Mira tu misión','En Inicio verás una sola recomendación principal. Empieza por ahí y deja el resto para después.','assets/reading.svg'],
    ['2. Practica sin miedo','Lee o escucha, elige una respuesta y toca “Siguiente”. Si fallas, la opción se marcará en rojo y podrás volver a intentarlo.','assets/listening.svg'],
    ['3. Reparamos los errores','Tus errores no desaparecen: se convierten en ejercicios de repaso hasta que los domines.','assets/writing.svg'],
    ['4. Mira cómo creces','Ganas XP, logros y progreso. Cuando estés listo, podrás probar un Mock Exam.','assets/speaking.svg']
  ],
  adult:[
    ['Bienvenido al modo Adulto','Esta vista prioriza progreso, tareas, riesgo académico y seguimiento. El niño mantiene una interfaz más simple.','assets/mascot.svg'],
    ['Supervisa sin interrumpir','Usa Progreso, Reportes y Riesgo académico para entender qué necesita refuerzo.','assets/reading.svg'],
    ['Convierte datos en acciones','Los errores, mastery, Writing, Speaking y mocks alimentan recomendaciones y planes de estudio.','assets/writing.svg'],
    ['Acompaña, no resuelvas','La experiencia infantil entrega pistas graduadas y explicaciones; el adulto puede observar el avance sin dar la respuesta.','assets/speaking.svg']
  ]
};

function uxRoleIsAdult(){return ['parent','teacher','school','admin'].includes(API.user?.role||data.profile.role)}
function uxMode(){return V10UX.mode==='adult'?'adult':'kid'}
function setUxMode(mode){V10UX.mode=mode;localStorage.setItem('petQuestUxMode',mode);document.documentElement.classList.toggle('kid-mode',mode==='kid');document.documentElement.classList.toggle('adult-mode',mode==='adult');render()}
function uxMission(){
  const due=dueWords().length,bad=data.history.filter(x=>!x.correct).length,r=readiness();
  if(due)return {title:'Tu misión de hoy: recordar',text:`Tienes ${due} repaso${due===1?'':'s'} listo${due===1?'':'s'}. Son cortos y te ayudarán a recordar mejor.`,action:'review',label:'Hacer mi repaso →'};
  if(bad>=3)return {title:'Tu misión de hoy: reparar',text:`Vamos a convertir ${Math.min(bad,5)} errores en aprendizaje. No pasa nada por equivocarse.`,action:'answers',label:'Reparar mis errores →'};
  if(r<45)return {title:'Tu misión de hoy: Reading nivel 1',text:'Empezamos fácil, con ayuda y explicaciones después de cada respuesta.',go:'reading',label:'Empezar mi misión →'};
  if(pct('listening')<pct('reading'))return {title:'Tu misión de hoy: escuchar',text:'Hoy entrenaremos el oído con una sesión corta de Listening.',go:'listening',label:'Entrenar Listening →'};
  return {title:'Tu misión de hoy: una sesión corta',text:`Tu foco es ${weakFocus()}. Practica 10–15 minutos y luego revisa lo aprendido.`,go:'reading',label:'Comenzar →'};
}
function uxStepState(){
  if(state.checked)return 4;if(state.selected!==null)return 3;return state.skill==='listening'?1:2;
}
function uxStepper(){const cur=uxStepState();const names=state.skill==='listening'?['1 Escucha','2 Lee','3 Elige','4 Aprende']:['1 Lee','2 Piensa','3 Elige','4 Aprende'];return `<div class="v10-stepper">${names.map((n,i)=>`<div class="v10-step ${i+1<cur?'done':i+1===cur?'active':''}">${n}</div>`).join('')}</div>`}
function uxCoachText(){if(state.checked)return state.selected===currentQuestions()[state.idx]?.a?'¡Muy bien! Lee la explicación para recordar por qué funciona.':'Equivocarse sirve para aprender. Mira la explicación y guarda el foco para repasarlo.';if(state.selected!==null)return 'Ya elegiste. Toca “Siguiente” para validar tu respuesta.';if(state.skill==='listening')return 'Primero escucha el audio. Puedes volver a escucharlo antes de responder.';return 'Lee con calma. Busca primero qué te pide la pregunta y después compara las opciones.'}
function uxCoachBlock(text){return `<div class="v10-coach"><img src="assets/mascot.svg" alt="Milo, guía de PET Quest"><div><b>Milo te guía</b><p>${esc(text)}</p></div></div>`}

function enhanceHomeV10(){
  const main=document.querySelector('main.container');if(!main)return;
  const hero=main.querySelector('.hero'); if(!hero)return;
  const m=uxMission(),isKid=uxMode()==='kid';
  const welcome=document.createElement('section');welcome.className='card v10-welcome';welcome.innerHTML=`<div><div class="mission-label">${isKid?'🚀 Misión guiada':'📊 Panel acompañado'}</div><h1>${isKid?`Hola, ${esc(data.profile.name||'explorador')}!`:'Acompañamiento claro, sin invadir la práctica.'}</h1><p>${isKid?'Yo te diré qué hacer primero. Avanza una misión a la vez y celebra cada mejora.':'Alterna entre el modo adulto y la experiencia infantil para validar cómo ve el producto cada tipo de usuario.'}</p><div class="mission-card"><b>${esc(m.title)}</b><span>${esc(m.text)}</span></div><div class="row" style="margin-top:14px">${m.go?`<button class="btn btn-primary" data-ux-go="${m.go}">${esc(m.label)}</button>`:`<button class="btn btn-primary" data-ux-view="${m.action}">${esc(m.label)}</button>`}<button class="btn btn-soft" data-open-tour>${isKid?'¿Cómo funciona?':'Ver recorrido'}</button></div></div><div class="v10-mascot"><img src="assets/mascot.svg" alt="Milo, el guía visual de PET Quest"></div>`;
  main.insertBefore(welcome,hero); hero.style.display='none';
  const title=main.querySelector('.section-title'); if(title&&isKid){title.querySelector('h2').textContent='Elige una aventura';title.querySelector('p').textContent='Si no sabes cuál elegir, usa la misión recomendada de arriba.'}
  main.querySelectorAll('.skill').forEach(btn=>{const id=btn.dataset.go;if(UX_SKILL_IMAGES[id]){btn.classList.add('v10-child');const old=btn.querySelector('.skill-icon');if(old)old.remove();btn.insertAdjacentHTML('afterbegin',`<img class="v10-skill-visual" src="${UX_SKILL_IMAGES[id]}" alt="Ilustración de ${esc(SKILLS[id])}">`)}});
  const portals=main.querySelector('.portal-row');if(portals){const path=document.createElement('section');path.innerHTML=`<div class="section-title"><div><h2>${isKid?'Tu camino PET':'Flujo de acompañamiento'}</h2><p>${isKid?'Siempre sabrás qué viene después.':'Un flujo simple para interpretar y actuar.'}</p></div></div><div class="guided-path">${(isKid?[['1','Entrena','Haz una misión corta'],['2','Comprueba','Recibe feedback'],['3','Repara','Vuelve sobre errores'],['4','Crece','Mira tu progreso'],['5','Simula','Prueba un Mock']]:[['1','Observa','Revisa progreso'],['2','Detecta','Encuentra riesgos'],['3','Acompaña','Asigna refuerzo'],['4','Verifica','Mide evolución']]).map((x,i)=>`<div class="guided-step ${i===0?'current':''}"><div class="step-dot">${x[0]}</div><b>${x[1]}</b><small>${x[2]}</small></div>`).join('')}</div>`;portals.parentNode.insertBefore(path,portals)}
}
function enhancePracticeV10(){const qcard=document.querySelector('.question-card');if(!qcard)return;qcard.insertAdjacentHTML('afterbegin',uxStepper()+uxCoachBlock(uxCoachText()));const side=document.querySelector('.side');if(side&&UX_SKILL_IMAGES[state.skill])side.insertAdjacentHTML('afterbegin',`<img class="v10-side-visual" src="${UX_SKILL_IMAGES[state.skill]}" alt="Ayuda visual de ${esc(SKILLS[state.skill])}">`)}
function enhanceStudioV10(){const qcard=document.querySelector('.question-card');if(!qcard)return;const txt=state.view==='writing'?'Primero entiende la tarea. Después escribe una idea por vez. Al final revisaremos contenido, organización y lenguaje.':'No necesitas sonar perfecto. Responde, da una razón y añade un ejemplo. Puedes escucharte después.';qcard.insertAdjacentHTML('afterbegin',uxCoachBlock(txt))}
function enhanceV10(){
  document.documentElement.classList.toggle('kid-mode',uxMode()==='kid');document.documentElement.classList.toggle('adult-mode',uxMode()==='adult');
  const topbar=document.querySelector('.topbar-inner');if(topbar&&!topbar.querySelector('.ux-mode-switch')){const sw=document.createElement('div');sw.className='ux-mode-switch';sw.innerHTML=`<button class="${uxMode()==='kid'?'active':''}" data-ux-mode="kid">🧒 Niño</button><button class="${uxMode()==='adult'?'active':''}" data-ux-mode="adult">🧑 Adulto</button>`;topbar.insertBefore(sw,topbar.querySelector('.spacer').nextSibling)}
  if(state.view==='home')enhanceHomeV10();if(state.view==='practice')enhancePracticeV10();if(['writing','speaking'].includes(state.view))enhanceStudioV10();
  if(!document.querySelector('.v10-guide-btn'))document.body.insertAdjacentHTML('beforeend','<button class="v10-guide-btn" data-open-tour><span>🦉</span> Guía</button>');
  bindV10();
  const key='petQuestV10TourDone_'+uxMode();if(state.view==='home'&&!localStorage.getItem(key)&&!V10UX.tourOpen){V10UX.tourOpen=true;V10UX.tourStep=0;showTourV10()}
}
function showTourV10(){document.querySelector('.v10-overlay')?.remove();const arr=UX_TOURS[uxMode()],s=arr[V10UX.tourStep];document.body.insertAdjacentHTML('beforeend',`<div class="v10-overlay" role="dialog" aria-modal="true" aria-label="Guía paso a paso"><div class="v10-tour"><div class="v10-tour-head"><img src="assets/mascot.svg" alt="Milo"><button class="tour-close" data-tour-close aria-label="Cerrar guía">×</button></div><img class="v10-tour-art" src="${s[2]}" alt="Ilustración del paso"><h2>${s[0]}</h2><p>${s[1]}</p><div class="tour-progress">${arr.map((_,i)=>`<span class="${i<=V10UX.tourStep?'active':''}"></span>`).join('')}</div><div class="tour-actions"><button class="btn btn-ghost" data-tour-prev ${V10UX.tourStep===0?'disabled':''}>← Anterior</button><button class="btn btn-primary" data-tour-next>${V10UX.tourStep===arr.length-1?(uxMode()==='kid'?'¡Empezar!':'Ir al panel'):'Siguiente →'}</button></div></div></div>`);bindTourV10()}
function closeTourV10(done=false){document.querySelector('.v10-overlay')?.remove();V10UX.tourOpen=false;if(done)localStorage.setItem('petQuestV10TourDone_'+uxMode(),'1')}
function bindTourV10(){document.querySelector('[data-tour-close]')?.addEventListener('click',()=>closeTourV10(true));document.querySelector('[data-tour-prev]')?.addEventListener('click',()=>{V10UX.tourStep=Math.max(0,V10UX.tourStep-1);showTourV10()});document.querySelector('[data-tour-next]')?.addEventListener('click',()=>{const arr=UX_TOURS[uxMode()];if(V10UX.tourStep<arr.length-1){V10UX.tourStep++;showTourV10()}else{closeTourV10(true);if(uxMode()==='kid')startSkill('reading',1);else{state.view='dashboard';render()}}})}
function bindV10(){document.querySelectorAll('[data-ux-mode]').forEach(b=>b.onclick=()=>setUxMode(b.dataset.uxMode));document.querySelectorAll('[data-open-tour]').forEach(b=>b.onclick=()=>{V10UX.tourOpen=true;V10UX.tourStep=0;showTourV10()});document.querySelectorAll('[data-ux-go]').forEach(b=>b.onclick=()=>startSkill(b.dataset.uxGo,1));document.querySelectorAll('[data-ux-view]').forEach(b=>b.onclick=()=>{state.view=b.dataset.uxView;render()})}

const v10RenderBase=render;
render=function(){v10RenderBase();requestAnimationFrame(enhanceV10)};
requestAnimationFrame(enhanceV10);
