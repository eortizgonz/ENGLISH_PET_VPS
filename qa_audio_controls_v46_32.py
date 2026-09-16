#!/usr/bin/env python3
import json, re, wave
from pathlib import Path
from mutagen.mp3 import MP3
R=Path(__file__).resolve().parent
checks=[]
def ok(name, cond, detail=''):
    checks.append((name,bool(cond),str(detail)))
    print(('PASS ' if cond else 'FAIL ')+name+((' '+str(detail)) if detail!='' else ''))

def read(name): return (R/name).read_text(encoding='utf-8')
idx=read('index.html'); sw=read('sw.js'); engine=read('v46_32_audio_safe_engine.js')
# Engine + load order
ok('engine_loaded', 'v46_32_audio_safe_engine.js?v=46.32-audiofix1' in idx)
ok('engine_before_listening', idx.find('v46_32_audio_safe_engine.js') < idx.find('v18_listening.js'))
ok('sw_audiofix_cache', "petquest-v46-32-audiofix-1" in sw)
ok('sw_engine_cached', "'./v46_32_audio_safe_engine.js'" in sw)
ok('volume_cap_085', 'const MAX_VOLUME=0.85' in engine)
ok('rate_bounds', 'const MIN_RATE=0.75' in engine and 'const MAX_RATE=1.10' in engine)
ok('smooth_volume_ramp', 'requestAnimationFrame(step)' in engine and 'duration||90' in engine)
ok('non1x_pitch_preservation_disabled', 'const preserve=Math.abs(rate-1)<0.001' in engine)
ok('rate_change_fade_pause_resume', 'setVolume(a,0,{duration:55})' in engine and 'await a.play();setVolume(a,target,{duration:100})' in engine)
# Module integration
mods={n:read(n) for n in ['v40_2_exam_fidelity.js','v46_11_mock_listening.js','v46_18_audio_bank.js','v18_listening.js','v46_21_practice_bank.js','v46_22_practice_diagnostic.js','v46_14_speaking_ai_examiner.js']}
ok('fidelity_safe_volume','PETAudioSafe.setVolume(activeAudio' in mods['v40_2_exam_fidelity.js'])
ok('fidelity_safe_speed','PETAudioSafe.setRate(activeAudio' in mods['v40_2_exam_fidelity.js'])
ok('fidelity_volume_ui_cap','max="0.85"' in mods['v40_2_exam_fidelity.js'])
ok('fidelity_speed_ui','data-v402-audio-speed' in mods['v40_2_exam_fidelity.js'])
ok('strict_exam_forces_1x','if(F.listening.strictTwoPlay)F.listening.speed=1' in mods['v40_2_exam_fidelity.js'])
ok('mock_safe_volume','PETAudioSafe.setVolume(currentAudio' in mods['v46_11_mock_listening.js'])
ok('mock_audio_configured_1x','PETAudioSafe.configure(a,{rate:1' in mods['v46_11_mock_listening.js'])
ok('mock_volume_ui_cap','max="0.85"' in mods['v46_11_mock_listening.js'])
ok('bank_safe_config','PETAudioSafe.configure(a,{rate,volume:0.72})' in mods['v46_18_audio_bank.js'])
ok('bank_safe_speed','PETAudioSafe.setRate(a,S.speed)' in mods['v46_18_audio_bank.js'])
ok('bank_four_training_rates', all(x in mods['v46_18_audio_bank.js'] for x in ['.75','.85','1,1.10']))
ok('tts_safe_output', all('u.volume=.78' in mods[n] for n in ['v18_listening.js','v46_21_practice_bank.js','v46_22_practice_diagnostic.js','v46_14_speaking_ai_examiner.js']))
# No known unsafe patterns remain outside fallback paths
js='\n'.join(p.read_text(errors='ignore') for p in R.glob('*.js') if p.name!='v46_32_audio_safe_engine.js' and not p.name.startswith('qa_'))
ok('no_forced_preservesPitch_true','preservesPitch=true' not in js)
# Audio inventory metadata
mp3=list((R/'assets/audio').rglob('*.mp3')); wavs=list((R/'assets/audio').rglob('*.wav'))
mp3_bad=[]; mp3_active_quality_bad=[]
for p in mp3:
    try:
        a=MP3(p); inf=a.info
        if inf.length<=0 or inf.sample_rate<=0 or getattr(inf,'channels',0)<1: mp3_bad.append(str(p.relative_to(R)))
        rel=str(p.relative_to(R)).replace('\\','/')
        if '/reference_original/' not in '/'+rel:
            if inf.sample_rate!=48000 or inf.channels!=1 or inf.bitrate<120000: mp3_active_quality_bad.append((rel,inf.sample_rate,inf.channels,inf.bitrate))
    except Exception as e: mp3_bad.append(f'{p.relative_to(R)}:{e}')
wav_bad=[]
for p in wavs:
    try:
        with wave.open(str(p),'rb') as w:
            if w.getnframes()<=0 or w.getframerate()<=0 or w.getnchannels()<1: wav_bad.append(str(p.relative_to(R)))
    except Exception as e: wav_bad.append(f'{p.relative_to(R)}:{e}')
ok('audio_inventory_877',len(mp3)+len(wavs)==877,len(mp3)+len(wavs))
ok('all_mp3_headers_parse',not mp3_bad,len(mp3_bad))
ok('all_wav_headers_parse',not wav_bad,len(wav_bad))
ok('active_mp3_mastering_48k_mono_120k_plus',not mp3_active_quality_bad,len(mp3_active_quality_bad))
# Current package integrity / mocks / master content
exam_idx=json.loads((R/'exam_packs/index.json').read_text())
ok('20_school_mock_packs',len(exam_idx.get('packs',[]))==20,len(exam_idx.get('packs',[])))
for fn in ['v46_20_full_mock_mastery.js','v46_11_mock_listening.js']:
    ok('script_loaded_'+fn,fn in idx)
ok('master_content_qa_present',(R/'qa_master_content_postgres_v46_30.py').exists())
# final
passed=sum(v for _,v,_ in checks)
print(f'RESULT {passed}/{len(checks)}')
if passed!=len(checks): raise SystemExit(1)
