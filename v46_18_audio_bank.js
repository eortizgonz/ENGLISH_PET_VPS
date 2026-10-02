/* PET Quest V46.35 — PET Audio Bank 500 · Validated answer flow */
(function(){
'use strict';
const BANK_URL='PET_AUDIO_BANK_V46_18.json';
const S={manifest:null,part:1,idx:0,mode:'learn',speed:1,learnPlays:{},examPlays:{},examSession:0,answer:null,checked:false,open:false};
let activeAudio=null;
let ttsRun=0;
let successTimer=null;
function englishVoices(){
  try{
    const all=speechSynthesis.getVoices?.()||[];
    const gb=all.filter(v=>/^en-GB/i.test(v.lang||''));
    const en=all.filter(v=>/^en/i.test(v.lang||''));
    const pool=gb.length?gb:(en.length?en:all),seen=new Set();
    return pool.filter(v=>{const k=(v.name||'')+'|'+(v.lang||'');if(seen.has(k))return false;seen.add(k);return true});
  }catch(_){return []}
}
function transcriptSegments(text){
  text=String(text||'').trim(); if(!text)return [];
  const re=/([A-Z][A-Za-z'’ -]{1,30}):\s*/g,hits=[...text.matchAll(re)];
  if(!hits.length)return [{speaker:'Narrator',text}];
  const out=[];
  for(let i=0;i<hits.length;i++){
    const h=hits[i],a=h.index+h[0].length,b=i+1<hits.length?hits[i+1].index:text.length,t=text.slice(a,b).trim();
    if(t)out.push({speaker:h[1].trim(),text:t});
  }
  return out.length?out:[{speaker:'Narrator',text}];
}
function stopAllAudio(){
  ttsRun++;
  try{speechSynthesis.cancel()}catch(_){ }
  if(activeAudio){try{activeAudio.pause()}catch(_){ }try{activeAudio.currentTime=0}catch(_){ }}
  activeAudio=null;
}
function speakCleanTranscript(q){
  if(!('speechSynthesis' in window)||!q?.transcript)return false;
  stopAllAudio(); const run=++ttsRun,voices=englishVoices(),segments=transcriptSegments(q.transcript),voiceMap=new Map(); let vi=0;
  for(const seg of segments){
    if(run!==ttsRun)break;
    if(!voiceMap.has(seg.speaker))voiceMap.set(seg.speaker,voices.length?voices[vi++%Math.min(voices.length,4)]:null);
    const u=new SpeechSynthesisUtterance(seg.text);u.lang='en-GB';u.rate=window.PETAudioSafe?PETAudioSafe.rateValue(S.speed):Math.max(.75,Math.min(1.10,Number(S.speed)||1));u.pitch=1;u.volume=.78;
    const v=voiceMap.get(seg.speaker);if(v)u.voice=v;speechSynthesis.speak(u);
  }
  return true;
}
function userId(){try{return (typeof API!=='undefined'&&API.user&&API.user.id)||'guest'}catch(_){return 'guest'}}
function key(){return 'petquest_v4619_audio_bank_u_'+userId()}
function loadLocal(){try{const x=JSON.parse(localStorage.getItem(key())||'{}');S.part=x.part||1;S.idx=x.idx||0;S.mode=x.mode==='exam'?'exam':'learn';S.speed=x.speed||1;S.learnPlays=x.learnPlays||{};S.examPlays=x.examPlays||{};S.examSession=x.examSession||0;S.open=!!x.open}catch(_){}}
function saveLocal(){localStorage.setItem(key(),JSON.stringify({part:S.part,idx:S.idx,mode:S.mode,speed:S.speed,learnPlays:S.learnPlays,examPlays:S.examPlays,examSession:S.examSession,open:S.open}))}
function E(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function stableAnswerSlot(id,count){let hash=2166136261;for(const char of 'v46.35:'+String(id||'')){hash^=char.charCodeAt(0);hash=Math.imul(hash,16777619)}return count?(hash>>>0)%count:0}
function balanceAnswerPositions(manifest){
 const items=(manifest?.items||[]).map(q=>{
  const options=[...(q.options||[])],correct=correctAnswerIndex(q);if(correct<0||correct>=options.length)return q;
  const target=stableAnswerSlot(q.id,options.length);[options[correct],options[target]]=[options[target],options[correct]];
  return {...q,options,answer:target};
 });
 return {...manifest,items};
}
async function ensure(){if(S.manifest)return S.manifest;try{if(typeof apiRequest==='function'&&API?.token)S.manifest=await apiRequest('/content/audio-bank')}catch(e){console.warn('PostgreSQL audio content fallback',e)}if(!S.manifest){const r=await fetch(BANK_URL+'?v=46.19',{cache:'no-store'});if(!r.ok)throw new Error('Audio bank unavailable');S.manifest=await r.json()}S.manifest=balanceAnswerPositions(S.manifest);loadLocal();return S.manifest}
function items(){return (S.manifest?.items||[]).filter(x=>x.part===S.part)}
function current(){const a=items();if(!a.length)return null;S.idx=Math.max(0,Math.min(S.idx,a.length-1));return a[S.idx]}
function correctAnswerIndex(q){
 const raw=q?.answer;if(Number.isInteger(raw))return raw;
 const value=String(raw??'').trim();if(/^\d+$/.test(value))return Number(value);
 if(/^[a-z]$/i.test(value))return value.toUpperCase().charCodeAt(0)-65;
 return (q?.options||[]).findIndex(option=>String(option).trim().toLowerCase()===value.toLowerCase());
}
function isCorrect(q){return S.answer===correctAnswerIndex(q)}
function audio(){return activeAudio}
function stop(){stopAllAudio()}
function play(){
  const q=current();if(!q)return;
  const map=S.mode==='exam'?S.examPlays:S.learnPlays,n=map[q.id]||0;
  if(S.mode==='exam'&&n>=2){window.toast?.('REAL EXAM MODE: ya usaste las 2 reproducciones permitidas');return}
  map[q.id]=n+1;
  const hasHumanStudio=q.human_recording===true;
  // Current synthetic reference bank: use clean system speech in both modes.
  // Once human studio files are loaded, REAL EXAM MODE automatically uses them.
  const useCleanVoice=S.mode==='learn'||!hasHumanStudio;
  if(useCleanVoice){
    const previous=S.speed;if(S.mode==='exam')S.speed=1;
    const ok=speakCleanTranscript(q);S.speed=previous;
    if(!ok){stopAllAudio();const a=new Audio(q.audio_file);activeAudio=a;if(window.PETAudioSafe)PETAudioSafe.configure(a,{rate:1,volume:.72});else{a.playbackRate=1;a.volume=.72}a.play().catch(()=>window.toast?.('No se pudo reproducir el audio.'));}
  }else{
    stopAllAudio();const a=new Audio(q.audio_file);activeAudio=a;
    if(window.PETAudioSafe)PETAudioSafe.configure(a,{rate:1,volume:.72});else{a.playbackRate=1;a.volume=.72}
    a.addEventListener('ended',()=>{if(activeAudio===a)activeAudio=null},{once:true});
    a.addEventListener('error',()=>window.toast?.('No se pudo reproducir el audio humano.'),{once:true});
    a.currentTime=0;a.play().catch(()=>window.toast?.('Pulsa reproducir de nuevo para habilitar el audio'));
  }
  saveLocal();updateCounter()
}
function updateCounter(){const q=current(),b=document.querySelector('[data-pqab-count]');if(!b||!q)return;const n=(S.mode==='exam'?S.examPlays:S.learnPlays)[q.id]||0;b.textContent=S.mode==='exam'?`${n} / 2`:`${n} · ♾`}
function cancelPendingAdvance(){if(successTimer!==null){clearTimeout(successTimer);successTimer=null}}
function next(){cancelPendingAdvance();stop();const a=items();S.idx=(S.idx+1)%Math.max(1,a.length);S.answer=null;S.checked=false;saveLocal();renderPanel()}
function randomItem(){cancelPendingAdvance();stop();const a=items();S.idx=Math.floor(Math.random()*Math.max(1,a.length));S.answer=null;S.checked=false;saveLocal();renderPanel()}
async function track(q,correct){try{if(typeof apiRequest==='function'&&typeof API!=='undefined'&&API.token)await apiRequest('/events',{method:'POST',body:{event_type:'audio_bank_answer',skill:'listening',item_id:q.id,success:correct,minutes:Math.max(.1,(q.duration_seconds||10)/60),meta:{part:q.part,mode:S.mode,speed:S.mode==='exam'?1:S.speed,plays:(S.mode==='exam'?S.examPlays:S.learnPlays)[q.id]||0,source:'v46.19-pet-audio-bank'}}})}catch(_){}}
function validateAndAdvance(){
 const q=current();if(!q||S.answer===null||S.checked)return;
 S.checked=true;const ok=isCorrect(q);track(q,ok);renderPanel();
 if(ok){const itemId=q.id;successTimer=setTimeout(()=>{successTimer=null;if(current()?.id===itemId&&S.checked&&isCorrect(current()))next()},900)}
}
function setPart(p){cancelPendingAdvance();stop();S.part=p;S.idx=0;S.answer=null;S.checked=false;saveLocal();renderPanel()}
function setMode(m){cancelPendingAdvance();stop();if(m==='exam'&&S.mode!=='exam'){S.examSession+=1;S.examPlays={};S.speed=1;window.toast?.('REAL EXAM MODE iniciado: 1.00× y exactamente 2 reproducciones por clip')}S.mode=m==='exam'?'exam':'learn';S.answer=null;S.checked=false;saveLocal();renderPanel()}
function panelHtml(){
 const q=current(); if(!q)return '<section class="card"><p>Cargando PET Audio Bank…</p></section>';
 const total=S.manifest.total, c=S.manifest.counts||{}, pcount=items().length, plays=(S.mode==='exam'?S.examPlays:S.learnPlays)[q.id]||0;
 const correct=isCorrect(q);
 const opts=q.options.map((o,i)=>{const chosen=S.answer===i,result=chosen&&S.checked?(correct?'correct':'wrong'):'';return `<button class="option ${chosen?'selected':''} ${result}" data-pqab-opt="${i}" ${S.checked&&correct?'disabled':''}><span>${String.fromCharCode(65+i)}</span>${E(o)}</button>`}).join('');
 const fb=S.checked?`<div class="feedback ${correct?'ok':'bad'}"><b>${correct?'✓ ¡Excelente! Respuesta correcta':'✗ Respuesta incorrecta'}</b><p>${correct?'Muy bien. Pasaremos a la siguiente pregunta.':'La opción seleccionada no es correcta. Escucha nuevamente, elige otra respuesta y vuelve a pulsar Siguiente.'}</p></div>`:'';
 return `<section class="card pqab" id="pqAudioBank"><div class="row between"><div><span class="mission-label">PET AUDIO BANK · V46.19</span><h2>🎧 ${total} grabaciones de práctica</h2><p>${c.part1||0} Part 1 · ${c.part2||0} Part 2 · ${c.part3||0} Part 3 · ${c.part4||0} Part 4</p></div><button class="btn btn-soft" data-pqab-toggle>${S.open?'Cerrar banco':'Abrir banco'}</button></div>${S.open?`
 <div class="pqab-tabs">${[1,2,3,4].map(p=>`<button class="${S.part===p?'active':''}" data-pqab-part="${p}">Part ${p}</button>`).join('')}</div>
 <div class="row between pqab-controls"><div class="row"><button class="btn ${S.mode==='learn'?'btn-primary':'btn-soft'}" data-pqab-mode="learn">♾️ LEARN MODE</button><button class="btn ${S.mode==='exam'?'btn-primary':'btn-soft'}" data-pqab-mode="exam">🎓 REAL EXAM MODE</button></div>${S.mode==='learn'?`<label>Velocidad <select id="pqabSpeed">${[.75,.85,1,1.10].map(v=>`<option value="${v}" ${S.speed===v?'selected':''}>${v.toFixed(2)}×</option>`).join('')}</select></label>`:'<span class="pill">1.00× · exactamente 2 reproducciones</span>'}</div>
 <div class="notice"><b>${S.mode==='learn'?'♾️ LEARN MODE':'🎓 REAL EXAM MODE'}</b><br>${S.mode==='learn'?'Aprende sin presión con voz clara: escucha ilimitadamente y usa 0.75× / 0.85× / 1.00× / 1.10×. Tus escuchas aquí NO consumen las del examen.':'Simulación estricta: voz clara a 1.00×, sin transcript visible y exactamente 2 reproducciones por clip. Al entrar a este modo comienza una sesión nueva 0/2.'}</div>
 <div class="pqab-player"><div><b>Part ${q.part} · Clip ${S.idx+1}/${pcount}</b><p class="small">${E(q.focus)} · ${E(q.voice_profiles.join(' + '))} · ${q.duration_seconds}s</p></div><audio id="pqAudioBankPlayer" preload="metadata" aria-hidden="true"></audio><div class="row"><button class="btn btn-primary" data-pqab-play>▶ Reproducir</button><button class="btn btn-soft" data-pqab-stop>■ Reiniciar</button><span class="pill" data-pqab-count>${plays}${S.mode==='exam'?' / 2':' · ♾'}</span></div></div>
 <div class="prompt">${E(q.question)}</div><div class="options">${opts}</div>${fb}<div class="row action-row"><button class="btn btn-primary" data-pqab-next ${S.answer===null||S.checked?'disabled':''}>Siguiente →</button><button class="btn btn-ghost" data-pqab-random>🎲 Aleatorio</button></div>
 <details ${S.mode==='exam'?'style="display:none"':''}><summary>Transcripción para revisión · LEARN MODE</summary><p>${S.mode==='learn'?E(q.transcript):''}</p></details>
 <p class="small">LEARN MODE usa voz clara del sistema a partir de la transcripción para evitar distorsión al cambiar velocidad. REAL EXAM MODE usa voz clara a 1.00× mientras el banco sea sintético; cuando el clip tenga human_recording=true usará automáticamente la grabación humana.</p>`:''}</section>`;
}
function bindPanel(){
 document.querySelector('[data-pqab-toggle]')?.addEventListener('click',()=>{S.open=!S.open;saveLocal();renderPanel()});
 document.querySelectorAll('[data-pqab-part]').forEach(b=>b.onclick=()=>setPart(+b.dataset.pqabPart));
 document.querySelectorAll('[data-pqab-mode]').forEach(b=>b.onclick=()=>setMode(b.dataset.pqabMode));
 document.getElementById('pqabSpeed')?.addEventListener('change',e=>{S.speed=window.PETAudioSafe?PETAudioSafe.rateValue(e.target.value):+e.target.value;saveLocal();stopAllAudio();window.toast?.('Velocidad ajustada. Pulsa Reproducir para escuchar con voz clara.');});
 document.querySelector('[data-pqab-play]')?.addEventListener('click',play);document.querySelector('[data-pqab-stop]')?.addEventListener('click',stop);document.querySelector('[data-pqab-next]')?.addEventListener('click',validateAndAdvance);document.querySelector('[data-pqab-random]')?.addEventListener('click',randomItem);
 document.querySelectorAll('[data-pqab-opt]').forEach(b=>b.onclick=()=>{S.answer=+b.dataset.pqabOpt;S.checked=false;renderPanel()});
}
function renderPanel(){const old=document.getElementById('pqAudioBank');if(old){old.outerHTML=panelHtml();bindPanel();return}mount()}
async function mount(){
 try{await ensure();const main=document.querySelector('main.container');if(!main||document.getElementById('pqAudioBank'))return;const should=(typeof state!=='undefined'&&state.skill==='listening'&&state.view==='practice');if(!should)return;main.insertAdjacentHTML('beforeend',panelHtml());bindPanel()}catch(e){console.warn('PET Audio Bank',e)}
}
const prevRender=(typeof render==='function')?render:null;if(prevRender){render=function(){const r=prevRender.apply(this,arguments);setTimeout(mount,0);return r}}
setTimeout(mount,400);
window.PETQuestAudioBank={version:'46.35',state:S,mount};
})();
