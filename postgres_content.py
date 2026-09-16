#!/usr/bin/env python3
"""PostgreSQL master-content store for PET Quest.
Loads the real study material shipped with the application into relational tables.
JSON files remain packaged as offline/fallback evidence; PostgreSQL is the primary
runtime source whenever it is available.
"""
from pathlib import Path
import os, json, hashlib, mimetypes, time
import postgres_auth

ROOT=Path(__file__).resolve().parent


def _json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def _sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def _header(obj, item_keys=('items','reading','listening','writing','speaking')):
    return {k:v for k,v in obj.items() if k not in item_keys}

def _j(v):
    return json.dumps(v,ensure_ascii=False)

def _package(cur,key,profile,ctype,version,title,source,count,metadata):
    cur.execute('''INSERT INTO content_packages(package_key,profile,content_type,version,title,source_file,item_count,source_sha256,metadata_json,loaded_at)
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,CURRENT_TIMESTAMP)
                   ON CONFLICT(package_key) DO UPDATE SET profile=EXCLUDED.profile,content_type=EXCLUDED.content_type,version=EXCLUDED.version,
                   title=EXCLUDED.title,source_file=EXCLUDED.source_file,item_count=EXCLUDED.item_count,source_sha256=EXCLUDED.source_sha256,
                   metadata_json=EXCLUDED.metadata_json,loaded_at=CURRENT_TIMESTAMP''',
                (key,profile,ctype,str(version or ''),title or key,source,int(count),_sha(ROOT/source),_j(metadata)))

def _seed_practice(cur, profile, filename):
    d=_json(ROOT/filename); items=d.get('items') or []; key=f'practice:{profile}'
    _package(cur,key,profile,'practice_bank',d.get('version'),d.get('title'),filename,len(items),_header(d))
    cur.execute('DELETE FROM practice_bank_items WHERE profile=%s',(profile,))
    sql='''INSERT INTO practice_bank_items(content_key,profile,item_id,skill,part,cefr,difficulty,competency,item_type,prompt,options_json,answer_index,explanation,audio_text,source,diagnostic_patterns_json,payload_json,package_key)
           VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s)'''
    for x in items:
        cur.execute(sql,(f'{profile}:{x.get("id")}',profile,x.get('id'),x.get('skill'),x.get('part'),x.get('cefr'),x.get('difficulty'),x.get('competency'),x.get('type'),x.get('prompt') or '',_j(x.get('options')) if x.get('options') is not None else None,x.get('answer'),x.get('explanation'),x.get('audio_text'),x.get('source'),_j(x.get('diagnostic_patterns') or []),_j(x),key))
    return len(items)

def _seed_curriculum(cur):
    filename='PET_LEARN_CURRICULUM_V46_27.json'; d=_json(ROOT/filename); items=d.get('items') or []; key='curriculum:schools'
    _package(cur,key,'schools','curriculum',d.get('version'),d.get('name'),filename,len(items),_header(d))
    cur.execute('DELETE FROM curriculum_lessons')
    sql='''INSERT INTO curriculum_lessons(lesson_id,level,lesson_order,difficulty,skill,competency,title,objective,teach_text,examples_json,strategy,check_json,recheck_json,practice_filter_json,mastery_json,payload_json,package_key)
           VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,%s)'''
    for x in items:
        cur.execute(sql,(x['id'],x.get('level') or '',x.get('order') or 0,x.get('difficulty'),x.get('skill'),x.get('competency'),x.get('title') or x['id'],x.get('objective'),x.get('teach'),_j(x.get('examples') or []),x.get('strategy'),_j(x.get('check') or {}),_j(x.get('recheck') or {}),_j(x.get('practice_filter') or {}),_j(x.get('mastery') or {}),_j(x),key))
    return len(items)

def _audio_metadata():
    meta={}
    def add(path, values):
        if not path:return
        path=str(path).replace('\\','/')
        current=meta.setdefault(path,{})
        for k,v in values.items():
            if v is not None and (k not in current or current[k] in (None,'',[],{})): current[k]=v
    school=_json(ROOT/'PET_AUDIO_BANK_V46_18.json')
    for x in school.get('items',[]):
        add(x.get('audio_file'),dict(x,profile='schools',source_manifest='PET_AUDIO_BANK_V46_18.json'))
    adult=_json(ROOT/'ADULT_MOCK_AUDIO_MANIFEST_V46_26.json')
    for x in adult.get('items',[]):
        add(x.get('audio_file'),{'audio_id':x.get('audio_id'),'profile':'adult','transcript':x.get('text'),'synthetic':x.get('synthetic'),'human_recording':x.get('human_recording'),'voice_profiles':[x.get('voice_profile')] if x.get('voice_profile') else [],'source_manifest':'ADULT_MOCK_AUDIO_MANIFEST_V46_26.json','pack_id':x.get('pack_id'),'speed_wpm':x.get('speed_wpm')})
    for fn,profile in [('VOICE_SIMULATION_MANIFEST_V46_12.json','schools_legacy'),('FIDELITY_VOICE_SIMULATION_MANIFEST_V46_12.json','fidelity')]:
        d=_json(ROOT/fn)
        for x in d.get('targets',[]):
            probe=x.get('probe') or {}; fmt=probe.get('format') or {}; streams=probe.get('streams') or []; st=streams[0] if streams else {}
            add(x.get('file'),{'audio_id':x.get('audio_id'),'profile':profile,'part':x.get('part'),'voice_profiles':x.get('voices') or [],'synthetic':d.get('synthetic'), 'human_recording':d.get('human_recording'),'sha256':x.get('sha256'),'duration_seconds':float(fmt.get('duration')) if fmt.get('duration') else None,'bit_rate':int(fmt.get('bit_rate')) if fmt.get('bit_rate') else None,'sample_rate':int(st.get('sample_rate')) if st.get('sample_rate') else None,'channels':st.get('channels'),'source_manifest':fn,'pack_id':x.get('pack_id')})
    # Enrich from exam pack transcripts when an audio id/path is referenced.
    for p in sorted((ROOT/'exam_packs').glob('*.json')):
        if p.name.endswith('index.json'): continue
        try:d=_json(p)
        except Exception:continue
        profile='adult' if str(d.get('pack_id','')).startswith('pq-adult-') else 'schools'
        for x in d.get('listening') or []:
            add(x.get('audio_file'),{'audio_id':x.get('audio_id'),'profile':profile,'part':x.get('part'),'transcript':x.get('transcript'),'question':x.get('prompt'),'options':x.get('options'),'answer':x.get('answer'),'focus':x.get('focus'),'source_manifest':p.as_posix()})
    return meta,school

def _seed_audio(cur):
    meta,school=_audio_metadata(); key='audio:all'
    files=[]
    for p in (ROOT/'assets'/'audio').rglob('*'):
        if p.is_file() and p.suffix.lower() in {'.mp3','.wav','.m4a','.ogg'}:
            files.append(p)
    _package(cur,key,'all','audio_assets',school.get('version'),'PET Quest Audio Assets','PET_AUDIO_BANK_V46_18.json',len(files),{'school_audio_bank':_header(school),'all_audio_file_count':len(files)})
    cur.execute('DELETE FROM audio_assets')
    sql='''INSERT INTO audio_assets(asset_path,audio_id,profile,part,item_index,transcript,question,options_json,answer_index,focus,voice_profiles_json,training_speeds_json,exam_speed,exam_max_plays,synthetic,human_recording,duration_seconds,bit_rate,sample_rate,channels,sha256,file_size,source_manifest,metadata_json)
           VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)'''
    for p in sorted(files):
        rel=p.relative_to(ROOT).as_posix(); x=meta.get(rel,{})
        sha=x.get('sha256') or _sha(p)
        cur.execute(sql,(rel,x.get('id') or x.get('audio_id'),x.get('profile') or 'unclassified',x.get('part'),x.get('index'),x.get('transcript') or x.get('text'),x.get('question'),_j(x.get('options')) if x.get('options') is not None else None,x.get('answer'),x.get('focus'),_j(x.get('voice_profiles') or x.get('voices') or []),_j(x.get('training_speeds') or []),x.get('exam_speed'),x.get('exam_max_plays'),x.get('synthetic'),x.get('human_recording'),x.get('duration_seconds'),x.get('bit_rate'),x.get('sample_rate'),x.get('channels'),sha,p.stat().st_size,x.get('source_manifest'),_j({k:v for k,v in x.items() if k not in {'transcript','text','question','options','answer'}})))
    return len(files)

def _derived_item_id(pack_id,skill,part,idx,x):
    return str(x.get('id') or f'{pack_id}-{skill[0]}{part or 0}-{idx:02d}')

def _seed_exam(cur):
    cur.execute('DELETE FROM exam_items'); cur.execute('DELETE FROM exam_packs')
    total_packs=total_items=0
    for profile,indexfile,prefix in [('schools','exam_packs/index.json','pq-mock-'),('adult','exam_packs/adult_index.json','pq-adult-')]:
        idx=_json(ROOT/indexfile); _package(cur,f'exam-index:{profile}',profile,'exam_index',idx.get('version'),f'Exam index {profile}',indexfile,len(idx.get('packs') or []),idx)
        for p in sorted((ROOT/'exam_packs').glob(prefix+'*.json')):
            d=_json(p); pack=d.get('pack_id') or p.stem
            counts={k:len(d.get(k) or []) for k in ('reading','listening','writing','speaking')}
            header=_header(d)
            cur.execute('''INSERT INTO exam_packs(pack_id,profile,title,version,status,theme,source_file,reading_count,listening_count,writing_count,speaking_count,header_json)
                           VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)''',(pack,profile,d.get('title') or pack,d.get('version'),d.get('status'),d.get('theme'),p.relative_to(ROOT).as_posix(),counts['reading'],counts['listening'],counts['writing'],counts['speaking'],_j(header)))
            total_packs+=1
            for skill in ('reading','listening','writing','speaking'):
                for n,x in enumerate(d.get(skill) or [],1):
                    part=x.get('part')
                    iid=_derived_item_id(pack,skill,part,n,x)
                    cur.execute('''INSERT INTO exam_items(pack_id,item_id,skill,part,item_order,interaction,prompt,source_text,source_label,options_json,answer_index,audio_id,audio_file,transcript,target_words,focus,audit_json,payload_json)
                                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb)''',(pack,iid,skill,part,n,x.get('interaction'),x.get('prompt'),x.get('source_text'),x.get('source_label'),_j(x.get('options')) if x.get('options') is not None else None,x.get('answer'),x.get('audio_id'),x.get('audio_file'),x.get('transcript'),x.get('target_words'),x.get('focus'),_j(x.get('audit_v46_28') or {}),_j(x)))
                    total_items+=1
    return total_packs,total_items

def seed_all():
    counts={}; errors=[]; run_id=None
    with postgres_auth.connect() as pg:
        with pg.cursor() as cur:
            cur.execute("INSERT INTO content_seed_runs(status,source_root) VALUES('running',%s) RETURNING id",(str(ROOT),)); run_id=cur.fetchone()[0]; pg.commit()
        try:
            with pg.cursor() as cur:
                counts['practice_schools']=_seed_practice(cur,'schools','PRACTICE_BANK_V46_21.json')
                counts['practice_adult']=_seed_practice(cur,'adult','PRACTICE_BANK_ADULT_V46_26.json')
                counts['curriculum_lessons']=_seed_curriculum(cur)
                counts['audio_assets']=_seed_audio(cur)
                packs,items=_seed_exam(cur); counts['exam_packs']=packs; counts['exam_items']=items
            pg.commit()
            with pg.cursor() as cur:
                cur.execute("UPDATE content_seed_runs SET finished_at=CURRENT_TIMESTAMP,status='ok',counts_json=%s::jsonb WHERE id=%s",(_j(counts),run_id))
            pg.commit(); return {'ok':True,'counts':counts,'run_id':run_id}
        except Exception as exc:
            pg.rollback(); errors.append(str(exc)[:1000])
            with pg.cursor() as cur:
                cur.execute("UPDATE content_seed_runs SET finished_at=CURRENT_TIMESTAMP,status='error',errors_json=%s::jsonb WHERE id=%s",(_j(errors),run_id))
            pg.commit(); raise

def health():
    expected={'practice_schools':5000,'practice_adult':3000,'curriculum_lessons':100,'exam_packs':40,'exam_items':2500,'audio_assets_min':800}
    try:
        with postgres_auth.connect() as c:
            with c.cursor() as cur:
                cur.execute("SELECT profile,COUNT(*) FROM practice_bank_items GROUP BY profile"); p=dict(cur.fetchall())
                cur.execute('SELECT COUNT(*) FROM curriculum_lessons'); lessons=cur.fetchone()[0]
                cur.execute('SELECT COUNT(*) FROM audio_assets'); audio=cur.fetchone()[0]
                cur.execute('SELECT COUNT(*) FROM exam_packs'); packs=cur.fetchone()[0]
                cur.execute('SELECT COUNT(*) FROM exam_items'); items=cur.fetchone()[0]
                cur.execute('SELECT COUNT(*) FROM content_packages'); packages=cur.fetchone()[0]
        counts={'practice_schools':int(p.get('schools',0)),'practice_adult':int(p.get('adult',0)),'curriculum_lessons':int(lessons),'audio_assets':int(audio),'exam_packs':int(packs),'exam_items':int(items),'content_packages':int(packages)}
        ok=counts['practice_schools']>=5000 and counts['practice_adult']>=3000 and counts['curriculum_lessons']>=100 and counts['audio_assets']>=800 and counts['exam_packs']>=40 and counts['exam_items']>=2500
        return {'ok':ok,'counts':counts,'expected':expected}
    except Exception as exc:
        return {'ok':False,'error':str(exc)[:300],'expected':expected}

def practice_bank(profile='schools'):
    profile='adult' if profile=='adult' else 'schools'; key=f'practice:{profile}'
    with postgres_auth.connect() as c:
        with c.cursor() as cur:
            cur.execute('SELECT metadata_json FROM content_packages WHERE package_key=%s',(key,)); row=cur.fetchone(); meta=row[0] if row else {}
            cur.execute('SELECT payload_json FROM practice_bank_items WHERE profile=%s ORDER BY content_key',(profile,)); items=[r[0] for r in cur.fetchall()]
    out=dict(meta or {}); out['items']=items; out['total']=len(items); return out

def curriculum():
    with postgres_auth.connect() as c:
        with c.cursor() as cur:
            cur.execute("SELECT metadata_json FROM content_packages WHERE package_key='curriculum:schools'"); row=cur.fetchone(); meta=row[0] if row else {}
            cur.execute('SELECT payload_json FROM curriculum_lessons ORDER BY lesson_order,lesson_id'); items=[r[0] for r in cur.fetchall()]
    out=dict(meta or {}); out['items']=items; out['lesson_count']=len(items); return out

def audio_bank():
    # Return exactly the school PET bank shape from DB-backed records.
    with postgres_auth.connect() as c:
        with c.cursor() as cur:
            cur.execute("SELECT metadata_json FROM content_packages WHERE package_key='audio:all'"); row=cur.fetchone(); pkg=row[0] if row else {}
            base=(pkg or {}).get('school_audio_bank') or {}
            cur.execute("SELECT metadata_json,asset_path,audio_id,part,item_index,transcript,question,options_json,answer_index,focus,voice_profiles_json,training_speeds_json,exam_speed,exam_max_plays,synthetic,human_recording,duration_seconds,bit_rate,sample_rate,channels,sha256 FROM audio_assets WHERE profile='schools' AND audio_id LIKE 'pqbank-%' ORDER BY part,item_index,audio_id")
            items=[]
            for r in cur.fetchall():
                md=dict(r[0] or {}); md.update({'audio_file':r[1],'id':r[2],'part':r[3],'index':r[4],'transcript':r[5],'question':r[6],'options':r[7],'answer':r[8],'focus':r[9],'voice_profiles':r[10],'training_speeds':r[11],'exam_speed':r[12],'exam_max_plays':r[13],'synthetic':r[14],'human_recording':r[15],'duration_seconds':r[16],'bit_rate':r[17],'sample_rate':r[18],'channels':r[19],'sha256':r[20]}); items.append(md)
    out=dict(base); out['items']=items; out['total']=len(items); return out

def exam_index(profile='schools'):
    profile='adult' if profile=='adult' else 'schools'; key=f'exam-index:{profile}'
    with postgres_auth.connect() as c:
        with c.cursor() as cur:
            cur.execute('SELECT metadata_json FROM content_packages WHERE package_key=%s',(key,)); row=cur.fetchone()
    return dict(row[0] if row else {})

def exam_pack(pack_id):
    with postgres_auth.connect() as c:
        with c.cursor() as cur:
            cur.execute('SELECT header_json FROM exam_packs WHERE pack_id=%s',(pack_id,)); row=cur.fetchone()
            if not row:return None
            out=dict(row[0] or {}); out['pack_id']=pack_id
            for skill in ('reading','listening','writing','speaking'):
                cur.execute('SELECT payload_json FROM exam_items WHERE pack_id=%s AND skill=%s ORDER BY item_order',(pack_id,skill)); out[skill]=[r[0] for r in cur.fetchall()]
    return out

if __name__=='__main__':
    postgres_auth.ensure_database_exists(); postgres_auth.init_schema(); print(seed_all()); print(health())
