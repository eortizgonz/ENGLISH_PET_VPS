/* PET Quest V46.16 - External Outcome Readiness Calibration */
(function(){
'use strict';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct=v=>v==null?'—':`${v}%`;
const num=v=>v==null?'—':String(v);
function gateRows(g){const labels={unique_external_students_300:'≥300 alumnos únicos con resultado externo',passes_75:'≥75 aprobados',fails_75:'≥75 no aprobados',holdout_50:'≥50 alumnos en holdout',holdout_auc_070:'Holdout AUC ≥ 0.70',holdout_brier_020:'Holdout Brier ≤ 0.20',holdout_ece_010:'Calibration error (ECE) ≤ 0.10',sensitivity_65:'Sensibilidad ≥65%',specificity_65:'Especificidad ≥65%',independent_review_approved:'Revisión psicométrica independiente aprobada'};return Object.entries(g||{}).map(([k,v])=>`<div class="notice ${v?'ok':''}"><b>${v?'✅':'⏳'} ${esc(labels[k]||k)}</b></div>`).join('')}
async function renderLab(){
 const main=document.querySelector('main.container'); if(!main||!['teacher','school','reports'].includes(state.view))return;
 let cal;try{cal=await apiRequest('/academic-calibration')}catch(_){return}
 main.querySelectorAll('.v42-calibration,.v4616-calibration').forEach(x=>x.remove());
 const h=cal.holdout_metrics||{},t=cal.training_metrics||{};
 const prob=cal.probability_enabled?'<span class="badge">ON · modelo validado</span>':'<span class="badge">OFF</span>';
 const review=cal.external_review?`<div class="feedback ok"><b>Revisión externa aprobada</b><br>${esc(cal.external_review.reviewer_name)} · ${esc(cal.external_review.organization)}<br><span class="small">${esc(cal.external_review.credentials)}</span></div>`:'<div class="notice"><b>Revisión externa pendiente.</b> El software no puede autoaprobar este gate.</div>';
 main.insertAdjacentHTML('beforeend',`<section class="card v4616-calibration"><h2>📐 PET Readiness Calibration Lab · V46.16</h2><p><b>Objetivo:</b> validar el índice PET Quest contra resultados externos reales, con separación train/holdout por alumno. <b>Teacher mocks no entrenan el modelo científico.</b></p><div class="rubric"><div class="stat"><b>${cal.external_unique_students}</b><span>Alumnos externos únicos</span></div><div class="stat"><b>${cal.train_size}</b><span>Train</span></div><div class="stat"><b>${cal.holdout_size}</b><span>Holdout</span></div><div class="stat"><b>${prob}</b><span>Probabilidad de aprobar</span></div></div><h3>Validación holdout</h3><div class="rubric"><div class="stat"><b>${num(h.auc)}</b><span>AUC</span></div><div class="stat"><b>${num(h.brier)}</b><span>Brier score</span></div><div class="stat"><b>${num(h.ece)}</b><span>ECE</span></div><div class="stat"><b>${pct(h.accuracy)}</b><span>Accuracy</span></div><div class="stat"><b>${pct(h.sensitivity)}</b><span>Sensibilidad</span></div><div class="stat"><b>${pct(h.specificity)}</b><span>Especificidad</span></div></div><h3>Gates de publicación</h3>${gateRows(cal.gates)}${review}<div class="notice"><b>Sin falsa precisión:</b> ${esc(cal.threshold_note)}</div><details><summary>Ver métricas de entrenamiento</summary><pre>${esc(JSON.stringify(t,null,2))}</pre></details></section>`);
}
const prev=window.render;window.render=function(){prev();setTimeout(renderLab,60)};
window.PETQUEST_V46_16={version:'46.16',renderLab};
setTimeout(renderLab,80);
})();
