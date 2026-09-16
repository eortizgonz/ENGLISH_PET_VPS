// PET Quest V23 — Healthy Motivation & Retention
(()=>{
'use strict';
const KEY='petQuestV23Retention';
const DEF={weeklyGoal:3,chosenGoal:'balanced',lastCelebratedWeek:'',rewardPoints:0,returnCount:0,version:'23.0'};
let V23;try{V23=Object.assign({},DEF,JSON.parse(localStorage.getItem(KEY)||'{}'))}catch(_){V23={...DEF}}
const save=()=>{try{localStorage.setItem(KEY,JSON.stringify(V23))}catch(_){}};
const E=s=>typeof esc==='function'?esc(String(s??'')):String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const kid=()=>typeof uxMode==='function'?uxMode()==='kid':document.documentElement.classList.contains('v15-kid');
const DAY=86400000;
function dayKey(d){const x=new Date(d);if(Number.isNaN(x.getTime()))return'';return x.toISOString().slice(0,10)}
function today0(){const d=new Date();d.setHours(0,0,0,0);return d}
function addDays(d,n){const x=new Date(d);x.setDate(x.getDate()+n);return x}
function monday(d=today0()){const x=new Date(d);x.setDate(x.getDate()-((x.getDay()+6)%7));return x}
function allActivity(){
 const s=new Set();
 (data?.history||[]).forEach(x=>{const k=dayKey(x.date);if(k)s.add(k)});
 (window.PETQUEST_V20?.state?.history||[]).forEach(x=>{const k=dayKey(x.at);if(k)s.add(k)});
 return [...s].sort();
}
function lastActivityDate(){const a=allActivity();return a.length?new Date(a[a.length-1]+'T00:00:00'):null}
function daysSinceLast(){const d=lastActivityDate();return d?Math.max(0,Math.floor((today0()-d)/DAY)):null}
function weekActivity(offset=0){const start=addDays(monday(),offset*7),end=addDays(start,7);return allActivity().filter(k=>{const d=new Date(k+'T00:00:00');return d>=start&&d<end})}
function journeysThisWeek(){const start=monday(),end=addDays(start,7);return (window.PETQUEST_V20?.state?.history||[]).filter(x=>{const d=new Date(x.at||0);return d>=start&&d<end})}
function healthyRhythm(){
 const days=weekActivity(0).length,prev=weekActivity(-1).length,gap=daysSinceLast();
 let label='Empezando',icon='🌱',copy='Una sesión corta ya cuenta como progreso.';
 if(days>=4){label='Ritmo sólido';icon='🌟';copy='Has encontrado un ritmo constante. Un día de descanso también es parte del aprendizaje.'}
 else if(days>=2){label='Buen ritmo';icon='🌿';copy='Vas construyendo constancia sin necesidad de estudiar todos los días.'}
 else if(gap!=null&&gap>=3){label='Bienvenido de vuelta';icon='💛';copy='No perdiste nada. Retoma con una misión corta y sigue desde donde estabas.'}
 else if(prev>=3&&days===0){label='Semana nueva';icon='🪴';copy='Tu progreso anterior sigue contigo. Empieza suave cuando quieras.'}
 return{days,prev,gap,label,icon,copy};
}
function goalProgress(){const done=journeysThisWeek().length,goal=Math.max(2,Math.min(5,+V23.weeklyGoal||3));return{done,goal,pct:Math.min(100,Math.round(done/goal*100))}}
function retentionSignal(){
 const gap=daysSinceLast(),gp=goalProgress(),acts=weekActivity(0).length;
 if(gap==null)return{level:'new',label:'Empezando',copy:'Todavía no hay historial. Una misión breve es suficiente para comenzar.',action:'start'};
 if(gap>=7)return{level:'return',label:'Regreso amable',copy:`Han pasado ${gap} días desde la última actividad. Recomendamos una misión de 5 minutos, sin recuperar tareas atrasadas.`,action:'short'};
 if(gap>=3)return{level:'soft',label:'Ritmo en pausa',copy:'Conviene volver con una actividad fácil o una fortaleza para recuperar confianza.',action:'easy'};
 if(gp.done>=gp.goal)return{level:'done',label:'Meta cumplida',copy:'La meta semanal ya está completa. Lo siguiente puede ser mantenimiento o descanso.',action:'rest'};
 if(acts>=2)return{level:'steady',label:'Buen ritmo',copy:'La frecuencia actual es saludable. Mantén sesiones cortas y variadas.',action:'continue'};
 return{level:'normal',label:'En marcha',copy:'Una ruta más esta semana ayudará a consolidar el hábito.',action:'continue'};
}
const GOALS={balanced:{icon:'🧭',title:'Equilibrio',copy:'Practicar varias habilidades sin sobrecargar.'},confidence:{icon:'🌟',title:'Confianza',copy:'Empezar por una fortaleza y terminar con un reto pequeño.'},repair:{icon:'🧠',title:'Reparar errores',copy:'Dar prioridad a errores recientes y volver a intentarlos.'},speak:{icon:'💬',title:'Hablar más',copy:'Dar más espacio a Speaking y respuestas propias.'}};
function calendarDays(){
 const start=addDays(today0(),-6),active=new Set(allActivity());
 return Array.from({length:14},(_,i)=>{const d=addDays(start,i),k=dayKey(d),future=d>today0(),isToday=k===dayKey(today0());return{d,k,active:active.has(k),future,isToday,label:['D','L','M','M','J','V','S'][d.getDay()]}})
}
function maybeReward(){const gp=goalProgress(),wk=dayKey(monday());if(gp.done>=gp.goal&&V23.lastCelebratedWeek!==wk){V23.lastCelebratedWeek=wk;V23.rewardPoints=(+V23.rewardPoints||0)+10;save();return true}return false}
function kidPanel(){
 const r=healthyRhythm(),gp=goalProgress(),sig=retentionSignal(),goal=GOALS[V23.chosenGoal]||GOALS.balanced,cal=calendarDays();
 const welcome=(r.gap!=null&&r.gap>=3)?`<div class="v23-return"><span>💛</span><div><b>Qué bueno verte otra vez</b><p>No tienes que recuperar días. Empecemos con algo corto.</p></div><button class="btn btn-primary" data-v23-short>Hacer 5 min</button></div>`:'';
 return `<section class="card v23-kid"><div class="v23-head"><div><span class="mission-label">V23 · Ritmo saludable</span><h2>${r.icon} ${E(r.label)}</h2><p>${E(r.copy)}</p></div><div class="v23-points"><b>${+V23.rewardPoints||0}</b><span>semillas</span></div></div>${welcome}<div class="v23-goal"><div class="row between"><div><b>Mi meta semanal</b><small>${gp.done}/${gp.goal} rutas · sin castigo por descansar</small></div><button class="btn btn-soft" data-v23-goal>${gp.goal} por semana</button></div><div class="v23-bar"><i style="width:${gp.pct}%"></i></div></div><div class="v23-calendar">${cal.map(x=>`<div class="${x.active?'active ':''}${x.isToday?'today ':''}${x.future?'future':''}"><span>${x.label}</span><b>${x.d.getDate()}</b><i>${x.active?'★':x.future?'':'·'}</i></div>`).join('')}</div><div class="v23-choice"><div><span>${goal.icon}</span><div><b>Objetivo elegido: ${E(goal.title)}</b><p>${E(goal.copy)}</p></div></div><button class="btn btn-soft" data-v23-choose>Cambiar</button></div><div class="v23-signal ${sig.level}"><b>${E(sig.label)}</b><p>${E(sig.copy)}</p></div><div class="v23-actions"><button class="btn btn-primary" data-v23-start>▶ Continuar mi camino</button><button class="btn btn-soft" data-v23-rest>🌿 Hoy quiero descansar</button></div><p class="tiny muted center">Descansar no borra progreso ni rompe ninguna racha.</p></section>`;
}
function adultPanel(){
 const r=healthyRhythm(),gp=goalProgress(),sig=retentionSignal(),a=allActivity(),last=a.length?a[a.length-1]:'—';
 return `<section class="card v23-adult"><span class="mission-label">V23 · Motivación y retención saludable</span><h2>🌱 Ritmo de aprendizaje</h2><div class="v23-adult-grid"><div><span>Días activos</span><b>${r.days}</b><small>esta semana</small></div><div><span>Meta</span><b>${gp.done}/${gp.goal}</b><small>rutas</small></div><div><span>Última actividad</span><b>${E(last)}</b><small>${r.gap==null?'sin historial':r.gap+' días'}</small></div><div><span>Señal de continuidad</span><b>${E(sig.label)}</b><small>no diagnóstica</small></div></div><div class="v23-adult-note"><b>Qué recomendamos</b><p>${E(sig.copy)}</p></div><div class="v23-principles"><span>✓ sin “racha perdida”</span><span>✓ sin recuperar tareas atrasadas</span><span>✓ regreso gradual</span><span>✓ descanso permitido</span></div></section>`;
}
function render23(){if(state.view!=='home')return;const main=document.querySelector('main.container');if(!main||main.querySelector('.v23-kid,.v23-adult'))return;const target=main.querySelector('.v22-intelligence')||main.querySelector('.v21-week-kid')||main.firstElementChild;target?.insertAdjacentHTML('afterend',kid()?kidPanel():adultPanel());bind23();if(maybeReward()&&kid()&&typeof toast==='function')toast('🌟 Meta semanal cumplida: +10 semillas')}
function chooseGoal(){const keys=Object.keys(GOALS),cur=Math.max(0,keys.indexOf(V23.chosenGoal));V23.chosenGoal=keys[(cur+1)%keys.length];save();render()}
function cycleWeeklyGoal(){V23.weeklyGoal=(+V23.weeklyGoal||3)>=5?2:(+V23.weeklyGoal||3)+1;save();render()}
function startShort(){try{const old=data?.profile?.dailyGoal;data.profile=data.profile||{};data.profile.dailyGoal=5;if(window.PETQUEST_V20?.startJourney)window.PETQUEST_V20.startJourney();else if(typeof go==='function')go('reading');data.profile.dailyGoal=old??10}catch(_){if(typeof go==='function')go('reading')}}
function startPath(){try{const j=window.PETQUEST_V20;if(j?.state?.paused&&j?.state?.plan?.length)j.resumeJourney();else if(j?.startJourney)j.startJourney();else if(typeof go==='function')go('reading')}catch(_){if(typeof go==='function')go('reading')}}
function restToday(){try{localStorage.setItem('petQuestV23RestDay',dayKey(today0()));if(typeof toast==='function')toast('🌿 Descanso guardado. Tu progreso sigue intacto.')}catch(_){}}
function bind23(){document.querySelector('[data-v23-goal]')?.addEventListener('click',cycleWeeklyGoal);document.querySelector('[data-v23-choose]')?.addEventListener('click',chooseGoal);document.querySelector('[data-v23-short]')?.addEventListener('click',startShort);document.querySelector('[data-v23-start]')?.addEventListener('click',startPath);document.querySelector('[data-v23-rest]')?.addEventListener('click',restToday)}
const css=`
.v23-kid,.v23-adult{margin-top:16px}.v23-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}.v23-head h2{margin:.25rem 0}.v23-points{min-width:86px;text-align:center;padding:10px;border-radius:18px;background:linear-gradient(135deg,#fff8d8,#fff)}.v23-points b{font-size:1.7rem;display:block}.v23-points span{font-size:.78rem}.v23-return{display:flex;gap:12px;align-items:center;padding:14px;margin:14px 0;border-radius:18px;background:#fff7e8}.v23-return>span{font-size:2rem}.v23-return div{flex:1}.v23-return p,.v23-choice p,.v23-signal p,.v23-adult-note p{margin:.25rem 0 0}.v23-goal{padding:14px;border:1px solid rgba(80,80,140,.13);border-radius:18px}.v23-goal small{display:block;margin-top:3px}.v23-bar{height:12px;background:#ececf6;border-radius:999px;margin-top:10px;overflow:hidden}.v23-bar i{display:block;height:100%;background:linear-gradient(90deg,#64c987,#ffd66b);border-radius:inherit}.v23-calendar{display:grid;grid-template-columns:repeat(7,1fr);gap:7px;margin:14px 0}.v23-calendar div{min-height:65px;border-radius:14px;background:#f6f6fb;display:flex;flex-direction:column;align-items:center;justify-content:center}.v23-calendar span{font-size:.72rem}.v23-calendar b{font-size:1rem}.v23-calendar i{font-style:normal;min-height:18px}.v23-calendar .active{background:#e9f8ee}.v23-calendar .active i{color:#37a45c}.v23-calendar .today{outline:2px solid #7777df}.v23-calendar .future{opacity:.45}.v23-choice{display:flex;justify-content:space-between;gap:12px;align-items:center;background:#f5f3ff;padding:14px;border-radius:18px}.v23-choice>div{display:flex;gap:10px;align-items:center}.v23-choice>div>span{font-size:1.7rem}.v23-signal{margin:12px 0;padding:12px 14px;border-radius:16px;background:#eef7ff}.v23-signal.return,.v23-signal.soft{background:#fff3e8}.v23-signal.done{background:#eaf8ed}.v23-actions{display:flex;gap:10px;flex-wrap:wrap}.v23-adult-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:12px 0}.v23-adult-grid div{padding:12px;border-radius:15px;background:#f7f7fb}.v23-adult-grid span,.v23-adult-grid small{display:block;font-size:.78rem}.v23-adult-grid b{display:block;font-size:1.08rem;margin:3px 0}.v23-adult-note{padding:14px;border-radius:16px;background:#eef7ff}.v23-principles{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}.v23-principles span{padding:7px 9px;border-radius:999px;background:#f1f1f6;font-size:.8rem}@media(max-width:700px){.v23-adult-grid{grid-template-columns:repeat(2,1fr)}.v23-calendar{gap:4px}.v23-calendar div{min-height:58px}.v23-return{align-items:flex-start;flex-wrap:wrap}.v23-actions .btn{width:100%}.v23-head{align-items:center}}
`;
if(!document.getElementById('v23-css')){const st=document.createElement('style');st.id='v23-css';st.textContent=css;document.head.appendChild(st)}
const prior=render;render=function(){prior();requestAnimationFrame(render23)};
window.PETQUEST_V23={state:V23,allActivity,healthyRhythm,goalProgress,retentionSignal,calendarDays,version:'23.0'};
requestAnimationFrame(render23);
})();
