const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

const v10 = process.env.PETQUEST_V10_SOURCE || fs.readFileSync('v10_ux.js', 'utf8');
const v12 = process.env.PETQUEST_V12_SOURCE || fs.readFileSync('v12_ux.js', 'utf8');

for (const removed of ['ux-mode-switch', 'data-ux-mode', 'setUxMode']) {
  assert(!v10.includes(removed), `removed mode control remains: ${removed}`);
}
for (const removed of ['v12AgeModal', 'data-v12-age-change', 'data-v12-age-save', '¿Para qué edad preparamos la guía?']) {
  assert(!v12.includes(removed), `removed age control remains: ${removed}`);
}

const roleHelper = v10.match(/function uxRoleIsAdult\(\)\{[^\n]+\}/)?.[0];
const modeHelper = v10.match(/function uxMode\(\)\{[^\n]+\}/)?.[0];
assert(roleHelper && modeHelper, 'automatic role-based mode helpers must exist');

function mode(role, examProfile = 'schools') {
  const context = {API: {user: {role}}, data: {profile: {role, examProfile}}};
  vm.createContext(context);
  vm.runInContext(`${roleHelper};${modeHelper};result=uxMode()`, context);
  return context.result;
}

assert.strictEqual(mode('student'), 'kid');
assert.strictEqual(mode('student', 'adult'), 'adult');
assert.strictEqual(mode('teacher'), 'adult');
assert.strictEqual(mode('admin'), 'adult');

console.log('PASS: age modal and manual Niño/Adult controls are removed');
