/* PET Quest V46.30 - Windows Safe Runtime Guard */
(()=>{'use strict';
const V='46.30';
const ADMIN_PREFIXES=['/decision-simulator','/budget-optimizer','/portfolio-optimizer','/schedule-planner','/ops/status','/commercial-readiness','/release-readiness'];
function isAdminPath(p){return ADMIN_PREFIXES.some(x=>String(p||'').startsWith(x))}
const raw=window.apiRequest;
if(typeof raw==='function'){
  let windowStart=Date.now(),count=0;
  window.apiRequest=async function(path,opt={}){
    const now=Date.now(); if(now-windowStart>1000){windowStart=now;count=0} count++;
    // Absolute circuit breaker. A normal UI action never needs >24 API calls in one second.
    if(count>24){console.error('[PET Quest V46.30] API circuit breaker activated');throw new Error('api_circuit_breaker')}
    const role=window.API?.user?.role;
    if(isAdminPath(path)&&!['school','admin'].includes(role))throw new Error('client_role_guard');
    return raw(path,opt);
  };
}
window.PETQUEST_V4630={version:V,windowsSafeLogin:true,backgroundPolling:false};
})();
