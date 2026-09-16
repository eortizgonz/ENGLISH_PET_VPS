// PET Quest V11 — Adventure Map, rewards, avatars and guided micro-sessions.
const V11_STORE='petQuestV11Ux';
const V11_DEFAULT={avatar:'owl',stars:0,chests:0,completedMissions:0,sessionMinutes:8,lastCelebration:'',introDone:false};
let V11=(()=>{try{return {...V11_DEFAULT,...JSON.parse(localStorage.getItem(V11_STORE)||'{}')}}catch{return {...V11_DEFAULT}}})();
const V11_AVATARS={owl:['🦉','Milo'],fox:['🦊','Foxy'],panda:['🐼','Panda'],lion:['🦁','Leo']};
const V11_WORLDS=[
 {id:'reading',title:'Bosque de las Historias',sub:'Reading',icon:'📖',img:'assets/reading.svg',goal:10},
 {id:'listening',title:'Bahía de los Sonidos',sub:'Listening',icon:'🎧',img:'assets/listening.svg',goal:20},
 {id:'writing',title:'Taller de las Ideas',sub:'Writing',icon:'✍️',img:'assets/writing.svg',goal:35},
 {id:'speaking',title:'Isla de la Voz',sub:'Speaking',icon:'🎙️',img:'assets/speaking.svg',goal:50},
 {id:'mock',title:'Castillo PET',sub:'Mock Exam',icon:'🏰',img:'assets/mascot.svg',goal:65}
];
function v11Save(){localStorage.setItem(V11_STORE,JSON.stringify(V11))}
function v11Kid(){return typeof uxMode==='function'&&uxMode()==='kid'&&!(typeof data!=='undefined'&&data.profile?.examProfile==='adult')}
function v11Avatar(){return V11_AVATARS[V11.avatar]||V11_AVATARS.owl}
function v11Progress(){return Math.max(0,Math.min(100,typeof readiness==='function'?readiness():0))}
function v11MissionTarget(){const m=typeof uxMission==='function'?uxMission():{go:'reading'};return m.go||((m.action==='review'||m.action==='answers')?'reading':'reading')}
function v11WorldUnlocked(w){return w.goal===10||v11Progress()>=w.goal-15||['reading','listening'].includes(w.id)}
function v11NextGoal(){return V11_WORLDS.find(w=>!v11WorldUnlocked(w))||V11_WORLDS[V11_WORLDS.length-1]}
function v11StarsToday(){const today=new Date().toISOString().slice(0,10);return data.history.filter(x=>(x.date||'').slice(0,10)===today&&x.correct).length}
function v11SessionLabel(){return `${V11.sessionMinutes} min`}
function v11Home(){
 const main=document.querySelector('main.container'); if(!main||!v11Kid())return;
 const welcome=main.querySelector('.v10-welcome'); if(!welcome)return;
 const av=v11Avatar(),target=v11MissionTarget(),progress=v11Progress(),next=v11NextGoal();
 welcome.insertAdjacentHTML('afterend',`<section class="card v11-status" aria-label="Tu aventura"><div class="v11-profile"><button class="v11-avatar-btn" data-v11-avatar aria-label="Cambiar avatar"><span>${av[0]}</span><small>${av[1]}</small></button><div><b>Tu aventura de hoy</b><p>Sesión corta · ${v11SessionLabel()} · una misión a la vez</p></div></div><div class="v11-counters"><div>⭐ <b>${V11.stars}</b><small>estrellas</small></div><div>🔥 <b>${data.profile.streak||1}</b><small>racha</small></div><div>🎁 <b>${V11.chests}</b><small>cofres</small></div></div></section>`);
 const firstTitle=[...main.querySelectorAll('.section-title')].find(x=>x.textContent.includes('Elige una aventura')); if(firstTitle)firstTitle.style.display='none';
 const skills=main.querySelector('.skills'); if(skills)skills.style.display='none';
 const map=document.createElement('section');map.className='v11-adventure';map.innerHTML=`<div class="section-title"><div><h2>🗺️ Tu mapa de aventuras</h2><p>Completa mundos poco a poco. No necesitas hacer todo hoy.</p></div><button class="btn btn-soft" data-v11-session>⏱ ${v11SessionLabel()}</button></div><div class="v11-map"><div class="v11-map-line"></div>${V11_WORLDS.map((w,i)=>{const unlocked=v11WorldUnlocked(w),active=w.id===target;return `<button class="v11-world ${unlocked?'unlocked':'locked'} ${active?'active':''}" data-v11-world="${w.id}" ${unlocked?'':'disabled'}><span class="v11-world-num">${i+1}</span><img src="${w.img}" alt=""><span class="v11-world-copy"><b>${w.title}</b><small>${w.icon} ${w.sub}</small>${active?'<em>Tu misión recomendada</em>':''}${!unlocked?`<em>Se abre al seguir avanzando</em>`:''}</span><span class="v11-world-state">${unlocked?(active?'▶':'✓'):'🔒'}</span></button>`}).join('')}</div><div class="v11-next"><div><b>Próximo gran objetivo</b><span>${progress}% preparado · ${next.title}</span></div><div class="v11-progress"><span style="width:${progress}%"></span></div></div>`;
 const path=main.querySelector('.guided-path')?.parentElement; if(path)path.parentNode.insertBefore(map,path); else main.appendChild(map);
 main.insertAdjacentHTML('beforeend',`<section class="card v11-reward"><div class="v11-reward-art">🎁</div><div><span class="mission-label">Recompensa</span><h2>${v11StarsToday()>=3?'¡Hoy ya ganaste tu premio!':'Consigue 3 respuestas correctas'}</h2><p>${v11StarsToday()>=3?'Sigue si quieres, pero tu misión mínima ya está cumplida.':'Cuando llegues a 3 aciertos, celebramos y puedes terminar la sesión con éxito.'}</p></div></section>`);
}
function v11Practice(){
 if(!v11Kid()||state.view!=='practice')return;
 const qcard=document.querySelector('.question-card');if(!qcard)return;
 const qs=currentQuestions(),n=state.idx+1,total=Math.max(1,qs.length),pct=Math.round(n/total*100);
 qcard.insertAdjacentHTML('afterbegin',`<div class="v11-mini-session"><span>${v11Avatar()[0]} Misión corta</span><b>${n}/${total}</b><div><i style="width:${pct}%"></i></div></div>`);
 if(state.checked){const q=qs[state.idx],correct=state.selected===q?.a;requestAnimationFrame(()=>v11Feedback(correct));}
}
function v11Feedback(correct){
 if(document.querySelector('.v11-celebration'))return;
 const key=`${state.skill}:${state.level}:${state.idx}:${state.checked}`; if(V11.lastCelebration===key)return;V11.lastCelebration=key;
 if(correct){V11.stars+=1; const today=v11StarsToday(); if(today===3){V11.chests+=1;V11.completedMissions+=1} v11Save();
  const el=document.createElement('div');el.className='v11-celebration';el.innerHTML=`<div class="v11-pop"><div class="v11-big">${today>=3?'🎁':'⭐'}</div><b>${today>=3?'¡Misión cumplida!':'¡Excelente!'}</b><span>${today>=3?'Ganaste un cofre. Puedes seguir o descansar.':'+1 estrella por aprender'}</span></div>${'<i></i>'.repeat(16)}`;document.body.appendChild(el);setTimeout(()=>el.remove(),1700);
 }
}
function v11Studio(){if(!v11Kid()||!['writing','speaking'].includes(state.view))return;const q=document.querySelector('.question-card');if(!q)return;q.insertAdjacentHTML('afterbegin',`<div class="v11-studio-goal"><span>${state.view==='writing'?'✍️':'🎙️'}</span><div><b>Objetivo pequeño</b><p>${state.view==='writing'?'Escribe primero 3 ideas. Después las convertimos en texto.':'Responde con 3 pasos: respuesta + razón + ejemplo.'}</p></div></div>`)}
function v11AvatarModal(){document.querySelector('.v11-modal')?.remove();document.body.insertAdjacentHTML('beforeend',`<div class="v11-modal" role="dialog" aria-modal="true"><div class="v11-modal-card"><h2>Elige tu compañero</h2><p>Tu avatar te acompaña mientras practicas.</p><div class="v11-avatar-grid">${Object.entries(V11_AVATARS).map(([id,a])=>`<button data-v11-pick="${id}" class="${V11.avatar===id?'active':''}"><span>${a[0]}</span><b>${a[1]}</b></button>`).join('')}</div><button class="btn btn-ghost" data-v11-close>Cerrar</button></div></div>`);v11BindModal()}
function v11SessionModal(){document.querySelector('.v11-modal')?.remove();document.body.insertAdjacentHTML('beforeend',`<div class="v11-modal" role="dialog" aria-modal="true"><div class="v11-modal-card"><h2>¿Cuánto quieres practicar?</h2><p>Para niños recomendamos sesiones cortas y frecuentes.</p><div class="v11-session-grid">${[5,8,10,15].map(n=>`<button data-v11-minutes="${n}" class="${V11.sessionMinutes===n?'active':''}"><b>${n}</b><span>minutos</span></button>`).join('')}</div><button class="btn btn-ghost" data-v11-close>Cerrar</button></div></div>`);v11BindModal()}
function v11BindModal(){document.querySelectorAll('[data-v11-pick]').forEach(b=>b.onclick=()=>{V11.avatar=b.dataset.v11Pick;v11Save();document.querySelector('.v11-modal')?.remove();render()});document.querySelectorAll('[data-v11-minutes]').forEach(b=>b.onclick=()=>{V11.sessionMinutes=+b.dataset.v11Minutes;v11Save();document.querySelector('.v11-modal')?.remove();render()});document.querySelector('[data-v11-close]')?.addEventListener('click',()=>document.querySelector('.v11-modal')?.remove())}
function v11Bind(){document.querySelector('[data-v11-avatar]')?.addEventListener('click',v11AvatarModal);document.querySelector('[data-v11-session]')?.addEventListener('click',v11SessionModal);document.querySelectorAll('[data-v11-world]').forEach(b=>b.onclick=()=>{const id=b.dataset.v11World;if(id==='mock'){state.view='mock';render()}else startSkill(id,1)})}
function enhanceV11(){if(v11Kid()){document.documentElement.classList.add('v11-kid');const main=document.querySelector('main.container');if(main)main.style.display=''}else document.documentElement.classList.remove('v11-kid');if(state.view==='home')v11Home();if(state.view==='practice')v11Practice();if(['writing','speaking'].includes(state.view))v11Studio();v11Bind()}
const v11RenderBase=render;
render=function(){v11RenderBase();requestAnimationFrame(enhanceV11)};
requestAnimationFrame(enhanceV11);
