global.window=global;
global.performance={now:()=>Date.now()};
global.requestAnimationFrame=(fn)=>setTimeout(()=>fn(Date.now()),2);
global.cancelAnimationFrame=(id)=>clearTimeout(id);
require('./v46_32_audio_safe_engine.js');
class MockAudio{
  constructor(){this.volume=1;this.playbackRate=1;this.defaultPlaybackRate=1;this.paused=true;this.ended=false;this.currentTime=12.5;this.preservesPitch=true;this.mozPreservesPitch=true;this.webkitPreservesPitch=true;}
  pause(){this.paused=true}
  async play(){this.paused=false}
}
(async()=>{
 const a=new MockAudio();
 PETAudioSafe.configure(a,{volume:1,rate:1});
 if(a.volume!==0.85)throw Error('volume max clamp failed');
 if(a.playbackRate!==1||a.preservesPitch!==true)throw Error('1x config failed');
 await PETAudioSafe.setRate(a,.75);
 if(a.playbackRate!==.75||a.preservesPitch!==false)throw Error('0.75 clarity mode failed');
 await PETAudioSafe.setRate(a,1.1);
 if(a.playbackRate!==1.1||a.preservesPitch!==false)throw Error('1.10 clarity mode failed');
 await PETAudioSafe.setRate(a,1);
 if(a.playbackRate!==1||a.preservesPitch!==true)throw Error('1x pitch mode failed');
 a.paused=false;a.volume=.7;PETAudioSafe.setVolume(a,.2,{duration:10});
 await new Promise(r=>setTimeout(r,40));
 if(Math.abs(a.volume-.2)>.02)throw Error('smooth volume ramp failed '+a.volume);
 if(PETAudioSafe.volumeValue(-1)!==0||PETAudioSafe.volumeValue(9)!==.85)throw Error('volume bounds failed');
 if(PETAudioSafe.rateValue(.1)!==.75||PETAudioSafe.rateValue(9)!==1.1)throw Error('rate bounds failed');
 const u={};PETAudioSafe.safeUtterance(u,{volume:1,rate:2});
 if(u.volume!==.85||u.rate!==1.1||u.pitch!==1)throw Error('tts bounds failed');
 console.log('AUDIO_CONTROL_ENGINE: 10/10 PASS');
})().catch(e=>{console.error(e);process.exit(1)});
