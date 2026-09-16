const fs=require('fs'),vm=require('vm');
const src0=fs.readFileSync('v46_18_audio_bank.js','utf8');
const manifest=JSON.parse(fs.readFileSync('PET_AUDIO_BANK_V46_18.json','utf8'));
let src=src0.replace("window.PETQuestAudioBank={version:'46.33',state:S,mount};","window.PETQuestAudioBank={version:'46.33',state:S,mount,__test:{transcriptSegments,speakCleanTranscript,stopAllAudio,englishVoices}};");
const spoken=[];let cancelled=0;
function U(t){this.text=t;this.lang='';this.rate=1;this.pitch=1;this.volume=1;this.voice=null}
const context={
 console,window:null,API:{token:null,user:{id:1}},state:{skill:'none',view:'none'},
 localStorage:{getItem(){return null},setItem(){}},
 document:{querySelector(){return null},querySelectorAll(){return []},getElementById(){return null}},
 speechSynthesis:{getVoices(){return [{name:'GB-A',lang:'en-GB'},{name:'GB-B',lang:'en-GB'},{name:'US-A',lang:'en-US'}]},cancel(){cancelled++},speak(u){spoken.push({text:u.text,lang:u.lang,rate:u.rate,volume:u.volume,voice:u.voice&&u.voice.name})}},
 SpeechSynthesisUtterance:U,setTimeout(){return 0},fetch:async()=>({ok:false}),Audio:function(){},CSS:{escape:x=>x}
};
context.window=context;context.PETAudioSafe={rateValue:r=>Math.max(.75,Math.min(1.1,Number(r)||1)),configure(){}};
vm.runInNewContext(src,context,{filename:'v46_18_audio_bank.js'});
const api=context.PETQuestAudioBank,T=api.__test,S=api.state;
let pass=0,total=0;function check(name,ok,detail=''){total++;if(ok){pass++;console.log('PASS',name,detail)}else console.log('FAIL',name,detail)}
check('version_46_33',api.version==='46.33');
check('manifest_500',manifest.items.length===500);
check('all_transcripts',manifest.items.every(x=>String(x.transcript||'').trim().length>0));
const dialogue=manifest.items.find(x=>/^[A-Z][A-Za-z'’ -]{1,30}:/.test(x.transcript));
const seg=T.transcriptSegments(dialogue.transcript);
check('dialogue_segments',seg.length>=2,seg.length);
check('speaker_names',seg.every(x=>x.speaker&&x.text));
S.speed=.75;spoken.length=0;const ok=T.speakCleanTranscript(dialogue);
check('clean_speech_started',ok===true);
check('utterances_queued',spoken.length===seg.length,spoken.length);
check('british_locale',spoken.every(x=>x.lang==='en-GB'));
check('speed_075',spoken.every(x=>Math.abs(x.rate-.75)<1e-9));
check('voices_alternate',new Set(spoken.map(x=>x.voice).filter(Boolean)).size>=2);
S.speed=1.1;spoken.length=0;T.speakCleanTranscript(dialogue);check('speed_110',spoken.every(x=>Math.abs(x.rate-1.1)<1e-9));
const mono=manifest.items.find(x=>!/[A-Z][A-Za-z'’ -]{1,30}:/.test(x.transcript));
check('monologue_segment',T.transcriptSegments(mono.transcript).length===1);
const before=cancelled;T.stopAllAudio();check('cancel_restart',cancelled>before);
check('learn_no_sourceFor',!src0.includes('PETAudioSafe.sourceFor'));
check('learn_no_speed_playbackrate',!src0.includes('playbackRate=S.speed')&&!src0.includes('setRate(a,S.speed)'));
check('synthetic_exam_clean_voice',src0.includes("const useCleanVoice=S.mode==='learn'||!hasHumanStudio"));
check('human_exam_file_switch',src0.includes('q.human_recording===true')&&src0.includes('new Audio(q.audio_file)'));
check('human_exam_1x',src0.includes("configure(a,{rate:1,volume:.72})"));
const sw=fs.readFileSync('sw.js','utf8'),html=fs.readFileSync('index.html','utf8');
check('new_cache',sw.includes('petquest-v46-33-clean-audio-1'));
check('new_query',html.includes('v46_18_audio_bank.js?v=46.33-cleanaudio1'));
console.log(`RESULT ${pass}/${total}`);if(pass!==total)process.exit(1);
