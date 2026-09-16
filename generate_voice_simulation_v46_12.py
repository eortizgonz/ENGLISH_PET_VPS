#!/usr/bin/env python3
import csv, re, subprocess, tempfile, os, json, hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parent
CSV=ROOT/'STUDIO_RECORDING_SCRIPT_V46_11.csv'
REPORT=ROOT/'VOICE_SIMULATION_MANIFEST_V46_12.json'

# Offline synthetic voice profiles. Distinct profiles reduce the "one robot voice" effect.
PROFILES={
 'girl_a':('en-gb+f3',158,53), 'girl_b':('en-uk-rp+f2',154,56), 'girl_c':('en-uk-north+f3',160,55),
 'boy_a':('en-gb+m3',156,47), 'boy_b':('en-uk-rp+m2',152,45), 'boy_c':('en-uk-north+m3',157,46),
 'woman_a':('en-uk-rp+f4',150,52), 'woman_b':('en-gb+f2',153,50), 'woman_c':('en-uk-wmids+f3',151,54),
 'man_a':('en-uk-rp+m2',149,44), 'man_b':('en-gb+m4',151,42), 'man_c':('en-sc+m3',150,45),
 'neutral_a':('en-uk-rp+m1',151,46), 'neutral_b':('en-gb+f4',152,51), 'neutral_c':('en-uk-north+m2',150,44),
}
PACK_VARIANT={'pq-mock-a':'a','pq-mock-b':'b','pq-mock-c':'c'}

def profile_for(label, pack):
    n=label.lower().strip(); v=PACK_VARIANT.get(pack,'a')
    if any(x in n for x in ['girl','emma','maya']): key='girl_'+v
    elif any(x in n for x in ['boy','josh']): key='boy_'+v
    elif any(x in n for x in ['woman','mum','teacher']): key='woman_'+v
    elif any(x in n for x in ['man','interviewer']): key='man_'+v
    elif 'student' in n: key=('girl_' if v!='b' else 'boy_')+v
    else: key='neutral_'+v
    return PROFILES[key],key

def split_dialogue(text):
    # Capture labels such as "Girl:", "Interviewer:", "Maya:" while preserving content.
    pat=re.compile(r'(?:^|\s)([A-Za-z][A-Za-z ]{0,24}):\s*')
    ms=list(pat.finditer(text))
    if not ms: return [('Speaker',text.strip())]
    out=[]
    for i,m in enumerate(ms):
        start=m.end(); end=ms[i+1].start() if i+1<len(ms) else len(text)
        body=text[start:end].strip()
        if body: out.append((m.group(1).strip(),body))
    return out or [('Speaker',text.strip())]

def run(cmd):
    subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def synth(row):
    target=ROOT/row['target_file']
    target.parent.mkdir(parents=True,exist_ok=True)
    segments=split_dialogue(row['transcript'])
    used=[]
    with tempfile.TemporaryDirectory(prefix='pqvoice_') as td:
        td=Path(td); concat=[]
        for i,(speaker,text) in enumerate(segments):
            (voice,speed,pitch),profile=profile_for(speaker,row['pack_id']); used.append({'speaker':speaker,'profile':profile,'voice':voice})
            raw=td/f'seg_{i}.wav'; clean=td/f'seg_{i}_clean.wav'
            # Slightly slower B1-friendly pace, varied pitch/profile by speaker.
            run(['espeak','-v',voice,'-s',str(speed),'-p',str(pitch),'-a','175','-w',str(raw),text])
            run(['ffmpeg','-y','-i',str(raw),'-af',
                 'highpass=f=70,lowpass=f=10500,equalizer=f=220:t=q:w=1:g=1.2,equalizer=f=3200:t=q:w=1:g=0.7,acompressor=threshold=-18dB:ratio=2:attack=20:release=160,loudnorm=I=-16:TP=-1.5:LRA=7',
                 '-ar','48000','-ac','1',str(clean)])
            concat.append(clean)
            if i < len(segments)-1:
                silence=td/f'sil_{i}.wav'
                run(['ffmpeg','-y','-f','lavfi','-i','anullsrc=r=48000:cl=mono','-t','0.22','-c:a','pcm_s16le',str(silence)])
                concat.append(silence)
        lst=td/'concat.txt'
        lst.write_text('\n'.join("file '%s'"%p.as_posix().replace("'","'\\''") for p in concat),encoding='utf-8')
        joined=td/'joined.wav'
        run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(lst),'-c:a','pcm_s16le',str(joined)])
        # Final derivative for browser playback. 192 kbps is intentionally generous; source remains synthetic.
        run(['ffmpeg','-y','-i',str(joined),'-af','loudnorm=I=-16:TP=-1.5:LRA=7','-ar','48000','-ac','1','-b:a','192k',str(target)])
    probe=subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration,bit_rate','-show_entries','stream=sample_rate,channels,codec_name','-of','json',str(target)],text=True)
    meta=json.loads(probe)
    h=hashlib.sha256(target.read_bytes()).hexdigest()
    return {'pack_id':row['pack_id'],'part':int(row['part']),'audio_id':row['audio_id'],'file':row['target_file'],'segments':len(segments),'voices':used,'sha256':h,'probe':meta}

def main():
    rows=list(csv.DictReader(CSV.open(encoding='utf-8-sig')))
    results=[]
    for n,row in enumerate(rows,1):
        print(f'[{n}/{len(rows)}] {row["audio_id"]}',flush=True)
        results.append(synth(row))
    REPORT.write_text(json.dumps({'version':'46.12','engine':'offline espeak voice simulation + ffmpeg mastering','synthetic':True,'human_recording':False,'targets':results},indent=2),encoding='utf-8')
    print(f'generated {len(results)} files')
if __name__=='__main__': main()
