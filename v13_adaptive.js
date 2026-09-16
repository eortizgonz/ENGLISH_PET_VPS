// PET Quest V13 — adaptive pedagogical guidance based on observable learning signals.
// Signals are descriptive and never presented as diagnoses or emotional facts.
const V13_STORE='petQuestV13Adaptive';
const V13_DEFAULT={questionStartedAt:0,questionKey:'',pending:null,sessionSignals:[],adaptations:0,lastNudge:'',preferredChallenge:'balanced',quietCoach:false};
let V13=(()=>{try{return {...V13_DEFAULT,...JSON.parse(localStorage.getItem(V13_STORE)||'{}')}}catch{return {...V13_DEFAULT}}})();
function v13Save(){try{localStorage.setItem(V13_STORE,JSON.stringify(V13))}catch{}}
function v13Kid(){return typeof uxMode==='function'&&uxMode()==='kid'&&!(typeof data!=='undefined'&&data.profile?.examProfile==='adult')}
function v13Recent(n=8,skill=null){let h=[...(data.history||[])];if(skill)h=h.filter(x=>x.skill===skill);return h.slice(-n)}
function v13Avg(arr){return arr.length?arr.reduce((a,b)=>a+b,0)/arr.length:0}
function v13Median(arr){if(!arr.length)return 0;const a=[...arr].sort((x,y)=>x-y),m=Math.floor(a.length/2);return a.length%2?a[m]:(a[m-1]+a[m])/2}
function v13Accuracy(rows){return rows.length?rows.filter(x=>x.correct).length/rows.length:0}
function v13Timed(rows){return rows.map(x=>Number(x.responseMs||0)).filter(x=>x>0&&x<180000)}
function v13RepeatedFocus(rows){const c={};rows.filter(x=>!x.correct).forEach(x=>c[x.focus]=(c[x.focus]||0)+1);const s=Object.entries(c).sort((a,b)=>b[1]-a[1])[0];return s&&s[1]>=2?s:null}
function v13Trend(skill){const h=v13Recent(12,skill);if(h.length<8)return 0;const half=Math.floor(h.length/2),a=v13Accuracy(h.slice(0,half)),b=v13Accuracy(h.slice(half));return b-a}
function v13Signal(skill=state.skill||'reading'){
 const rows=v13Recent(8,skill),acc=v13Accuracy(rows),times=v13Timed(rows),med=v13Median(times),focus=v13RepeatedFocus(rows),trend=v13Trend(skill);
 if(rows.length<3)return {id:'warming',icon:'🌱',label:'Conociéndote',tone:'neutral',message:'Haz unas pocas preguntas y ajustaré la ayuda a tu ritmo.',action:'Seguir practicando',level:state.level||1};
 if(rows.length>=5&&times.length>=4&&med>0&&med<1800&&acc<.75)return {id:'rush',icon:'🐢',label:'Bajemos un poco el ritmo',tone:'support',message:'Tus respuestas recientes fueron muy rápidas y mezclan aciertos con errores. Te mostraré pasos más claros antes de elegir.',action:'Practicar con calma',level:state.level||1};
 if(rows.length>=5&&acc>=.88&&(!med||med<7000))return {id:'challenge',icon:'🚀',label:'Listo para más reto',tone:'up',message:'Estás acertando con mucha seguridad. Te propondré un reto un poco mayor.',action:'Subir un poco el reto',level:Math.min(3,(state.level||1)+1)};
 if(rows.length>=4&&acc<=.4)return {id:'support',icon:'🛟',label:'Conviene más apoyo',tone:'support',message:focus?`Veo varios tropiezos con “${focus[0]}”. Vamos a dividirlo en pasos más pequeños.`:'Vamos a reducir la carga y darte una pista extra antes de seguir.',action:'Activar ayuda',level:Math.max(1,(state.level||1)-1)};
 if(focus)return {id:'focus',icon:'🧠',label:'Foco para reforzar',tone:'support',message:`“${focus[0]}” se repite en tus errores recientes. Practiquemos ese punto antes de avanzar.`,action:'Reparar este foco',focus:focus[0],level:state.level||1};
 if(rows.length>=6&&Math.abs(trend)<.08&&acc>=.45&&acc<=.75)return {id:'change',icon:'🔄',label:'Cambiemos la forma',tone:'neutral',message:'Tu resultado está estable. Cambiar de tipo de actividad puede ayudarte a destrabar el aprendizaje.',action:'Cambiar actividad',level:state.level||1};
 if(rows.length>=5&&acc>=.8)return {id:'mastery',icon:'🏆',label:'Dominio en progreso',tone:'up',message:'Vas consolidando esta habilidad. Mantén una sesión corta y luego cambia de mundo.',action:'Consolidar y avanzar',level:state.level||1};
 return {id:'balanced',icon:'🎯',label:'Ritmo adecuado',tone:'neutral',message:'El nivel se ve equilibrado: hay reto, pero también aciertos. Sigue una misión más.',action:'Continuar',level:state.level||1};
}
function v13Overall(){const skills=['reading','listening'];const signals=skills.map(v13Signal);const urgent=signals.find(s=>s.id==='support')||signals.find(s=>s.id==='focus')||signals.find(s=>s.id==='challenge');return urgent||signals[0]||v13Signal('reading')}
function v13QuestionKey(){if(state.view!=='practice')return '';const qs=typeof currentQuestions==='function'?currentQuestions():[];const q=qs[state.idx];return q?`${state.skill}:${state.level}:${q.id}`:''}
function v13StartClock(){const key=v13QuestionKey();if(!key)return;if(V13.questionKey!==key){V13.questionKey=key;V13.questionStartedAt=Date.now();v13Save()}}
function v13CaptureCheck(btn){if(!btn||btn.dataset.v13Bound)return;btn.dataset.v13Bound='1';btn.addEventListener('click',()=>{const q=(typeof currentQuestions==='function'?currentQuestions():[])[state.idx];if(!q)return;V13.pending={qid:q.id,at:Date.now(),responseMs:Math.max(0,Date.now()-(V13.questionStartedAt||Date.now())),skill:state.skill,level:state.level};v13Save();setTimeout(v13FinalizeHistory,40)},true)}
function v13FinalizeHistory(){if(!V13.pending)return;const p=V13.pending,h=data.history||[];for(let i=h.length-1;i>=0;i--){const x=h[i];if(x.qid===p.qid&&x.skill===p.skill&&!x.responseMs){x.responseMs=p.responseMs;x.adaptiveVersion=13;save();break}}V13.pending=null;V13.adaptations++;v13Save()}
function v13HelpMode(signal){if(signal.id!=='support'&&signal.id!=='focus')return '';return `<div class="v13-help-steps"><span>1️⃣ Lee solo la pregunta</span><span>2️⃣ Busca una palabra pista</span><span>3️⃣ Descarta una opción</span><span>4️⃣ Elige sin prisa</span></div>`}
function v13CoachCard(signal,compact=false){return `<section class="v13-coach ${signal.tone} ${compact?'compact':''}" data-v13-signal="${signal.id}"><div class="v13-coach-icon">${signal.icon}</div><div class="v13-coach-copy"><span class="mission-label">Coach adaptativo</span><b>${signal.label}</b><p>${signal.message}</p>${!compact?v13HelpMode(signal):''}</div><button class="btn btn-soft" data-v13-adapt="${signal.id}">${signal.action}</button></section>`}
function v13Practice(){if(!v13Kid()||state.view!=='practice')return;v13StartClock();const qcard=document.querySelector('.question-card');if(!qcard)return;const signal=v13Signal(state.skill);const anchor=qcard.querySelector('.v12-scene')||qcard.querySelector('.v11-mini-session');if(anchor)anchor.insertAdjacentHTML('afterend',v13CoachCard(signal,true));else qcard.insertAdjacentHTML('afterbegin',v13CoachCard(signal,true));v13CaptureCheck(document.querySelector('[data-check]'));
 if(signal.id==='support'||signal.id==='rush'){data.settings.support='guided';save();document.documentElement.classList.add('v13-support-mode')}else document.documentElement.classList.remove('v13-support-mode');
}
function v13Home(){if(!v13Kid()||state.view!=='home')return;const main=document.querySelector('main.container');if(!main)return;const s=v13Overall();const hero=main.querySelector('.v12-hero-scene')||main.querySelector('.v11-adventure');if(hero)hero.insertAdjacentHTML('afterend',`<section class="card v13-home-intel"><div><span class="mission-label">Tu ruta se adapta a ti</span><h2>${s.icon} ${s.label}</h2><p>${s.message}</p></div><div class="v13-intel-stats"><div><b>${Math.round(v13Accuracy(v13Recent(8))*100)||0}%</b><small>últimos intentos</small></div><div><b>${v13Median(v13Timed(v13Recent(8)))?Math.round(v13Median(v13Timed(v13Recent(8)))/1000)+'s':'—'}</b><small>ritmo mediano</small></div></div><button class="btn btn-primary" data-v13-adapt="${s.id}">${s.action}</button></section>`)}
function v13Adult(){if(v13Kid()||state.view!=='home')return;const main=document.querySelector('main.container');if(!main)return;const sr=v13Signal('reading'),sl=v13Signal('listening');main.insertAdjacentHTML('beforeend',`<section class="card v13-adult-intel"><div class="section-title"><div><h2>🧭 Señales adaptativas</h2><p>Indicadores pedagógicos observables; no son diagnósticos emocionales.</p></div></div><div class="v13-adult-grid"><div><b>Reading</b><span>${sr.icon} ${sr.label}</span><small>${sr.message}</small></div><div><b>Listening</b><span>${sl.icon} ${sl.label}</span><small>${sl.message}</small></div></div><p class="small">La plataforma usa precisión reciente, repetición de focos, tendencia y tiempo de respuesta cuando está disponible para recomendar el siguiente paso.</p></section>`)}
function v13AlternativeSkill(){const order=['reading','listening','writing','speaking'];const cur=state.skill||'reading';return order[(order.indexOf(cur)+1)%order.length]}
function v13Apply(id){const s=v13Signal(state.skill||'reading');V13.lastNudge=id;V13.adaptations++;v13Save();
 if(id==='challenge'){startSkill(state.skill||'reading',Math.min(3,s.level||2));return}
 if(id==='rush'){data.settings.support='guided';save();startSkill(state.skill||'reading',state.level||1,'normal');return}
 if(id==='support'){data.settings.support='guided';save();startSkill(state.skill||'reading',Math.max(1,s.level||1),'fix');return}
 if(id==='focus'){startSkill(state.skill||'reading',state.level||1,'fix');return}
 if(id==='change'){const next=v13AlternativeSkill();startSkill(next,1);return}
 if(id==='mastery'){const next=v13AlternativeSkill();startSkill(next,1);return}
 if(id==='warming'||id==='balanced'){if(state.view==='home'){const m=typeof v11MissionTarget==='function'?v11MissionTarget():'reading';if(m==='mock'){state.view='mock';render()}else startSkill(m,1)}return}
}
function v13Bind(){document.querySelectorAll('[data-v13-adapt]').forEach(b=>{if(b.dataset.bound)return;b.dataset.bound='1';b.onclick=()=>v13Apply(b.dataset.v13Adapt)})}
function enhanceV13(){document.documentElement.classList.toggle('v13-kid',v13Kid());if(state.view==='practice')v13Practice();if(state.view==='home'){v13Home();v13Adult()}v13Bind()}
const v13RenderBase=render;
render=function(){v13RenderBase();requestAnimationFrame(enhanceV13)};
requestAnimationFrame(enhanceV13);
