/* PET Quest V40.2 - Cambridge-format fidelity corrections.
   Original PET Quest content. No official Cambridge questions/audio are included. */
(function(){
'use strict';
const KEY='petquest_v40_2_fidelity';
const DEFAULT={reading:{active:false,part:1,answers:{},startedAt:null,finished:[]},listening:{active:false,stage:'p1',index:0,answers:{},plays:{},strictTwoPlay:false,volume:0.72,speed:1,startedAt:null,finished:[]},openDrafts:{},speakingReviews:[]};
let F;
try{F=Object.assign({},DEFAULT,JSON.parse(localStorage.getItem(KEY)||'{}'));F.reading=Object.assign({},DEFAULT.reading,F.reading||{});F.listening=Object.assign({},DEFAULT.listening,F.listening||{});F.openDrafts=F.openDrafts||{};F.speakingReviews=F.speakingReviews||[]}catch(_){F=JSON.parse(JSON.stringify(DEFAULT))}
function save(){localStorage.setItem(KEY,JSON.stringify(F))}
function E(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function norm(s){return String(s||'').trim().toLowerCase().replace(/^[\s.,;:!?]+|[\s.,;:!?]+$/g,'')}
function oneWord(s){return /^[A-Za-z]+(?:['-][A-Za-z]+)?$/.test(String(s||'').trim())}
function pctn(a,b){return b?Math.round(a/b*100):0}
let readTimer=null,listenTimer=null;
function clock(ms){const mm=String(Math.floor(ms/60000)).padStart(2,'0'),ss=String(Math.floor((ms%60000)/1000)).padStart(2,'0');return mm+':'+ss}
function armReadTimer(){clearInterval(readTimer);readTimer=setInterval(()=>{const el=document.getElementById('v402ReadTimer');if(!el){clearInterval(readTimer);return}const remain=Math.max(0,45*60*1000-(Date.now()-F.reading.startedAt));el.textContent=clock(remain);if(remain<=0){clearInterval(readTimer);finishReadingExact()}},1000)}
function armListenTimer(){clearInterval(listenTimer);listenTimer=setInterval(()=>{const el=document.getElementById('v402ListenTimer');if(!el){clearInterval(listenTimer);return}const remain=Math.max(0,30*60*1000-(Date.now()-F.listening.startedAt));el.textContent=clock(remain);if(remain<=0){clearInterval(listenTimer);finishListeningExact()}},1000)}

const RP1=(BANK.reading||[]).filter(q=>q.part===1).slice(0,5);
const RP2={
 people:[
  ['1','Maya wants a free activity after school. She enjoys making things and prefers to be indoors.','A'],
  ['2','Leo wants to practise English online with teenagers twice a week, but never on Fridays.','B'],
  ['3','Nora loves animals and wants an outdoor Saturday activity that costs nothing.','C'],
  ['4','Sam enjoys music and wants an evening activity where beginners can join without owning an instrument.','D'],
  ['5','Ella wants exercise on Sunday morning and prefers an activity she can do with a friend.','E']
 ],
 options:[
  ['A','Creative Lab','Free craft club, Tue/Thu 4 p.m., indoors. Materials included.'],
  ['B','Teen Talk Online','Live conversation club, Tue/Thu evenings. Ages 12-16.'],
  ['C','Park Wildlife Walk','Free Saturday morning walk with a local nature guide.'],
  ['D','Try Music Night','Wednesday 6 p.m. Beginners welcome; instruments provided.'],
  ['E','Sunday Fitness Pair','Sunday 10 a.m. circuit session; bring a friend at no extra cost.'],
  ['F','Friday Film Club','Watch and discuss a film every Friday after school.'],
  ['G','Horse Skills','Outdoor riding lesson Saturday afternoon; fee required.'],
  ['H','Solo Running Plan','Downloadable individual running plan for any day.']
 ]
};
const RP3={text:`Last year, students at Westbridge School asked for a place where they could work on personal projects after lessons. The school opened a small 'makerspace' with simple tools, recycled materials and computers. At first, teachers expected students mainly to build science models, but the room quickly became popular for many different ideas. One group repaired old bicycles for a charity, while another designed signs for the school garden. Students say the best part is being allowed to test an idea, make mistakes and try again. Teachers have noticed another benefit: students from different year groups now work together more often. The school plans to keep the room open later next term, although it will still close on Fridays so that equipment can be checked safely.`,qs:[
 ['What was the original reason for opening the makerspace?',['To give students somewhere for their own projects','To replace science lessons','To store old computers','To run a bicycle business'],0,'detail'],
 ['What surprised the teachers?',['Students used the room for a wide range of projects','Students refused to use computers','Only older students visited','The charity closed'],0,'inference'],
 ['What do students value most?',['Receiving prizes','Avoiding mistakes','Being able to experiment','Working only with friends'],2,'main-idea'],
 ['What additional benefit have teachers noticed?',['Different age groups cooperate more','Students finish school earlier','The garden needs fewer signs','All equipment is new'],0,'detail'],
 ['Why will the room still close on Fridays?',['For staff training','For equipment safety checks','Because students requested it','Because the school finishes early'],1,'purpose']
]};
const RP4={
 before:`Five students created a podcast about life at their school. At first, they thought recording would be the difficult part. [1] The group therefore spent several days deciding exactly who their listeners would be. Once they had a clear audience, choosing topics became easier. [2] They also learned that a good interview needs more than a list of questions. [3] After recording, the students listened to everything again before editing. [4] Finally, they published the episode on the school website. [5] Their teacher says the project worked because everyone had a clear job and listened to each other's ideas.`,
 gaps:{1:'C',2:'F',3:'A',4:'H',5:'D'},
 options:[
  ['A','They practised responding naturally when an answer led to an unexpected subject.'],
  ['B','The school had recently bought several new sports uniforms.'],
  ['C','However, they soon discovered that planning the content came first.'],
  ['D','Within a week, messages from students in other classes began to arrive.'],
  ['E','One student decided that podcasts were less interesting than books.'],
  ['F','For example, they chose short stories about clubs, projects and school events.'],
  ['G','The website was unavailable during the summer holiday.'],
  ['H','This helped them remove repeated ideas and parts that were difficult to hear.']
 ]
};
const RP5={parts:[
 ['Our class recently started a small garden behind the sports hall. We chose the area because it was ___ (1) enough to get sunlight for most of the day.','bright',['bright','heavy','deep','noisy'],0],
 ['At first, nobody was sure which plants would ___ (2) best there.','grow',['grow','rise','lift','increase'],0],
 ['A local gardener came to school and ___ (3) us some useful advice.','gave',['gave','made','did','took'],0],
 ['She explained that herbs were a good choice ___ (4) they are easy to look after.','because',['because','although','unless','before'],0],
 ['Now students take ___ (5) watering the plants each morning.','turns',['turns','times','places','parts'],0],
 ['We hope to use some of the herbs in the school café when they are ready to be ___ (6).','picked',['picked','caught','reached','held'],0]
]};
const RP6={textParts:['My sister wants to be ',' engineer when she grows up. She has always been interested ',' how machines work. Last month, she joined a weekend engineering club, ',' meets every Saturday. There are not ',' girls in the group yet, but she hopes more will join. She says the projects are difficult, ',' she enjoys solving problems with the other students. She would like to study engineering at university ',' the future.'],answers:['an','in','which','many','but','in']};

function readingPartMarks(){return {1:5,2:5,3:5,4:5,5:6,6:6}}
function readingAnswered(part){const a=F.reading.answers; if(part===1)return RP1.filter((_,i)=>a['p1_'+i]!==undefined).length;if(part===2)return RP2.people.filter((_,i)=>a['p2_'+i]).length;if(part===3)return RP3.qs.filter((_,i)=>a['p3_'+i]!==undefined).length;if(part===4)return [1,2,3,4,5].filter(i=>a['p4_'+i]).length;if(part===5)return RP5.parts.filter((_,i)=>a['p5_'+i]!==undefined).length;return RP6.answers.filter((_,i)=>String(a['p6_'+i]||'').trim()).length}
function readingScore(){let c=0,total=32,a=F.reading.answers;RP1.forEach((q,i)=>{if(+a['p1_'+i]===q.a)c++});RP2.people.forEach((p,i)=>{if(a['p2_'+i]===p[2])c++});RP3.qs.forEach((q,i)=>{if(+a['p3_'+i]===q[2])c++});Object.entries(RP4.gaps).forEach(([g,ans])=>{if(a['p4_'+g]===ans)c++});RP5.parts.forEach((p,i)=>{if(+a['p5_'+i]===p[3])c++});RP6.answers.forEach((ans,i)=>{if(norm(a['p6_'+i])===ans)c++});return {correct:c,total,score:pctn(c,total)}}
function readingNav(){return `<div class="v402-partnav">${[1,2,3,4,5,6].map(p=>`<button class="${F.reading.part===p?'active':''}" data-v402-rpart="${p}">Parte ${p}<small>${readingAnswered(p)}/${readingPartMarks()[p]}</small></button>`).join('')}</div>`}
function readInput(key,value='',ph='Escribe una palabra'){return `<input class="v402-gap-input" data-v402-rtext="${key}" value="${E(value)}" autocomplete="off" spellcheck="false" placeholder="${E(ph)}">`}
function readingPartHtml(){const p=F.reading.part,a=F.reading.answers;
 if(p===1)return `<h2>Parte 1 · Multiple choice</h2><p class="small">Lee cinco textos breves y elige el mensaje correcto.</p>${RP1.map((q,i)=>`<article class="v402-task"><div class="v402-source">${E(q.notice)}</div><b>${i+1}. ${E(q.q)}</b><div class="options">${q.opts.map((o,j)=>`<button class="option ${+a['p1_'+i]===j?'selected':''}" data-v402-rmc="p1_${i}:${j}">${String.fromCharCode(65+j)}. ${E(o)}</button>`).join('')}</div></article>`).join('')}`;
 if(p===2)return `<h2>Parte 2 · Matching</h2><p class="small">Relaciona las cinco personas con una de las ocho actividades. Hay tres opciones extra.</p><div class="v402-match-options">${RP2.options.map(o=>`<div><b>${o[0]}. ${E(o[1])}</b><span>${E(o[2])}</span></div>`).join('')}</div>${RP2.people.map((x,i)=>`<article class="v402-task"><b>${x[0]}. ${E(x[1])}</b><select data-v402-rselect="p2_${i}"><option value="">Elige A-H</option>${RP2.options.map(o=>`<option value="${o[0]}" ${a['p2_'+i]===o[0]?'selected':''}>${o[0]}</option>`).join('')}</select></article>`).join('')}`;
 if(p===3)return `<h2>Parte 3 · Longer text multiple choice</h2><div class="v402-longtext">${E(RP3.text)}</div>${RP3.qs.map((q,i)=>`<article class="v402-task"><b>${i+1}. ${E(q[0])}</b><div class="options">${q[1].map((o,j)=>`<button class="option ${+a['p3_'+i]===j?'selected':''}" data-v402-rmc="p3_${i}:${j}">${String.fromCharCode(65+j)}. ${E(o)}</button>`).join('')}</div></article>`).join('')}`;
 if(p===4){let txt=E(RP4.before);[1,2,3,4,5].forEach(g=>{txt=txt.replace('['+g+']',`<select class="v402-inline-select" data-v402-rselect="p4_${g}"><option value="">${g}</option>${RP4.options.map(o=>`<option value="${o[0]}" ${a['p4_'+g]===o[0]?'selected':''}>${o[0]}</option>`).join('')}</select>`)});return `<h2>Parte 4 · Gapped text</h2><p class="small">Completa cinco espacios con cinco de las ocho frases. Hay tres frases extra.</p><div class="v402-sentence-bank">${RP4.options.map(o=>`<div><b>${o[0]}</b><span>${E(o[1])}</span></div>`).join('')}</div><div class="v402-longtext">${txt}</div>`}
 if(p===5){let body=RP5.parts.map((x,i)=>{const before=E(x[0].split('___')[0]),after=E(x[0].split('___')[1]||'');return `<p>${before}<select class="v402-inline-select" data-v402-rmc-select="p5_${i}"><option value="">${i+1}</option>${x[2].map((o,j)=>`<option value="${j}" ${+a['p5_'+i]===j?'selected':''}>${E(o)}</option>`).join('')}</select>${after}</p>`}).join('');return `<h2>Parte 5 · Multiple-choice cloze</h2><p class="small">Elige la opción correcta para cada uno de los seis espacios.</p><div class="v402-longtext">${body}</div>`}
 let text='';RP6.answers.forEach((ans,i)=>{text+=E(RP6.textParts[i])+readInput('p6_'+i,a['p6_'+i]||'',String(i+1));});text+=E(RP6.textParts[6]);return `<h2>Parte 6 · Open cloze</h2><p class="small"><b>Escribe UNA palabra en cada espacio.</b> No hay opciones: debes producir la respuesta.</p><div class="v402-longtext v402-opencloze">${text}</div><div class="notice"><b>Fidelidad PET:</b> seis espacios · una palabra por espacio.</div>`}
function startReadingExact(){F.reading={active:true,part:1,answers:{},startedAt:Date.now(),finished:F.reading.finished||[]};save();state.view='practice';state.skill='reading';if(window.PETQUEST_V19)PETQUEST_V19.state.mode='exam';render()}
function finishReadingExact(){const s=readingScore(),rec={at:new Date().toISOString(),...s,answers:{...F.reading.answers},source:'v40.2-exact-reading'};F.reading.finished.push(rec);F.reading.active=false;save();data.mockAttempts.push({date:rec.at,skill:'reading',score:s.score,correct:s.correct,total:32,source:'v40.2-exact-reading'});save();el(`<div class="app-shell">${topBar()}<main class="container">${screenHead('Reading Exam Review · V40.2','Interacciones corregidas por parte')}<section class="card highlight"><div class="label">RESULTADO</div><div class="big-number">${s.score}%</div><p>${s.correct}/32 correctas</p></section><section class="card"><h2>Corrección de fidelidad</h2><p>Parte 6 fue evaluada como <b>open cloze</b>: una palabra producida por el alumno en cada espacio.</p><button class="btn btn-primary" data-v402-reading-restart>Repetir Reading</button></section></main></div>`);bind402()}
function readingExactScreen(){if(!F.reading.active){el(`<div class="app-shell">${topBar()}<main class="container">${screenHead('Reading Exam · formato fiel','6 partes · 32 preguntas · 45 minutos')}<section class="card"><h2>Interacciones por parte</h2><p>Part 1 multiple choice · Part 2 matching · Part 3 longer-text multiple choice · Part 4 gapped text · Part 5 multiple-choice cloze · <b>Part 6 open cloze</b>.</p><button class="btn btn-primary" data-v402-reading-start>Empezar Reading fiel</button></section></main></div>`);return}
 const elapsed=Date.now()-F.reading.startedAt,remain=Math.max(0,45*60*1000-elapsed);if(remain<=0)return finishReadingExact();el(`<div class="app-shell">${topBar()}<main class="container"><div class="mock-top"><div><h1>Reading Exam · V40.2</h1><p>32 puntos · Parte ${F.reading.part}/6</p></div><div class="timer" id="v402ReadTimer">${clock(remain)}</div></div>${readingNav()}<section class="card question-card">${readingPartHtml()}<div class="row action-row"><button class="btn btn-ghost" data-v402-rprev ${F.reading.part===1?'disabled':''}>← Parte anterior</button><button class="btn btn-primary" data-v402-rnext>${F.reading.part===6?'Finalizar':'Guardar y seguir →'}</button></div></section></main></div>`);armReadTimer()}

const LP1=(BANK.listening||[]).filter(q=>q.part===1).slice(0,7).map((q,i)=>({...q,audioFile:`assets/audio/fidelity/lp1_${i+1}_clean.wav`}));
const LP2=(BANK.listening||[]).filter(q=>q.part===2).slice(0,6).map((q,i)=>({...q,audioFile:`assets/audio/fidelity/lp2_${i+1}_clean.wav`}));
const LP3={audioFile:'assets/audio/fidelity/lp3_monologue_clean.wav',script:'',items:[
 ['The visit takes place on', 'Friday', ['friday']],
 ['Students should meet at', '8:30', ['8:30','eight thirty','half past eight']],
 ['The coach will leave from the school', 'car park', ['car park','carpark']],
 ['Everyone should bring a light', 'jacket', ['jacket']],
 ['Lunch will be provided in the', 'cafe', ['cafe','café']],
 ['The group expects to return at about', '5:15', ['5:15','five fifteen','quarter past five']]
]};
const LP4={audioFile:'assets/audio/fidelity/lp4_interview_clean.wav',items:[
 ['Why did Olivia first start volunteering at the community garden?',['A friend invited her','She needed school marks','Her parents worked there'],0],
 ['What did Olivia find difficult at first?',['Using the tools safely','Remembering plant names','Getting there on time'],1],
 ['What does she enjoy most now?',['Working with different people','Growing the biggest vegetables','Spending time alone'],0],
 ['What change has the garden made recently?',['It opens earlier','It gives food to a local café','It runs activities for younger children'],2],
 ['What does Olivia say about bad weather?',['It sometimes makes the work harder','It usually cancels the session','She prefers working in rain'],0],
 ['What would Olivia like to do next?',['Learn more about cooking','Design a new garden area','Become a science teacher'],1]
]};

function visualFor(q,o,j){
 const f=q.focus||'';
 const icon=f==='time'?'🕒':f==='places'?'📍':f==='numbers'?'🔢':f==='objects'?(j===0?'🧴':j===1?'🍱':'🧢'):'🖼️';
 return `<div class="v402-visual-card"><div class="v402-visual-icon">${icon}</div><div>${E(o)}</div></div>`
}

function lStages(){return ['p1','p2','p3','p4']}
let activeAudio=null,activeAudioPath='';
function audioFor(path){if(!activeAudio||activeAudioPath!==path){if(activeAudio){activeAudio.pause()}activeAudio=new Audio(path);activeAudioPath=path;const rate=Number(F.listening.speed??1),vol=Number(F.listening.volume??0.72);if(window.PETAudioSafe)PETAudioSafe.configure(activeAudio,{rate,volume:vol});else{activeAudio.preload='auto';activeAudio.playbackRate=rate;activeAudio.volume=Math.min(0.85,vol)}}return activeAudio}
function playAudioFile(path,key){const n=F.listening.plays[key]||0;const strict=!!F.listening.strictTwoPlay&&!String(key).startsWith('learn_');if(strict&&n>=2){window.toast?.('Simulación estricta: máximo 2 escuchas. Desactívala para repetición libre.');return}F.listening.plays[key]=n+1;save();const a=audioFor(path);a.currentTime=0;a.play().catch(()=>window.toast?.('No se pudo reproducir el audio empaquetado.'));const c=document.getElementById('v402PlayCount');if(c)c.textContent=`${F.listening.plays[key]} escuchas · ${strict?'máximo 2':'sin límite'}`}
function pauseAudioFile(){if(activeAudio)activeAudio.pause()}
function restartAudioFile(){if(!activeAudio)return;activeAudio.currentTime=0;activeAudio.play().catch(()=>{})}
function setAudioVolume(v){F.listening.volume=window.PETAudioSafe?PETAudioSafe.volumeValue(v):Math.max(0,Math.min(.85,Number(v)));save();if(activeAudio){if(window.PETAudioSafe)PETAudioSafe.setVolume(activeAudio,F.listening.volume);else activeAudio.volume=F.listening.volume}}
async function setAudioSpeed(v){F.listening.speed=window.PETAudioSafe?PETAudioSafe.rateValue(v):Math.max(.75,Math.min(1.1,Number(v)||1));save();if(activeAudio){if(window.PETAudioSafe)await PETAudioSafe.setRate(activeAudio,F.listening.speed);else activeAudio.playbackRate=F.listening.speed}}
function audioControls(path,key,plays){const strict=!!F.listening.strictTwoPlay&&!String(key).startsWith('learn_');const blocked=strict&&plays>=2;const speed=strict?1:Number(F.listening.speed??1);return `<div class="v18-exam-audio v4610-audio"><button class="btn btn-primary" data-v402-audio="${E(path)}|${E(key)}" ${blocked?'disabled':''}>🔊 ${plays?'Repetir desde el inicio':'Reproducir audio'}</button><button class="btn btn-soft" data-v402-audio-pause>⏸ Pausa</button><button class="btn btn-soft" data-v402-audio-restart>↺ Reiniciar</button><label class="small">Volumen <input type="range" min="0" max="0.85" step="0.05" value="${Math.min(.85,Number(F.listening.volume??.72))}" data-v402-audio-volume></label>${strict?'':`<label class="small">Velocidad <select data-v402-audio-speed>${[.75,.85,1,1.1].map(v=>`<option value="${v}" ${Math.abs(speed-v)<.001?'selected':''}>${v.toFixed(2)}×</option>`).join('')}</select></label>`}<span id="v402PlayCount">${plays} escuchas · ${strict?'máximo 2':'sin límite'}</span></div>`}
function lProgress(){const a=F.listening.answers;let n=0;Object.keys(a).forEach(()=>n++);return n}
function startListeningExact(){F.listening={active:true,stage:'p1',index:0,answers:{},plays:{},strictTwoPlay:!!F.listening.strictTwoPlay,volume:Number(F.listening.volume??0.72),speed:F.listening.strictTwoPlay?1:Number(F.listening.speed??1),startedAt:Date.now(),finished:F.listening.finished||[]};save();state.view='practice';state.skill='listening';if(window.PETQUEST_V18)PETQUEST_V18.state.mode='exam';render()}
function lCorrect(){let c=0,a=F.listening.answers;LP1.forEach((q,i)=>{if(+a['p1_'+i]===q.a)c++});LP2.forEach((q,i)=>{if(+a['p2_'+i]===q.a)c++});LP3.items.forEach((x,i)=>{if(x[2].map(norm).includes(norm(a['p3_'+i])))c++});LP4.items.forEach((q,i)=>{if(+a['p4_'+i]===q[2])c++});return c}
function finishListeningExact(){const c=lCorrect(),score=pctn(c,25),rec={at:new Date().toISOString(),score,correct:c,total:25,answers:{...F.listening.answers},source:'v40.2-exact-listening'};F.listening.finished.push(rec);F.listening.active=false;save();data.mockAttempts.push({date:rec.at,skill:'listening',score,correct:c,total:25,source:'v40.2-exact-listening'});save();el(`<div class="app-shell">${topBar()}<main class="container">${screenHead('Listening Exam Review · V40.2','25 puntos · interacción Part 3 corregida')}<section class="card highlight"><div class="label">RESULTADO</div><div class="big-number">${score}%</div><p>${c}/25 correctas</p></section><section class="card"><p><b>Part 3:</b> monólogo único + seis gap fills escritos por el alumno.</p><button class="btn btn-primary" data-v402-listening-restart>Repetir Listening</button></section></main></div>`);bind402()}
function listeningExactScreen(){if(!F.listening.active){el(`<div class="app-shell">${topBar()}<main class="container">${screenHead('Listening Exam · formato corregido','7 + 6 + 6 + 6 = 25 preguntas')}<section class="card"><h2>Part 3 ahora es Gap Fill</h2><p>El alumno escucha un único monólogo y completa seis espacios. <b>La repetición libre está activada por defecto:</b> puede escuchar cada audio todas las veces que necesite.</p><div class="notice"><b>Modo de escucha:</b> <span>${F.listening.strictTwoPlay?'Simulación estricta · máximo 2 escuchas':'Aprendizaje · repeticiones ilimitadas'}</span><br><button class="btn btn-soft mini" data-v402-strict>${F.listening.strictTwoPlay?'Activar repeticiones ilimitadas':'Activar simulación estricta (2 escuchas)'}</button></div><div class="notice"><b>Audio:</b> el mock usa archivos MP3 empaquetados; no usa SpeechSynthesisUtterance. Los MP3 incluidos son audio de referencia original PET Quest y pueden sustituirse por grabaciones de estudio mediante el mismo manifest.</div><button class="btn btn-primary" data-v402-listening-start>Empezar Listening corregido</button></section></main></div>`);return}
 const elapsed=Date.now()-F.listening.startedAt,remain=Math.max(0,30*60*1000-elapsed);if(remain<=0)return finishListeningExact();const st=F.listening.stage,idx=F.listening.index,a=F.listening.answers;let body='',playPath='',playKey='';
 if(st==='p1'){const q=LP1[idx];playPath=q.audioFile;playKey='p1_'+idx;body=`<h2>Part 1 · Multiple choice</h2><p class="small">Recording ${idx+1}/7</p><div class="prompt">${E(q.q)}</div><div class="options">${q.opts.map((o,j)=>`<button class="option v402-visual-choice ${+a['p1_'+idx]===j?'selected':''}" data-v402-lmc="p1_${idx}:${j}">${visualFor(q,o,j)}</button>`).join('')}</div>`}
 if(st==='p2'){const q=LP2[idx];playPath=q.audioFile;playKey='p2_'+idx;body=`<h2>Part 2 · Multiple choice</h2><p class="small">Dialogue ${idx+1}/6</p><div class="prompt">${E(q.q)}</div><div class="options">${q.opts.map((o,j)=>`<button class="option ${+a['p2_'+idx]===j?'selected':''}" data-v402-lmc="p2_${idx}:${j}">${String.fromCharCode(65+j)}. ${E(o)}</button>`).join('')}</div>`}
 if(st==='p3'){playPath=LP3.audioFile;playKey='p3_shared';body=`<h2>Part 3 · Gap fill</h2><p class="small"><b>Escucha un monólogo y completa seis espacios.</b> Escribe la palabra, número o frase corta que oyes.</p><div class="v402-gap-sheet">${LP3.items.map((x,i)=>`<label><span>${i+1}. ${E(x[0])}</span><input data-v402-ltext="p3_${i}" value="${E(a['p3_'+i]||'')}" autocomplete="off" spellcheck="false" placeholder="respuesta"></label>`).join('')}</div>`}
 if(st==='p4'){playPath=LP4.audioFile;playKey='p4_shared';body=`<h2>Part 4 · Multiple choice</h2><p class="small">Escucha una entrevista y responde las seis preguntas.</p>${LP4.items.map((q,i)=>`<article class="v402-task"><b>${i+1}. ${E(q[0])}</b><div class="options">${q[1].map((o,j)=>`<button class="option ${+a['p4_'+i]===j?'selected':''}" data-v402-lmc="p4_${i}:${j}">${String.fromCharCode(65+j)}. ${E(o)}</button>`).join('')}</div></article>`).join('')}`}
 const plays=F.listening.plays[playKey]||0;el(`<div class="app-shell">${topBar()}<main class="container"><div class="mock-top"><div><h1>Listening Exam · V40.2</h1><p>${lProgress()}/25 respondidas · ${st.toUpperCase()} · ${F.listening.strictTwoPlay?'simulación estricta':'repetición libre'}</p></div><div class="timer" id="v402ListenTimer">${clock(remain)}</div></div><section class="card question-card">${audioControls(playPath,playKey,plays)}<div class="row"><button class="btn btn-ghost mini" data-v402-strict>${F.listening.strictTwoPlay?'♾ Cambiar a ilimitado':'🎓 Simulación estricta: 2 escuchas'}</button></div>${body}<div class="row action-row"><button class="btn btn-primary" data-v402-lnext>Guardar y seguir →</button></div></section></main></div>`);armListenTimer()}

function part6Learning(){const q=currentQuestions()[state.idx],key=q.id,val=F.openDrafts[key]||'',ans=String(q.answerText||q.opts?.[q.a]||'').trim(),checked=F.openDrafts[key+'_checked'],ok=checked&&norm(val)===norm(ans);el(`<div class="app-shell">${topBar()}<main class="container">${screenHead('Reading Lab · Part 6 Open Cloze',`Pregunta ${state.idx+1} de ${currentQuestions().length}`)}<div class="exercise-layout"><section class="card question-card"><div class="notice"><b>Una palabra:</b> produce la respuesta; no hay opciones.</div><div class="v402-open-single">${E(q.notice).replace('___',`<input id="v402OpenLearn" value="${E(val)}" autocomplete="off" spellcheck="false" placeholder="escribe una palabra">`)}</div>${checked?`<div class="feedback ${ok?'ok':'bad'}"><b>${ok?'Correcto':'Revisa la respuesta'}</b><p>${E(q.why)}</p>${!ok?`<p>Respuesta: <b>${E(ans)}</b></p>`:''}</div>`:''}<div class="row action-row"><button class="btn btn-primary" data-v402-open-check ${checked?'disabled':''}>Comprobar</button><button class="btn btn-soft" data-v402-open-next ${!checked?'disabled':''}>Siguiente →</button></div></section><aside class="card side"><h3>Part 6</h3><p>Cambridge exige una palabra por espacio. Aquí entrenas producción, no reconocimiento.</p></aside></div></main></div>`)}
function listeningPart3Learning(){const a=F.listening.answers;el(`<div class="app-shell">${topBar()}<main class="container">${screenHead('Listening Lab · Part 3 Gap Fill','Monólogo · 6 espacios')}<section class="card question-card">${audioControls(LP3.audioFile,'learn_p3',F.listening.plays.learn_p3||0)}<div class="v402-gap-sheet">${LP3.items.map((x,i)=>`<label><span>${i+1}. ${E(x[0])}</span><input data-v402-ltext="p3_${i}" value="${E(a['p3_'+i]||'')}" placeholder="respuesta"></label>`).join('')}</div><button class="btn btn-primary" data-v402-lp3-check>Comprobar 6 espacios</button><div id="v402Lp3Feedback"></div></section></main></div>`)}

function automaticPronunciationAttempts(){const out=[];(window.data?.speaking||[]).forEach(x=>{const score=Number(x?.metrics?.pronunciation_proxy);if(Number.isFinite(score))out.push({score:Math.max(0,Math.min(100,score)),at:x.date||x.created_at,source:x.source==='v46.14-speaking-ai'?'Examinador de voz':'Práctica de pronunciación'})});(window.PETQUEST_V16?.state?.speaking?.attempts||[]).forEach(x=>{const score=Number(x?.score);if(x?.recognized&&Number.isFinite(score))out.push({score:Math.max(0,Math.min(100,score)),at:x.at,source:'Repetición guiada'})});return [...new Map(out.map(x=>[`${x.at||''}|${x.score}`,x])).values()]}
function speakingScoreHtml(){const attempts=automaticPronunciationAttempts(),best=attempts.reduce((a,x)=>!a||x.score>a.score?x:a,null);return `<h2>🎙️ Pronunciación automática</h2>${best?`<div class="v16-speak-hero"><div><p>La aplicación conserva automáticamente tu mejor resultado de pronunciación.</p><p class="small">${E(best.source)}${best.at?` · ${E(new Date(best.at).toLocaleString())}`:''} · ${attempts.length} intento${attempts.length===1?'':'s'} registrado${attempts.length===1?'':'s'}</p></div><div class="v16-score-orb"><b>${Math.round(best.score)}%</b><span>mejor pronunciación</span></div></div>`:'<div class="notice"><b>Sin intentos de pronunciación todavía.</b><p>Repite una frase del modelo o usa el Examinador de voz para registrar tu primera nota.</p></div>'}<div class="notice"><b>Evaluación automática de práctica:</b> se usa una aproximación basada en reconocimiento e inteligibilidad. Los intentos posteriores con menor resultado no reducen tu nota máxima y este porcentaje no es una calificación oficial de Cambridge.</div>`}
function refreshSpeakingScore(){const host=document.querySelector('.v402-speaking-review');if(host)host.innerHTML=speakingScoreHtml()}
function injectSpeakingReview(){if(state.view!=='speaking')return;const main=document.querySelector('main.container');if(!main)return;const existing=main.querySelector('.v402-speaking-review');if(existing){refreshSpeakingScore();return}main.insertAdjacentHTML('beforeend',`<section class="card v402-speaking-review">${speakingScoreHtml()}</section>`)}

const previousPractice=practice;
practice=function(){
 if(state.skill==='reading'){
  const q=currentQuestions?.()?.[state.idx];
  if(window.PETQUEST_V19?.state?.mode==='exam')return readingExactScreen();
  if(q?.part===6)return part6Learning();
 }
 if(state.skill==='listening'){
  const q=currentQuestions?.()?.[state.idx];
  if(window.PETQUEST_V18?.state?.mode==='exam')return listeningExactScreen();
  if(q?.part===3)return listeningPart3Learning();
 }
 return previousPractice();
};
const previousStartMock=startMock;
startMock=function(skill){if(skill==='reading')return startReadingExact();if(skill==='listening')return startListeningExact();return previousStartMock(skill)};
const previousBind=bind;
bind=function(){previousBind();bind402()};
const previousRender=render;
render=function(){previousRender();requestAnimationFrame(()=>{bind402();injectSpeakingReview()})};
function bind402(){
 document.querySelector('[data-v402-reading-start]')?.addEventListener('click',startReadingExact);document.querySelector('[data-v402-reading-restart]')?.addEventListener('click',startReadingExact);
 document.querySelectorAll('[data-v402-rpart]').forEach(b=>b.onclick=()=>{F.reading.part=+b.dataset.v402Rpart;save();render()});
 document.querySelectorAll('[data-v402-rmc]').forEach(b=>b.onclick=()=>{const [k,v]=b.dataset.v402Rmc.split(':');F.reading.answers[k]=+v;save();render()});
 document.querySelectorAll('[data-v402-rselect]').forEach(s=>s.onchange=()=>{F.reading.answers[s.dataset.v402Rselect]=s.value;save()});
 document.querySelectorAll('[data-v402-rmc-select]').forEach(s=>s.onchange=()=>{F.reading.answers[s.dataset.v402RmcSelect]=s.value===''?undefined:+s.value;save()});
 document.querySelectorAll('[data-v402-rtext]').forEach(i=>i.oninput=()=>{F.reading.answers[i.dataset.v402Rtext]=i.value;save()});
 document.querySelector('[data-v402-rprev]')?.addEventListener('click',()=>{F.reading.part=Math.max(1,F.reading.part-1);save();render()});document.querySelector('[data-v402-rnext]')?.addEventListener('click',()=>{if(F.reading.part<6){F.reading.part++;save();render()}else finishReadingExact()});
 document.querySelector('[data-v402-listening-start]')?.addEventListener('click',startListeningExact);document.querySelector('[data-v402-listening-restart]')?.addEventListener('click',startListeningExact);
 document.querySelectorAll('[data-v402-lmc]').forEach(b=>b.onclick=()=>{const [k,v]=b.dataset.v402Lmc.split(':');F.listening.answers[k]=+v;save();render()});document.querySelectorAll('[data-v402-ltext]').forEach(i=>i.oninput=()=>{F.listening.answers[i.dataset.v402Ltext]=i.value;save()});
 document.querySelector('[data-v402-audio]')?.addEventListener('click',e=>{const [path,key]=e.currentTarget.dataset.v402Audio.split('|');playAudioFile(path,key)});document.querySelector('[data-v402-audio-pause]')?.addEventListener('click',pauseAudioFile);document.querySelector('[data-v402-audio-restart]')?.addEventListener('click',restartAudioFile);document.querySelector('[data-v402-audio-volume]')?.addEventListener('input',e=>setAudioVolume(e.target.value));document.querySelector('[data-v402-audio-speed]')?.addEventListener('change',e=>setAudioSpeed(e.target.value));document.querySelector('[data-v402-strict]')?.addEventListener('click',()=>{F.listening.strictTwoPlay=!F.listening.strictTwoPlay;if(F.listening.strictTwoPlay)F.listening.speed=1;save();render()});
 document.querySelector('[data-v402-lnext]')?.addEventListener('click',()=>{const st=F.listening.stage;if(st==='p1'&&F.listening.index<6)F.listening.index++;else if(st==='p1'){F.listening.stage='p2';F.listening.index=0}else if(st==='p2'&&F.listening.index<5)F.listening.index++;else if(st==='p2'){F.listening.stage='p3';F.listening.index=0}else if(st==='p3'){F.listening.stage='p4';F.listening.index=0}else finishListeningExact();save();render()});
 const ol=document.getElementById('v402OpenLearn');if(ol)ol.oninput=()=>{const q=currentQuestions()[state.idx];if(!q)return;F.openDrafts[q.id]=ol.value;save()};const openCheck=document.querySelector('[data-v402-open-check]');if(openCheck)openCheck.onclick=()=>{const q=currentQuestions()[state.idx];if(!q){render();return}const v=F.openDrafts[q.id]||'';if(!oneWord(v)){window.toast?.('Escribe una sola palabra');return}F.openDrafts[q.id+'_checked']=true;const ans=q.answerText||q.opts?.[q.a]||'';const correct=norm(v)===norm(ans);data.history.push({date:new Date().toISOString(),qid:q.id,skill:'reading',level:q.level,focus:q.focus,correct,answerText:v,source:'v40.2-open-cloze'});save();if(typeof window.save==='function')window.save(true);render()};const openNext=document.querySelector('[data-v402-open-next]');if(openNext)openNext.onclick=()=>{const qs=currentQuestions(),q=qs[state.idx];if(!q){render();return}delete F.openDrafts[q.id+'_checked'];state.idx=Math.min(state.idx+1,qs.length);state.selected=null;state.checked=false;save();render()};
 document.querySelector('[data-v402-lp3-check]')?.addEventListener('click',()=>{let c=0;LP3.items.forEach((x,i)=>{if(x[2].map(norm).includes(norm(F.listening.answers['p3_'+i])))c++});document.getElementById('v402Lp3Feedback').innerHTML=`<div class="feedback ${c>=4?'ok':'bad'}"><b>${c}/6 correctas</b><p>Revisa los espacios y vuelve a escuchar el monólogo si lo necesitas.</p></div>`});
}
window.PETQUEST_V40_2={state:F,version:'40.2',readingScore,lCorrect,automaticPronunciationAttempts,refreshSpeakingScore};
requestAnimationFrame(()=>{bind402();injectSpeakingReview()});
})();
