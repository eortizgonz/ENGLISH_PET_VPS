/* PET Quest V17 — Interactive Conversation & Speaking Exam Practice */
(function(){
'use strict';
const KEY='petquest_v17_conversation';
const BASE={mode:'learn',scenario:0,turn:0,history:[],exam:{active:false,part:0,startedAt:null,answers:[],completed:[]},stats:{turns:0,freeAnswers:0,completedScenarios:0}};
let V17;
try{V17=Object.assign({},BASE,JSON.parse(localStorage.getItem(KEY)||'{}'));V17.exam=Object.assign({},BASE.exam,V17.exam||{});V17.stats=Object.assign({},BASE.stats,V17.stats||{});}catch(_){V17=JSON.parse(JSON.stringify(BASE))}
function save17(){localStorage.setItem(KEY,JSON.stringify(V17))}
function E(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function say(text){if(!('speechSynthesis' in window)){window.toast?.('Audio no disponible en este navegador');return}speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(text);u.lang='en-GB';u.rate=.9;speechSynthesis.speak(u)}
function recognize(cb){const R=window.SpeechRecognition||window.webkitSpeechRecognition;if(!R){window.toast?.('Reconocimiento de voz no disponible. Puedes escribir tu respuesta.');return}const r=new R();r.lang='en-GB';r.interimResults=false;r.maxAlternatives=1;r.onresult=e=>cb(e.results[0][0].transcript,e.results[0][0].confidence||0);r.onerror=()=>window.toast?.('No pude reconocer la voz. Intenta otra vez o escribe.');r.start()}
const SCENARIOS=[
 {icon:'🏫',title:'New school club',place:'School',goal:'Preguntar, responder y explicar una preferencia.',turns:[
   {milo:'Hi! I want to join a school club. Which club do you like?',choices:['I like the art club because I enjoy drawing.','Maybe the science club. It sounds interesting.','I prefer the sports club because I love team games.'],coach:'Di qué prefieres y añade una razón.'},
   {milo:'That sounds fun! When does the club meet?',choices:['It meets on Tuesday after school.','We meet twice a week, on Tuesday and Thursday.','I think it starts at four o’clock.'],coach:'Responde con un día, frecuencia u hora.'},
   {milo:'Would you like me to come with you next week?',choices:['Yes, that would be great!','Sure. We can go together after class.','Yes, and I can show you where it is.'],coach:'Acepta la invitación y añade un pequeño detalle.'}
 ]},
 {icon:'🛍️',title:'At the shop',place:'Shop',goal:'Pedir algo, preguntar precio y decidir.',turns:[
   {milo:'Hello! Can I help you?',choices:['Yes, I’m looking for a blue T-shirt.','Yes, please. I need a present for my friend.','No, thank you. I’m just looking.'],coach:'Di claramente qué necesitas.'},
   {milo:'This one is popular. Would you like to try it?',choices:['Yes, please. Where is the changing room?','Yes, but do you have a smaller size?','Maybe. How much is it?'],coach:'Haz una pregunta útil para continuar.'},
   {milo:'It is fifteen pounds. What do you think?',choices:['That’s fine. I’ll take it.','It’s a little expensive, so I’ll think about it.','I like it, but I want to see another colour first.'],coach:'Toma una decisión y explica brevemente.'}
 ]},
 {icon:'🏖️',title:'Holiday plans',place:'Holiday',goal:'Hablar de planes, sugerir y acordar.',turns:[
   {milo:'We have a free day on holiday. What should we do?',choices:['We could visit the old town.','How about going to the beach?','I think we should rent bikes and explore.'],coach:'Haz una sugerencia con could, should o how about.'},
   {milo:'Good idea. Why would that be fun?',choices:['Because we can see new places.','It would be fun because we can relax together.','Because it is something we don’t do at home.'],coach:'Explica una razón.'},
   {milo:'Great! What should we take with us?',choices:['We should take water and sunscreen.','Let’s take a camera and some snacks.','We need comfortable shoes and a map.'],coach:'Cierra el plan con detalles prácticos.'}
 ]},
 {icon:'🎮',title:'Free-time hobbies',place:'Friends',goal:'Comparar hobbies y hacer preguntas.',turns:[
   {milo:'What do you usually do in your free time?',choices:['I usually play basketball with my friends.','I enjoy reading adventure books.','I often play games, but I also like drawing.'],coach:'Habla de una actividad habitual.'},
   {milo:'Why do you enjoy it?',choices:['Because it helps me relax.','I like it because I can be creative.','Because I can spend time with my friends.'],coach:'Da una razón personal.'},
   {milo:'Ask me something about my hobbies.',choices:['What hobby do you enjoy most?','How often do you do it?','Who do you usually do it with?'],coach:'Ahora tú haces la pregunta.'}
 ]},
 {icon:'🎉',title:'Plan a celebration',place:'School event',goal:'Sugerir, comparar y llegar a un acuerdo.',turns:[
   {milo:'Our class needs an end-of-term celebration. Any ideas?',choices:['We could have a picnic in the park.','Maybe we could organise a games afternoon.','How about a small party at school?'],coach:'Propón una idea.'},
   {milo:'Which idea is best for everyone?',choices:['A picnic is best because everyone can join.','The games afternoon is better because it works in any weather.','A school party is easier to organise.'],coach:'Compara y justifica.'},
   {milo:'Okay, let’s choose one. What do you decide?',choices:['Let’s choose the picnic. We can bring food and games.','I vote for the games afternoon because it is simple.','Let’s have the school party and make a music playlist.'],coach:'Toma una decisión final y añade un detalle.'}
 ]}
];
const EXAM=[
 {part:1,label:'Parte 1 · Entrevista',prompt:'Tell me about your school and one thing you enjoy doing there.',seconds:45},
 {part:2,label:'Parte 2 · Describir',prompt:'Imagine two young people preparing food together. Describe what they are doing and what the situation may be like.',seconds:60},
 {part:3,label:'Parte 3 · Discusión',prompt:'Your class wants to celebrate the end of term. Talk about different activities the class could do and choose one.',seconds:90},
 {part:4,label:'Parte 4 · Conversación',prompt:'Do you prefer spending your free time indoors or outdoors? Why? Give examples.',seconds:60}
];
function modeBar(){return `<div class="v17-modebar" role="tablist" aria-label="Modo de Speaking"><button class="${V17.mode==='learn'?'active':''}" data-v17-mode="learn">🌱 Aprender</button><button class="${V17.mode==='conversation'?'active':''}" data-v17-mode="conversation">💬 Conversar</button><button class="${V17.mode==='exam'?'active':''}" data-v17-mode="exam">🏁 Simular examen</button></div>`}
function injectModeBar(){const head=document.querySelector('.screen-head');if(!head||document.querySelector('.v17-modebar'))return;head.insertAdjacentHTML('afterend',modeBar())}
function conversationScreen(){const s=SCENARIOS[Math.max(0,Math.min(SCENARIOS.length-1,V17.scenario||0))],t=Math.max(0,Math.min(s.turns.length-1,V17.turn||0)),q=s.turns[t],progress=Math.round(((t+1)/s.turns.length)*100);
 el(`<div class="app-shell">${topBar()}<main class="container">${screenHead('Speaking Adventure','Conversa por turnos. Puedes elegir una respuesta o crear la tuya.')}${modeBar()}
 <section class="card v17-scenario-hero"><div class="v17-scene-icon">${s.icon}</div><div><span class="mission-label">${E(s.place)}</span><h2>${E(s.title)}</h2><p>${E(s.goal)}</p></div><div class="v17-turn-orb"><b>${t+1}/${s.turns.length}</b><span>turnos</span></div></section>
 <div class="v17-scenario-tabs">${SCENARIOS.map((x,i)=>`<button class="${i===V17.scenario?'active':''}" data-v17-scenario="${i}" title="${E(x.title)}"><span>${x.icon}</span><small>${E(x.title)}</small></button>`).join('')}</div>
 <div class="progress v17-conv-progress"><span style="width:${progress}%"></span></div>
 <section class="card v17-dialog-card"><div class="v17-speaker"><img src="assets/mascot.svg" alt="Milo"/><div><b>Milo</b><p>${E(q.milo)}</p></div><button class="btn btn-soft mini" data-v17-hear="${E(q.milo)}">🔊</button></div>
 <div class="v17-coach-note"><b>🎯 Tu objetivo:</b> ${E(q.coach)}</div>
 <h3>Elige una respuesta que te guste</h3><div class="v17-choice-grid">${q.choices.map((c,i)=>`<button class="v17-choice" data-v17-choice="${i}"><span>${String.fromCharCode(65+i)}</span>${E(c)}</button>`).join('')}</div>
 <div class="v17-or"><span>o crea la tuya</span></div>
 <textarea id="v17FreeAnswer" class="textarea" placeholder="Write your answer here, or use the microphone..."></textarea>
 <div class="row"><button class="btn btn-primary" data-v17-speak-free>🎙️ Hablar</button><button class="btn btn-soft" data-v17-send-free>Enviar mi respuesta</button></div>
 <div id="v17ConversationFeedback" aria-live="polite"></div></section>
 <section class="card v17-safe-note"><b>🌿 Aquí estás aprendiendo.</b><span>Puedes escuchar a Milo, probar otra respuesta y equivocarte sin perder progreso.</span></section>
 </main></div>`)}
function feedbackFor(text,free){const words=String(text||'').trim().split(/\s+/).filter(Boolean);const low=String(text||'').toLowerCase();const reason=/\b(because|so|as)\b/.test(low),question=/\?$|\b(what|when|where|who|how|which|do you|would you|can you)\b/.test(low);let score=Math.min(100,50+Math.min(25,words.length*2)+(reason?15:0)+(question?10:0));const tip=words.length<5?'Añade una frase más para que la conversación siga.':reason?'Muy bien: diste una idea y una razón.':'Muy bien. Para enriquecerla, puedes añadir “because…” o un detalle.';return{score,tip,free}}
function acceptConversation(text,free){const s=SCENARIOS[V17.scenario],turn=V17.turn,r=feedbackFor(text,free);V17.history.push({at:new Date().toISOString(),scenario:V17.scenario,turn,text,free,score:r.score});V17.stats.turns++;if(free)V17.stats.freeAnswers++;save17();const host=document.getElementById('v17ConversationFeedback');if(host)host.innerHTML=`<div class="feedback ok"><b>🌟 Turno completado</b><p>“${E(text)}”</p><p>${E(r.tip)}</p><button class="btn btn-primary" data-v17-next-turn>${turn>=s.turns.length-1?'Completar escenario ✓':'Escuchar siguiente turno →'}</button></div>`;bind17()}
function nextTurn(){const s=SCENARIOS[V17.scenario];if(V17.turn<s.turns.length-1){V17.turn++;save17();render();return}V17.stats.completedScenarios++;V17.turn=0;V17.scenario=(V17.scenario+1)%SCENARIOS.length;save17();window.toast?.('🎉 Escenario completado. ¡Ganaste práctica de conversación!');render()}
function examScreen(){const ex=V17.exam;if(!ex.active){el(`<div class="app-shell">${topBar()}<main class="container">${screenHead('Speaking Exam Practice','Simulación individual de las 4 partes, sin pistas ni modelos.')}${modeBar()}<section class="card v17-exam-start"><div class="v17-scene-icon">🏁</div><h2>¿Listo para practicar sin ayudas?</h2><p>Este modo oculta modelos, pistas y respuestas sugeridas. Son 4 tareas. Puedes hablar con el micrófono o escribir una transcripción.</p><div class="notice"><b>Importante:</b> es una simulación individual de práctica. El Speaking oficial incluye interacción con examinadores y otro candidato.</div><button class="btn btn-primary" data-v17-start-exam>Empezar las 4 partes</button></section></main></div>`);return}
 const i=Math.max(0,Math.min(3,ex.part||0)),q=EXAM[i],ans=ex.answers[i]||'';
 el(`<div class="app-shell">${topBar()}<main class="container">${screenHead('Speaking Exam Practice',`${q.label} · sin pistas`)}${modeBar()}<section class="card v17-exam-card"><div class="row between"><span class="badge">${E(q.label)}</span><span class="v17-exam-time">⏱ ${q.seconds}s sugeridos</span></div><div class="prompt">${E(q.prompt)}</div><textarea id="v17ExamAnswer" class="textarea" placeholder="Tu transcripción puede aparecer aquí. En examen real, responde hablando.">${E(ans)}</textarea><div class="row"><button class="btn btn-primary" data-v17-exam-speak>🎙️ Responder hablando</button><button class="btn btn-soft" data-v17-exam-next>${i===3?'Finalizar simulación':'Guardar y siguiente →'}</button></div><div class="small">No se muestran ayudas durante esta simulación. La transcripción sirve para revisar estructura y contenido después.</div></section></main></div>`)}
function finishExam(){const answers=V17.exam.answers.slice();const details=answers.map((a,i)=>{const w=String(a||'').trim().split(/\s+/).filter(Boolean).length;const low=String(a||'').toLowerCase(),reason=/\b(because|so|as)\b/.test(low),link=/\b(and|but|also|however|then)\b/.test(low);return{part:i+1,words:w,developed:w>=12,reason,link}});const score=Math.round(details.reduce((s,d)=>s+(d.developed?15:5)+(d.reason?7:0)+(d.link?3:0),0)),at=new Date().toISOString();V17.exam.completed.push({at,answers,details,score});V17.exam={active:false,part:0,startedAt:null,answers:[],completed:V17.exam.completed};save17();if(window.data){data.speaking=data.speaking||[];data.speaking.push({date:at,part:0,score:score/5,score_pct:score,metrics:{structure_score:score,parts_completed:details.filter(d=>d.words>0).length},rubric:{global_achievement:Math.round(score/20)},source:'v17-speaking-exam'});data.mockAttempts=data.mockAttempts||[];data.mockAttempts.push({date:at,skill:'speaking',score,total:4,source:'v17-speaking-exam'});window.save?.(true).then(()=>window.PETQUEST_V468?.refresh?.(100))}
 el(`<div class="app-shell">${topBar()}<main class="container">${screenHead('Speaking Exam Review','Revisa tu desarrollo antes de volver al modo aprendizaje.')}${modeBar()}<section class="card"><h2>🏁 Simulación completada</h2><div class="v17-exam-summary"><div><b>${score}%</b><small>desarrollo estructural</small></div><div><b>${details.filter(d=>d.developed).length}/4</b><small>respuestas desarrolladas</small></div><div><b>${details.filter(d=>d.reason).length}/4</b><small>con razón</small></div></div><p class="small">Esta revisión evalúa longitud y estructura de la transcripción. No es una puntuación oficial ni mide pronunciación acústica.</p></section>${details.map((d,i)=>`<section class="card"><h3>Parte ${i+1}</h3><p>${E(answers[i]||'Sin transcripción')}</p><div class="v17-review-chips"><span>${d.developed?'✅':'🌱'} Desarrollo</span><span>${d.reason?'✅':'🌱'} Razón</span><span>${d.link?'✅':'🌱'} Conectores</span><span>${d.words} palabras</span></div></section>`).join('')}<button class="btn btn-primary" data-v17-mode="learn">Volver a aprender con Milo</button></main></div>`);bind17()}
function speakingV17(){if(V17.mode==='conversation')return conversationScreen();if(V17.mode==='exam')return examScreen();v16Speaking();requestAnimationFrame(()=>{injectModeBar();bind17()})}
function adultInsight17(){const kidMode=document.documentElement.classList.contains('v15-kid') || (window.V10&&V10.mode==='kid');if(kidMode||state.view!=='home')return;const main=document.querySelector('main.container');if(!main||main.querySelector('.v17-adult-insight'))return;const last=V17.exam.completed?.slice(-1)[0];main.insertAdjacentHTML('beforeend',`<section class="card v17-adult-insight"><h2>💬 Conversation V17</h2><div class="v16-summary-grid"><div><b>${V17.stats.turns||0}</b><small>turnos conversados</small></div><div><b>${V17.stats.completedScenarios||0}</b><small>escenarios completados</small></div><div><b>${V17.stats.freeAnswers||0}</b><small>respuestas propias</small></div><div><b>${last?last.score:'—'}${last?'%':''}</b><small>última simulación</small></div></div><p class="small">La simulación oral analiza estructura de la transcripción; no sustituye evaluación humana ni medición acústica de pronunciación.</p></section>`)}
function bind17(){
 document.querySelectorAll('[data-v17-mode]').forEach(b=>b.onclick=()=>{V17.mode=b.dataset.v17Mode;save17();if(V17.mode!=='exam')V17.exam.active=false;render()});
 document.querySelectorAll('[data-v17-scenario]').forEach(b=>b.onclick=()=>{V17.scenario=+b.dataset.v17Scenario;V17.turn=0;save17();render()});
 document.querySelectorAll('[data-v17-hear]').forEach(b=>b.onclick=()=>say(b.dataset.v17Hear));
 document.querySelectorAll('[data-v17-choice]').forEach(b=>b.onclick=()=>{const s=SCENARIOS[V17.scenario],q=s.turns[V17.turn],text=q.choices[+b.dataset.v17Choice];document.querySelectorAll('.v17-choice').forEach(x=>x.classList.toggle('selected',x===b));say(text);acceptConversation(text,false)});
 document.querySelector('[data-v17-speak-free]')?.addEventListener('click',()=>recognize(text=>{const t=document.getElementById('v17FreeAnswer');if(t)t.value=text}));
 document.querySelector('[data-v17-send-free]')?.addEventListener('click',()=>{const t=document.getElementById('v17FreeAnswer');if(!t||!t.value.trim())return window.toast?.('Escribe o di una respuesta primero');acceptConversation(t.value.trim(),true)});
 document.querySelector('[data-v17-next-turn]')?.addEventListener('click',nextTurn);
 document.querySelector('[data-v17-start-exam]')?.addEventListener('click',()=>{V17.exam.active=true;V17.exam.part=0;V17.exam.startedAt=new Date().toISOString();V17.exam.answers=[];save17();render()});
 document.querySelector('[data-v17-exam-speak]')?.addEventListener('click',()=>recognize(text=>{const t=document.getElementById('v17ExamAnswer');if(t)t.value=text}));
 document.querySelector('[data-v17-exam-next]')?.addEventListener('click',()=>{const t=document.getElementById('v17ExamAnswer');V17.exam.answers[V17.exam.part]=t?.value.trim()||'';if(V17.exam.part<3){V17.exam.part++;save17();render()}else finishExam()});
}
const v16Speaking=speaking;
speaking=speakingV17;
const renderBeforeV17=render;
render=function(){renderBeforeV17();requestAnimationFrame(()=>{if(state.view==='speaking')bind17();adultInsight17()})};
window.PETQUEST_V17={state:V17,scenarios:SCENARIOS,exam:EXAM,feedbackFor,version:'17.0'};
requestAnimationFrame(()=>{if(state.view==='speaking')render();else adultInsight17()});
})();
