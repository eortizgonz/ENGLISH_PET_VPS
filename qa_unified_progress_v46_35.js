const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

const v5 = process.env.PETQUEST_V5_SOURCE || fs.readFileSync('v5_enhancements.js', 'utf8');
const v468 = process.env.PETQUEST_V468_SOURCE || fs.readFileSync('v46_8_user_progress.js', 'utf8');
const v4627 = process.env.PETQUEST_V4627_SOURCE || fs.readFileSync('v46_27_mastery_orchestrator.js', 'utf8');

for (const marker of ['data-progress-readiness', 'data-progress-accuracy', 'data-progress-attempts', 'unifiedProgressV5']) {
  assert(v5.includes(marker), `dashboard is missing unified marker: ${marker}`);
}
const helper = v468.match(/function syncVisibleProgress\(s\)\{[^\n]+\}/)?.[0];
const fmtHelper = v468.match(/function fmt\(v\)\{[^\n]+\}/)?.[0];
assert(helper && fmtHelper, 'progress formatting helpers must exist');
assert(/state\?\.view==='dashboard'/.test(v468), 'dashboard must not append a duplicate progress panel');
assert(v468.includes("CustomEvent('petquest:progress-updated'"), 'shared progress loader must publish refreshed summaries');
assert(v468.includes('if(V.promise)return V.promise'), 'concurrent progress requests must share one promise');
assert(!v468.includes('window.API') && !v468.includes('window.state'), 'progress loader must use the lexical API and state globals declared by app.js');
assert(v4627.includes('shared?.load?await shared.load(true)'), 'orchestrator must consume the shared progress loader');
assert(v4627.includes("addEventListener('petquest:progress-updated'"), 'orchestrator must react to refreshed progress');
assert(v4627.includes('hydrateSharedProgress()'), 'orchestrator must hydrate from the shared cached summary before rendering');
assert(v4627.includes('Calculando tu progreso'), 'orchestrator must not present temporary zeroes as real progress');
assert(v5.includes("pending?'Sincronizando evidencia…'"), 'progress view must not mix the legacy local formula while server data loads');

const elements = new Map();
function element(selector) {
  if (!elements.has(selector)) elements.set(selector, {textContent: '', style: {width: ''}});
  return elements.get(selector);
}
const context = {document: {querySelector: element}};
vm.createContext(context);
vm.runInContext(`${fmtHelper};${helper};syncVisibleProgress({activity:{attempts:4,accuracy:75,xp:30},preparation:{score:41.7},skills:{reading:66.7,writing:0,listening:100,speaking:0}})`, context);

assert.strictEqual(element('[data-progress-readiness]').textContent, '41.7%');
assert.strictEqual(element('[data-progress-accuracy]').textContent, '75%');
assert.strictEqual(element('[data-progress-attempts]').textContent, '4');
const reading = [...elements].find(([key]) => key.includes('progress-skill') && key.includes('reading'))?.[1];
const listeningBar = [...elements].find(([key]) => key.includes('progress-bar') && key.includes('listening'))?.[1];
assert.strictEqual(reading?.textContent, '66.7%');
assert.strictEqual(listeningBar?.style.width, '100%');
assert.strictEqual(element('.pill.xp').textContent, '⭐ 30 XP');

console.log('PASS: unified server progress updates the existing dashboard and XP');
