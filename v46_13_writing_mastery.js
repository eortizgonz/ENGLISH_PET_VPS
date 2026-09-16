/* PET Quest V46.13 - Writing 0-20 rubric + automatic improvement-to-18 mastery path. */
(function(){
'use strict';
const V='46.13';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const clamp=(n,a=0,b=5)=>Math.max(a,Math.min(b,n));
const words=t=>(String(t||'').trim().match(/\b[\w’'-]+\b/g)||[]);
const sentences=t=>(String(t||'').match(/[^.!?]+[.!?]+/g)||[]).length;
const connectors=t=>(String(t||'').toLowerCase().match(/\b(because|but|so|when|although|however|first|then|finally|also|while|after|before|therefore|for example|in addition|on the other hand)\b/g)||[]).length;
const paragraphs=t=>String(t||'').trim().split(/\n\s*\n/).filter(x=>x.trim()).length;
const uniqueRatio=t=>{const w=words(t).map(x=>x.toLowerCase());return w.length?new Set(w).size/w.length:0};
function promptInfo(part){
  if(Number(part)===1)return {kind:'email',points:[
    {id:'club',label:'decir qué club/actividad elegiste',re:/\b(club|activity|team|group)\b/i},
    {id:'reason',label:'explicar por qué lo elegiste',re:/\b(because|reason|chose|choose|wanted|interested|enjoy)\b/i},
    {id:'invite',label:'invitar a Alex',re:/\b(join|come|visit|with me|together|would you like|do you want)\b/i}
  ]};
  return {kind:'article-story',points:[
    {id:'development',label:'desarrollar claramente una idea o secuencia',re:/[.!?]/},
    {id:'detail',label:'añadir detalles o ejemplos',re:/\b(because|for example|when|while|then|after|before|felt|saw|thought)\b/i},
    {id:'ending',label:'cerrar la idea o historia',re:/\b(finally|in the end|overall|so|since then|after that|at last)\b/i}
  ]};
}
function toneStats(text,kind){
 const l=text.toLowerCase();
 const greeting=/\b(hi|hello|dear)\b/.test(l), closing=/\b(best wishes|see you|take care|bye|love|regards)\b/.test(l);
 const veryInformal=(l.match(/\b(gonna|wanna|lol|omg|bro|dude|u|ur)\b/g)||[]).length;
 const direct=(l.match(/\b(please|could|would|thanks|thank you|i think|in my opinion|i'd like|i would like)\b/g)||[]).length;
 return {greeting,closing,veryInformal,direct,appropriate:kind==='email'?(greeting&&closing&&veryInformal===0):(veryInformal===0)};
}
function detectLocalErrors(text){
 try{return window.PETQUEST_V42?.detectErrors?.(text)||window.PETQUEST_V41?.detectErrors?.(text)||[]}catch(_){return []}
}
function rubric(text,part){
 const w=words(text),n=w.length,info=promptInfo(part),covered=info.points.filter(p=>p.re.test(text)),missing=info.points.filter(p=>!p.re.test(text));
 const errs=detectLocalErrors(text), hi=errs.filter(e=>e.severity==='high').length, med=errs.filter(e=>e.severity==='medium').length, low=errs.filter(e=>e.severity==='low').length;
 const conn=connectors(text), sent=sentences(text), paras=paragraphs(text), lex=uniqueRatio(text), tone=toneStats(text,info.kind);
 const content=clamp(covered.length===3?5:covered.length===2?3:covered.length===1?1:0);
 let communication=2;
 if(n>=70)communication++;
 if(tone.appropriate)communication++;
 if(covered.length>=3)communication++;
 if(tone.veryInformal>0)communication--;
 communication=clamp(communication);
 let organisation=1+(sent>=4?1:0)+(paras>=2?1:0)+Math.min(2,Math.floor(conn/2));
 organisation=clamp(organisation);
 let language=5-Math.min(4,hi*2+med+Math.floor(low/2));
 if(n<50)language=Math.min(language,2); else if(lex<0.48)language=Math.min(language,3);
 language=clamp(language);
 const total=content+communication+organisation+language;
 return {content,communication,organisation,language,total,n,covered,missing,errs,conn,sent,paras,lex,tone,kind:info.kind};
}
function criterionExplanations(r){
 const content=r.content===5?'Respondiste todos los puntos principales de la tarea.':r.missing.length?`Faltó desarrollar: ${r.missing.map(x=>x.label).join('; ')}.`:'El contenido necesita responder más claramente a la consigna.';
 const communication=r.communication>=4?'El registro y el propósito comunicativo son adecuados para la tarea.':r.tone.veryInformal?`El mensaje se entiende, pero hay ${r.tone.veryInformal} expresión(es) demasiado informal(es) para una respuesta PET cuidada.`:r.kind==='email'&&!r.tone.greeting?'El mensaje se entiende, pero el email necesita una apertura clara y un tono consistente.':'El propósito se entiende, pero debes ajustar mejor el tono y dirigirte al lector.';
 const organisation=r.organisation>=4?`La información está conectada y resulta fácil de seguir (${r.conn} conectores detectados).`:r.conn<2?'Faltan conectores para unir ideas y hacer más clara la progresión.':r.paras<2?'Hay conectores, pero conviene separar las ideas en párrafos claros.':'La secuencia es comprensible, pero puede organizarse con mayor claridad.';
 const language=r.language>=4?'El vocabulario y las estructuras son suficientemente variados para esta práctica.':r.errs.length?`Detecté ${r.errs.length} patrón(es) de lengua que debes corregir, especialmente ${[...new Set(r.errs.map(e=>e.subcompetence))].slice(0,3).join(', ')}.`:r.lex<0.48?'El vocabulario se repite demasiado; necesitas más variedad y estructuras B1.':'Hay margen para mejorar precisión gramatical, vocabulario y estructuras B1.';
 return {content,communication,organisation,language};
}
function makeExercise(code,title,prompt,options,answer,why){return {code,title,prompt,options,answer,why,status:'pending',selected:null}}
function weaknesses(r){
 const out=[];
 if(r.content<5){const miss=r.missing[0];out.push({criterion:'Content',code:'writing-content',title:'Completar todos los puntos',why:miss?`No desarrollaste suficientemente ${miss.label}.`:'Necesitas cubrir toda la consigna.',exercise:makeExercise('writing-content','Content','¿Cuál frase ayuda mejor a completar una tarea que pide invitar a un amigo?',['The club is on Tuesday.','Would you like to come with me next Tuesday?','My school is quite big.'],1,'La segunda frase responde directamente al punto de invitación.')})}
 if(r.communication<5){out.push({criterion:'Communicative Achievement',code:'writing-communication',title:'Ajustar tono y propósito',why:'El lector debe reconocer con claridad el propósito y un registro apropiado.',exercise:makeExercise('writing-communication','Communicative Achievement','Elige la opción más adecuada para un email amistoso B1.',['Hey bro, u gotta come lol!','Would you like to join me? I think you would really enjoy it.','Participation is hereby requested.'],1,'Es amistosa, clara y apropiada sin ser demasiado informal ni excesivamente formal.')})}
 if(r.organisation<5){out.push({criterion:'Organisation',code:'writing-organisation',title:'Conectar y ordenar ideas',why:r.conn<2?'Usaste pocos conectores; las ideas necesitan relaciones más claras.':'La organización puede mejorar con párrafos y una secuencia más clara.',exercise:makeExercise('writing-organisation','Organisation','Completa: “I chose the science club ___ I love doing experiments.”',['because','although','finally'],0,'“Because” introduce la razón de forma natural.')})}
 if(r.language<5){const e=r.errs[0];if(e?.practice?.length){const p=e.practice[0],a=String(e.practiceAnswers?.[0]||'').trim();out.push({criterion:'Language',code:e.rule||'writing-language',title:e.subcompetence||'Mejorar precisión',why:e.explanation||'Corrige el patrón lingüístico detectado.',exercise:{code:e.rule||'writing-language',title:e.subcompetence||'Language',prompt:p,options:null,answerText:a,why:e.explanation||'Aplica la forma correcta.',status:'pending',selected:null}})}else out.push({criterion:'Language',code:'writing-language',title:'Aumentar precisión y variedad',why:'Necesitas más control de gramática y vocabulario B1.',exercise:makeExercise('writing-language','Language','Elige la frase correcta.',['Yesterday I go to the club.','Yesterday I went to the club.','Yesterday I gone to the club.'],1,'Con “yesterday” usamos past simple: went.')})}
 const fallbacks=[
 {criterion:'Content',code:'writing-content-detail',title:'Añadir detalle relevante',why:'Un detalle específico ayuda a completar el mensaje.',exercise:makeExercise('writing-content-detail','Content','¿Qué frase añade un detalle útil?',['It was nice.','We meet every Thursday after school and build small robots.','Things happen.'],1,'La segunda aporta información concreta y relevante.')},
 {criterion:'Organisation',code:'writing-sequencing',title:'Mejorar secuencia',why:'Ordenar temporalmente ayuda al lector.',exercise:makeExercise('writing-sequencing','Organisation','¿Qué conector muestra una secuencia final?',['Finally','Because','Although'],0,'“Finally” señala la última etapa de una secuencia.')},
 {criterion:'Language',code:'writing-prepositions',title:'Revisar preposiciones',why:'Las colocaciones correctas mejoran precisión.',exercise:makeExercise('writing-prepositions','Language','Complete: “I am interested ___ science.”',['on','in','at'],1,'La colocación correcta es “interested in”.')},
 {criterion:'Communicative Achievement',code:'writing-reader',title:'Pensar en el lector',why:'Una buena producción guía e involucra al lector.',exercise:makeExercise('writing-reader','Communicative Achievement','¿Qué frase involucra mejor al lector?',['Activities exist.','You could come with me and try it next week.','The facility is operational.'],1,'La segunda se dirige al lector de manera natural.')}
 ];
 for(const f of fallbacks){if(out.length>=4)break;if(!out.some(x=>x.code===f.code))out.push(f)}
 return out.slice(0,4);
}
function renderExercise(ex,i){const x=ex.exercise;const controls=x.options?x.options.map((o,j)=>`<label class="option ${x.selected===j?'selected':''}"><input type="radio" name="w4613_${i}" value="${j}" ${x.selected===j?'checked':''}> <span>${esc(o)}</span></label>`).join(''):`<input class="input" data-w4613-text="${i}" placeholder="Escribe la respuesta" value="${esc(x.entered||'')}">`;
 const result=x.status==='pending'?'':`<div class="feedback ${x.status==='correct'?'ok':'bad'}"><b>${x.status==='correct'?'✅ Correcto':'❌ Aún no'}</b> ${esc(x.why)}</div>`;
 return `<article class="card v4613-exercise" data-w4613-exercise="${i}"><div class="row between"><div><span class="badge">${esc(ex.criterion)}</span><h3>${esc(ex.title)}</h3></div><b>${x.status==='correct'?'Dominado':'Pendiente'}</b></div><p>${esc(x.prompt)}</p>${controls}<div class="row"><button class="btn btn-primary btn-sm" data-w4613-check="${i}">Comprobar</button></div>${result}</article>`}
function renderFeedback(rec){const e=rec.explanations,w=rec.weaknesses,gap=Math.max(0,18-rec.score),mastered=w.filter(x=>x.exercise.status==='correct').length;
 return `<div class="feedback ${rec.score>=18?'ok':rec.score>=14?'neutral':'bad'}"><h2>Writing PET Quest: ${rec.score}/20</h2><div class="rubric"><div class="stat"><b>${rec.rubric.content}/5</b><span>Content</span></div><div class="stat"><b>${rec.rubric.communication}/5</b><span>Communicative Achievement</span></div><div class="stat"><b>${rec.rubric.organisation}/5</b><span>Organisation</span></div><div class="stat"><b>${rec.rubric.language}/5</b><span>Language</span></div></div></div>
 <section class="card"><h2>¿Por qué obtuviste esta nota?</h2><p><b>Content: ${rec.rubric.content}/5</b><br>${esc(e.content)}</p><p><b>Communicative Achievement: ${rec.rubric.communication}/5</b><br>${esc(e.communication)}</p><p><b>Organisation: ${rec.rubric.organisation}/5</b><br>${esc(e.organisation)}</p><p><b>Language: ${rec.rubric.language}/5</b><br>${esc(e.language)}</p><div class="notice"><b>Resultado: ${rec.score}/20.</b> ${gap?`Para acercar este Writing a 18/20 necesitas recuperar ${gap} punto(s) y trabajar estas 4 debilidades.`:'Ya estás en 18/20 o más; usa los ejercicios para consolidar y buscar mayor consistencia.'}</div></section>
 <section class="card"><div class="row between"><div><h2>🎯 Plan automático: de ${rec.score}/20 hacia 18/20</h2><p>Corrige las cuatro debilidades y luego reescribe tu producción.</p></div><span class="badge">${mastered}/4 corregidas</span></div><ol>${w.map(x=>`<li><b>${esc(x.criterion)} — ${esc(x.title)}</b>: ${esc(x.why)}</li>`).join('')}</ol></section>
 <section><h2>Ejercicios inmediatos</h2>${w.map(renderExercise).join('')}</section>
 <div class="card recommendation"><h2>🔁 Reintento</h2><p>Cuando termines los ejercicios, corrige el texto original y vuelve a pulsar <b>Evaluar práctica</b>. PET Quest guardará la nueva nota como otro intento para mostrar tu evolución.</p><div class="small">Evaluación automática formativa alineada a cuatro criterios de Writing. No es una calificación oficial de Cambridge.</div>${state.writingPartsDone?.[1]&&state.writingPartsDone?.[2]?'<div class="row action-row"><button class="btn btn-primary" data-v4613-finish>Finalizar Writing y volver al panel</button></div>':''}</div>`}
function evaluate(text){
 const builder=!!document.getElementById('v16FinalText');
 const out=document.getElementById('writingFeedback')||document.getElementById('v16WritingFeedback'); if(!out)return;
 if(!String(text||'').trim()){out.innerHTML='<div class="feedback bad">Escribe tu respuesta antes de evaluar.</div>';return}
 const taskIndex=(state.idx||0),part=builder?(taskIndex===0?1:2):taskIndex+1,variant=builder?(taskIndex===0?'email':taskIndex===1?'article':'story'):(part===1?'email':'article-story'),r=rubric(text,part),ex=criterionExplanations(r),weak=weaknesses(r),rec={date:new Date().toISOString(),engine:'v46.13-writing-mastery',part,taskVariant:variant,words:r.n,score:r.total,text,rubric:{content:r.content,communication:r.communication,organisation:r.organisation,language:r.language},explanations:ex,errors:r.errs,weaknesses:weak,targetScore:18};
 data.writing.push(rec); data.profile.xp+=Math.max(5,rec.score); data.profile.lastStudy=rec.date; state.writingPartsDone=state.writingPartsDone||{};state.writingPartsDone[part]=true; save();
 if(r.errs.length&&window.apiRequest){const events=r.errs.map(er=>({skill:'writing',part,competence:er.category||'Language',subcompetence:er.subcompetence||'Writing accuracy',error_code:er.rule||'writing-language',severity:er.severity||'medium',original_text:er.original||'',correction:er.correction||'',mastery_proxy:Math.max(10,100-(er.recurrence||1)*18),occurred_at:rec.date,source:'v46.13-writing'}));apiRequest('/academic-errors',{method:'POST',body:{events}}).catch(()=>{})}
 out.innerHTML=renderFeedback(rec);wireFeedback(rec);
}
function currentRecord(){for(let i=data.writing.length-1;i>=0;i--){if(data.writing[i]?.engine==='v46.13-writing-mastery'&&data.writing[i].part===(state.idx||0)+1)return data.writing[i]}return null}
function isCorrect(x,idx,root){if(x.options){const checked=root.querySelector('input[type=radio]:checked');if(!checked)return {answered:false,ok:false,answer:''};const n=Number(checked.value);return {answered:true,ok:n===x.answer,answer:x.options[n]||''}}const inp=root.querySelector(`[data-w4613-text="${idx}"]`);const a=(inp?.value||'').trim();return {answered:!!a,ok:a.toLowerCase()===String(x.answerText||'').trim().toLowerCase(),answer:a}}
function wireFeedback(rec){const finish=document.querySelector('[data-v4613-finish]');if(finish)finish.onclick=()=>{if(typeof completeLearningSession==='function')completeLearningSession('writing_complete');state.view='dashboard';render()};document.querySelectorAll('[data-w4613-check]').forEach(btn=>btn.onclick=async()=>{const i=Number(btn.dataset.w4613Check),w=rec.weaknesses[i],x=w?.exercise,root=btn.closest('[data-w4613-exercise]');if(!x||!root)return;const result=isCorrect(x,i,root);if(!result.answered){toast('Responde el ejercicio antes de comprobar');return}x.status=result.ok?'correct':'incorrect';x.entered=result.answer;if(x.options){const checked=root.querySelector('input[type=radio]:checked');x.selected=checked?Number(checked.value):null}save();if(window.apiRequest&&API.token){apiRequest('/academic-remediation',{method:'POST',body:{error_code:w.code,prompt:x.prompt,answer:result.answer,correct:result.ok,source:'v46.13-writing-mastery'}}).catch(()=>{})}document.getElementById('writingFeedback').innerHTML=renderFeedback(rec);wireFeedback(rec)})}
function replaceEvalButton(){const b=document.querySelector('[data-eval-writing]')||document.querySelector('[data-v16-writing-review]');if(!b||b.dataset.v4613==='1')return;const n=b.cloneNode(true);n.dataset.v4613='1';b.replaceWith(n);n.onclick=e=>{e.preventDefault();e.stopPropagation();const text=document.getElementById('writingText')?.value??document.getElementById('v16FinalText')?.value??'';evaluate(text)}}
const prevRender=window.render;window.render=function(){prevRender();requestAnimationFrame(()=>{if(state.view==='writing')replaceEvalButton()})};
requestAnimationFrame(()=>{if(state.view==='writing')replaceEvalButton()});
window.PETQUEST_V46_13={version:V,evaluate,rubric,criterionExplanations,weaknesses};
})();
