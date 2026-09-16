/* PET Quest V18 — Immersive Listening Lab & Exam Mode */
(function(){
'use strict';
const KEY='petquest_v18_listening';
const BASE={mode:'learn',speed:.9,segment:0,replays:{},exam:{active:false,idx:0,answers:[],plays:{},startedAt:null,finished:[]},stats:{plays:0,segments:0,vocabOpens:0,examAttempts:0}};
let V18;
try{V18=Object.assign({},BASE,JSON.parse(localStorage.getItem(KEY)||'{}'));V18.exam=Object.assign({},BASE.exam,V18.exam||{});V18.stats=Object.assign({},BASE.stats,V18.stats||{});V18.replays=V18.replays||{};}catch(_){V18=JSON.parse(JSON.stringify(BASE))}
V18.strictTwoPlay=!!V18.strictTwoPlay;
function save18(){localStorage.setItem(KEY,JSON.stringify(V18))}
function E(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function listeningBank(){return (window.BANK?.listening||BANK.listening||[]).slice()}
function splitAudio(text){const parts=String(text||'').split(/(?<=[.!?])\s+/).map(x=>x.trim()).filter(Boolean);if(parts.length>=2)return parts;const words=String(text||'').split(/\s+/),mid=Math.ceil(words.length/2);return [words.slice(0,mid).join(' '),words.slice(mid).join(' ')].filter(Boolean)}
function voiceLangFor(q){const focus=String(q?.focus||'');if(/numbers|time|dates/.test(focus))return 'en-GB';const pool=['en-GB','en-US','en-AU'];const n=[...String(q?.id||'')].reduce((a,c)=>a+c.charCodeAt(0),0);return pool[n%pool.length]}
function speakText(text,opt={}){if(!('speechSynthesis' in window)){window.toast?.('Audio no disponible en este navegador');return}speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(text);u.lang=opt.lang||'en-GB';u.rate=window.PETAudioSafe?PETAudioSafe.rateValue(opt.rate||V18.speed||.9):(opt.rate||V18.speed||.9);u.pitch=1;u.volume=.78;const voices=speechSynthesis.getVoices?.()||[];const match=voices.find(v=>String(v.lang).toLowerCase().startsWith(u.lang.toLowerCase().slice(0,2)))||voices[0];if(match)u.voice=match;speechSynthesis.speak(u)}
function vocabFor(q){const maps={
 time:[['half past','treinta minutos después de la hora'],['quarter past','quince minutos después'],['starts','comienza']],
 places:[['instead','en cambio / en su lugar'],['floor','piso / planta'],['next door','al lado']],
 numbers:[['costs','cuesta'],['under','menor de'],['free','gratis']],
 opinion:[['actually','en realidad'],['prefer','preferir'],['expected','esperaba']],
 reason:[['because','porque'],['earlier','más temprano'],['heavy','fuerte/intenso']],
 detail:[['provide','proporcionar'],['included','incluido'],['bring','traer']],
 attitude:[['nervous','nervioso/a'],['enjoyed','disfrutó'],['relaxed','relajado/a']],
 inference:[['nearly','casi'],['luckily','por suerte'],['probably','probablemente']],
 dates:[['closes','cierra/fecha límite'],['announced','anunciado'],['twenty-second','veintidós']],
 agreement:[['agree','estar de acuerdo'],['although','aunque'],['useful','útil']],
 change:[['used to','solía'],['now','ahora'],['earlier','más temprano']],
 purpose:[['so I can','para poder'],['write down','anotar'],['before','antes de']],
 objects:[['forgot','olvidó'],['remembered','recordó'],['bottle','botella']]
 };return maps[q.focus]||[['listen for','escucha buscando'],['key word','palabra clave'],['detail','detalle']]
}
function modeBar(){return `<div class="v18-modebar" role="tablist" aria-label="Modo Listening"><button class="${V18.mode==='learn'?'active':''}" data-v18-mode="learn">🌱 Aprender</button><button class="${V18.mode==='exam'?'active':''}" data-v18-mode="exam">🏁 Simular examen</button></div>`}
function sceneFor(q){const icons={time:'🕒',places:'📍',numbers:'🔢',opinion:'💭',reason:'🔎',detail:'🧩',attitude:'🙂',inference:'🧠',dates:'📅',agreement:'🤝',change:'🔄',purpose:'🎯',objects:'🎒'};return icons[q.focus]||'🎧'}
function learningScreen(){
 const qs=currentQuestions();const q=qs[state.idx];if(!q)return basePractice();
 const segments=splitAudio(q.audio),seg=Math.min(V18.segment,segments.length-1),plays=V18.replays[q.id]||0;
 const opts=q.opts.map((o,i)=>`<button class="option ${state.selected===i?'selected':''} ${state.checked?(i===q.a?'correct':state.selected===i?'wrong':''):''}" data-opt="${i}"><span>${String.fromCharCode(65+i)}</span>${E(o)}</button>`).join('');
 const fb=state.checked?`<div class="feedback ${state.selected===q.a?'ok':'bad'}"><b>${state.selected===q.a?'🌟 ¡Muy bien!':'🌱 Vamos a repararlo'}</b><p>${E(q.why)}</p><p class="small"><b>Clave de escucha:</b> ${E(q.tip)}</p></div>`:'';
 el(`<div class="app-shell">${topBar()}<main class="container">${screenHead('Listening Lab · Nivel '+state.level,`Parte ${q.part} · ${state.idx+1} de ${qs.length}`)}${modeBar()}
 <section class="card v18-listen-hero"><div class="v18-listen-scene">${sceneFor(q)}</div><div><span class="mission-label">Escena de escucha</span><h2>${E(q.focus)}</h2><p>Milo te ayuda a escuchar por intención, no palabra por palabra.</p></div><div class="v18-play-count"><b>${plays}</b><small>escuchas</small></div></section>
 <div class="exercise-layout"><section class="card question-card">
 <div class="v18-listen-steps"><span class="active">1 Vocabulario</span><span>2 Escucha</span><span>3 Elige</span><span>4 Aprende</span></div>
 <details class="v18-vocab" data-v18-vocab><summary>🧠 Ver vocabulario previo (opcional)</summary><div class="v18-vocab-grid">${vocabFor(q).map(([a,b])=>`<div><b>${E(a)}</b><span>${E(b)}</span></div>`).join('')}</div></details>
 <div class="v18-player"><div class="row between"><div><b>🎧 Audio de práctica</b><p class="small">Acento simulado por la voz disponible del dispositivo: ${voiceLangFor(q)}</p></div><label class="v18-speed">Velocidad <select id="v18Speed"><option value="0.78" ${V18.speed<.84?'selected':''}>0.8×</option><option value="0.9" ${V18.speed>=.84&&V18.speed<.98?'selected':''}>0.9×</option><option value="1.0" ${V18.speed>=.98?'selected':''}>1.0×</option></select></label></div>
 <div class="row"><button class="btn btn-primary" data-v18-play-full>▶ Escuchar completo</button><button class="btn btn-soft" data-v18-play-segment>🔹 Escuchar parte ${seg+1}/${segments.length}</button><button class="btn btn-ghost" data-v18-next-segment>Parte siguiente →</button></div>
 <div class="v18-wave" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div></div>
 <div class="prompt">${E(q.q)}</div><div class="options">${opts}</div>${fb}
 <div class="row action-row"><button class="btn btn-primary" data-check ${state.selected===null||state.checked?'disabled':''}>Comprobar</button><button class="btn btn-soft" data-next ${!state.checked?'disabled':''}>${state.idx===qs.length-1?'Finalizar':'Siguiente →'}</button></div>
 </section><aside class="card side"><h3>🎯 Escucha con intención</h3><p class="small">Foco: <b>${E(q.focus)}</b></p><p>Primera escucha: idea general.</p><p>Segunda escucha: busca el detalle que responde la pregunta.</p><hr><div class="metric"><span>Precisión Listening</span><b>${pct('listening')}%</b></div><button class="btn btn-ghost mini" data-v18-mode="exam">Probar modo examen</button></aside></div></main></div>`);
}
function examQuestions(){return listeningBank().slice(0,25)}
function startExam(){V18.exam={active:true,idx:0,answers:[],plays:{},startedAt:new Date().toISOString(),finished:V18.exam.finished||[]};V18.stats.examAttempts++;save18();render()}
function examScreen(){
 if(!V18.exam.active){el(`<div class="app-shell">${topBar()}<main class="container">${screenHead('Listening Exam Practice','25 preguntas · 4 partes · sin vocabulario ni pistas')}${modeBar()}<section class="card v18-exam-intro"><div class="v18-listen-scene">🏁</div><h2>Modo examen</h2><p>Practica con el banco completo de 25 preguntas. La <b>repetición libre</b> está activa por defecto: puedes escuchar tantas veces como necesites. Si quieres entrenar con la condición oficial, activa la simulación estricta de 2 escuchas. No se muestran vocabulario, segmentos, explicación ni velocidad reducida durante la prueba.</p><div class="notice"><b>Práctica PET Quest:</b> contenido original y simulación orientativa. No reproduce materiales oficiales.</div><button class="btn btn-primary" data-v18-start-exam>Empezar Listening Exam</button><button class="btn btn-soft" data-v18-strict>${V18.strictTwoPlay?'♾ Usar repeticiones ilimitadas':'🎓 Usar simulación estricta (2)'}</button></section></main></div>`);return}
 const qs=examQuestions(),q=qs[V18.exam.idx];if(!q)return finishExam();const plays=V18.exam.plays[q.id]||0,selected=V18.exam.answers[V18.exam.idx]?.answer;
 const opts=q.opts.map((o,i)=>`<button class="option ${selected===i?'selected':''}" data-v18-exam-opt="${i}">${String.fromCharCode(65+i)}. ${E(o)}</button>`).join('');
 el(`<div class="app-shell">${topBar()}<main class="container"><div class="mock-top"><div><h1>Listening Exam Practice</h1><p>${V18.exam.idx+1}/25 · Parte ${q.part}</p></div><div class="timer">🎧 ${plays} ${V18.strictTwoPlay?'/2':'· ♾'}</div></div>${modeBar()}<section class="card question-card"><div class="v18-exam-audio"><button class="btn btn-primary" data-v18-exam-play ${V18.strictTwoPlay&&plays>=2?'disabled':''}>🔊 ${plays?'Escuchar de nuevo':'Reproducir audio'}</button><span>${V18.strictTwoPlay?(plays>=2?'Límite estricto de 2 alcanzado':'Simulación estricta · velocidad normal'):'Repetición libre · sin límite'}</span></div><div class="prompt">${E(q.q)}</div><div class="options">${opts}</div><div class="row action-row"><button class="btn btn-primary" data-v18-exam-next ${selected===undefined?'disabled':''}>${V18.exam.idx===24?'Finalizar examen':'Guardar y seguir →'}</button></div></section></main></div>`)
}
function finishExam(){
 const qs=examQuestions(),answers=V18.exam.answers,details=qs.map((q,i)=>({qid:q.id,part:q.part,focus:q.focus,correct:answers[i]?.answer===q.a,answer:answers[i]?.answer}));const correct=details.filter(x=>x.correct).length,score=Math.round(correct/Math.max(1,details.length)*100);const byPart=[1,2,3,4].map(p=>{const x=details.filter(d=>d.part===p);return{part:p,total:x.length,correct:x.filter(d=>d.correct).length,pct:x.length?Math.round(x.filter(d=>d.correct).length/x.length*100):0}});const byFocus={};details.forEach(d=>{byFocus[d.focus]=byFocus[d.focus]||{total:0,correct:0};byFocus[d.focus].total++;if(d.correct)byFocus[d.focus].correct++});const focusRows=Object.entries(byFocus).map(([focus,x])=>({focus,pct:Math.round(x.correct/x.total*100),total:x.total})).sort((a,b)=>a.pct-b.pct);const record={at:new Date().toISOString(),score,correct,total:details.length,byPart,byFocus:focusRows};V18.exam.finished.push(record);V18.exam.active=false;save18();data.mockAttempts.push({date:record.at,skill:'listening',score,correct,total:details.length,source:'v18-listening-exam'});details.forEach(d=>data.history.push({date:record.at,qid:d.qid,skill:'listening',level:3,focus:d.focus,correct:d.correct,answer:d.answer,source:'v18-exam'}));save();
 el(`<div class="app-shell">${topBar()}<main class="container">${screenHead('Listening Exam Review','Resultados de tu simulación V18')}${modeBar()}<section class="card highlight"><div class="label">RESULTADO</div><div class="big-number">${score}%</div><p>${correct}/25 respuestas correctas</p></section><div class="dashboard-grid four">${byPart.map(x=>`<div class="card"><div class="label">Parte ${x.part}</div><div class="big-number">${x.pct}%</div><p>${x.correct}/${x.total}</p></div>`).join('')}</div><section class="card"><h2>🧠 Focos que conviene reforzar</h2><div class="v18-focus-list">${focusRows.slice(0,5).map(x=>`<div><span>${E(x.focus)}</span><b>${x.pct}%</b></div>`).join('')}</div><p class="small">Vuelve a modo Aprender para usar vocabulario, segmentación y explicaciones.</p><button class="btn btn-primary" data-v18-mode="learn">Volver al Listening Lab</button></section></main></div>`);bind18()
}
function adultInsight(){const kid=document.documentElement.classList.contains('v15-kid')||(window.V10&&V10.mode==='kid');if(kid||state.view!=='home')return;const main=document.querySelector('main.container');if(!main||main.querySelector('.v18-adult-insight'))return;const last=V18.exam.finished?.slice(-1)[0];main.insertAdjacentHTML('beforeend',`<section class="card v18-adult-insight"><h2>🎧 Listening V18</h2><div class="v16-summary-grid"><div><b>${V18.stats.plays||0}</b><small>escuchas guiadas</small></div><div><b>${V18.stats.segments||0}</b><small>segmentos usados</small></div><div><b>${V18.stats.vocabOpens||0}</b><small>aperturas vocabulario</small></div><div><b>${last?last.score:'—'}${last?'%':''}</b><small>último exam practice</small></div></div><p class="small">Las voces dependen del motor de síntesis del dispositivo. Para producción premium se recomienda audio grabado profesional y validado pedagógicamente.</p></section>`)}
function bind18(){
 document.querySelectorAll('[data-v18-mode]').forEach(b=>b.onclick=()=>{V18.mode=b.dataset.v18Mode;V18.segment=0;save18();if(V18.mode==='exam'){state.view='practice';state.skill='listening'}render()});
 document.querySelector('[data-v18-play-full]')?.addEventListener('click',()=>{const q=currentQuestions()[state.idx];V18.stats.plays++;V18.replays[q.id]=(V18.replays[q.id]||0)+1;save18();speakText(q.audio,{lang:voiceLangFor(q)})});
 document.querySelector('[data-v18-play-segment]')?.addEventListener('click',()=>{const q=currentQuestions()[state.idx],parts=splitAudio(q.audio),seg=Math.min(V18.segment,parts.length-1);V18.stats.plays++;V18.stats.segments++;V18.replays[q.id]=(V18.replays[q.id]||0)+1;save18();speakText(parts[seg],{lang:voiceLangFor(q),rate:Math.max(.72,V18.speed-.05)})});
 document.querySelector('[data-v18-next-segment]')?.addEventListener('click',()=>{const q=currentQuestions()[state.idx],parts=splitAudio(q.audio);V18.segment=(V18.segment+1)%parts.length;save18();render()});
 document.getElementById('v18Speed')?.addEventListener('change',e=>{V18.speed=+e.target.value;save18()});
 document.querySelector('[data-v18-vocab]')?.addEventListener('toggle',e=>{if(e.target.open){V18.stats.vocabOpens++;save18()}});
 document.querySelector('[data-v18-start-exam]')?.addEventListener('click',startExam);document.querySelector('[data-v18-strict]')?.addEventListener('click',()=>{V18.strictTwoPlay=!V18.strictTwoPlay;save18();render()});
 document.querySelector('[data-v18-exam-play]')?.addEventListener('click',()=>{const q=examQuestions()[V18.exam.idx],n=V18.exam.plays[q.id]||0;if(V18.strictTwoPlay&&n>=2)return;V18.exam.plays[q.id]=n+1;save18();speakText(q.audio,{lang:voiceLangFor(q),rate:1});render()});
 document.querySelectorAll('[data-v18-exam-opt]').forEach(b=>b.onclick=()=>{V18.exam.answers[V18.exam.idx]={answer:+b.dataset.v18ExamOpt};save18();render()});
 document.querySelector('[data-v18-exam-next]')?.addEventListener('click',()=>{if(V18.exam.idx<24){V18.exam.idx++;save18();render()}else finishExam()});
}
const basePractice=practice;
practice=function(){if(state.skill==='listening'){if(V18.mode==='exam')return examScreen();return learningScreen()}return basePractice()};
const baseBind=bind;
bind=function(){baseBind();if(state.view==='practice'&&state.skill==='listening')bind18()};
const baseRender=render;
render=function(){baseRender();requestAnimationFrame(()=>{if(state.view==='practice'&&state.skill==='listening')bind18();adultInsight()})};
window.PETQUEST_V18={state:V18,splitAudio,vocabFor,voiceLangFor,version:'18.0'};
requestAnimationFrame(adultInsight);
})();
