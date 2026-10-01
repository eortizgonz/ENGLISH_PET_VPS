const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const source = fs.readFileSync('app.js', 'utf8');
const bootstrap = source.slice(source.indexOf('async function _apiBootstrapOnce(){'), source.indexOf('async function apiBootstrap(){'));
(async () => {
  for (const token of ['', 'existing-session']) {
    for (const offline of [false, true]) {
      const calls = [], views = [];
      const ctx = {
        API: {token}, state: {view: 'login'},
        location: {search: '?reset_token=test-recovery-token'}, URLSearchParams,
        apiRequest: async path => {
          calls.push(path);
          await new Promise(resolve => setTimeout(resolve, 10));
          if (offline) throw new Error('offline');
          return {ok:true};
        },
        render() { views.push(ctx.state.view); }
      };
      vm.createContext(ctx);
      vm.runInContext(bootstrap, ctx);
      await ctx._apiBootstrapOnce();
      assert.deepStrictEqual(views, ['resetPassword']);
      assert.deepStrictEqual(calls, ['/health']);
    }
  }
  console.log('PASS: recovery survives async bootstrap, with/without session and health failure (4 cases)');
})().catch(error => { console.error(error); process.exitCode = 1; });
