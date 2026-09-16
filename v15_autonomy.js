// PET Quest V15 — Autonomous Guided Session
// Milo orchestrates a short learning session using observable learning signals.
// It recommends the next step, breaks and level progression; navigation remains user-controlled.
const V15_STORE='petQuestV15Autonomy';
const V15_DEFAULT={
  active:false, sessionId:'', startedAt:0, targetMinutes:8, stepIndex:0, stepStartedHistory:0,
  plan:[], events:[], lastSession:null, sessionsCompleted:0, breakShown:false, lastNudge:'',
  baselineHelp:0, baselineHistory:0
};
let V15=(()=>{try{return {...V15_DEFAULT,...JSON.parse(localStorage.getItem(V15_STORE)||'{}')}}catch{return JSON.parse(JSON.stringify(V15_DEFAULT))}})();
function v15Save(){try{localStorage.setItem(V15_STORE,JSON.stringify(V15))}catch{}}
function v15Kid(){return typeof uxMode==='function'&&uxMode()==='kid'&&!(typeof data!=='undefined'&&data.profile?.examProfile==='adult')}
function v15Esc(x){return typeof esc==='function'?esc(String(x??'')):String(x??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
function v15History(){return data.history||[]}
function v15HelpTotal(){try{return Object.values(V14.helpCounts||{}).reduce((a,b)=>a+(+b||0),0)}catch{return 0}}
function v15ElapsedMin(){return V15.startedAt?Math.max(0,(Date.now()-V15.startedAt)/60000):0}
function v15Recent(skill,n=10){return v15History().filter(x=>!skill||x.skill===skill).slice(-n)}
function v15Accuracy(rows){return rows.length?rows.filter(x=>x.correct).length/rows.length:0}
function v15LevelReady(skill){
  const rows=v15Recent(skill,12); if(rows.length<8)return {ready:false,score:0,reason:'Necesitamos algunos intentos más para decidirlo.'};
  const acc=v15Accuracy(rows), helps=Math.max(0,v15HelpTotal()-(V15.baselineHelp||0));
  const stable=acc>=.85, enough=rows.length>=8, lowHelp=helps<=Math.ceil(rows.length*.5);
  return {ready:stable&&enough&&lowHelp,score:Math.round(acc*100),reason:stable?(lowHelp?'Precisión estable y buen nivel de autonomía.':'La precisión es buena; consolidemos con menos ayuda antes de subir.'):'Todavía conviene consolidar esta habilidad.'};
}
function v15WeakSkill(){
  const skills=['reading','listening'];
  return skills.map(skill=>{const r=v15Recent(skill,8);return {skill,n:r.length,acc:r.length?v15Accuracy(r):.65}}).sort((a,b)=>a.acc-b.acc)[0]?.skill||'reading';
}
function v15Plan(){
  const signal=typeof v13Overall==='function'?v13Overall():{id:'balanced'};
  const primary=(signal.id==='focus'||signal.id==='support'||signal.id==='rush')?(state.skill||v15WeakSkill()):v15WeakSkill();
  const other=primary==='reading'?'listening':'reading';
  const focus=signal.focus||'';
  const steps=[
    {id:'warm',icon:'🌱',title:'Calentamiento',skill:primary,level:1,mode:'normal',goal:2,copy:'Dos preguntas tranquilas para entrar en ritmo.'},
    {id:'core',icon:'🎯',title:'Misión principal',skill:primary,level:Math.min(3,Math.max(1,signal.level||1)),mode:(signal.id==='focus'||signal.id==='support')?'fix':'normal',goal:3,copy:focus?`Vamos a reforzar ${focus}.`:'Practica la habilidad que más te conviene hoy.'},
    {id:'switch',icon:'🔄',title:'Cambio de mundo',skill:other,level:1,mode:'normal',goal:2,copy:'Cambiamos de actividad para mantener la atención fresca.'},
    {id:'repair',icon:'🧠',title:'Repara y aprende',skill:primary,level:1,mode:'fix',goal:2,copy:'Volvemos a los errores para convertirlos en aprendizaje.'},
    {id:'finish',icon:'🏁',title:'Cierre',skill:'home',level:1,mode:'normal',goal:0,copy:'Mira lo que lograste y termina con una meta clara.'}
  ];
  const mins=+(V11?.sessionMinutes||data?.profile?.dailyGoal||8);
  if(mins<=5)return steps.filter(x=>['warm','core','finish'].includes(x.id));
  if(mins<=8)return steps.filter(x=>['warm','core','switch','finish'].includes(x.id));
  return steps;
}
function v15Start(){
  V15.active=true;V15.sessionId='s'+Date.now();V15.startedAt=Date.now();V15.targetMinutes=+(V11?.sessionMinutes||8);
  V15.stepIndex=0;V15.plan=v15Plan();V15.events=[];V15.breakShown=false;V15.lastNudge='';
  V15.baselineHelp=v15HelpTotal();V15.baselineHistory=v15History().length;V15.stepStartedHistory=v15History().length;v15Save();
  v15OpenCurrent();
}
function v15Current(){return V15.plan?.[V15.stepIndex]||null}
function v15StepDoneCount(){return Math.max(0,v15History().length-(V15.stepStartedHistory||0))}
function v15Record(type,extra={}){V15.events.push({type,at:new Date().toISOString(),...extra});if(V15.events.length>80)V15.events=V15.events.slice(-80);v15Save()}
function v15OpenCurrent(){
  const step=v15Current(); if(!step){v15Finish();return}
  V15.stepStartedHistory=v15History().length;v15Record('step_open',{step:step.id,skill:step.skill});v15Save();
  if(step.id==='finish'||step.skill==='home'){state.view='home';render();return}
  startSkill(step.skill,step.level||1,step.mode||'normal');
}
function v15Advance(){
  if(!V15.active)return;const step=v15Current();v15Record('step_complete',{step:step?.id,answers:v15StepDoneCount()});
  V15.stepIndex++;v15Save();if(V15.stepIndex>=V15.plan.length)v15Finish();else v15OpenCurrent();
}
function v15Summary(){
  const rows=v15History().slice(V15.baselineHistory||0);const helps=Math.max(0,v15HelpTotal()-(V15.baselineHelp||0));
  const skills={};rows.forEach(x=>{if(!skills[x.skill])skills[x.skill]={n:0,ok:0};skills[x.skill].n++;if(x.correct)skills[x.skill].ok++});
  const accuracy=rows.length?Math.round(v15Accuracy(rows)*100):0;
  const best=Object.entries(skills).sort((a,b)=>(b[1].n?b[1].ok/b[1].n:0)-(a[1].n?a[1].ok/a[1].n:0))[0];
  const needs=Object.entries(skills).sort((a,b)=>(a[1].n?a[1].ok/a[1].n:1)-(b[1].n?b[1].ok/b[1].n:1))[0];
  return {date:new Date().toISOString(),minutes:Math.max(1,Math.round(v15ElapsedMin())),answers:rows.length,accuracy,helps,best:best?.[0]||'',needs:needs?.[0]||'',steps:V15.stepIndex+1};
}
function v15Finish(){
  if(!V15.active)return;V15.lastSession=v15Summary();V15.sessionsCompleted=(V15.sessionsCompleted||0)+1;V15.active=false;v15Record('session_complete',V15.lastSession);v15Save();state.view='home';render();
}
function v15Pause(){V15.active=false;V15.lastNudge='paused';v15Record('session_paused',{step:v15Current()?.id});v15Save();state.view='home';render()}
function v15Recommendation(){
  if(!V15.active)return null;const step=v15Current();const done=v15StepDoneCount();const elapsed=v15ElapsedMin();
  const recent=v15History().slice(-3), errors=recent.filter(x=>!x.correct).length;
  const helps=Math.max(0,v15HelpTotal()-(V15.baselineHelp||0));
  if(!V15.breakShown && elapsed>=Math.max(6,V15.targetMinutes*.8)){return {id:'break',icon:'💧',title:'Pausa corta recomendada',copy:'Has trabajado varios minutos. Mira lejos de la pantalla, mueve el cuerpo y vuelve cuando quieras.',action:'Hacer pausa'}}
  if(errors>=3)return {id:'support',icon:'🛟',title:'Milo propone más ayuda',copy:'Hubo varios tropiezos seguidos. Conviene usar una pista o una mini práctica antes de continuar.',action:'Pedir una pista'};
  if(helps>=4 && done>=2)return {id:'independent',icon:'🌿',title:'Probemos una sin ayuda',copy:'Has usado varias ayudas. Intenta la siguiente pregunta por tu cuenta y luego revisamos juntos.',action:'Seguir por mi cuenta'};
  if(step && step.goal>0 && done>=step.goal)return {id:'next',icon:'✅',title:'Paso completado',copy:`Ya hiciste ${done} actividad${done===1?'':'es'} en “${step.title}”. Puedes seguir al siguiente paso.`,action:'Siguiente paso'};
  return null;
}
function v15TopBar(){
  if(!V15.active||!v15Kid())return;const container=document.querySelector('main.container');if(!container||container.querySelector('.v15-session-bar'))return;
  const step=v15Current(), total=V15.plan.length, pct=Math.round((V15.stepIndex/Math.max(1,total))*100), done=v15StepDoneCount();
  container.insertAdjacentHTML('afterbegin',`<section class="v15-session-bar" aria-label="Sesión guiada por Milo"><div class="v15-session-milo"><img src="assets/mascot.svg" alt="Milo"><div><span class="mission-label">Sesión guiada · ${V15.targetMinutes} min</span><b>${step?.icon||'🦉'} ${v15Esc(step?.title||'Tu sesión')}</b><small>${v15Esc(step?.copy||'Una misión a la vez.')}</small></div></div><div class="v15-session-progress"><span><i style="width:${Math.min(100,pct)}%"></i></span><small>Paso ${Math.min(V15.stepIndex+1,total)} de ${total}${step?.goal?` · ${Math.min(done,step.goal)}/${step.goal} actividades`:''}</small></div><button class="btn btn-ghost mini" data-v15-pause>Guardar y salir</button></section>`);
}
function v15Nudge(){
  if(!V15.active||!v15Kid())return;const n=v15Recommendation();if(!n)return;const host=document.querySelector('.question-card')||document.querySelector('main.container');if(!host||host.querySelector('.v15-nudge'))return;
  host.insertAdjacentHTML(document.querySelector('.question-card')?'afterbegin':'beforeend',`<aside class="v15-nudge ${n.id}" aria-live="polite"><div>${n.icon}</div><div><b>${n.title}</b><p>${n.copy}</p></div><button class="btn btn-soft" data-v15-nudge="${n.id}">${n.action}</button></aside>`);
}
function v15Home(){
  const main=document.querySelector('main.container');if(!main)return;
  if(v15Kid()){
    const target=+(V11?.sessionMinutes||8), signal=typeof v13Overall==='function'?v13Overall():{label:'Ritmo adecuado'};
    const hero=main.querySelector('.v12-hero-scene')||main.querySelector('.v11-adventure')||main.firstElementChild;
    if(hero&&!main.querySelector('.v15-autonomy-home'))hero.insertAdjacentHTML('afterend',`<section class="card v15-autonomy-home"><div class="v15-autonomy-copy"><span class="mission-label">Milo organiza tu camino</span><h2>🦉 Sesión guiada de ${target} minutos</h2><p>Yo te diré qué hacer primero, cuándo cambiar de actividad y cuándo ya hiciste suficiente por hoy.</p><div class="v15-plan-preview"><span>🌱 Calienta</span><span>🎯 Practica</span><span>🔄 Cambia</span><span>🏁 Cierra</span></div></div><button class="btn btn-primary" data-v15-start>▶ Empezar con Milo</button></section>`);
    if(V15.lastSession&&!main.querySelector('.v15-kid-summary')){const s=V15.lastSession;main.insertAdjacentHTML('beforeend',`<section class="card v15-kid-summary"><h2>🌟 Tu última misión</h2><div class="v15-summary-grid"><div><b>${s.answers}</b><small>actividades</small></div><div><b>${s.accuracy}%</b><small>precisión</small></div><div><b>${s.helps}</b><small>ayudas usadas</small></div><div><b>${s.minutes} min</b><small>tiempo</small></div></div><p>${s.accuracy>=80?'¡Buen trabajo! Estás construyendo confianza paso a paso.':'Cada error que revisaste cuenta como aprendizaje. Seguimos poco a poco.'}</p></section>`)}
  } else v15AdultSummary(main);
}
function v15AdultSummary(main){
  if(main.querySelector('.v15-adult-summary'))return;const s=V15.lastSession;const readyR=v15LevelReady('reading'),readyL=v15LevelReady('listening');
  main.insertAdjacentHTML('beforeend',`<section class="card v15-adult-summary"><div class="section-title"><div><h2>📋 Resumen de autonomía</h2><p>Qué hizo el estudiante y qué recomienda Milo para la próxima sesión.</p></div></div>${s?`<div class="v15-summary-grid"><div><b>${s.minutes} min</b><small>duración</small></div><div><b>${s.answers}</b><small>actividades</small></div><div><b>${s.accuracy}%</b><small>precisión</small></div><div><b>${s.helps}</b><small>ayudas</small></div></div><p class="small">Fortaleza observada: <b>${v15Esc(s.best||'—')}</b> · Conviene reforzar: <b>${v15Esc(s.needs||'—')}</b>.</p>`:'<p class="small">Aún no hay una sesión V15 completada.</p>'}<div class="v15-ready-grid"><div><span>Reading</span><b>${readyR.ready?'✅ Listo para subir':'🌱 Consolidando'}</b><small>${readyR.score}% reciente · ${v15Esc(readyR.reason)}</small></div><div><span>Listening</span><b>${readyL.ready?'✅ Listo para subir':'🌱 Consolidando'}</b><small>${readyL.score}% reciente · ${v15Esc(readyL.reason)}</small></div></div><p class="small">“Listo para subir” es una recomendación pedagógica basada en desempeño reciente y uso de ayudas; no reemplaza el criterio del profesor.</p></section>`)
}
function v15Bind(){
  document.querySelector('[data-v15-start]')?.addEventListener('click',v15Start);
  document.querySelector('[data-v15-pause]')?.addEventListener('click',v15Pause);
  document.querySelectorAll('[data-v15-nudge]').forEach(b=>{if(b.dataset.bound)return;b.dataset.bound='1';b.addEventListener('click',()=>{const id=b.dataset.v15Nudge;V15.lastNudge=id;v15Record('nudge_action',{id});if(id==='next')v15Advance();else if(id==='break'){V15.breakShown=true;v15Save();document.querySelector('.v15-nudge')?.remove();toast?.('Pausa guardada. Vuelve cuando estés listo.')}else if(id==='support'){if(typeof v14Show==='function')v14Show('hint')}else document.querySelector('.v15-nudge')?.remove()})});
  const check=document.querySelector('[data-check]');if(check&&!check.dataset.v15Bound){check.dataset.v15Bound='1';check.addEventListener('click',()=>setTimeout(()=>{if(V15.active){v15Record('answer',{skill:state.skill,step:v15Current()?.id});requestAnimationFrame(()=>{v15Nudge();v15Bind()})}},90),true)}
}
function enhanceV15(){
  document.documentElement.classList.toggle('v15-kid',v15Kid());
  if(state.view==='home')v15Home();
  if(V15.active&&v15Kid()){v15TopBar();v15Nudge()}
  v15Bind();
}
const v15RenderBase=render;
render=function(){v15RenderBase();requestAnimationFrame(enhanceV15)};
requestAnimationFrame(enhanceV15);
