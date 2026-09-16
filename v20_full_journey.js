// PET Quest V20 — Full Learning Journey
// Orchestrates balanced daily learning across Reading, Listening, Writing and Speaking.
(()=>{
'use strict';
const KEY='petQuestV20Journey';
const DEFAULT={active:false,paused:false,journeyId:'',startedAt:0,targetMinutes:10,index:0,plan:[],baseline:{},events:[],lastJourney:null,journeysCompleted:0,history:[],dismissedWhy:false};
let V20;try{V20=Object.assign({},DEFAULT,JSON.parse(localStorage.getItem(KEY)||'{}'));V20.plan=V20.plan||[];V20.events=V20.events||[];V20.history=V20.history||[]}catch(_){V20=JSON.parse(JSON.stringify(DEFAULT))}
const save20=()=>{try{localStorage.setItem(KEY,JSON.stringify(V20))}catch(_){}};
const E=s=>typeof esc==='function'?esc(String(s??'')):String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const kid=()=>typeof uxMode==='function'?uxMode()==='kid':document.documentElement.classList.contains('v15-kid');
const skillMeta={reading:{icon:'📖',label:'Reading',color:'read'},listening:{icon:'🎧',label:'Listening',color:'listen'},writing:{icon:'✍️',label:'Writing',color:'write'},speaking:{icon:'🎙️',label:'Speaking',color:'speak'},review:{icon:'🧠',label:'Repaso',color:'review'}};
function rows(skill,n=12){return (data.history||[]).filter(x=>x.skill===skill).slice(-n)}
function accuracy(skill){const r=rows(skill);return r.length?Math.round(r.filter(x=>x.correct).length/r.length*100):null}
function lastExam(skill){try{
 if(skill==='reading')return window.PETQUEST_V19?.state?.exam?.finished?.slice(-1)[0]?.score??null;
 if(skill==='listening')return window.PETQUEST_V18?.state?.exam?.finished?.slice(-1)[0]?.score??null;
 if(skill==='speaking')return window.PETQUEST_V17?.state?.exam?.completed?.slice(-1)[0]?.score??null;
 }catch(_){ }return null
}
function writingScore(){try{const ds=window.PETQUEST_V16?.state?.writing?.drafts||[];const scored=ds.filter(d=>Number.isFinite(+d.score));if(scored.length)return Math.round(scored.slice(-3).reduce((s,d)=>s+(+d.score||0),0)/Math.min(3,scored.length));}catch(_){}return null}
function speakingScore(){try{const ex=lastExam('speaking');if(ex!=null)return +ex;const a=window.PETQUEST_V16?.state?.speaking?.attempts||[];if(a.length)return Math.round(a.slice(-5).reduce((s,x)=>s+(+x.score||0),0)/Math.min(5,a.length));}catch(_){}return null}
function skillSnapshot(){
 const snap={};
 ['reading','listening'].forEach(s=>{const hist=accuracy(s),exam=lastExam(s);const score=exam!=null?Math.round(exam*.65+(hist??exam)*.35):(hist??60);snap[s]={score, evidence:rows(s).length+(exam!=null?8:0), recent:hist, exam}});
 const ws=writingScore(),ss=speakingScore();
 snap.writing={score:ws??58,evidence:(window.PETQUEST_V16?.state?.writing?.drafts||[]).length*3,recent:ws,exam:null};
 snap.speaking={score:ss??58,evidence:(window.PETQUEST_V16?.state?.speaking?.attempts||[]).length+(window.PETQUEST_V17?.state?.stats?.turns||0),recent:ss,exam:lastExam('speaking')};
 return snap
}
function supportUse(){try{const h=(typeof V14!=='undefined'&&V14?.helpCounts)?V14.helpCounts:{};return Object.values(h).reduce((a,b)=>a+(+b||0),0)}catch(_){return 0}}
function weakestFocus(){const h=(data.history||[]).slice(-30);const m={};h.forEach(x=>{const f=x.focus||'general';m[f]=m[f]||{n:0,ok:0};m[f].n++;if(x.correct)m[f].ok++});return Object.entries(m).filter(([,x])=>x.n>=2).sort((a,b)=>(a[1].ok/a[1].n)-(b[1].ok/b[1].n))[0]?.[0]||''}
function rankSkills(){const snap=skillSnapshot();return Object.entries(snap).map(([skill,x])=>({skill,...x,priority:(100-x.score)+(x.evidence<5?12:0)})).sort((a,b)=>b.priority-a.priority)}
function nextProduction(ranked){const w=ranked.find(x=>x.skill==='writing'),s=ranked.find(x=>x.skill==='speaking');return (w?.priority||0)>=(s?.priority||0)?'writing':'speaking'}
function mkStep(skill,minutes,reason,goal=1,kind='practice'){const m=skillMeta[skill]||skillMeta.review;return{id:kind+'-'+skill+'-'+Math.random().toString(36).slice(2,7),skill,minutes,reason,goal,kind,icon:m.icon,label:m.label}}
function buildPlan(){
 const ranked=rankSkills(),target=+((typeof V11!=='undefined'&&V11?.sessionMinutes)||data?.profile?.dailyGoal||10),weak=ranked[0],second=ranked[1],prod=nextProduction(ranked),strong=ranked.slice().sort((a,b)=>b.score-a.score)[0],focus=weakestFocus();let p=[];
 const weakReason=weak.evidence<5?`Necesito conocerte mejor en ${skillMeta[weak.skill].label}.`:`Es la habilidad con más oportunidad hoy (${weak.score}%).`;
 if(target<=5){p=[mkStep(weak.skill,3,weakReason,weak.skill==='writing'||weak.skill==='speaking'?1:2),mkStep(prod===weak.skill?(prod==='writing'?'speaking':'writing'):prod,2,'Terminamos produciendo inglés con tus propias ideas.',1)]}
 else if(target<=8){p=[mkStep(weak.skill,3,weakReason,2),mkStep(second.skill,2,`Equilibramos la sesión con ${skillMeta[second.skill].label}.`,2),mkStep(prod,3,'Cerramos con producción activa para usar el inglés, no solo reconocerlo.',1)]}
 else if(target<=10){const ordered=[weak.skill,second.skill,prod,(prod==='writing'?'speaking':'writing')];const unique=[...new Set(ordered)];p=unique.slice(0,4).map((s,i)=>mkStep(s,i===0?3:2,i===0?weakReason:i===1?'Cambiamos de habilidad para mantener atención y transferencia.':s===prod?'Usa el inglés con tus propias ideas.':'Completamos el equilibrio de las cuatro habilidades.',s==='reading'||s==='listening'?2:1));}
 else {p=[mkStep(weak.skill,4,weakReason,3),mkStep(second.skill,3,'Segunda prioridad según tu historial reciente.',2),mkStep(prod,3,'Producción activa: organiza y expresa tus ideas.',1),mkStep(strong.skill,2,`También cuidamos tu fortaleza (${strong.score}%) para mantener confianza.`,2),mkStep('review',3,focus?`Reparamos el foco “${focus}” para convertir el error en aprendizaje.`:'Terminamos reparando errores recientes.',2,'review')];}
 return {target,ranked,plan:p,focus}
}
function metric(skill){
 if(skill==='reading'||skill==='listening')return (data.history||[]).filter(x=>x.skill===skill).length;
 if(skill==='writing')return (window.PETQUEST_V16?.state?.writing?.drafts||[]).reduce((n,d)=>n+(d.updated?1:0)+(d.score?1:0),0);
 if(skill==='speaking')return (window.PETQUEST_V16?.state?.speaking?.attempts||[]).length+(window.PETQUEST_V17?.state?.stats?.turns||0);
 if(skill==='review')return (data.words||[]).filter(w=>w.nextReview&&new Date(w.nextReview)<=new Date()).length;
 return 0
}
function baseline(){const b={help:supportUse(),history:(data.history||[]).length};['reading','listening','writing','speaking','review'].forEach(s=>b[s]=metric(s));return b}
function startJourney(){const x=buildPlan();try{if(typeof V15!=='undefined'){V15.active=false;v15Save?.()}}catch(_){}V20.active=true;V20.paused=false;V20.journeyId='j'+Date.now();V20.startedAt=Date.now();V20.targetMinutes=x.target;V20.index=0;V20.plan=x.plan;V20.baseline=baseline();V20.events=[{type:'journey_start',at:new Date().toISOString(),target:x.target,focus:x.focus}];V20.dismissedWhy=false;save20();openCurrent()}
function current(){return V20.plan[V20.index]||null}
function elapsed(){return V20.startedAt?Math.max(0,(Date.now()-V20.startedAt)/60000):0}
function stepBaseline(s){const ev=V20.events.filter(e=>e.type==='step_open'&&e.skill===s).slice(-1)[0];return ev?.metric??V20.baseline[s]??0}
function stepProgress(){const s=current();if(!s)return{done:0,goal:0,pct:100};if(s.skill==='review'){const base=stepBaseline('review'),now=metric('review');const done=Math.max(0,base-now);return{done,goal:s.goal,pct:Math.min(100,Math.round(done/s.goal*100))}}const done=Math.max(0,metric(s.skill)-stepBaseline(s.skill));return{done,goal:s.goal,pct:Math.min(100,Math.round(done/Math.max(1,s.goal)*100))}}
function navigateStep(s){if(!s)return finishJourney();if(s.skill==='review'){state.view='review';render();return}try{if(s.skill==='reading'&&typeof V19!=='undefined'){V19.mode='learn';save19?.()}if(s.skill==='listening'&&typeof V18!=='undefined'){V18.mode='learn';save18?.()}if(s.skill==='speaking'&&typeof V17!=='undefined'){V17.mode='conversation';save17?.()}}catch(_){}if(s.skill==='writing'||s.skill==='speaking'){startSkill(s.skill,1,'normal');return}startSkill(s.skill,Math.max(1,Math.min(3,(typeof v13Overall==='function'?v13Overall().level:1)||1)),'normal')}
function openCurrent(){const s=current();if(!s)return finishJourney();V20.events.push({type:'step_open',at:new Date().toISOString(),skill:s.skill,metric:metric(s.skill),index:V20.index});save20();navigateStep(s)}
function resumeJourney(){if(!V20.plan?.length)return startJourney();V20.active=true;V20.paused=false;V20.events.push({type:'journey_resumed',at:new Date().toISOString(),index:V20.index});save20();navigateStep(current())}
function advance(){const s=current();if(!s)return finishJourney();const p=stepProgress();V20.events.push({type:'step_complete',at:new Date().toISOString(),skill:s.skill,done:p.done,goal:p.goal});V20.index++;save20();if(V20.index>=V20.plan.length)finishJourney();else openCurrent()}
function pauseJourney(){V20.events.push({type:'journey_paused',at:new Date().toISOString(),index:V20.index});V20.active=false;V20.paused=true;save20();state.view='home';render()}
function summary(){const snap=skillSnapshot(), touched={};V20.plan.forEach(s=>touched[s.skill]=(touched[s.skill]||0)+1);const doneEvents=V20.events.filter(e=>e.type==='step_complete');const helps=Math.max(0,supportUse()-(V20.baseline.help||0));const rowGain=Math.max(0,(data.history||[]).length-(V20.baseline.history||0));return{at:new Date().toISOString(),minutes:Math.max(1,Math.round(elapsed())),steps:doneEvents.length,totalSteps:V20.plan.length,helps,answers:rowGain,touched,skills:snap,focus:weakestFocus()}}
function finishJourney(){const s=summary();V20.lastJourney=s;V20.journeysCompleted=(V20.journeysCompleted||0)+1;V20.history.push(s);if(V20.history.length>40)V20.history=V20.history.slice(-40);V20.events.push({type:'journey_complete',at:s.at});V20.active=false;V20.paused=false;save20();state.view='home';render()}
function planPreview(plan){return plan.map((s,i)=>`<div class="v20-plan-item"><span class="v20-plan-num">${i+1}</span><span class="v20-plan-icon">${s.icon}</span><div><b>${E(s.label)} · ${s.minutes} min</b><small>${E(s.reason)}</small></div></div>`).join('')}
function journeyHome(){const main=document.querySelector('main.container');if(!main||main.querySelector('.v20-journey-home'))return;const oldV15=main.querySelector('.v15-autonomy-home');if(oldV15)oldV15.classList.add('v20-superseded');const x=buildPlan(),hero=oldV15||main.querySelector('.v12-hero-scene')||main.firstElementChild;
 if(kid()){
  const html=`<section class="card v20-journey-home"><div class="v20-journey-head"><div><span class="mission-label">V20 · Tu ruta completa de hoy</span><h2>🗺️ Milo preparó ${x.target} minutos para ti</h2><p>Vamos a mezclar habilidades para aprender sin aburrirte y reforzar lo que más necesitas.</p></div><img src="assets/mascot.svg" alt="Milo, guía de PET Quest"></div><div class="v20-plan">${planPreview(x.plan)}</div><details class="v20-why"><summary>¿Por qué elegiste esta ruta, Milo?</summary><div class="v20-skill-health">${x.ranked.map(r=>`<div><span>${skillMeta[r.skill].icon} ${skillMeta[r.skill].label}</span><b>${r.score}%</b><small>${r.evidence<5?'Aún te estoy conociendo':'Basado en tu actividad reciente'}</small></div>`).join('')}</div></details>${V20.paused&&V20.plan?.length?'<button class="btn btn-primary v20-start" data-v20-resume>▶ Continuar mi ruta guardada</button>':'<button class="btn btn-primary v20-start" data-v20-start>▶ Empezar mi ruta</button>'}</section>`;
  hero?.insertAdjacentHTML('afterend',html);
  if(V20.lastJourney&&!main.querySelector('.v20-last-kid')){const s=V20.lastJourney;main.insertAdjacentHTML('beforeend',`<section class="card v20-last-kid"><span class="mission-label">🌟 Tu última ruta</span><h2>${s.steps}/${s.totalSteps} misiones completadas</h2><div class="v20-summary-row"><span>⏱ ${s.minutes} min</span><span>✅ ${s.answers} respuestas</span><span>🦉 ${s.helps} ayudas</span></div><p>${s.steps===s.totalSteps?'¡Ruta completa! Hoy entrenaste varias formas de usar tu inglés.':'Guardamos tu avance. La próxima ruta vuelve a empezar clara y sencilla.'}</p></section>`)}
 } else {
  const s=V20.lastJourney,rank=x.ranked;main.insertAdjacentHTML('beforeend',`<section class="card v20-journey-home v20-adult"><div class="row between"><div><span class="mission-label">Full Learning Journey V20</span><h2>🗺️ Orquestación diaria de 4 habilidades</h2><p>La ruta pondera necesidad, variedad y producción activa. No fuerza el mismo reparto todos los días.</p></div><b>${V20.journeysCompleted||0} rutas</b></div><div class="v20-skill-health">${rank.map(r=>`<div><span>${skillMeta[r.skill].icon} ${skillMeta[r.skill].label}</span><b>${r.score}%</b><small>evidencia ${r.evidence}</small></div>`).join('')}</div>${s?`<div class="notice"><b>Última ruta:</b> ${s.minutes} min · ${s.steps}/${s.totalSteps} pasos · ${s.answers} respuestas · ${s.helps} ayudas.</div>`:''}<details><summary>Ver ruta que se propondría hoy</summary><div class="v20-plan">${planPreview(x.plan)}</div></details></section>`)}
}
function activeBar(){if(!V20.active||!kid())return;const main=document.querySelector('main.container');if(!main||main.querySelector('.v20-active-bar'))return;const s=current(),p=stepProgress(),pct=Math.round((V20.index/Math.max(1,V20.plan.length))*100);main.insertAdjacentHTML('afterbegin',`<section class="v20-active-bar"><div class="v20-active-main"><span class="v20-step-icon">${s?.icon||'🦉'}</span><div><span class="mission-label">Ruta completa · ${V20.targetMinutes} min</span><b>${E(s?.label||'Misión')}</b><small>${E(s?.reason||'Una misión a la vez.')}</small></div></div><div class="v20-route-progress"><span><i style="width:${Math.min(100,pct)}%"></i></span><small>Paso ${V20.index+1}/${V20.plan.length} · ${Math.min(p.done,p.goal)}/${p.goal} objetivo</small></div><div class="row"><button class="btn btn-ghost mini" data-v20-pause>Guardar y salir</button><button class="btn btn-primary mini" data-v20-next ${p.done<p.goal?'disabled':''}>${V20.index===V20.plan.length-1?'Terminar ruta':'Siguiente misión →'}</button></div></section>`)}
function gentleNudge(){if(!V20.active||!kid())return;const main=document.querySelector('main.container'),s=current(),p=stepProgress();if(!main||main.querySelector('.v20-gentle-nudge'))return;const recent=(data.history||[]).slice(-3),errors=recent.filter(x=>!x.correct).length,mins=elapsed();let n=null;if(mins>=Math.max(7,V20.targetMinutes*.85))n={icon:'💧',title:'Tu cerebro también necesita aire',copy:'Puedes terminar esta misión y hacer una pausa corta. No perderás tu avance.'};else if(errors>=3)n={icon:'🛟',title:'Milo puede ayudarte',copy:'Hubo varios tropiezos. Usa una pista o una mini práctica; no tienes que adivinar.'};else if(p.done>=p.goal)n={icon:'✅',title:'Misión cumplida',copy:'Ya alcanzaste el objetivo de este paso. Puedes pasar a la siguiente habilidad.'};if(!n)return;main.insertAdjacentHTML('afterbegin',`<aside class="v20-gentle-nudge"><span>${n.icon}</span><div><b>${n.title}</b><p>${n.copy}</p></div></aside>`)}
function bind20(){document.querySelector('[data-v20-start]')?.addEventListener('click',startJourney);document.querySelector('[data-v20-resume]')?.addEventListener('click',resumeJourney);document.querySelector('[data-v20-next]')?.addEventListener('click',advance);document.querySelector('[data-v20-pause]')?.addEventListener('click',pauseJourney)}
const renderBeforeV20=render;render=function(){renderBeforeV20();requestAnimationFrame(()=>{if(state.view==='home')journeyHome();activeBar();gentleNudge();bind20()})};
window.PETQUEST_V20={state:V20,skillSnapshot,rankSkills,buildPlan,stepProgress,startJourney,resumeJourney,advance,finishJourney,version:'20.0'};
requestAnimationFrame(()=>{if(state.view==='home')journeyHome();activeBar();gentleNudge();bind20()});
})();
