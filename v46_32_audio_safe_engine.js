/* PET Quest V46.32 - Safe Audio Control Engine
   Centralizes media volume/rate handling to avoid audible zipper noise and
   browser pitch-preservation artifacts when controls change during playback. */
(function(){
'use strict';
const VERSION='46.32';
const DEFAULT_VOLUME=0.72;
const MAX_VOLUME=0.85;
const MIN_RATE=0.75;
const MAX_RATE=1.10;
const state=new WeakMap();
function clamp(n,min,max,fallback){n=Number(n);return Number.isFinite(n)?Math.max(min,Math.min(max,n)):fallback}
function volumeValue(v){return clamp(v,0,MAX_VOLUME,DEFAULT_VOLUME)}
function rateValue(r){return clamp(r,MIN_RATE,MAX_RATE,1)}
function remember(a){let s=state.get(a);if(!s){s={targetVolume:volumeValue(a?.volume),raf:0,rate:rateValue(a?.playbackRate||1)};state.set(a,s)}return s}
function cancelRamp(s){if(s.raf&&typeof cancelAnimationFrame==='function')cancelAnimationFrame(s.raf);s.raf=0}
function pitchMode(a,rate){
  // Chromium/WebKit pitch-preserving time stretching can sound metallic/warbly
  // on synthetic speech. At non-1x rates we prefer clean resampling.
  const preserve=Math.abs(rate-1)<0.001;
  try{a.preservesPitch=preserve}catch(_){ }
  try{a.mozPreservesPitch=preserve}catch(_){ }
  try{a.webkitPreservesPitch=preserve}catch(_){ }
}
function setVolume(a,v,opt={}){
  if(!a)return DEFAULT_VOLUME;
  const s=remember(a),target=volumeValue(v);s.targetVolume=target;
  cancelRamp(s);
  if(opt.immediate||a.paused||typeof requestAnimationFrame!=='function'){
    try{a.volume=target}catch(_){ }
    return target;
  }
  const start=volumeValue(a.volume),started=(typeof performance!=='undefined'&&performance.now)?performance.now():Date.now(),duration=Number(opt.duration||90);
  const step=now=>{const elapsed=Math.max(0,Number(now||Date.now())-started),p=Math.min(1,elapsed/duration),smooth=p*p*(3-2*p);try{a.volume=start+(target-start)*smooth}catch(_){ }if(p<1)s.raf=requestAnimationFrame(step);else s.raf=0};
  s.raf=requestAnimationFrame(step);return target;
}
function configure(a,opt={}){
  if(!a)return null;
  const s=remember(a),rate=rateValue(opt.rate==null?s.rate:opt.rate),vol=volumeValue(opt.volume==null?s.targetVolume:opt.volume);
  s.rate=rate;s.targetVolume=vol;
  try{a.preload=opt.preload||'auto'}catch(_){ }
  pitchMode(a,rate);
  try{a.defaultPlaybackRate=rate;a.playbackRate=rate}catch(_){ }
  setVolume(a,vol,{immediate:true});
  return a;
}
async function setRate(a,r,opt={}){
  if(!a)return 1;
  const s=remember(a),rate=rateValue(r);s.rate=rate;
  const wasPlaying=!a.paused&&!a.ended;
  if(!wasPlaying){pitchMode(a,rate);try{a.defaultPlaybackRate=rate;a.playbackRate=rate}catch(_){ }return rate}
  const target=s.targetVolume,time=Number(a.currentTime||0);
  setVolume(a,0,{duration:55});
  await new Promise(resolve=>setTimeout(resolve,65));
  try{a.pause()}catch(_){ }
  pitchMode(a,rate);
  try{a.defaultPlaybackRate=rate;a.playbackRate=rate;a.currentTime=time}catch(_){ }
  try{await a.play();setVolume(a,target,{duration:100})}catch(_){setVolume(a,target,{immediate:true})}
  return rate;
}
function reset(a,opt={}){if(!a)return;try{a.pause()}catch(_){ }try{a.currentTime=0}catch(_){ }configure(a,opt)}
function safeUtterance(u,opt={}){if(!u)return u;u.volume=volumeValue(opt.volume==null?0.78:opt.volume);u.rate=rateValue(opt.rate==null?1:opt.rate);u.pitch=1;return u}
window.PETAudioSafe={version:VERSION,DEFAULT_VOLUME,MAX_VOLUME,MIN_RATE,MAX_RATE,volumeValue,rateValue,configure,setVolume,setRate,reset,safeUtterance};
})();
