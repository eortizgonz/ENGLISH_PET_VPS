#!/usr/bin/env python3
import os, json, hashlib, hmac, secrets, datetime, time, csv, io, re, shutil, threading, smtplib, ssl, math, subprocess
from email.message import EmailMessage
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import postgres_auth
import password_recovery
import postgres_content

ROOT=Path(__file__).resolve().parent
BACKUP_DIR=Path(os.environ.get('PETQUEST_BACKUP_DIR', str(ROOT/'backups')))
HOST=os.environ.get('PETQUEST_HOST','127.0.0.1')
PORT=int(os.environ.get('PORT','8080'))
SESSION_HOURS=int(os.environ.get('PETQUEST_SESSION_HOURS','12'))
DEV_MODE=os.environ.get('PETQUEST_DEV_MODE','1')=='1'
APP_ENV=os.environ.get('PETQUEST_ENV','development').strip().lower()
PUBLIC_BASE_URL=os.environ.get('PETQUEST_PUBLIC_BASE_URL',f'http://{HOST}:{PORT}')
BACKUP_RETENTION=int(os.environ.get('PETQUEST_BACKUP_RETENTION','14'))
REQUIRE_GUARDIAN_CONSENT=os.environ.get('PETQUEST_REQUIRE_GUARDIAN_CONSENT','1')=='1'
DATA_RETENTION_DAYS=int(os.environ.get('PETQUEST_DATA_RETENTION_DAYS','365'))
REQUIRE_POSTGRES_PRODUCTION=os.environ.get('PETQUEST_REQUIRE_POSTGRES_IN_PRODUCTION','1')=='1'
SEED_DEMO_DATA=os.environ.get('PETQUEST_SEED_DEMO_DATA','1' if APP_ENV in {'development','test'} else '0')=='1'
DATABASE_URL=os.environ.get('DATABASE_URL','').strip()
REQUIRE_SMTP_PRODUCTION=os.environ.get('PETQUEST_REQUIRE_SMTP_IN_PRODUCTION','1')=='1'
REQUIRE_HTTPS_PRODUCTION=os.environ.get('PETQUEST_REQUIRE_HTTPS_IN_PRODUCTION','1')=='1'
MAX_REQUEST_BYTES=int(os.environ.get('PETQUEST_MAX_REQUEST_BYTES','1048576'))
STRICT_CORS_ORIGINS=[x.strip() for x in os.environ.get('PETQUEST_CORS_ORIGINS','').split(',') if x.strip()]
DATABASE_ENGINE='postgres'
AUTH_DATABASE_ENGINE='postgres'
REQUIRE_POSTGRES_AUTH=os.environ.get('PETQUEST_REQUIRE_POSTGRES_AUTH','1')=='1'
RATE_LIMIT_WINDOW=60
RATE_LIMIT_MAX=30
SMTP_HOST=os.environ.get('PETQUEST_SMTP_HOST','').strip()
SMTP_PORT=int(os.environ.get('PETQUEST_SMTP_PORT','587'))
SMTP_USER=os.environ.get('PETQUEST_SMTP_USER','').strip()
SMTP_PASSWORD=os.environ.get('PETQUEST_SMTP_PASSWORD','')
SMTP_FROM=os.environ.get('PETQUEST_SMTP_FROM',SMTP_USER or 'no-reply@petquest.local').strip()
SMTP_TLS=os.environ.get('PETQUEST_SMTP_TLS','1')=='1'
_RATE={}
_RATE_LOCK=threading.Lock()
MAX_LOGIN_ATTEMPTS=5
LOCK_MINUTES=10
RESET_MINUTES=30
VERIFY_HOURS=24
PBKDF2_ITERS=310000
ALLOWED_ROLES={'student','guardian','teacher','school','platform_support','admin','academic_reviewer','content_author'}
ALLOWED_SKILLS={'reading','writing','listening','speaking'}
APP_VERSION='46.32-pg'
LICENSE_PLANS={'pilot':30,'school':500,'enterprise':5000}


DEMO_EMAILS={
    'student@petquest.local','teacher@petquest.local','school@petquest.local','admin@petquest.local'
}

def production_startup_checks():
    errors=[]
    if APP_ENV=='production':
        if DEV_MODE: errors.append('PETQUEST_DEV_MODE must be 0 in production')
        if REQUIRE_POSTGRES_PRODUCTION and not DATABASE_URL.lower().startswith(('postgresql://','postgres://')):
            errors.append('DATABASE_URL must be PostgreSQL in production')
        if SEED_DEMO_DATA: errors.append('PETQUEST_SEED_DEMO_DATA must be false in production')
        if REQUIRE_HTTPS_PRODUCTION and not PUBLIC_BASE_URL.lower().startswith('https://'):
            errors.append('PETQUEST_PUBLIC_BASE_URL must use HTTPS in production')
        if REQUIRE_SMTP_PRODUCTION and not email_configured():
            errors.append('SMTP/email provider must be configured in production')
    return errors

def known_demo_accounts_present():
    try:
        c=conn(); q=','.join('?' for _ in DEMO_EMAILS)
        n=c.execute(f'SELECT COUNT(*) FROM users WHERE lower(email) IN ({q})',tuple(sorted(DEMO_EMAILS))).fetchone()[0]
        c.close(); return n>0
    except Exception:
        return False

def now_dt(): return datetime.datetime.now(datetime.timezone.utc)
def now(): return now_dt().isoformat()
def iso_after(**kw): return (now_dt()+datetime.timedelta(**kw)).isoformat()
def hash_pw(password,salt=None):
    salt=salt or secrets.token_bytes(16)
    digest=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,PBKDF2_ITERS)
    return salt.hex()+'$'+digest.hex()
def password_hash_scheme(stored):
    """Identify supported password-hash formats.

    Current PET Quest hashes use: <32 hex salt>$<64 hex PBKDF2-SHA256 digest>.
    Legacy V46.30 PostgreSQL builds could leave a bare 64-hex SHA-256 digest.
    The legacy format is accepted only to permit an automatic one-time migration.
    """
    value=str(stored or '').strip()
    if re.fullmatch(r'[0-9a-fA-F]{32}\$[0-9a-fA-F]{64}',value):
        return 'pbkdf2_sha256'
    if re.fullmatch(r'[0-9a-fA-F]{64}',value):
        return 'legacy_sha256'
    return 'unknown'

def verify_pw(password,stored):
    scheme=password_hash_scheme(stored)
    try:
        if scheme=='pbkdf2_sha256':
            s,d=str(stored).split('$',1); salt=bytes.fromhex(s)
            test=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,PBKDF2_ITERS).hex()
            return hmac.compare_digest(test,d.lower())
        if scheme=='legacy_sha256':
            # Compatibility bridge only. A successful login upgrades this hash immediately.
            test=hashlib.sha256(password.encode()).hexdigest()
            return hmac.compare_digest(test,str(stored).lower())
    except Exception:
        return False
    return False

def strong_password(v):
    return len(v or '')>=10 and bool(re.search(r'[A-Z]',v)) and bool(re.search(r'[a-z]',v)) and bool(re.search(r'\d',v))
def valid_email(v): return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$',v or ''))
def clean_text(v,n=400): return str(v or '').strip()[:n]
def rate_ok(key, limit=RATE_LIMIT_MAX, window=RATE_LIMIT_WINDOW):
    t=time.time()
    with _RATE_LOCK:
        arr=[x for x in _RATE.get(key,[]) if t-x<window]
        if len(arr)>=limit:
            _RATE[key]=arr; return False
        arr.append(t); _RATE[key]=arr; return True
def email_configured(): return bool(SMTP_HOST and SMTP_FROM and (not SMTP_USER or SMTP_PASSWORD))
def send_email(to, subject, text):
    if not email_configured(): return False
    msg=EmailMessage(); msg['From']=SMTP_FROM; msg['To']=to; msg['Subject']=subject; msg.set_content(text)
    try:
        with smtplib.SMTP(SMTP_HOST,SMTP_PORT,timeout=10) as smtp:
            if SMTP_TLS: smtp.starttls(context=ssl.create_default_context())
            if SMTP_USER: smtp.login(SMTP_USER,SMTP_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as exc:
        print('[PETQuest] email delivery failed:',type(exc).__name__); return False
def cleanup_backups():
    items=sorted(BACKUP_DIR.glob('*.dump'), key=lambda x:x.stat().st_mtime, reverse=True)
    for old in items[max(1,BACKUP_RETENTION):]:
        try: old.unlink()
        except OSError: pass
def safe_json(raw, fallback=None):
    try:return json.loads(raw)
    except Exception:return fallback

def student_preparation_summary(student_id, school_id):
    """Build a per-user formative preparation record from persisted snapshot + academic evidence."""
    c=conn()
    st=c.execute('SELECT id,name,email,role,school_id FROM users WHERE id=? AND school_id=?',(student_id,school_id)).fetchone()
    if not st:
        c.close(); return None
    snap=c.execute('SELECT payload,updated_at FROM snapshots WHERE user_id=?',(student_id,)).fetchone()
    payload=safe_json(snap['payload'],{}) if snap and snap['payload'] else {}
    hist=payload.get('history',[]) if isinstance(payload.get('history',[]),list) else []
    hist=[x for x in hist if isinstance(x,dict)]
    writing=payload.get('writing',[]) if isinstance(payload.get('writing',[]),list) else []
    speaking=payload.get('speaking',[]) if isinstance(payload.get('speaking',[]),list) else []
    local_mocks=payload.get('mockAttempts',[]) if isinstance(payload.get('mockAttempts',[]),list) else []

    # Modern practice modules persist directly to learning_events instead of the
    # legacy snapshot history. Merge only non-duplicated event families here;
    # practice_answer/mock_answer are mirrors of snapshot entries and are omitted.
    event_rows=[dict(r) for r in c.execute(
        "SELECT id,event_type,skill,item_id,success,created_at FROM learning_events "
        "WHERE user_id=? AND event_type IN ('practice_bank_answer','practice_remediation_answer','audio_bank_answer') "
        "AND success IS NOT NULL ORDER BY id",(student_id,)).fetchall()]
    event_hist=[{'qid':str(x.get('item_id') or ('event-'+str(x.get('id')))),
                 'skill':str(x.get('skill') or '').lower(),'correct':bool(x.get('success')),
                 'date':x.get('created_at'),'source':x.get('event_type')} for x in event_rows]
    evidence=hist+event_hist

    attempts=len(evidence)
    correct=sum(1 for x in evidence if bool(x.get('correct')))
    wrong=max(0,attempts-correct)
    accuracy=round(correct*100/attempts,1) if attempts else 0.0

    # A question-level mistake is considered corrected only if a later attempt for the same qid is correct.
    q_events={}
    for i,x in enumerate(evidence):
        qid=str(x.get('qid') or '').strip()
        if qid: q_events.setdefault(qid,[]).append((i,bool(x.get('correct'))))
    mistake_qids={qid for qid,events in q_events.items() if any(not ok for _,ok in events)}
    corrected_qids=set()
    for qid in mistake_qids:
        events=q_events[qid]
        first_wrong=min(i for i,ok in events if not ok)
        if any(ok and i>first_wrong for i,ok in events): corrected_qids.add(qid)
    pending_qids=mistake_qids-corrected_qids

    err_rows=[dict(r) for r in c.execute('SELECT error_code,skill,subcompetence,occurred_at FROM academic_error_events WHERE student_id=? ORDER BY id',(student_id,)).fetchall()]
    rem_rows=[dict(r) for r in c.execute('SELECT error_code,correct,attempted_at FROM academic_remediation_attempts WHERE student_id=? ORDER BY id',(student_id,)).fetchall()]
    error_codes={str(x.get('error_code') or '').strip() for x in err_rows if str(x.get('error_code') or '').strip()}
    rem_correct={str(x.get('error_code') or '').strip() for x in rem_rows if x.get('correct') and str(x.get('error_code') or '').strip()}
    corrected_codes=error_codes & rem_correct
    pending_codes=error_codes-corrected_codes

    # Recurrent errors are targets that fail more than once. This remains a formative signal, not a diagnosis.
    recurrent_qids=0
    for qid,events in q_events.items():
        if sum(1 for _,ok in events if not ok)>=2: recurrent_qids+=1
    recurrent_codes=0
    code_counts={}
    for x in err_rows:
        code=str(x.get('error_code') or '').strip()
        if code: code_counts[code]=code_counts.get(code,0)+1
    recurrent_codes=sum(1 for n in code_counts.values() if n>=2)
    recurrent_targets=recurrent_qids+recurrent_codes

    total_error_targets=len(mistake_qids)+len(error_codes)
    corrected_targets=len(corrected_qids)+len(corrected_codes)
    pending_targets=len(pending_qids)+len(pending_codes)
    correction_rate=round(corrected_targets*100/total_error_targets,1) if total_error_targets else 100.0

    def skill_pct(skill):
        vals=[x for x in evidence if str(x.get('skill','')).lower()==skill and 'correct' in x]
        if vals: return round(sum(1 for x in vals if x.get('correct'))*100/len(vals),1)
        return 0.0
    reading=skill_pct('reading')
    listening=skill_pct('listening')
    wvals=[float(x.get('score')) for x in writing if isinstance(x,dict) and isinstance(x.get('score'),(int,float))]
    svals=[float(x.get('score')) for x in speaking if isinstance(x,dict) and isinstance(x.get('score'),(int,float))]
    pronunciation_scores=[]
    for x in speaking:
        if not isinstance(x,dict): continue
        metrics=x.get('metrics') if isinstance(x.get('metrics'),dict) else {}
        value=metrics.get('pronunciation_proxy')
        if isinstance(value,(int,float)): pronunciation_scores.append(max(0.0,min(100.0,float(value))))
    wscore=round(max(0.0,min(100.0,(sum(wvals)/len(wvals))*5)),1) if wvals else 0.0
    sscore=round(max(pronunciation_scores),1) if pronunciation_scores else (round(max(0.0,min(100.0,(sum(svals)/len(svals))*5)),1) if svals else 0.0)

    db_mocks=[dict(r) for r in c.execute('SELECT id,pack_id,skill,total_items,correct_items,pct,started_at,finished_at,source FROM mock_attempts WHERE student_id=? ORDER BY id DESC',(student_id,)).fetchall()]
    db_speaking=[dict(r) for r in c.execute('SELECT score_pct,part,metrics_json,created_at FROM speaking_attempts WHERE student_id=? ORDER BY id DESC LIMIT 40',(student_id,)).fetchall()]
    today_minutes_row=c.execute("SELECT COALESCE(SUM(minutes),0) m FROM learning_events WHERE user_id=? AND date(created_at)=date('now')",(student_id,)).fetchone()
    today_minutes=round(float(today_minutes_row['m'] or 0),1) if today_minutes_row else 0.0
    if db_speaking:
        for r in db_speaking:
            metrics=safe_json(r.get('metrics_json'),{}) if r.get('metrics_json') else {}
            value=metrics.get('pronunciation_proxy') if isinstance(metrics,dict) else None
            if isinstance(value,(int,float)): pronunciation_scores.append(max(0.0,min(100.0,float(value))))
        if pronunciation_scores:
            # Pronunciation is a personal-best practice indicator: a later lower
            # attempt must not erase the learner's highest demonstrated result.
            sscore=round(max(pronunciation_scores),1)
        else:
            # Preserve legacy records that predate the pronunciation metric.
            # For those, use the latest overall Speaking score per part.
            latest_by_part={}
            for r in db_speaking:
                latest_by_part.setdefault(int(r.get('part') or 0),float(r.get('score_pct') or 0))
            vals=[v for k,v in latest_by_part.items() if 1<=k<=4]
            if vals: sscore=round(sum(vals)/len(vals),1)
    c.close()

    # Combine persisted exact mocks with local mock attempts, retaining latest by exam/skill label.
    exams=[]
    seen=set()
    for m in db_mocks:
        key=(m.get('pack_id'),m.get('skill'))
        if key in seen: continue
        seen.add(key)
        pct=max(0.0,min(100.0,float(m.get('pct') or 0)))
        exams.append({'exam_id':m.get('pack_id'),'exam':m.get('pack_id'),'skill':m.get('skill'),'score':round(pct,1),'remaining':round(100-pct,1),'correct':int(m.get('correct_items') or 0),'total':int(m.get('total_items') or 0),'date':m.get('finished_at'),'source':m.get('source') or 'mock'})
    for i,m in enumerate(reversed(local_mocks)):
        skill=str(m.get('skill') or 'mock').lower(); exam_id=str(m.get('pack_id') or m.get('source') or f'local-{skill}')
        key=(exam_id,skill)
        if key in seen: continue
        seen.add(key)
        pct=max(0.0,min(100.0,float(m.get('score') or 0)))
        exams.append({'exam_id':exam_id,'exam':exam_id,'skill':skill,'score':round(pct,1),'remaining':round(100-pct,1),'correct':None,'total':m.get('total'),'date':m.get('date'),'source':m.get('source') or 'local-mock'})

    # Internal preparation grade: equal 25% skill weighting. Missing evidence remains 0 by design.
    skill_scores={'reading':reading,'writing':wscore,'listening':listening,'speaking':sscore}
    preparation=round(sum(skill_scores.values())/4,1)
    remaining=round(max(0.0,100-preparation),1)
    if preparation>=90: band='Excelente preparación'
    elif preparation>=75: band='Preparación alta'
    elif preparation>=60: band='En progreso'
    elif preparation>0: band='Requiere refuerzo'
    else: band='Sin evidencia suficiente'
    snapshot_xp=max(0,int(float((payload.get('profile') or {}).get('xp') or 0)))
    event_xp=sum(10 if x.get('correct') else 3 for x in event_hist)
    evidence_dates=[str(x.get('date') or '') for x in evidence if x.get('date')]
    updated_at=max(([str(snap['updated_at'])] if snap and snap['updated_at'] else [])+evidence_dates,default=None)
    return {
        'student':dict(st),'updated_at':updated_at,
        'activity':{'attempts':attempts,'snapshot_attempts':len(hist),'event_attempts':len(event_hist),'correct_answers':correct,'wrong_answers':wrong,'accuracy':accuracy,'today_minutes':today_minutes,'xp':snapshot_xp+event_xp},
        'errors':{'total_error_targets':total_error_targets,'corrected':corrected_targets,'pending':pending_targets,'recurrent':recurrent_targets,'correction_rate':correction_rate,'question_errors':len(mistake_qids),'academic_error_patterns':len(error_codes)},
        'learner_target':{'exam_profile':str((payload.get('profile') or {}).get('examProfile') or 'schools'),'mastery_goal':str((payload.get('profile') or {}).get('masteryGoal') or 'solid'),'exam_date':str((payload.get('profile') or {}).get('examDate') or '')},
        'skills':skill_scores,
        'preparation':{'score':preparation,'remaining':remaining,'band':band,'label':'PET Quest Preparation Score','official_cambridge_score':False},
        'exams':exams[:30],
        'note':'Indicador formativo interno de PET Quest. No es una Cambridge English Scale ni una probabilidad oficial de aprobación.'
    }


class CompatRow:
    """SQLite-row compatible wrapper around a PostgreSQL tuple."""
    __slots__=('columns','values','index')
    def __init__(self, columns, values):
        self.columns=tuple(columns or ())
        self.values=tuple(values or ())
        self.index={name:i for i,name in enumerate(self.columns)}
    def __getitem__(self, key):
        if isinstance(key,int): return self.values[key]
        return self.values[self.index[key]]
    def __iter__(self): return iter(self.values)
    def __len__(self): return len(self.values)
    def keys(self): return self.columns
    def get(self,key,default=None):
        try:return self[key]
        except (KeyError,IndexError):return default
    def items(self): return [(k,self[k]) for k in self.columns]
    def __repr__(self): return repr(dict(self.items()))


def _translate_sql(sql):
    """Translate the small SQLite dialect used by the legacy runtime to PostgreSQL."""
    q=str(sql)
    q=re.sub(r'(?P<op>=|<>|!=)\s*"([^"\\]*)"', lambda m: m.group('op')+"'"+m.group(2).replace("'","''")+"'", q)
    q=q.replace("date(created_at)=date('now')", "created_at::timestamptz::date=CURRENT_DATE")
    q=q.replace("datetime('now','-24 hours')", "(CURRENT_TIMESTAMP - INTERVAL '24 hours')")
    q=q.replace("datetime('now')", "CURRENT_TIMESTAMP")
    ignore=False
    if re.search(r'\bINSERT\s+OR\s+IGNORE\s+INTO\b',q,re.I):
        q=re.sub(r'\bINSERT\s+OR\s+IGNORE\s+INTO\b','INSERT INTO',q,flags=re.I)
        ignore=True
    out=[]; single=False; double=False; i=0
    while i<len(q):
        ch=q[i]
        if ch=="'" and not double:
            out.append(ch)
            if single and i+1<len(q) and q[i+1]=="'":
                out.append(q[i+1]); i+=2; continue
            single=not single; i+=1; continue
        if ch=='"' and not single:
            double=not double; out.append(ch); i+=1; continue
        if ch=='?' and not single and not double: out.append('%s')
        else: out.append(ch)
        i+=1
    q=''.join(out)
    if ignore and ' ON CONFLICT ' not in q.upper(): q=q.rstrip().rstrip(';')+' ON CONFLICT DO NOTHING'
    q=re.sub(r'ROUND\(AVG\(([^)]+)\),\s*1\)', r'ROUND(AVG(\1)::numeric,1)', q, flags=re.I)
    return q


_ID_TABLES={
    'schools','users','courses','assignments','support_groups','intervention_runs',
    'school_quality_snapshots','academic_review_snapshots','governance_goals','governance_actions',
    'governance_reviews','teacher_availability','schedule_sessions','school_licenses','onboarding_items',
    'release_acceptance_runs','strategic_targets','questions','audit_log','guardian_consents','privacy_requests',
    'calibration_outcomes','anonymous_calibration_candidates','psychometric_reviews','academic_error_events',
    'academic_remediation_attempts','mock_attempts','mock_item_responses','speaking_attempts',
    'speaking_interaction_sessions','speaking_interaction_turns','learning_events','recovery_checks','planning_scenarios'
}

class PgResult:
    def __init__(self, cursor, lastrowid=None):
        self.cursor=cursor; self.lastrowid=lastrowid; self.rowcount=cursor.rowcount
        self.columns=[d.name if hasattr(d,'name') else d[0] for d in (cursor.description or [])]
    def _wrap(self,row): return None if row is None else CompatRow(self.columns,row)
    def fetchone(self): return self._wrap(self.cursor.fetchone())
    def fetchall(self): return [self._wrap(x) for x in self.cursor.fetchall()]

class PgCompatConnection:
    def __init__(self): self.raw=postgres_auth.connect()
    def execute(self, sql, params=()):
        q=_translate_sql(sql); cur=self.raw.cursor(); cur.execute(q,tuple(params or ()))
        last_id=None
        m=re.match(r'\s*INSERT\s+INTO\s+(?:public\.)?([a-zA-Z_][a-zA-Z0-9_]*)',q,re.I)
        if m and m.group(1).lower() in _ID_TABLES:
            try:
                x=self.raw.cursor(); x.execute('SELECT LASTVAL()'); last_id=int(x.fetchone()[0]); x.close()
            except Exception: last_id=None
        return PgResult(cur,last_id)
    def commit(self): self.raw.commit()
    def rollback(self): self.raw.rollback()
    def close(self): self.raw.close()


def conn(): return PgCompatConnection()


def audit(c,user_id,action,entity='',entity_id='',meta=None):
    c.execute('INSERT INTO audit_log(user_id,action,entity,entity_id,meta_json,created_at) VALUES(?,?,?,?,?,?)',
              (user_id,action,entity,str(entity_id or ''),json.dumps(meta or {},ensure_ascii=False),now()))


def _ensure_postgres_id_sequences():
    """Give legacy BIGINT primary-key columns sequence defaults without dropping data."""
    sql=r'''DO $$
    DECLARE r record; seq text; mx bigint;
    BEGIN
      FOR r IN
        SELECT c.table_name
        FROM information_schema.columns c
        JOIN information_schema.tables t ON t.table_schema=c.table_schema AND t.table_name=c.table_name
        WHERE c.table_schema='public' AND c.column_name='id'
          AND c.data_type IN ('smallint','integer','bigint')
          AND c.column_default IS NULL AND t.table_type='BASE TABLE'
      LOOP
        seq := r.table_name || '_id_seq';
        EXECUTE format('CREATE SEQUENCE IF NOT EXISTS public.%I',seq);
        EXECUTE format('ALTER TABLE public.%I ALTER COLUMN id SET DEFAULT nextval(%L::regclass)',r.table_name,'public.'||seq);
        EXECUTE format('SELECT COALESCE(MAX(id),0) FROM public.%I',r.table_name) INTO mx;
        IF mx>0 THEN EXECUTE format('SELECT setval(%L::regclass,%s,true)','public.'||seq,mx);
        ELSE EXECUTE format('SELECT setval(%L::regclass,1,false)','public.'||seq); END IF;
      END LOOP;
    END $$;'''
    with postgres_auth.connect() as pg:
        with pg.cursor() as cur: cur.execute(sql)
        pg.commit()


def runtime_health():
    try:
        c=conn(); r=c.execute('SELECT current_database() database,current_user db_user,(SELECT COUNT(*) FROM users) registered_users').fetchone(); c.close()
        return {'ok':True,'database':r['database'],'user':r['db_user'],'registered_users':int(r['registered_users'] or 0),'identity_table':'users'}
    except Exception as exc:
        return {'ok':False,'database':postgres_auth.PG_DB,'user':postgres_auth.PG_USER,'error':str(exc)[:240]}


def init_db():
    postgres_auth.ensure_database_exists(); postgres_auth.init_schema(); postgres_auth.migrate_legacy_pet_users(); _ensure_postgres_id_sequences(); BACKUP_DIR.mkdir(parents=True,exist_ok=True)
    if SEED_DEMO_DATA:
        c=conn()
        if c.execute('SELECT COUNT(*) FROM schools').fetchone()[0]==0:
            sid=c.execute('INSERT INTO schools(name,created_at) VALUES(?,?)',('PET Quest Demo School',now())).lastrowid
            demos=[('student@petquest.local','Student123!','Mia Student','student'),('teacher@petquest.local','Teacher123!','Alex Teacher','teacher'),('school@petquest.local','School123!','School Coordinator','school'),('admin@petquest.local','Admin123!','Platform Admin','admin')]
            ids={}
            for email,pw,name,role in demos:
                ids[role]=c.execute('INSERT INTO users(email,password_hash,name,role,school_id,created_at,verified_at,username,profile_mode) VALUES(?,?,?,?,?,?,?,?,?)',(email,hash_pw(pw),name,role,sid,now(),now(),email.split('@')[0],'schools')).lastrowid
            cid=c.execute('INSERT INTO courses(school_id,name,teacher_id,created_at) VALUES(?,?,?,?)',(sid,'B1 PET - Year 6',ids['teacher'],now())).lastrowid
            c.execute('INSERT INTO enrollments(course_id,user_id) VALUES(?,?)',(cid,ids['student']))
            c.execute('INSERT INTO assignments(course_id,title,skill,due_date,created_at) VALUES(?,?,?,?,?)',(cid,'Reading Parts 1-3','reading',(datetime.date.today()+datetime.timedelta(days=5)).isoformat(),now()))
            c.execute('INSERT INTO assignments(course_id,title,skill,due_date,created_at) VALUES(?,?,?,?,?)',(cid,'Listening confidence','listening',(datetime.date.today()+datetime.timedelta(days=8)).isoformat(),now()))
            c.commit()
        c.close()


def ensure_individual_school(c):
    row=c.execute("SELECT id FROM schools WHERE name=? ORDER BY id LIMIT 1",('PET Quest Individual Learners',)).fetchone()
    if row:return row['id']
    sid=c.execute('INSERT INTO schools(name,created_at) VALUES(?,?)',('PET Quest Individual Learners',now())).lastrowid
    c.execute('INSERT INTO school_licenses(school_id,plan,status,student_seats,teacher_seats,starts_at,expires_at,created_at,created_by) VALUES(?,?,?,?,?,?,?,?,?)',(sid,'individual','active',100000,5,now(),None,now(),None))
    return sid


def create_backup():
    stamp=now_dt().strftime('%Y%m%dT%H%M%SZ'); out=BACKUP_DIR/f'petquest-{stamp}.dump'
    env=os.environ.copy(); env['PGPASSWORD']=postgres_auth.PG_PASSWORD
    cmd=['pg_dump','-h',postgres_auth.PG_HOST,'-p',str(postgres_auth.PG_PORT),'-U',postgres_auth.PG_USER,'-d',postgres_auth.PG_DB,'-Fc','-f',str(out)]
    try: subprocess.run(cmd,check=True,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180)
    except FileNotFoundError as exc: raise RuntimeError('pg_dump_not_installed: instala postgresql-client en la imagen PET') from exc
    cleanup_backups(); return out

def db_stats():
    c=conn(); tables=['schools','users','courses','assignments','questions','snapshots','audit_log','guardian_consents','privacy_requests','support_groups','support_group_members','intervention_runs','intervention_run_members']; result={}
    for t in tables: result[t]=c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
    result['active_sessions']=c.execute('SELECT COUNT(*) FROM sessions WHERE expires_at>?',(now(),)).fetchone()[0]
    c.close(); return result

def intervention_decision(baseline,current,member_deltas):
    delta=round(current-baseline,1)
    improved=sum(1 for d in member_deltas if d>=5)
    ratio=(improved/len(member_deltas)) if member_deltas else 0
    if current>=75 and (delta>=3 or ratio>=0.6): return 'close','Objetivo alcanzado: cerrar y volver a ruta individual.'
    if delta>=8 or ratio>=0.7: return 'close','Mejora suficiente: cerrar y comprobar mantenimiento.'
    if delta>=3: return 'extend','Hay progreso: extender una semana y reevaluar.'
    if member_deltas: return 'change_strategy','Progreso insuficiente: cambiar estrategia o tipo de práctica.'
    return 'collect_more_data','Falta evidencia posterior: reunir más actividad antes de decidir.'

def audio_quality_status():
    path=ROOT/'assets'/'audio'/'fidelity'/'audio_manifest.json'
    try:
        m=json.loads(path.read_text())
        return {'manifest':True,'production_ready':bool(m.get('production_ready')),'recording_type':m.get('recording_type') or 'unknown','files':len(m.get('files') or [])}
    except Exception:return {'manifest':False,'production_ready':False,'recording_type':'missing','files':0}

def privacy_export_payload(user):
    c=conn()
    account=c.execute("SELECT id,email,name,role,school_id,created_at,disabled,verified_at,last_login_at FROM users WHERE id=?",(user['id'],)).fetchone()
    snap=c.execute("SELECT payload,updated_at FROM snapshots WHERE user_id=?",(user['id'],)).fetchone()
    cons=c.execute("SELECT guardian_name,guardian_email,consent_version,accepted_at,revoked_at FROM guardian_consents WHERE student_id=? ORDER BY id",(user['id'],)).fetchall()
    req=c.execute("SELECT id,request_type,status,note,requested_at,resolved_at FROM privacy_requests WHERE user_id=? ORDER BY id",(user['id'],)).fetchall()
    audits=c.execute("SELECT action,entity,entity_id,meta_json,created_at FROM audit_log WHERE user_id=? ORDER BY id DESC LIMIT 500",(user['id'],)).fetchall()
    courses=c.execute("SELECT c.id,c.name FROM courses c JOIN enrollments e ON e.course_id=c.id WHERE e.user_id=? ORDER BY c.name",(user['id'],)).fetchall() if user.get('role')=='student' else []
    events=c.execute("SELECT event_type,skill,item_id,success,minutes,meta_json,created_at FROM learning_events WHERE user_id=? ORDER BY id",(user['id'],)).fetchall()
    scenarios=c.execute("SELECT scenario_type,inputs_json,result_json,created_at FROM planning_scenarios WHERE created_by=? ORDER BY id",(user['id'],)).fetchall()
    speaking=c.execute("SELECT part,mode,transcript,duration_ms,metrics_json,rubric_json,score_pct,audio_local_key,created_at,source FROM speaking_attempts WHERE student_id=? ORDER BY id",(user['id'],)).fetchall()
    c.close()
    return {'generated_at':now(),'account':dict(account) if account else None,'snapshot':safe_json(snap['payload'],{}) if snap else None,'snapshot_updated_at':snap['updated_at'] if snap else None,'guardian_consents':[dict(x) for x in cons],'privacy_requests':[dict(x) for x in req],'audit_events':[dict(x) for x in audits],'courses':[dict(x) for x in courses],'learning_events':[dict(x) for x in events],'planning_scenarios':[dict(x) for x in scenarios],'speaking_attempts':[dict(x) for x in speaking],'retention_days':DATA_RETENTION_DAYS}

def persist_planning_scenario(user, scenario_type, inputs, result):
    c=conn(); cur=c.execute('INSERT INTO planning_scenarios(school_id,scenario_type,inputs_json,result_json,created_at,created_by) VALUES(?,?,?,?,?,?)',(user['school_id'],scenario_type,json.dumps(inputs,ensure_ascii=False),json.dumps(result,ensure_ascii=False),now(),user['id'])); c.commit(); sid=cur.lastrowid; c.close(); return sid

def mastery_from_snapshot(student_id, school_id):
    prep=student_preparation_summary(student_id,school_id) or {}
    skills={k:{'accuracy':float(prep.get(k,0) or 0),'mastery':float(prep.get(k,0) or 0)} for k in ('reading','listening','writing','speaking')}
    weak=sorted(({'focus':k,'mastery':v['mastery']} for k,v in skills.items()), key=lambda x:x['mastery'])[:3]
    accuracy=float(prep.get('accuracy',0) or 0); readiness=float(prep.get('preparation_score',prep.get('readiness',0)) or 0)
    risk='high' if readiness<55 else ('medium' if readiness<70 else 'low')
    return {'accuracy':accuracy,'readiness':readiness,'risk':risk,'skills':skills,'weak_focus':weak,'attempts':int(prep.get('attempts',0) or 0)}

def production_gate_status():
    required=['ACADEMIC','DATABASE','SECURITY','MULTI_TENANT','PRIVACY','EMAIL','AUDIO','BACKUP_RESTORE','DEVICE_MATRIX','LOAD_TEST','PENTEST','PILOT']
    snap=ROOT/'release_gate_snapshot.json'
    if snap.exists():
        try:
            data=json.loads(snap.read_text())
            checks={k:bool((data.get('checks') or {}).get(k,False)) for k in required}
            critical=int(data.get('critical_issues',0) or 0); high=int(data.get('high_issues',0) or 0)
            blocked=[k for k in required if not checks[k]]
            approved=(not blocked and critical==0 and high==0)
            return {'version':APP_VERSION,'criteria':required,'checks':checks,'blocked':blocked,'critical_issues':critical,'high_issues':high,'commercial_release':'APPROVED' if approved else 'BLOCKED','snapshot_generated':True,'internal_subcontrols':data.get('internal_subcontrols',{})}
        except Exception:
            pass
    checks={k:False for k in required}
    # Only lightweight truths are surfaced before the unified release gate has generated evidence.
    checks['DATABASE']=DATABASE_ENGINE=='postgres'
    checks['EMAIL']=email_configured()
    checks['AUDIO']=audio_quality_status().get('production_ready',False)
    blocked=[k for k in required if not checks[k]]
    return {'version':APP_VERSION,'criteria':required,'checks':checks,'blocked':blocked,'critical_issues':0,'high_issues':0,'commercial_release':'BLOCKED','snapshot_generated':False,'message':'Run PETQUEST_RELEASE_GATE.py to generate the validated release snapshot.'}


def _sigmoid(z):
    z=max(-35.0,min(35.0,z))
    return 1.0/(1.0+math.exp(-z))

def _fit_logistic(rows, iterations=1800, lr=0.08):
    if not rows:return None
    a=0.0;b=0.0
    for _ in range(iterations):
        ga=gb=0.0
        for r in rows:
            x=(float(r['predicted_readiness'])-70.0)/15.0; y=float(r['actual_pass'])
            p=_sigmoid(a+b*x); d=p-y; ga+=d; gb+=d*x
        n=float(len(rows)); a-=lr*ga/n; b-=lr*gb/n
    return {'intercept':a,'slope':b}

def _auc(pairs):
    pos=[p for p,y in pairs if y==1]; neg=[p for p,y in pairs if y==0]
    if not pos or not neg:return None
    wins=0.0
    for p in pos:
        for n in neg:wins += 1 if p>n else (0.5 if p==n else 0)
    return wins/(len(pos)*len(neg))

def _calibration_metrics(rows, model):
    if not rows or not model:return {}
    pairs=[]
    for r in rows:
        x=(float(r['predicted_readiness'])-70.0)/15.0
        p=_sigmoid(model['intercept']+model['slope']*x); pairs.append((p,int(r['actual_pass'])))
    n=len(pairs); brier=sum((p-y)**2 for p,y in pairs)/n
    logloss=-sum(y*math.log(max(p,1e-9))+(1-y)*math.log(max(1-p,1e-9)) for p,y in pairs)/n
    preds=[1 if p>=0.5 else 0 for p,y in pairs]; ys=[y for p,y in pairs]
    tp=sum(1 for pr,y in zip(preds,ys) if pr==1 and y==1); tn=sum(1 for pr,y in zip(preds,ys) if pr==0 and y==0)
    fp=sum(1 for pr,y in zip(preds,ys) if pr==1 and y==0); fn=sum(1 for pr,y in zip(preds,ys) if pr==0 and y==1)
    acc=(tp+tn)/n; sens=tp/(tp+fn) if tp+fn else None; spec=tn/(tn+fp) if tn+fp else None
    # 5-bin expected calibration error
    ece=0.0
    for lo in [0,.2,.4,.6,.8]:
        bucket=[(p,y) for p,y in pairs if lo<=p<(lo+.2) or (lo==.8 and p==1)]
        if bucket:
            conf=sum(p for p,y in bucket)/len(bucket); obs=sum(y for p,y in bucket)/len(bucket)
            ece += len(bucket)/n*abs(conf-obs)
    auc=_auc(pairs)
    return {'n':n,'brier':round(brier,4),'log_loss':round(logloss,4),'ece':round(ece,4),'accuracy':round(acc*100,1),'sensitivity':None if sens is None else round(sens*100,1),'specificity':None if spec is None else round(spec*100,1),'auc':None if auc is None else round(auc,3)}

def build_calibration_report(school_id):
    c=conn(); raw=[dict(r) for r in c.execute("SELECT * FROM calibration_outcomes WHERE school_id=? AND actual_pass IS NOT NULL ORDER BY COALESCE(exam_date,recorded_at),id",(school_id,)).fetchall()]
    review=c.execute("SELECT * FROM psychometric_reviews WHERE school_id=? AND independent=1 AND decision='approved' ORDER BY reviewed_at DESC,id DESC LIMIT 1",(school_id,)).fetchone(); c.close()
    # scientific model uses only outcomes external to PET Quest teaching judgement
    ext=[r for r in raw if r.get('source') in ('official_exam','external_mock')]
    # one latest external outcome per student avoids leakage/repeated-student inflation
    by={}
    for r in ext:by[int(r['student_id'])]=r
    unique=list(by.values())
    train=[]; hold=[]
    for r in unique:
        key=f"{r['student_id']}|{r.get('exam_date') or r.get('recorded_at')}".encode(); bucket=int(hashlib.sha256(key).hexdigest()[:8],16)%5
        (hold if bucket==0 else train).append(r)
    pass_n=sum(int(r['actual_pass'])==1 for r in unique); fail_n=len(unique)-pass_n
    model=_fit_logistic(train) if len(train)>=20 and sum(int(r['actual_pass']) for r in train)>0 and sum(1-int(r['actual_pass']) for r in train)>0 else None
    train_m=_calibration_metrics(train,model); hold_m=_calibration_metrics(hold,model)
    gates={
      'unique_external_students_300':len(unique)>=300,
      'passes_75':pass_n>=75,
      'fails_75':fail_n>=75,
      'holdout_50':len(hold)>=50,
      'holdout_auc_070':bool(hold_m.get('auc') is not None and hold_m['auc']>=.70),
      'holdout_brier_020':bool(hold_m.get('brier') is not None and hold_m['brier']<=.20),
      'holdout_ece_010':bool(hold_m.get('ece') is not None and hold_m['ece']<=.10),
      'sensitivity_65':bool(hold_m.get('sensitivity') is not None and hold_m['sensitivity']>=65),
      'specificity_65':bool(hold_m.get('specificity') is not None and hold_m['specificity']>=65),
      'independent_review_approved':bool(review)
    }
    statistical=all(v for k,v in gates.items() if k!='independent_review_approved')
    enabled=statistical and gates['independent_review_approved'] and model is not None
    status='validated' if enabled else ('holdout-ready' if statistical else ('provisional' if len(unique)>=40 else 'insufficient'))
    return {'status':status,'sample_size':len(raw),'external_unique_students':len(unique),'train_size':len(train),'holdout_size':len(hold),'pass_count':pass_n,'fail_count':fail_n,'training_metrics':train_m,'holdout_metrics':hold_m,'gates':gates,'statistical_gate_passed':statistical,'external_review':dict(review) if review else None,'probability_enabled':enabled,'model':model if enabled else None,'threshold_note':'Probability remains OFF until all external-outcome holdout gates and an independent psychometric review are approved. PET Quest Readiness is otherwise a preparation index, not a pass probability.'}


def _cambridge_band(score):
    score=float(score)
    if score>=160:return 'grade_a_b2_distinction'
    if score>=153:return 'grade_b_b1_merit'
    if score>=140:return 'grade_c_b1_pass'
    if score>=120:return 'level_a2'
    return 'below_a2_no_b1_certificate'

def _calibration_group(score):
    score=float(score)
    if score<140:return 'fail_a2'
    if score<153:return 'pass_b1'
    if score<160:return 'merit_b1'
    return 'distinction_b2'

def _fit_linear(rows):
    if len(rows)<2:return None
    xs=[float(r['predicted_readiness']) for r in rows]; ys=[float(r['actual_scale_score']) for r in rows]
    mx=sum(xs)/len(xs); my=sum(ys)/len(ys); den=sum((x-mx)**2 for x in xs)
    if den<=1e-9:return None
    slope=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/den; intercept=my-slope*mx
    return {'intercept':round(intercept,6),'slope':round(slope,6)}

def _scale_metrics(rows,model):
    if not rows or not model:return {'n':len(rows),'mae':None,'rmse':None,'r2':None}
    pairs=[]
    for r in rows:
        actual=float(r['actual_scale_score']); pred=model['intercept']+model['slope']*float(r['predicted_readiness']); pairs.append((pred,actual))
    n=len(pairs); mae=sum(abs(p-a) for p,a in pairs)/n; mse=sum((p-a)**2 for p,a in pairs)/n; rmse=math.sqrt(mse)
    mean=sum(a for _,a in pairs)/n; ss_tot=sum((a-mean)**2 for _,a in pairs); ss_res=sum((a-p)**2 for p,a in pairs)
    r2=None if ss_tot<=1e-9 else 1-ss_res/ss_tot
    return {'n':n,'mae':round(mae,3),'rmse':round(rmse,3),'r2':None if r2 is None else round(r2,3)}

def build_scale_equivalence_report(school_id):
    c=conn(); rows=[dict(r) for r in c.execute("SELECT * FROM anonymous_calibration_candidates WHERE school_id=? AND source IN ('official_exam','external_mock') ORDER BY recorded_at,id",(school_id,)).fetchall()]
    review=c.execute("SELECT * FROM psychometric_reviews WHERE school_id=? AND independent=1 AND decision='approved' ORDER BY reviewed_at DESC,id DESC LIMIT 1",(school_id,)).fetchone(); c.close()
    # One row per anonymous candidate by UNIQUE(school_id,anon_id); deterministic subject-level split avoids leakage.
    train=[]; hold=[]
    for r in rows:
        bucket=int(hashlib.sha256(str(r['anon_id']).encode()).hexdigest()[:8],16)%5
        (hold if bucket==0 else train).append(r)
    groups={'fail_a2':0,'pass_b1':0,'merit_b1':0,'distinction_b2':0}
    bands={}
    for r in rows:
        groups[_calibration_group(r['actual_scale_score'])]+=1
        bands[r['cambridge_band']]=bands.get(r['cambridge_band'],0)+1
    model=_fit_linear(train) if len(train)>=40 else None
    train_m=_scale_metrics(train,model); hold_m=_scale_metrics(hold,model)
    gates={
      'anonymous_external_candidates_300':len(rows)>=300,
      'fail_a2_40':groups['fail_a2']>=40,
      'pass_b1_40':groups['pass_b1']>=40,
      'merit_b1_40':groups['merit_b1']>=40,
      'distinction_b2_40':groups['distinction_b2']>=40,
      'holdout_60':len(hold)>=60,
      'holdout_mae_5':bool(hold_m.get('mae') is not None and hold_m['mae']<=5.0),
      'holdout_rmse_7':bool(hold_m.get('rmse') is not None and hold_m['rmse']<=7.0),
      'holdout_r2_065':bool(hold_m.get('r2') is not None and hold_m['r2']>=.65),
      'independent_review_approved':bool(review)
    }
    statistical=all(v for k,v in gates.items() if k!='independent_review_approved')
    enabled=statistical and gates['independent_review_approved'] and model is not None
    if len(rows)>=1000:maturity='mature_1000_plus'
    elif len(rows)>=500:maturity='robust_500_plus'
    elif len(rows)>=300:maturity='minimum_300_plus'
    else:maturity='building_evidence'
    status='validated' if enabled else ('holdout-ready' if statistical else ('provisional' if len(rows)>=40 else 'insufficient'))
    progress={'to_300':round(min(100,len(rows)/300*100),1),'to_500':round(min(100,len(rows)/500*100),1),'to_1000':round(min(100,len(rows)/1000*100),1)}
    return {'status':status,'maturity':maturity,'sample_size':len(rows),'train_size':len(train),'holdout_size':len(hold),'distribution':groups,'official_band_distribution':bands,'progress':progress,'training_metrics':train_m,'holdout_metrics':hold_m,'gates':gates,'statistical_gate_passed':statistical,'external_review':dict(review) if review else None,'scale_equivalence_enabled':enabled,'model':model if enabled else None,'note':'PET Quest ↔ Cambridge English Scale equivalence remains OFF until the anonymous external cohort, band-balance, holdout quality, and independent psychometric review gates all pass.'}

class Handler(SimpleHTTPRequestHandler):
    server_version='PETQuest/46.31-pg'
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
    def log_message(self,fmt,*args):
        message=re.sub(r'([?&](?:reset_token|verify_token)=)[^&\s\"]+',r'\1[REDACTED]',fmt%args)
        print('[PETQuest]',message)
    def copyfile(self, source, outputfile):
        try:
            return super().copyfile(source, outputfile)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # Browsers may cancel parallel/static requests during navigation or reload.
            # This is not an application failure and should not flood the Windows console.
            return None
    def end_headers(self):
        path=urlparse(self.path).path
        if not path.startswith('/api/') and (path.endswith('.html') or path.endswith('.js') or path.endswith('.css') or path.endswith('manifest.webmanifest') or path.endswith('sw.js')):
            self.send_header('Cache-Control','no-store, max-age=0, must-revalidate')
            self.send_header('Pragma','no-cache')
        self.send_header('X-PETQuest-Version',APP_VERSION)
        self.send_header('X-Content-Type-Options','nosniff'); self.send_header('X-Frame-Options','DENY')
        self.send_header('Referrer-Policy','same-origin'); self.send_header('Permissions-Policy','camera=(), geolocation=()')
        self.send_header('Cross-Origin-Opener-Policy','same-origin')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none';")
        super().end_headers()
    def json(self,obj,status=200):
        raw=json.dumps(obj,ensure_ascii=False).encode(); self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(raw))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(raw)
    def body(self):
        try:
            n=int(self.headers.get('Content-Length','0') or 0)
            if n>MAX_REQUEST_BYTES:return {}
            return json.loads(self.rfile.read(n) or b'{}')
        except Exception:return {}
    def bearer(self):
        h=self.headers.get('Authorization',''); return h[7:] if h.startswith('Bearer ') else ''
    def auth(self):
        token=self.bearer()
        if not token:return None
        c=conn(); r=c.execute('SELECT u.*,s.expires_at FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=?',(token,)).fetchone()
        if not r:c.close();return None
        try: expired=datetime.datetime.fromisoformat(r['expires_at'])<=now_dt()
        except Exception: expired=True
        if expired or r['disabled']:
            c.execute('DELETE FROM sessions WHERE token=?',(token,)); c.commit(); c.close(); return None
        c.execute('UPDATE sessions SET last_seen_at=? WHERE token=?',(now(),token)); c.commit(); user=dict(r); user.pop('password_hash',None); user.pop('expires_at',None); user['tenant_id']=user.get('school_id'); c.close(); return user
    def require_roles(self,u,*roles): return bool(u and u.get('role') in roles)
    def school_scope(self,u): return u.get('school_id')
    def do_GET(self):
        parsed=urlparse(self.path); p=parsed.path; qs=parse_qs(parsed.query)
        if p in ('/favicon.ico','/.well-known/appspecific/com.chrome.devtools.json'):
            self.send_response(204); self.send_header('Content-Length','0'); self.end_headers(); return
        if p=='/api/health':
            pg_health=runtime_health()
            content_health=postgres_content.health() if REQUIRE_POSTGRES_AUTH and pg_health.get('ok') else {'ok':False,'reason':'postgres_unavailable'}
            return self.json({'ok':True,'master_content':content_health,'version':APP_VERSION,'environment':APP_ENV,'database':DATABASE_ENGINE,'academic_database_engine':DATABASE_ENGINE,'auth_database_engine':AUTH_DATABASE_ENGINE,'database_url_configured':bool(DATABASE_URL),'production_database_ok':(APP_ENV!='production' or (DATABASE_URL.lower().startswith(('postgresql://','postgres://')) and DATABASE_ENGINE=='postgres')),'postgres_schema_available':(ROOT/'postgres_schema.sql').exists(),'postgres_runtime_active':bool(pg_health.get('ok')),'postgres_auth':pg_health,'time':now(),'stats':db_stats(),'security':{'pbkdf2_iterations':PBKDF2_ITERS,'session_hours':SESSION_HOURS,'login_lockout':True,'audit_log':True,'account_recovery':True,'csp':True,'guardian_consent_required':REQUIRE_GUARDIAN_CONSENT,'privacy_lifecycle':True,'max_request_bytes':MAX_REQUEST_BYTES,'strict_cors_origins':STRICT_CORS_ORIGINS},'multi_tenant':{'tenant_key':'school_id','backend_scope_enforced':True,'demo_seed_enabled':SEED_DEMO_DATA,'demo_accounts_available':known_demo_accounts_present()},'privacy':{'export':True,'delete_request':True,'rectification':True,'consent_revocation':True,'retention_days':DATA_RETENTION_DAYS},'academic_fidelity':{'audio':audio_quality_status()},'email_configured':email_configured(),'production_ready':APP_ENV=='production' and not DEV_MODE and email_configured() and PUBLIC_BASE_URL.lower().startswith('https://') and (not REQUIRE_POSTGRES_AUTH or pg_health.get('ok')) and (not REQUIRE_POSTGRES_PRODUCTION or DATABASE_ENGINE=='postgres')})
        if p=='/api/ready':
            try:
                c=conn(); c.execute('SELECT 1').fetchone(); c.close(); db_ok=True
            except Exception: db_ok=False
            pg_health=runtime_health(); pg_ok=bool(pg_health.get('ok')); content_health=postgres_content.health() if pg_ok else {'ok':False}; content_ok=bool(content_health.get('ok')); prod_db_ok=(APP_ENV!='production' or (not REQUIRE_POSTGRES_PRODUCTION or DATABASE_ENGINE=='postgres')); demo_ok=(APP_ENV!='production' or (not SEED_DEMO_DATA and not known_demo_accounts_present())); smtp_ok=(APP_ENV!='production' or not REQUIRE_SMTP_PRODUCTION or email_configured()); https_ok=(APP_ENV!='production' or not REQUIRE_HTTPS_PRODUCTION or PUBLIC_BASE_URL.lower().startswith('https://')); base_ok=db_ok and pg_ok and content_ok; ready_ok=(base_ok and prod_db_ok and demo_ok and smtp_ok and https_ok and not DEV_MODE) if APP_ENV=='production' else base_ok; return self.json({'ok':ready_ok,'version':APP_VERSION,'database':db_ok,'database_engine':DATABASE_ENGINE,'auth_database_engine':AUTH_DATABASE_ENGINE,'postgres_auth_ok':pg_ok,'postgres_auth':pg_health,'master_content_ok':content_ok,'master_content':content_health,'production_database_ok':prod_db_ok,'demo_accounts_ok':demo_ok,'smtp_ok':smtp_ok,'https_ok':https_ok,'postgres_required_in_production':REQUIRE_POSTGRES_PRODUCTION,'backup_dir_writable':os.access(BACKUP_DIR,os.W_OK),'dev_mode':DEV_MODE,'environment':APP_ENV,'public_base_url':PUBLIC_BASE_URL,'email_configured':email_configured()},200 if ready_ok else 503)
        if p=='/api/me':
            u=self.auth();return self.json({'user':u}) if u else self.json({'error':'unauthorized'},401)
        u=self.auth()
        if p.startswith('/api/') and not u:return self.json({'error':'unauthorized'},401)
        if p=='/api/content/status':
            return self.json(postgres_content.health())
        if p=='/api/content/practice-bank':
            profile=(qs.get('profile') or ['schools'])[0].lower()
            try:return self.json(postgres_content.practice_bank(profile))
            except Exception as exc:return self.json({'error':'content_unavailable','detail':str(exc)[:200]},503)
        if p=='/api/content/audio-bank':
            try:return self.json(postgres_content.audio_bank())
            except Exception as exc:return self.json({'error':'content_unavailable','detail':str(exc)[:200]},503)
        if p=='/api/content/curriculum':
            try:return self.json(postgres_content.curriculum())
            except Exception as exc:return self.json({'error':'content_unavailable','detail':str(exc)[:200]},503)
        if p=='/api/content/exam-index':
            profile=(qs.get('profile') or ['schools'])[0].lower()
            try:return self.json(postgres_content.exam_index(profile))
            except Exception as exc:return self.json({'error':'content_unavailable','detail':str(exc)[:200]},503)
        if p.startswith('/api/content/exam-pack/'):
            pack_id=p.rsplit('/',1)[-1]
            try:
                pack=postgres_content.exam_pack(pack_id)
                return self.json(pack) if pack else self.json({'error':'not_found'},404)
            except Exception as exc:return self.json({'error':'content_unavailable','detail':str(exc)[:200]},503)
        if p=='/api/practice-diagnostic':
            if u.get('role')=='student': student_id=u['id']
            else:
                if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
                try: student_id=int((qs.get('student_id') or ['0'])[0])
                except Exception:return self.json({'error':'invalid_student'},400)
                c=conn(); own=c.execute("SELECT id FROM users WHERE id=? AND school_id=? AND role='student'",(student_id,u['school_id'])).fetchone(); c.close()
                if not own:return self.json({'error':'invalid_student'},404)
            c=conn(); rows=c.execute("SELECT skill,success,meta_json FROM learning_events WHERE user_id=? AND event_type IN ('practice_bank_answer','practice_remediation_answer') AND success IS NOT NULL ORDER BY id",(student_id,)).fetchall(); c.close()
            skills={}; patterns={}
            def bump(d,k,ok):
                z=d.setdefault(k,{'attempts':0,'correct':0}); z['attempts']+=1; z['correct']+=1 if ok else 0
            for r in rows:
                ok=bool(r['success']); sk=(r['skill'] or 'general').lower(); bump(skills,sk,ok)
                meta=safe_json(r['meta_json'],{}) or {}; pats=meta.get('diagnostic_patterns') if isinstance(meta.get('diagnostic_patterns'),list) else []
                if not pats:
                    comp=str(meta.get('competency') or '').lower(); target=str(meta.get('target') or '').lower(); cog=str(meta.get('cognitive_skill') or '').lower(); dist=str(meta.get('distractor_type') or '').lower()
                    if target=='gist' or cog=='gist' or comp=='gist': pats.append('gist')
                    if comp=='spelling': pats.append('spelling')
                    if comp=='attitude' or target=='attitude' or cog=='attitude': pats += ['opinion','attitude']
                    if dist=='corrected_information': pats.append('corrected_information')
                    if target=='detail' or cog=='detail' or comp=='detail': pats.append('detail')
                    if target=='inference' or cog=='inference' or comp=='reading inference': pats.append('inference')
                for pat in dict.fromkeys(str(x) for x in pats if x): bump(patterns,pat,ok)
            for z in skills.values(): z['accuracy']=round(z['correct']*100/z['attempts'],1) if z['attempts'] else None
            plist=[]
            for pat,z in patterns.items(): plist.append({'pattern':pat,'n':z['attempts'],'correct':z['correct'],'accuracy':round(z['correct']*100/z['attempts'],1) if z['attempts'] else None})
            plist.sort(key=lambda x:((x['accuracy'] if x['accuracy'] is not None else 101),-x['n'],x['pattern']))
            eligible=[x for x in plist if x['n']>=3]
            primary=None
            if eligible:
                x=eligible[0]; primary={**x,'skill':'listening' if x['pattern'] in ('numbers','times','corrected_information') else None}
            return self.json({'student_id':student_id,'source':'learning_events','min_evidence':3,'total_attempts':len(rows),'skills':skills,'patterns':plist,'primary_issue':primary,'probability_claim':False,'note':'Diagnóstico pedagógico basado en intentos reales del usuario; no es una calificación oficial Cambridge.'})
        if p=='/api/error-dna':
            if u.get('role')=='student': student_id=u['id']
            else:
                if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
                try: student_id=int((qs.get('student_id') or ['0'])[0])
                except Exception:return self.json({'error':'invalid_student'},400)
                c=conn(); own=c.execute("SELECT id FROM users WHERE id=? AND school_id=? AND role='student'",(student_id,u['school_id'])).fetchone(); c.close()
                if not own:return self.json({'error':'invalid_student'},404)
            c=conn()
            evs=[dict(r) for r in c.execute('SELECT * FROM academic_error_events WHERE student_id=? ORDER BY id',(student_id,)).fetchall()]
            rems=[dict(r) for r in c.execute('SELECT * FROM academic_remediation_attempts WHERE student_id=? ORDER BY id DESC',(student_id,)).fetchall()]
            learn=[dict(r) for r in c.execute("SELECT skill,success,meta_json,created_at FROM learning_events WHERE user_id=? AND event_type IN ('practice_bank_answer','practice_remediation_answer') AND success IS NOT NULL ORDER BY id",(student_id,)).fetchall()]
            speak=[dict(r) for r in c.execute('SELECT metrics_json,rubric_json,score_pct,created_at FROM speaking_attempts WHERE student_id=? ORDER BY id DESC LIMIT 20',(student_id,)).fetchall()]
            snap=c.execute('SELECT payload FROM snapshots WHERE user_id=?',(student_id,)).fetchone(); c.close()
            payload=safe_json(snap['payload'],{}) if snap else {}
            writing=(payload.get('writing') or []) if isinstance(payload,dict) else []
            evidence={}
            def norm(x):
                return str(x or '').strip().lower().replace('&','and').replace(' ','_').replace('-','_').replace('/','_')
            def add(key,score,source,code=None,when=None):
                try: score=float(score)
                except Exception:return
                if score<0 or score>100:return
                d=evidence.setdefault(key,{'scores':[],'sources':set(),'codes':set(),'dates':[]})
                d['scores'].append(score); d['sources'].add(source)
                if code:d['codes'].add(str(code))
                if when:d['dates'].append(str(when))
            # Practice-bank evidence: every response contributes to the exact metadata dimensions it tested.
            for r in learn:
                meta=safe_json(r.get('meta_json'),{}) or {}; ok=100.0 if bool(r.get('success')) else 0.0; sk=norm(r.get('skill'))
                pats=meta.get('diagnostic_patterns') if isinstance(meta.get('diagnostic_patterns'),list) else []
                for pat in pats:
                    k=norm(pat)
                    if sk=='listening' and k in ('gist','numbers','times','opinion','corrected_information','spelling','detail'): add('listening:'+k,ok,'practice_bank',when=r.get('created_at'))
                    if sk=='reading' and k in ('inference','detail','cohesion','gist'): add('reading:'+k,ok,'practice_bank',when=r.get('created_at'))
                    if k in ('prepositions','grammar'): add('grammar:'+k,ok,'practice_bank',when=r.get('created_at'))
                gram=norm(meta.get('grammar'))
                if gram and gram not in ('none','n_a','na','general'):
                    add('grammar:'+gram,ok,'practice_bank',when=r.get('created_at'))
                comp=norm(meta.get('competency')); target=norm(meta.get('target')); cog=norm(meta.get('cognitive_skill'))
                if sk=='reading':
                    if comp=='sentence_cohesion' or target=='cohesion' or cog=='cohesion': add('reading:cohesion',ok,'practice_bank',when=r.get('created_at'))
                    if comp=='reading_inference' or target=='inference' or cog=='inference': add('reading:inference',ok,'practice_bank',when=r.get('created_at'))
                    if comp=='detail' or target=='detail' or cog=='detail': add('reading:detail',ok,'practice_bank',when=r.get('created_at'))
                if sk=='listening':
                    if comp=='attitude' or target=='attitude' or cog=='attitude': add('listening:opinion',ok,'practice_bank',when=r.get('created_at'))
                    if comp=='spelling': add('listening:spelling',ok,'practice_bank',when=r.get('created_at'))
            # Academic-error evidence contributes a mastery proxy and is linked to corrective attempts.
            rem_by={}
            for r in rems:
                d=rem_by.setdefault(str(r.get('error_code') or ''),[]); d.append(bool(r.get('correct')))
            for e in evs:
                sk=norm(e.get('skill')); sub=norm(e.get('subcompetence')); code=norm(e.get('error_code')); comp=norm(e.get('competence')); mp=float(e.get('mastery_proxy') or 0)
                keys=[]
                if sk=='writing':
                    if 'organ' in sub or 'organ' in code:keys.append('writing:organisation')
                    elif 'content' in sub or 'content' in code:keys.append('writing:content')
                    else:keys.append('writing:language')
                elif sk=='listening':
                    for x in ('times','numbers','opinion','corrected_information','spelling','gist','detail'):
                        if x in sub or x in code:keys.append('listening:'+x);break
                elif sk=='reading':
                    if 'infer' in sub or 'infer' in code:keys.append('reading:inference')
                    elif 'cohes' in sub or 'cohes' in code:keys.append('reading:cohesion')
                    elif 'detail' in sub or 'detail' in code:keys.append('reading:detail')
                # Grammar is cross-skill: a Writing grammar error also belongs to the Grammar DNA domain.
                if 'grammar' in comp or sk in ('writing','grammar'):
                    if 'present_perfect' in sub or 'present_perfect' in code or ('present' in sub and 'perfect' in sub):keys.append('grammar:present_perfect')
                    elif 'past_simple' in sub or 'past_simple' in code or ('past' in sub and 'simple' in sub):keys.append('grammar:past_simple')
                    elif 'preposition' in sub or 'preposition' in code:keys.append('grammar:prepositions')
                    elif 'article' in sub or 'article' in code:keys.append('grammar:articles')
                recent=rem_by.get(str(e.get('error_code') or ''),[])[:3]; mastered=len(recent)>=3 and all(recent)
                score=max(mp,85.0) if mastered else mp
                for key in dict.fromkeys(keys):add(key,score,'academic_errors',e.get('error_code'),e.get('occurred_at'))
            # Writing rubric evidence from saved productions.
            for w in writing[-20:]:
                if not isinstance(w,dict):continue
                rub=w.get('rubric') if isinstance(w.get('rubric'),dict) else {}
                if rub:
                    if rub.get('content') is not None:add('writing:content',float(rub['content'])*20,'writing_rubric',when=w.get('date'))
                    if rub.get('organisation') is not None:add('writing:organisation',float(rub['organisation'])*20,'writing_rubric',when=w.get('date'))
                    if rub.get('language') is not None:add('writing:language',float(rub['language'])*20,'writing_rubric',when=w.get('date'))
            # Speaking evidence from real stored attempts. Pronunciation remains an automatic practice proxy.
            for a in speak:
                m=safe_json(a.get('metrics_json'),{}) or {}; rb=safe_json(a.get('rubric_json'),{}) or {}; dt=a.get('created_at')
                if m.get('fluency') is not None:add('speaking:fluency',m.get('fluency'),'speaking_ai',when=dt)
                if m.get('pronunciation_proxy') is not None:add('speaking:pronunciation',m.get('pronunciation_proxy'),'speaking_ai_proxy',when=dt)
                elif rb.get('pronunciation') is not None:add('speaking:pronunciation',float(rb.get('pronunciation'))*20,'speaking_ai_proxy',when=dt)
                if m.get('interaction') is not None:add('speaking:interaction',m.get('interaction'),'speaking_ai',when=dt)
                elif rb.get('interactive_communication') is not None:add('speaking:interaction',float(rb.get('interactive_communication'))*20,'speaking_ai',when=dt)
            specs={
              'Grammar':[('past_simple','Past simple'),('present_perfect','Present perfect'),('prepositions','Prepositions'),('articles','Articles')],
              'Listening':[('times','Times'),('numbers','Numbers'),('opinion','Opinions'),('corrected_information','Corrected information'),('spelling','Spelling')],
              'Reading':[('inference','Inference'),('detail','Detail'),('cohesion','Text cohesion')],
              'Writing':[('organisation','Organisation'),('content','Content'),('language','Language')],
              'Speaking':[('fluency','Fluency'),('pronunciation','Pronunciation'),('interaction','Interaction')]
            }
            causes={
              'grammar:past_simple':'el pasado simple todavía no es estable cuando debes elegir o producir la forma verbal correcta.',
              'grammar:present_perfect':'todavía mezclas present perfect y past simple o no automatizas have/has + past participle.',
              'grammar:prepositions':'las combinaciones de preposición todavía no están automatizadas.',
              'grammar:articles':'necesitas decidir con mayor consistencia cuándo usar a/an, the o ningún artículo.',
              'listening:times':'te cuesta conservar la hora final cuando aparecen varias referencias temporales.',
              'listening:numbers':'te cuesta retener y distinguir números cuando compiten con otros datos.',
              'listening:opinion':'te cuesta distinguir la opinión o actitud final del hablante.',
              'listening:corrected_information':'detectas la primera información, pero no reconoces con suficiente consistencia cuando el hablante la corrige posteriormente.',
              'listening:spelling':'reconoces el contenido, pero todavía cometes errores al reconstruir la ortografía exacta.',
              'reading:inference':'te cuesta combinar pistas para deducir información que no aparece de forma literal.',
              'reading:detail':'comprendes el tema general, pero pierdes información específica.',
              'reading:cohesion':'te cuesta reconocer cómo conectores, pronombres y referencias unen las ideas del texto.',
              'writing:organisation':'necesitas ordenar y conectar mejor las ideas para que el texto avance con claridad.',
              'writing:content':'necesitas responder de forma completa y relevante a todos los puntos de la consigna.',
              'writing:language':'la precisión y variedad de gramática y vocabulario todavía necesitan consolidación.',
              'speaking:fluency':'tu producción oral necesita mayor continuidad, con menos pausas largas, bloqueos o reinicios.',
              'speaking:pronunciation':'la claridad e inteligibilidad necesitan práctica adicional; esta señal de pronunciación es un proxy automático.',
              'speaking:interaction':'necesitas responder más activamente al compañero, proponer, reaccionar, negociar y desarrollar la interacción.'
            }
            match={
              'grammar:past_simple':{'field':'grammar','value':'past_simple'},'grammar:present_perfect':{'field':'grammar','value':'present_perfect'},'grammar:prepositions':{'field':'diagnostic_patterns','value':'prepositions'},'grammar:articles':{'field':'grammar','value':'articles'},
              'listening:times':{'field':'diagnostic_patterns','value':'times'},'listening:numbers':{'field':'diagnostic_patterns','value':'numbers'},'listening:opinion':{'field':'diagnostic_patterns','value':'opinion'},'listening:corrected_information':{'field':'diagnostic_patterns','value':'corrected_information'},'listening:spelling':{'field':'diagnostic_patterns','value':'spelling'},
              'reading:inference':{'field':'diagnostic_patterns','value':'inference'},'reading:detail':{'field':'diagnostic_patterns','value':'detail'},'reading:cohesion':{'field':'diagnostic_patterns','value':'cohesion'},
              'writing:organisation':{'field':'target','value':'cohesion'},'writing:content':{'field':'target','value':'purpose'},'writing:language':{'field':'competency','value':'grammar'},
              'speaking:fluency':{'field':'target','value':'pronunciation_awareness'},'speaking:pronunciation':{'field':'diagnostic_patterns','value':'pronunciation'},'speaking:interaction':{'field':'competency','value':'linkers'}
            }
            domains=[]; all_nodes=[]
            for domain,arr in specs.items():
                nodes=[]
                for key,label in arr:
                    ek=domain.lower()+':'+key; d=evidence.get(ek,{'scores':[],'sources':set(),'codes':set(),'dates':[]}); n=len(d['scores'])
                    score=round(sum(d['scores'])/n,1) if n else None
                    # A minimum of three observations is required for a colour claim.
                    if n<3: status='insufficient'; icon='⚪'
                    elif score>=80: status='mastered'; icon='🟢'
                    elif score>=60: status='progress'; icon='🟠'
                    else: status='critical'; icon='🔴'
                    node={'key':ek,'label':label,'score':score,'evidence_count':n,'status':status,'icon':icon,'cause':causes.get(ek,''),'sources':sorted(d['sources']),'error_codes':sorted(d['codes']),'last_seen':max(d['dates']) if d['dates'] else None,'practice_match':match.get(ek)}
                    nodes.append(node); all_nodes.append({'domain':domain,**node})
                domains.append({'domain':domain,'nodes':nodes})
            eligible=[x for x in all_nodes if x['evidence_count']>=3 and x['score'] is not None]
            eligible.sort(key=lambda x:(x['score'],-x['evidence_count'],x['domain'],x['label']))
            primary=eligible[0] if eligible else None
            dna_score=round(sum(x['score'] for x in eligible)/len(eligible),1) if eligible else None
            coverage=round(len(eligible)*100/len(all_nodes),1) if all_nodes else 0
            return self.json({'student_id':student_id,'name':'Error DNA™','version':'46.24','dna_score':dna_score,'diagnostic_coverage_pct':coverage,'minimum_evidence':3,'domains':domains,'primary_issue':primary,'legend':{'critical':'🔴 <60%','progress':'🟠 60–79.9%','mastered':'🟢 ≥80%','insufficient':'⚪ menos de 3 evidencias'},'automatic_pronunciation_note':'Pronunciation is an automatic practice proxy and does not replace human examiner judgement.','generated_at':now()})
        if p=='/api/my-preparation':
            if u.get('role')=='student': student_id=u['id']
            else:
                if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
                try: student_id=int((qs.get('student_id') or ['0'])[0])
                except Exception:return self.json({'error':'invalid_student'},400)
            summary=student_preparation_summary(student_id,u['school_id'])
            return self.json(summary) if summary else self.json({'error':'invalid_student'},404)
        if p=='/api/observability':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            c=conn(); reqs=c.execute("SELECT COUNT(*) n FROM audit_log WHERE created_at>=datetime('now','-24 hours')").fetchone()['n']; errs=c.execute("SELECT COUNT(*) n FROM audit_log WHERE action LIKE '%error%' AND created_at>=datetime('now','-24 hours')").fetchone()['n']; c.close()
            return self.json({'window':'24h','metrics':{'requests':reqs,'errors':errs,'p50_ms':0,'p95_ms':0},'note':'Application-level observability counters. HTTP latency belongs to deployment monitoring.'})
        if p=='/api/analytics':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            c=conn(); rows=c.execute('SELECT le.*,usr.school_id FROM learning_events le JOIN users usr ON usr.id=le.user_id WHERE usr.school_id=? ORDER BY le.id',(u['school_id'],)).fetchall(); c.close()
            by_skill={}
            for r in rows:
                sk=(r['skill'] or 'general').lower(); d=by_skill.setdefault(sk,{'events':0,'answers':0,'correct':0,'minutes':0.0}); d['events']+=1; d['minutes']+=float(r['minutes'] or 0)
                if r['success'] is not None: d['answers']+=1; d['correct']+=1 if r['success'] else 0
            for d in by_skill.values(): d['accuracy']=round(d.pop('correct')*100/d['answers'],1) if d['answers'] else 0.0; d['minutes']=round(d['minutes'],1)
            return self.json({'active_students':len({r['user_id'] for r in rows}),'events':len(rows),'by_skill':by_skill})
        if p=='/api/mastery/me':
            if u.get('role')!='student':return self.json({'error':'forbidden'},403)
            return self.json(mastery_from_snapshot(u['id'],u['school_id']))
        if p=='/api/mastery/school':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            c=conn(); sts=c.execute("SELECT id,name FROM users WHERE school_id=? AND role='student' AND disabled=0 ORDER BY name",(u['school_id'],)).fetchall(); c.close(); items=[]
            for st in sts:
                m=mastery_from_snapshot(st['id'],u['school_id']); items.append({'id':st['id'],'name':st['name'],'answers':m['attempts'],'accuracy':m['accuracy'],'risk':m['risk'],'weak_focus':m['weak_focus']})
            return self.json({'students':items,'evaluated':len(items),'at_risk':sum(1 for x in items if x['risk'] in ('high','medium'))})
        if p=='/api/recovery/checks':
            if not self.require_roles(u,'admin'):return self.json({'error':'forbidden'},403)
            c=conn(); rows=c.execute('SELECT id,backup_name,ok,integrity_result,checked_at,checked_by FROM recovery_checks ORDER BY id DESC LIMIT 50').fetchall(); c.close(); return self.json({'checks':[dict(x) for x in rows]})
        if p=='/api/production-gate':
            if not self.require_roles(u,'admin','school'):return self.json({'error':'forbidden'},403)
            return self.json(production_gate_status())
        if p=='/api/courses':
            c=conn(); rows=c.execute('SELECT c.* FROM courses c JOIN enrollments e ON e.course_id=c.id WHERE e.user_id=?',(u['id'],)).fetchall() if u['role']=='student' else c.execute('SELECT * FROM courses WHERE school_id=?',(u['school_id'],)).fetchall(); c.close(); return self.json({'courses':[dict(x) for x in rows]})
        if p=='/api/school-students':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            c=conn(); rows=c.execute('SELECT id,name,email,disabled FROM users WHERE school_id=? AND role="student" ORDER BY name',(u['school_id'],)).fetchall(); c.close(); return self.json({'students':[dict(x) for x in rows]})
        if p=='/api/classes':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            c=conn(); rows=c.execute('SELECT c.*,t.name teacher_name,COUNT(e.user_id) student_count FROM courses c LEFT JOIN users t ON t.id=c.teacher_id LEFT JOIN enrollments e ON e.course_id=c.id WHERE c.school_id=? GROUP BY c.id ORDER BY c.name',(u['school_id'],)).fetchall(); c.close(); return self.json({'classes':[dict(x) for x in rows]})
        if p=='/api/class-students':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            try: cid=int((qs.get('course_id') or ['0'])[0])
            except Exception:return self.json({'error':'invalid_course'},400)
            c=conn(); own=c.execute('SELECT id FROM courses WHERE id=? AND school_id=?',(cid,u['school_id'])).fetchone()
            if not own:c.close();return self.json({'error':'invalid_course'},400)
            rows=c.execute('SELECT u.id,u.name,u.email,u.disabled FROM users u JOIN enrollments e ON e.user_id=u.id WHERE e.course_id=? AND u.role="student" ORDER BY u.name',(cid,)).fetchall(); c.close(); return self.json({'students':[dict(x) for x in rows]})
        if p=='/api/class-intelligence':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            try: cid=int((qs.get('course_id') or ['0'])[0])
            except Exception:return self.json({'error':'invalid_course'},400)
            c=conn(); own=c.execute('SELECT id,name FROM courses WHERE id=? AND school_id=?',(cid,u['school_id'])).fetchone()
            if not own:c.close();return self.json({'error':'invalid_course'},400)
            ids={r['user_id'] for r in c.execute('SELECT user_id FROM enrollments WHERE course_id=?',(cid,)).fetchall()}; c.close()
            reports=[r for r in self.build_report(u) if r.get('id') in ids]
            skills=['reading','listening','writing','speaking']; avgs={}
            for sk in skills:
                vals=[float(r.get(sk,0) or 0) for r in reports if (r.get(sk,0) or 0)>0]
                avgs[sk]=round(sum(vals)/len(vals)) if vals else 0
            common=min(avgs,key=lambda k: avgs[k] if avgs[k]>0 else 999) if any(avgs.values()) else 'reading'
            risk=[r for r in reports if (r.get('readiness',0)<65 or r.get('accuracy',0)<60) and r.get('attempts',0)>0]
            return self.json({'course':dict(own),'students':reports,'averages':avgs,'common_priority':common,'risk_count':len(risk),'risk_students':risk})
        if p=='/api/school-intelligence':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            c=conn(); courses=c.execute('SELECT c.id,c.name,c.teacher_id,t.name teacher_name,COUNT(e.user_id) enrolled FROM courses c LEFT JOIN users t ON t.id=c.teacher_id LEFT JOIN enrollments e ON e.course_id=c.id WHERE c.school_id=? GROUP BY c.id ORDER BY c.name',(u['school_id'],)).fetchall(); c.close()
            all_reports=self.build_report(u); by_id={r['id']:r for r in all_reports}; out=[]; skills=['reading','listening','writing','speaking']
            c=conn()
            for course in courses:
                ids={r['user_id'] for r in c.execute('SELECT user_id FROM enrollments WHERE course_id=?',(course['id'],)).fetchall()}
                reps=[by_id[i] for i in ids if i in by_id]
                avgs={}
                for sk in skills:
                    vals=[float(r.get(sk,0) or 0) for r in reps if float(r.get(sk,0) or 0)>0]
                    avgs[sk]=round(sum(vals)/len(vals)) if vals else 0
                readiness_vals=[float(r.get('readiness',0) or 0) for r in reps if float(r.get('readiness',0) or 0)>0]
                accuracy_vals=[float(r.get('accuracy',0) or 0) for r in reps if float(r.get('attempts',0) or 0)>0]
                common=min(avgs,key=lambda k: avgs[k] if avgs[k]>0 else 999) if any(avgs.values()) else 'reading'
                risk=sum(1 for r in reps if (r.get('readiness',0)<65 or r.get('accuracy',0)<60) and r.get('attempts',0)>0)
                evidence=sum(int(r.get('attempts',0) or 0) for r in reps)
                out.append({'id':course['id'],'name':course['name'],'teacher_name':course['teacher_name'],'enrolled':course['enrolled'],'students_with_data':len(reps),'averages':avgs,'readiness':round(sum(readiness_vals)/len(readiness_vals)) if readiness_vals else 0,'accuracy':round(sum(accuracy_vals)/len(accuracy_vals)) if accuracy_vals else 0,'common_priority':common,'risk_count':risk,'evidence':evidence})
            groups=c.execute('SELECT g.*,c.name course_name,COUNT(m.user_id) member_count FROM support_groups g LEFT JOIN courses c ON c.id=g.course_id LEFT JOIN support_group_members m ON m.group_id=g.id WHERE g.school_id=? GROUP BY g.id ORDER BY g.id DESC',(u['school_id'],)).fetchall(); c.close()
            return self.json({'classes':out,'support_groups':[dict(x) for x in groups]})
        if p=='/api/support-groups':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            c=conn(); rows=c.execute('SELECT g.*,c.name course_name,COUNT(m.user_id) member_count FROM support_groups g LEFT JOIN courses c ON c.id=g.course_id LEFT JOIN support_group_members m ON m.group_id=g.id WHERE g.school_id=? GROUP BY g.id ORDER BY g.id DESC',(u['school_id'],)).fetchall(); c.close(); return self.json({'groups':[dict(x) for x in rows]})
        if p=='/api/weekly-class-plan':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            try: cid=int((qs.get('course_id') or ['0'])[0])
            except Exception:return self.json({'error':'invalid_course'},400)
            c=conn(); own=c.execute('SELECT id,name FROM courses WHERE id=? AND school_id=?',(cid,u['school_id'])).fetchone()
            if not own:c.close();return self.json({'error':'invalid_course'},400)
            ids={r['user_id'] for r in c.execute('SELECT user_id FROM enrollments WHERE course_id=?',(cid,)).fetchall()}; c.close()
            reports=[r for r in self.build_report(u) if r.get('id') in ids]; skills=['reading','listening','writing','speaking']; avgs={}
            for sk in skills:
                vals=[float(r.get(sk,0) or 0) for r in reports if float(r.get(sk,0) or 0)>0]; avgs[sk]=round(sum(vals)/len(vals)) if vals else 0
            ranked=sorted(skills,key=lambda k: avgs[k] if avgs[k]>0 else 999); priority=ranked[0] if ranked else 'reading'; second=ranked[1] if len(ranked)>1 else 'listening'; strongest=max(skills,key=lambda k:avgs[k]) if any(avgs.values()) else 'speaking'
            days=[{'day':'Lunes','skill':priority,'minutes':12,'purpose':'Refuerzo principal'},{'day':'Miércoles','skill':second,'minutes':10,'purpose':'Segunda prioridad'},{'day':'Jueves','skill':strongest,'minutes':8,'purpose':'Mantener fortaleza'},{'day':'Viernes','skill':priority,'minutes':10,'purpose':'Mini comprobación'}]
            return self.json({'course':dict(own),'averages':avgs,'priority':priority,'secondary':second,'strength':strongest,'plan':days,'student_count':len(reports)})
        if p=='/api/intervention-plan':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            try: cid=int((qs.get('course_id') or ['0'])[0])
            except Exception:return self.json({'error':'invalid_course'},400)
            c=conn(); own=c.execute('SELECT id,name FROM courses WHERE id=? AND school_id=?',(cid,u['school_id'])).fetchone()
            if not own:c.close();return self.json({'error':'invalid_course'},400)
            ids={r['user_id'] for r in c.execute('SELECT user_id FROM enrollments WHERE course_id=?',(cid,)).fetchall()}; c.close()
            reports=[r for r in self.build_report(u) if r.get('id') in ids]
            skills=['reading','listening','writing','speaking']; labels={'reading':'Reading','listening':'Listening','writing':'Writing','speaking':'Speaking'}
            buckets={k:[] for k in skills}; advance=[]; watch=[]
            for r in reports:
                vals={k:float(r.get(k,0) or 0) for k in skills}
                valid={k:v for k,v in vals.items() if v>0}
                if valid:
                    wk=min(valid,key=valid.get); wv=valid[wk]
                    if wv<72:buckets[wk].append({'id':r.get('id'),'name':r.get('name'),'score':round(wv),'readiness':r.get('readiness',0),'accuracy':r.get('accuracy',0)})
                available=[v for v in vals.values() if v>0]
                pathway_avg=(sum(available)/len(available)) if available else 0
                if pathway_avg>=82 and float(r.get('accuracy',0) or 0)>=82 and int(r.get('attempts',0) or 0)>=12:
                    advance.append({'id':r.get('id'),'name':r.get('name'),'readiness':r.get('readiness',0),'accuracy':r.get('accuracy',0),'pathway_average':round(pathway_avg)})
                elif int(r.get('attempts',0) or 0)>0 and (float(r.get('readiness',0) or 0)<65 or float(r.get('accuracy',0) or 0)<60):
                    watch.append({'id':r.get('id'),'name':r.get('name'),'readiness':r.get('readiness',0),'accuracy':r.get('accuracy',0)})
            interventions=[]
            for sk,students in buckets.items():
                if not students:continue
                avg=round(sum(x['score'] for x in students)/len(students))
                mins=12 if avg<60 else 10
                interventions.append({'skill':sk,'label':labels[sk],'student_ids':[x['id'] for x in students],'students':students,'count':len(students),'average':avg,'minutes':mins,'priority':'alta' if avg<60 else 'media','activity':f'Refuerzo {labels[sk]} · evidencia + práctica guiada','success_criteria':'Subir 8 puntos o lograr 75%+ en dos sesiones consecutivas'})
            interventions.sort(key=lambda x:(0 if x['priority']=='alta' else 1,x['average']))
            return self.json({'course':dict(own),'student_count':len(reports),'interventions':interventions,'advance_candidates':advance,'follow_up':watch,'generated_at':now()})
        if p=='/api/strategy-forecast':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            reports=self.build_report(u); skills=['reading','listening','writing','speaking']
            def avg(vals): return round(sum(vals)/len(vals),1) if vals else 0
            current={'readiness':avg([float(r.get('readiness',0) or 0) for r in reports if float(r.get('readiness',0) or 0)>0]),'accuracy':avg([float(r.get('accuracy',0) or 0) for r in reports if int(r.get('attempts',0) or 0)>0])}
            for sk in skills: current[sk]=avg([float(r.get(sk,0) or 0) for r in reports if float(r.get(sk,0) or 0)>0])
            current['risk_count']=sum(1 for r in reports if int(r.get('attempts',0) or 0)>0 and (float(r.get('readiness',0) or 0)<65 or float(r.get('accuracy',0) or 0)<60))
            c=conn(); rows=c.execute("SELECT payload_json,period_label,created_at FROM academic_review_snapshots WHERE school_id=? AND window_type='monthly' ORDER BY id DESC LIMIT 8",(u['school_id'],)).fetchall(); hist=[]
            for row in reversed(rows):
                pay=safe_json(row['payload_json'],{}) or {}; sch=pay.get('school',{}); hist.append({'label':row['period_label'],'readiness':float(sch.get('readiness',0) or 0),'accuracy':float(sch.get('accuracy',0) or 0),'reading':float(sch.get('reading',0) or 0),'listening':float(sch.get('listening',0) or 0),'writing':float(sch.get('writing',0) or 0),'speaking':float(sch.get('speaking',0) or 0)})
            closed=c.execute("SELECT delta FROM intervention_runs WHERE school_id=? AND status='closed' AND delta>0 ORDER BY id DESC LIMIT 30",(u['school_id'],)).fetchall(); gains=[float(x['delta'] or 0) for x in closed]
            targets=[dict(x) for x in c.execute('SELECT t.*,u.name owner_name FROM strategic_targets t LEFT JOIN users u ON u.id=t.owner_user_id WHERE t.school_id=? ORDER BY t.year DESC,t.metric',(u['school_id'],)).fetchall()]; c.close()
            def trend(metric):
                vals=[x.get(metric,0) for x in hist if x.get(metric,0)>0]
                if len(vals)<2:return 0.0
                # robust-ish recent monthly slope: average adjacent delta, capped to avoid wild forecasts
                ds=[vals[i]-vals[i-1] for i in range(1,len(vals))]
                return round(max(-6,min(6,sum(ds)/len(ds))),2)
            base_gain=round(sum(gains)/len(gains),1) if gains else 0
            # Only a conservative fraction of historic intervention gain is added to a school-wide scenario.
            action_bonus=max(0,min(3.0,base_gain*0.25))
            confidence='low' if len(hist)<2 else ('medium' if len(hist)<4 else 'high')
            horizons={30:1,60:2,90:3}; forecasts={}
            for days,months in horizons.items():
                f={}
                for metric in ['readiness','accuracy']+skills:
                    cur=float(current.get(metric,0) or 0); sl=trend(metric)
                    no=max(0,min(100,cur+sl*months)); act=max(0,min(100,no+action_bonus*months))
                    f[metric]={'current':round(cur,1),'no_action':round(no,1),'with_action':round(act,1),'monthly_trend':sl}
                forecasts[str(days)]=f
            risk=int(current['risk_count']); groups=(risk+5)//6 if risk else 0; sessions_per_week=2 if risk else 0; teacher_hours=round(groups*sessions_per_week*0.5,1)
            capacity={'students_at_risk':risk,'suggested_groups':groups,'students_per_group':6,'sessions_per_group_week':sessions_per_week,'teacher_hours_week':teacher_hours,'assumption':'30 min por grupo, 2 sesiones/semana; ajustar según contexto del colegio.'}
            priorities=sorted(skills,key=lambda k: current.get(k,0) if current.get(k,0)>0 else 999)
            return self.json({'current':current,'history':hist,'forecast':forecasts,'confidence':confidence,'historic_intervention_gain':base_gain,'scenario_action_bonus_monthly':round(action_bonus,1),'capacity':capacity,'strategic_targets':targets,'priority_skill':priorities[0] if priorities else 'reading','method_note':'Escenario orientativo basado en tendencia mensual reciente e impacto histórico conservador; no garantiza resultados futuros.','generated_at':now()})
        if p=='/api/decision-simulator':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            reports=self.build_report(u); skills=['reading','listening','writing','speaking']
            def avg(vals): return round(sum(vals)/len(vals),1) if vals else 0
            current={'readiness':avg([float(r.get('readiness',0) or 0) for r in reports if float(r.get('readiness',0) or 0)>0]),'accuracy':avg([float(r.get('accuracy',0) or 0) for r in reports if int(r.get('attempts',0) or 0)>0])}
            for sk in skills: current[sk]=avg([float(r.get(sk,0) or 0) for r in reports if float(r.get(sk,0) or 0)>0])
            current['risk_count']=sum(1 for r in reports if int(r.get('attempts',0) or 0)>0 and (float(r.get('readiness',0) or 0)<65 or float(r.get('accuracy',0) or 0)<60))
            current['students_with_data']=sum(1 for r in reports if int(r.get('attempts',0) or 0)>0)
            priority=min(skills,key=lambda k: current.get(k,0) if current.get(k,0)>0 else 999) if reports else 'reading'
            c=conn(); closed=c.execute("SELECT delta FROM intervention_runs WHERE school_id=? AND status='closed' AND delta>0 ORDER BY id DESC LIMIT 40",(u['school_id'],)).fetchall(); gains=[float(x['delta'] or 0) for x in closed]
            hist_count=len(gains); historic=round(sum(gains)/hist_count,1) if gains else 0
            c.close()
            presets=[
                {'id':'focused','name':'Refuerzo focalizado','extra_teacher_hours':2,'weeks':8,'target_skill':priority,'coverage':'risk_only','intensity':'standard'},
                {'id':'intensive','name':'Intervención intensiva','extra_teacher_hours':4,'weeks':8,'target_skill':priority,'coverage':'risk_only','intensity':'intensive'},
                {'id':'broad','name':'Refuerzo amplio','extra_teacher_hours':4,'weeks':8,'target_skill':priority,'coverage':'all','intensity':'standard'},
                {'id':'short','name':'Sprint 4 semanas','extra_teacher_hours':3,'weeks':4,'target_skill':priority,'coverage':'priority','intensity':'intensive'}]
            return self.json({'current':current,'priority_skill':priority,'historic_intervention_gain':historic,'historic_intervention_count':hist_count,'presets':presets,'model_note':'Simulador orientativo: compara esfuerzo y posible impacto. Usa impacto historico cuando existe; con poca evidencia aplica supuestos conservadores y muestra menor confianza. No garantiza resultados.','generated_at':now()})
        if p=='/api/budget-optimizer':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            reports=self.build_report(u); skills=['reading','listening','writing','speaking']
            def avg(vals): return round(sum(vals)/len(vals),1) if vals else 0
            current={'readiness':avg([float(r.get('readiness',0) or 0) for r in reports if float(r.get('readiness',0) or 0)>0]),'accuracy':avg([float(r.get('accuracy',0) or 0) for r in reports if int(r.get('attempts',0) or 0)>0])}
            for sk in skills: current[sk]=avg([float(r.get(sk,0) or 0) for r in reports if float(r.get(sk,0) or 0)>0])
            current['risk_count']=sum(1 for r in reports if int(r.get('attempts',0) or 0)>0 and (float(r.get('readiness',0) or 0)<65 or float(r.get('accuracy',0) or 0)<60))
            priority=min(skills,key=lambda k: current.get(k,0) if current.get(k,0)>0 else 999) if reports else 'reading'
            return self.json({'current':current,'priority_skill':priority,'defaults':{'budget':1200,'cost_per_hour':30,'max_hours_week':6,'weeks':8,'strategy':'balanced'},'strategies':['balanced','risk_first','priority_skill','max_coverage'],'method_note':'Optimizador orientativo: usa el simulador V34 para comparar alternativas factibles dentro de presupuesto y capacidad. No garantiza resultados.','generated_at':now()})
        if p=='/api/portfolio-optimizer':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            reports=self.build_report(u); skills=['reading','listening','writing','speaking']
            def avg(vals): return round(sum(vals)/len(vals),1) if vals else 0
            current={sk:avg([float(r.get(sk,0) or 0) for r in reports if float(r.get(sk,0) or 0)>0]) for sk in skills}
            current['readiness']=avg([float(r.get('readiness',0) or 0) for r in reports if float(r.get('readiness',0) or 0)>0])
            current['risk_count']=sum(1 for r in reports if int(r.get('attempts',0) or 0)>0 and (float(r.get('readiness',0) or 0)<65 or float(r.get('accuracy',0) or 0)<60))
            current['students_with_data']=sum(1 for r in reports if int(r.get('attempts',0) or 0)>0)
            priority=min(skills,key=lambda k:current[k] if current[k]>0 else 999) if reports else 'reading'
            return self.json({'current':current,'priority_skill':priority,'defaults':{'budget':1800,'cost_per_hour':30,'max_hours_week':8,'weeks':8,'max_interventions':3,'max_student_overlap':2,'strategy':'balanced'},'strategies':['balanced','risk_first','coverage','weak_skills'],'method_note':'Optimizador de portafolio orientativo: distribuye presupuesto y horas entre varias intervenciones simultaneas, penaliza solapamiento innecesario y no garantiza resultados.','generated_at':now()})
        if p=='/api/schedule-planner':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            c=conn(); teachers=[dict(x) for x in c.execute("SELECT id,name,email FROM users WHERE school_id=? AND role='teacher' AND disabled=0 ORDER BY name",(u['school_id'],)).fetchall()]
            courses=[dict(x) for x in c.execute("SELECT c.id,c.name,c.teacher_id,u.name teacher_name FROM courses c LEFT JOIN users u ON u.id=c.teacher_id WHERE c.school_id=? ORDER BY c.name",(u['school_id'],)).fetchall()]
            groups=[dict(x) for x in c.execute("SELECT g.id,g.name,g.skill,g.course_id,g.status,c.name course_name FROM support_groups g LEFT JOIN courses c ON c.id=g.course_id WHERE g.school_id=? AND g.status='active' ORDER BY g.id DESC",(u['school_id'],)).fetchall()]
            availability=[dict(x) for x in c.execute("SELECT * FROM teacher_availability WHERE school_id=? ORDER BY teacher_id,weekday,start_min",(u['school_id'],)).fetchall()]
            sessions=[dict(x) for x in c.execute("SELECT s.*,u.name teacher_name,c.name course_name,g.name group_name FROM schedule_sessions s LEFT JOIN users u ON u.id=s.teacher_id LEFT JOIN courses c ON c.id=s.course_id LEFT JOIN support_groups g ON g.id=s.support_group_id WHERE s.school_id=? AND s.status<>'cancelled' ORDER BY weekday,start_min",(u['school_id'],)).fetchall()]
            c.close();return self.json({'teachers':teachers,'courses':courses,'groups':groups,'availability':availability,'sessions':sessions,'weekdays':['Lunes','Martes','Miércoles','Jueves','Viernes'],'generated_at':now()})
        if p=='/api/ops/status':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            c=conn(); sessions=c.execute('SELECT COUNT(*) n FROM sessions').fetchone()['n']; audits=c.execute('SELECT COUNT(*) n FROM audit_log').fetchone()['n']; tokens=c.execute('SELECT COUNT(*) n FROM account_tokens WHERE used_at IS NULL').fetchone()['n']; c.close()
            backups=sorted(BACKUP_DIR.glob('*.dump'),key=lambda x:x.stat().st_mtime,reverse=True); latest=backups[0] if backups else None; age_hours=round((time.time()-latest.stat().st_mtime)/3600,1) if latest else None
            blockers=[]; warnings=[]
            if APP_ENV=='production' and DEV_MODE:blockers.append('PETQUEST_DEV_MODE debe ser 0 en producción.')
            if APP_ENV=='production' and not PUBLIC_BASE_URL.lower().startswith('https://'):blockers.append('La URL pública de producción debe usar HTTPS.')
            if APP_ENV=='production' and not email_configured():blockers.append('SMTP debe estar configurado para recuperación/verificación de cuentas.')
            if age_hours is None or age_hours>48:warnings.append('No existe backup reciente de menos de 48 horas.')
            if "'unsafe-inline'" in "script-src 'self' 'unsafe-inline'":warnings.append('La CSP todavía permite script inline por compatibilidad; endurecer en despliegue final.')
            return self.json({'version':APP_VERSION,'environment':APP_ENV,'dev_mode':DEV_MODE,'public_base_url':PUBLIC_BASE_URL,'email_configured':email_configured(),'database_bytes':(lambda cc: (lambda rr: (cc.close(),int(rr['bytes']))[1])(cc.execute("SELECT pg_database_size(current_database()) bytes").fetchone()))(conn()),'active_sessions':sessions,'audit_events':audits,'unused_account_tokens':tokens,'latest_backup':latest.name if latest else None,'latest_backup_age_hours':age_hours,'blockers':blockers,'warnings':warnings,'operational_ready':not blockers})
        if p=='/api/calibration/scale-equivalence':
            if not self.require_roles(u,'teacher','school','academic_reviewer','admin'):return self.json({'error':'forbidden'},403)
            report=build_scale_equivalence_report(u['school_id']); report['generated_at']=now(); return self.json(report)
        if p=='/api/readiness/scale-equivalent':
            report=build_scale_equivalence_report(u['school_id'])
            if not report.get('scale_equivalence_enabled'):return self.json({'scale_equivalence_enabled':False,'status':report.get('status'),'note':report.get('note'),'gates':report.get('gates')})
            try: readiness=float((qs.get('readiness') or [''])[0])
            except Exception:return self.json({'error':'invalid_readiness'},400)
            if readiness<0 or readiness>100:return self.json({'error':'invalid_readiness'},400)
            m=report['model']; est=max(102,min(170,m['intercept']+m['slope']*readiness)); return self.json({'scale_equivalence_enabled':True,'readiness':readiness,'estimated_cambridge_scale':round(est,1),'estimated_band':_cambridge_band(est),'holdout_metrics':report['holdout_metrics'],'model_status':'externally_validated','generated_at':now()})
        if p=='/api/commercial-readiness':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            c=conn(); school_id=u['school_id']; lic=c.execute("SELECT * FROM school_licenses WHERE school_id=? AND status='active' ORDER BY id DESC LIMIT 1",(school_id,)).fetchone(); counts={}
            for role in ('student','teacher'):counts[role]=c.execute('SELECT COUNT(*) n FROM users WHERE school_id=? AND role=? AND disabled=0',(school_id,role)).fetchone()['n']
            counts['courses']=c.execute('SELECT COUNT(*) n FROM courses WHERE school_id=?',(school_id,)).fetchone()['n']; counts['consents']=c.execute("SELECT COUNT(DISTINCT student_id) n FROM guardian_consents gc JOIN users u2 ON u2.id=gc.student_id WHERE u2.school_id=? AND gc.revoked_at IS NULL",(school_id,)).fetchone()['n']
            items=[dict(x) for x in c.execute('SELECT * FROM onboarding_items WHERE school_id=? ORDER BY item_key',(school_id,)).fetchall()]; c.close()
            license_data=dict(lic) if lic else None; seat_ok=bool(lic and counts['student']<=lic['student_seats'] and counts['teacher']<=lic['teacher_seats'])
            return self.json({'license':license_data,'counts':counts,'seat_compliance':seat_ok,'onboarding':items,'onboarding_complete':bool(items) and all(x['status']=='done' for x in items),'available_plans':LICENSE_PLANS,'generated_at':now()})
        if p=='/api/academic-calibration':
            if not self.require_roles(u,'teacher','school','admin','academic_reviewer'):return self.json({'error':'forbidden'},403)
            report=build_calibration_report(u['school_id']); report['generated_at']=now(); return self.json(report)
        if p=='/api/readiness/probability':
            report=build_calibration_report(u['school_id'])
            if not report.get('probability_enabled'):
                return self.json({'probability_enabled':False,'status':report['status'],'reason':report['threshold_note'],'gates':report['gates'],'generated_at':now()})
            try: readiness=float((qs.get('readiness') or [''])[0])
            except Exception:return self.json({'error':'invalid_readiness'},400)
            if readiness<0 or readiness>100:return self.json({'error':'invalid_readiness'},400)
            m=report['model']; x=(readiness-70.0)/15.0; prob=round(_sigmoid(m['intercept']+m['slope']*x)*100,1)
            return self.json({'probability_enabled':True,'readiness':readiness,'estimated_pass_probability':prob,'model_status':'externally_validated','holdout_metrics':report['holdout_metrics'],'generated_at':now()})
        if p=='/api/academic-errors':
            if u.get('role')=='student': student_id=u['id']
            else:
                if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
                try: student_id=int((qs.get('student_id') or ['0'])[0])
                except Exception:return self.json({'error':'invalid_student'},400)
            c=conn(); student=c.execute('SELECT id FROM users WHERE id=? AND school_id=?',(student_id,u['school_id'])).fetchone()
            if not student:c.close();return self.json({'error':'invalid_student'},400)
            rows=[dict(r) for r in c.execute('SELECT * FROM academic_error_events WHERE student_id=? ORDER BY id DESC LIMIT 300',(student_id,)).fetchall()]; c.close()
            by={}
            for r in rows:
                k=r.get('error_code') or r.get('subcompetence') or 'other'; d=by.setdefault(k,{'count':0,'last_seen':None,'skill':r.get('skill'),'subcompetence':r.get('subcompetence'),'mastery_proxy':100})
                d['count']+=1; d['last_seen']=d['last_seen'] or r.get('occurred_at'); d['mastery_proxy']=min(d['mastery_proxy'],float(r.get('mastery_proxy') or 0))
            return self.json({'student_id':student_id,'events':rows,'patterns':by,'generated_at':now()})
        if p=='/api/mock-quality':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            pack=(qs.get('pack_id') or [''])[0].strip(); skill=(qs.get('skill') or ['reading'])[0].strip().lower()
            c=conn(); params=[u['school_id'],skill]; where='WHERE us.school_id=? AND ma.skill=?'
            if pack: where+=' AND ma.pack_id=?'; params.append(pack)
            sql='SELECT ma.* FROM mock_attempts ma JOIN users us ON us.id=ma.student_id '+where+' ORDER BY ma.id'
            attempts=[dict(r) for r in c.execute(sql,tuple(params)).fetchall()]
            ids=[a['id'] for a in attempts]; responses=[]
            if ids:
                ph=','.join('?'*len(ids)); responses=[dict(r) for r in c.execute('SELECT * FROM mock_item_responses WHERE attempt_id IN ('+ph+')',tuple(ids)).fetchall()]
            c.close(); by_item={}
            for r in responses:
                d=by_item.setdefault(r['item_id'],{'item_id':r['item_id'],'part':r['part'],'n':0,'correct':0,'options':{}}); d['n']+=1; d['correct']+=1 if r['is_correct'] else 0
                key=str(r['answer_option']) if r['answer_option'] is not None else (r['answer_text'] or '').strip().lower(); d['options'][key]=d['options'].get(key,0)+1
            totals={a['id']:float(a['pct']) for a in attempts}; ordered=sorted(totals,key=lambda x:totals[x]); k=max(1,int(round(len(ordered)*0.27))) if ordered else 0; low=set(ordered[:k]); high=set(ordered[-k:]) if k else set()
            for item in by_item.values():
                n=item['n']; item['facility']=round(item['correct']/n,3) if n else None; hi=[r for r in responses if r['item_id']==item['item_id'] and r['attempt_id'] in high]; lo=[r for r in responses if r['item_id']==item['item_id'] and r['attempt_id'] in low]; hp=sum(x['is_correct'] for x in hi)/len(hi) if hi else None; lp=sum(x['is_correct'] for x in lo)/len(lo) if lo else None; item['discrimination']=round(hp-lp,3) if hp is not None and lp is not None and len(attempts)>=20 else None; item['evidence']='adequate' if n>=30 else ('provisional' if n>=10 else 'insufficient'); flags=[]
                if n>=10 and item['facility'] is not None:
                    if item['facility']>0.9: flags.append('too_easy')
                    if item['facility']<0.3: flags.append('too_hard')
                if item['discrimination'] is not None and item['discrimination']<0.2: flags.append('low_discrimination')
                item['flags']=flags
            forms=[]
            for pid in sorted(set(a['pack_id'] for a in attempts)):
                vals=[float(a['pct']) for a in attempts if a['pack_id']==pid]; mean=round(sum(vals)/len(vals),1) if vals else 0; sd=round((sum((x-mean)**2 for x in vals)/len(vals))**0.5,1) if vals else 0; forms.append({'pack_id':pid,'n':len(vals),'mean_pct':mean,'sd_pct':sd,'evidence':'provisional' if len(vals)>=20 else 'insufficient'})
            comparable=len(forms)>=2 and all(x['n']>=20 for x in forms); spread=round(max((x['mean_pct'] for x in forms),default=0)-min((x['mean_pct'] for x in forms),default=0),1) if forms else None
            return self.json({'pack_id':pack or None,'skill':skill,'attempts':len(attempts),'items':sorted(by_item.values(),key=lambda x:(x['part'],x['item_id'])),'forms':forms,'equivalence':{'status':'provisional' if comparable else 'insufficient','mean_spread_points':spread,'within_5_points':bool(comparable and spread<=5),'note':'Comparación descriptiva; requiere muestra representativa y revisión psicométrica externa.'},'generated_at':now()})
        if p=='/api/academic-remediation':
            if u.get('role')=='student': student_id=u['id']
            else:
                if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
                try: student_id=int((qs.get('student_id') or ['0'])[0])
                except Exception:return self.json({'error':'invalid_student'},400)
            c=conn(); st=c.execute('SELECT id FROM users WHERE id=? AND school_id=?',(student_id,u['school_id'])).fetchone()
            if not st:c.close();return self.json({'error':'invalid_student'},400)
            rows=[dict(r) for r in c.execute('SELECT * FROM academic_remediation_attempts WHERE student_id=? ORDER BY id DESC LIMIT 500',(student_id,)).fetchall()]
            errs=[dict(r) for r in c.execute('SELECT error_code,subcompetence,severity,COUNT(*) occurrences,MIN(COALESCE(mastery_proxy,0)) mastery_proxy,MAX(occurred_at) last_seen FROM academic_error_events WHERE student_id=? GROUP BY error_code,subcompetence,severity ORDER BY occurrences DESC',(student_id,)).fetchall()]; c.close()
            by={}
            for r in rows:
                d=by.setdefault(r['error_code'],{'attempts':0,'correct':0,'recent':[]}); d['attempts']+=1; d['correct']+=1 if r.get('correct') else 0
                if len(d['recent'])<3:d['recent'].append(bool(r.get('correct')))
            patterns=[]
            for e in errs:
                d=by.get(e.get('error_code'),{'attempts':0,'correct':0,'recent':[]}); acc=round(d['correct']*100/d['attempts'],1) if d['attempts'] else None
                mastered=bool(d['attempts']>=3 and len(d['recent'])>=3 and all(d['recent'][:3]))
                patterns.append({**e,'practice_attempts':d['attempts'],'practice_accuracy':acc,'mastered':mastered,'recent_three_correct':mastered})
            return self.json({'student_id':student_id,'patterns':patterns,'attempts':rows[:100],'generated_at':now()})
        if p=='/api/release-readiness':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            c=conn(); sid=u['school_id']; lic=c.execute("SELECT * FROM school_licenses WHERE school_id=? AND status='active' ORDER BY id DESC LIMIT 1",(sid,)).fetchone(); teachers=c.execute("SELECT COUNT(*) n FROM users WHERE school_id=? AND role='teacher' AND disabled=0",(sid,)).fetchone()['n']; students=c.execute("SELECT COUNT(*) n FROM users WHERE school_id=? AND role='student' AND disabled=0",(sid,)).fetchone()['n']; courses=c.execute('SELECT COUNT(*) n FROM courses WHERE school_id=?',(sid,)).fetchone()['n']; consents=c.execute("SELECT COUNT(DISTINCT gc.student_id) n FROM guardian_consents gc JOIN users su ON su.id=gc.student_id WHERE su.school_id=? AND gc.revoked_at IS NULL",(sid,)).fetchone()['n']; snaps=c.execute("SELECT COUNT(*) n FROM snapshots s JOIN users su ON su.id=s.user_id WHERE su.school_id=?",(sid,)).fetchone()['n']; c.close()
            backups=sorted(BACKUP_DIR.glob('*.dump'),key=lambda x:x.stat().st_mtime,reverse=True); backup_recent=bool(backups and time.time()-backups[0].stat().st_mtime<48*3600)
            checks=[
              {'key':'license','ok':bool(lic),'weight':15,'label':'Licencia activa'},
              {'key':'teacher','ok':teachers>0,'weight':8,'label':'Profesor activo'},
              {'key':'student','ok':students>0,'weight':8,'label':'Alumno piloto'},
              {'key':'course','ok':courses>0,'weight':8,'label':'Curso creado'},
              {'key':'consent','ok':students==0 or consents>=students,'weight':10,'label':'Consentimiento de tutores'},
              {'key':'data','ok':snaps>0,'weight':8,'label':'Evidencia académica sincronizada'},
              {'key':'backup','ok':backup_recent,'weight':8,'label':'Backup reciente'},
              {'key':'email','ok':email_configured() or APP_ENV!='production','weight':8,'label':'Correo transaccional'},
              {'key':'https','ok':PUBLIC_BASE_URL.lower().startswith('https://') or APP_ENV!='production','weight':10,'label':'HTTPS público'},
              {'key':'devmode','ok':not DEV_MODE or APP_ENV!='production','weight':10,'label':'Modo desarrollo desactivado'},
              {'key':'db','ok':bool(runtime_health().get('ok')),'weight':7,'label':'Base de datos operativa'}]
            score=round(sum(x['weight'] for x in checks if x['ok'])*100/sum(x['weight'] for x in checks),1); blockers=[x['label'] for x in checks if not x['ok'] and x['weight']>=10]; warnings=[x['label'] for x in checks if not x['ok'] and x['weight']<10]
            return self.json({'score':score,'commercial_candidate':score>=95 and not blockers,'checks':checks,'blockers':blockers,'warnings':warnings,'external_validation_required':['Piloto con niños reales','Revisión legal local de privacidad infantil','Prueba cloud con dominio/HTTPS','Pentest independiente'],'generated_at':now()})
        if p=='/api/governance':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            reports=self.build_report(u); skills=['reading','listening','writing','speaking']
            def avg(vals): return round(sum(vals)/len(vals),1) if vals else 0
            metrics={'readiness':avg([float(r.get('readiness',0) or 0) for r in reports if float(r.get('readiness',0) or 0)>0]),'accuracy':avg([float(r.get('accuracy',0) or 0) for r in reports if int(r.get('attempts',0) or 0)>0])}
            for sk in skills: metrics[sk]=avg([float(r.get(sk,0) or 0) for r in reports if float(r.get(sk,0) or 0)>0])
            metrics['risk_count']=sum(1 for r in reports if int(r.get('attempts',0) or 0)>0 and (float(r.get('readiness',0) or 0)<65 or float(r.get('accuracy',0) or 0)<60))
            c=conn(); goals=[dict(x) for x in c.execute('SELECT g.*,u.name owner_name FROM governance_goals g LEFT JOIN users u ON u.id=g.owner_user_id WHERE g.school_id=? ORDER BY g.status,g.due_date,g.id DESC',(u['school_id'],)).fetchall()]
            actions=[dict(x) for x in c.execute('SELECT a.*,u.name owner_name FROM governance_actions a LEFT JOIN users u ON u.id=a.owner_user_id WHERE a.school_id=? ORDER BY a.status,a.due_date,a.id DESC',(u['school_id'],)).fetchall()]
            reviews=[dict(x) for x in c.execute('SELECT * FROM governance_reviews WHERE school_id=? ORDER BY id DESC LIMIT 50',(u['school_id'],)).fetchall()]; c.close()
            today=now()[:10]; alerts=[]
            for g in goals:
                current=float(metrics.get(g['metric'],g.get('current_value') or 0) or 0); g['live_value']=current; target=float(g.get('target_value') or 0); gap=round(target-current,1); g['gap']=gap
                if g.get('status')=='active' and g.get('due_date') and g['due_date']<today and gap>0: alerts.append({'type':'overdue_goal','goal_id':g['id'],'label':g['title'],'message':f'Objetivo vencido con brecha de {gap:+.1f} puntos.'})
                elif g.get('status')=='active' and gap>8: alerts.append({'type':'off_track','goal_id':g['id'],'label':g['title'],'message':f'Brecha actual de {gap:+.1f} puntos frente a la meta.'})
            for a in actions:
                if a.get('status')=='open' and a.get('due_date') and a['due_date']<today: alerts.append({'type':'overdue_action','action_id':a['id'],'label':a['title'],'message':'Accion vencida pendiente de cierre.'})
            return self.json({'metrics':metrics,'goals':goals,'actions':actions,'reviews':reviews,'alerts':alerts,'generated_at':now()})
        if p=='/api/executive-review':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            window=((qs.get('window') or ['monthly'])[0] or 'monthly').lower()
            if window not in ('monthly','quarterly'):window='monthly'
            reports=self.build_report(u); skills=['reading','listening','writing','speaking']
            def avg(vals): return round(sum(vals)/len(vals),1) if vals else 0
            school={'students_total':len(reports),'students_with_data':sum(1 for r in reports if int(r.get('attempts',0) or 0)>0),'readiness':avg([float(r.get('readiness',0) or 0) for r in reports if float(r.get('readiness',0) or 0)>0]),'accuracy':avg([float(r.get('accuracy',0) or 0) for r in reports if int(r.get('attempts',0) or 0)>0])}
            for sk in skills:school[sk]=avg([float(r.get(sk,0) or 0) for r in reports if float(r.get(sk,0) or 0)>0])
            school['risk_count']=sum(1 for r in reports if int(r.get('attempts',0) or 0)>0 and (float(r.get('readiness',0) or 0)<65 or float(r.get('accuracy',0) or 0)<60))
            c=conn(); by_id={r['id']:r for r in reports}; courses=c.execute("SELECT c.id,c.name,c.teacher_id,u.name teacher_name FROM courses c LEFT JOIN users u ON u.id=c.teacher_id WHERE c.school_id=? ORDER BY c.name",(u['school_id'],)).fetchall(); classes=[]
            for cr in courses:
                ids={x['user_id'] for x in c.execute('SELECT user_id FROM enrollments WHERE course_id=?',(cr['id'],)).fetchall()}; reps=[by_id[i] for i in ids if i in by_id]
                cm={'id':cr['id'],'name':cr['name'],'teacher':cr['teacher_name'] or 'Sin profesor','students':len(reps),'readiness':avg([float(r.get('readiness',0) or 0) for r in reps if float(r.get('readiness',0) or 0)>0]),'accuracy':avg([float(r.get('accuracy',0) or 0) for r in reps if int(r.get('attempts',0) or 0)>0])}
                for sk in skills:cm[sk]=avg([float(r.get(sk,0) or 0) for r in reps if float(r.get(sk,0) or 0)>0])
                cm['risk_count']=sum(1 for r in reps if int(r.get('attempts',0) or 0)>0 and (float(r.get('readiness',0) or 0)<65 or float(r.get('accuracy',0) or 0)<60)); classes.append(cm)
            ir=c.execute("SELECT COUNT(*) n,ROUND(AVG(delta),1) gain,SUM(CASE WHEN recommendation='close' THEN 1 ELSE 0 END) successful FROM intervention_runs WHERE school_id=? AND last_evaluated_at IS NOT NULL",(u['school_id'],)).fetchone()
            byskill=c.execute("SELECT skill,COUNT(*) interventions,ROUND(AVG(delta),1) average_gain,SUM(CASE WHEN recommendation='close' THEN 1 ELSE 0 END) successful FROM intervention_runs WHERE school_id=? AND last_evaluated_at IS NOT NULL GROUP BY skill ORDER BY average_gain DESC",(u['school_id'],)).fetchall()
            snaps=c.execute('SELECT * FROM academic_review_snapshots WHERE school_id=? AND window_type=? ORDER BY id DESC LIMIT 8',(u['school_id'],window)).fetchall(); c.close()
            history=[]
            for row in reversed(snaps):
                payload=safe_json(row['payload_json'],{}); sm=payload.get('school',{}); history.append({'id':row['id'],'period_label':row['period_label'],'created_at':row['created_at'],'readiness':sm.get('readiness',0),'accuracy':sm.get('accuracy',0),'risk_count':sm.get('risk_count',0),'classes':payload.get('classes',[])})
            previous=history[-1] if history else None; growth={}
            if previous:
                prev_payload=safe_json(snaps[0]['payload_json'],{})
                prev_school=prev_payload.get('school',{})
                for k in ['readiness','accuracy','reading','listening','writing','speaking']:growth[k]=round(float(school.get(k,0))-float(prev_school.get(k,0)),1)
            prev_classes={int(x.get('id',0)):x for x in (previous.get('classes',[]) if previous else [])}; improvements=[]
            for cm in classes:
                prev=prev_classes.get(cm['id']); d=round(float(cm['readiness'])-float(prev.get('readiness',0)),1) if prev else None
                improvements.append({'id':cm['id'],'name':cm['name'],'teacher':cm['teacher'],'readiness':cm['readiness'],'delta':d,'risk_count':cm['risk_count']})
            improvements=[x for x in improvements if x['delta'] is not None]; improvements.sort(key=lambda x:x['delta'],reverse=True)
            priorities=[]
            weak=min(skills,key=lambda k:school.get(k,0) if school.get(k,0)>0 else 999)
            if school.get(weak,0)>0:priorities.append({'label':f'Priorizar {weak.title()}','reason':f'Promedio institucional {school[weak]:.0f}%.'})
            if school['risk_count']:priorities.append({'label':'Reducir riesgo académico','reason':f"{school['risk_count']} alumno(s) con señal de seguimiento."})
            if int(ir['n'] or 0):priorities.append({'label':'Escalar estrategias efectivas','reason':f"Ganancia media observada {float(ir['gain'] or 0):+.1f} puntos."})
            return self.json({'window':window,'school':school,'growth':growth,'classes':classes,'class_improvements':improvements,'interventions':{'evaluated':int(ir['n'] or 0),'average_gain':float(ir['gain'] or 0),'successful':int(ir['successful'] or 0),'by_skill':[dict(x) for x in byskill]},'history':history,'priorities':priorities,'generated_at':now()})
        if p=='/api/executive-review.csv':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            reports=self.build_report(u); buf=io.StringIO(); w=csv.writer(buf); w.writerow(['student','readiness','accuracy','reading','listening','writing','speaking','attempts'])
            for r in reports:w.writerow([r.get('name'),r.get('readiness'),r.get('accuracy'),r.get('reading'),r.get('listening'),r.get('writing'),r.get('speaking'),r.get('attempts')])
            raw=buf.getvalue().encode('utf-8-sig'); self.send_response(200); self.send_header('Content-Type','text/csv; charset=utf-8'); self.send_header('Content-Disposition','attachment; filename="petquest_executive_review.csv"'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw); return
        if p=='/api/school-impact':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            reports=self.build_report(u); skills=['reading','listening','writing','speaking']
            def avg(vals): return round(sum(vals)/len(vals),1) if vals else 0
            school_metrics={'students_with_data':sum(1 for r in reports if int(r.get('attempts',0) or 0)>0),'students_total':len(reports),'readiness':avg([float(r.get('readiness',0) or 0) for r in reports if float(r.get('readiness',0) or 0)>0]),'accuracy':avg([float(r.get('accuracy',0) or 0) for r in reports if int(r.get('attempts',0) or 0)>0])}
            for sk in skills: school_metrics[sk]=avg([float(r.get(sk,0) or 0) for r in reports if float(r.get(sk,0) or 0)>0])
            school_metrics['risk_count']=sum(1 for r in reports if int(r.get('attempts',0) or 0)>0 and (float(r.get('readiness',0) or 0)<65 or float(r.get('accuracy',0) or 0)<60))
            c=conn(); courses=c.execute('SELECT id,name FROM courses WHERE school_id=? ORDER BY name',(u['school_id'],)).fetchall(); by_id={r['id']:r for r in reports}; classes=[]
            for cr in courses:
                ids={x['user_id'] for x in c.execute('SELECT user_id FROM enrollments WHERE course_id=?',(cr['id'],)).fetchall()}; reps=[by_id[i] for i in ids if i in by_id]
                cm={'id':cr['id'],'name':cr['name'],'students':len(reps),'readiness':avg([float(r.get('readiness',0) or 0) for r in reps if float(r.get('readiness',0) or 0)>0]),'accuracy':avg([float(r.get('accuracy',0) or 0) for r in reps if int(r.get('attempts',0) or 0)>0])}
                for sk in skills: cm[sk]=avg([float(r.get(sk,0) or 0) for r in reps if float(r.get(sk,0) or 0)>0])
                cm['risk_count']=sum(1 for r in reps if int(r.get('attempts',0) or 0)>0 and (float(r.get('readiness',0) or 0)<65 or float(r.get('accuracy',0) or 0)<60))
                classes.append(cm)
            ir=c.execute("SELECT COUNT(*) n,ROUND(AVG(delta),1) gain,SUM(CASE WHEN recommendation='close' THEN 1 ELSE 0 END) closed FROM intervention_runs WHERE school_id=? AND last_evaluated_at IS NOT NULL",(u['school_id'],)).fetchone()
            byskill=c.execute("SELECT skill,COUNT(*) interventions,ROUND(AVG(delta),1) average_gain,SUM(CASE WHEN recommendation='close' THEN 1 ELSE 0 END) successful FROM intervention_runs WHERE school_id=? AND last_evaluated_at IS NOT NULL GROUP BY skill ORDER BY average_gain DESC",(u['school_id'],)).fetchall()
            snaps=c.execute('SELECT * FROM school_quality_snapshots WHERE school_id=? ORDER BY id DESC LIMIT 2',(u['school_id'],)).fetchall(); c.close()
            previous=safe_json(snaps[0]['metrics_json'],{}) if snaps else None
            growth={}
            if previous:
                for k in ['readiness','accuracy','reading','listening','writing','speaking']:growth[k]=round(float(school_metrics.get(k,0))-float(previous.get(k,0)),1)
            risk_level='high' if school_metrics['risk_count']>=max(3,round(max(1,school_metrics['students_with_data'])*.25)) else ('medium' if school_metrics['risk_count']>0 else 'low')
            priorities=[]
            weak=sorted(skills,key=lambda k:school_metrics.get(k,0) if school_metrics.get(k,0)>0 else 999)[:2]
            if weak: priorities.append({'type':'academic','label':f'Reforzar {weak[0].title()}','reason':f'Promedio institucional {school_metrics.get(weak[0],0):.0f}%'})
            if school_metrics['risk_count']>0: priorities.append({'type':'risk','label':'Reducir alumnos en seguimiento','reason':f"{school_metrics['risk_count']} alumno(s) requieren atención"})
            if int(ir['n'] or 0)>0: priorities.append({'type':'quality','label':'Escalar intervenciones efectivas','reason':f"Ganancia media {float(ir['gain'] or 0):+.1f} pts"})
            return self.json({'school':school_metrics,'classes':classes,'interventions':{'evaluated':int(ir['n'] or 0),'average_gain':float(ir['gain'] or 0),'successful':int(ir['closed'] or 0),'by_skill':[dict(x) for x in byskill]},'growth':growth,'previous_snapshot':previous,'risk_level':risk_level,'priorities':priorities,'generated_at':now()})
        if p=='/api/school-impact.csv':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            reports=self.build_report(u); skills=['reading','listening','writing','speaking']; buf=io.StringIO(); w=csv.writer(buf); w.writerow(['student','readiness','accuracy','reading','listening','writing','speaking','attempts'])
            for r in reports:w.writerow([r.get('name'),r.get('readiness'),r.get('accuracy'),r.get('reading'),r.get('listening'),r.get('writing'),r.get('speaking'),r.get('attempts')])
            raw=buf.getvalue().encode('utf-8-sig'); self.send_response(200); self.send_header('Content-Type','text/csv; charset=utf-8'); self.send_header('Content-Disposition','attachment; filename="petquest_school_impact.csv"'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw); return
        if p=='/api/intervention-outcomes':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            try: cid=int((qs.get('course_id') or ['0'])[0])
            except Exception:return self.json({'error':'invalid_course'},400)
            c=conn(); own=c.execute('SELECT id,name FROM courses WHERE id=? AND school_id=?',(cid,u['school_id'])).fetchone()
            if not own:c.close();return self.json({'error':'invalid_course'},400)
            rows=c.execute("""SELECT ir.*,g.name group_name,COUNT(irm.user_id) member_count FROM intervention_runs ir JOIN support_groups g ON g.id=ir.group_id LEFT JOIN intervention_run_members irm ON irm.run_id=ir.id WHERE ir.course_id=? AND ir.school_id=? GROUP BY ir.id ORDER BY ir.id DESC""",(cid,u['school_id'])).fetchall()
            out=[]
            for r in rows:
                d=dict(r); members=c.execute('SELECT irm.*,u.name FROM intervention_run_members irm JOIN users u ON u.id=irm.user_id WHERE irm.run_id=? ORDER BY u.name',(r['id'],)).fetchall(); d['members']=[dict(x) for x in members]; out.append(d)
            c.close();return self.json({'course':dict(own),'outcomes':out})
        if p=='/api/intervention-effectiveness':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            c=conn(); rows=c.execute("""SELECT skill,COUNT(*) interventions,ROUND(AVG(delta),1) average_gain,SUM(CASE WHEN recommendation='close' THEN 1 ELSE 0 END) successful FROM intervention_runs WHERE school_id=? GROUP BY skill ORDER BY average_gain DESC""",(u['school_id'],)).fetchall()
            courses=c.execute("""SELECT c.id,c.name,COUNT(ir.id) interventions,ROUND(AVG(ir.delta),1) average_gain,SUM(CASE WHEN ir.recommendation='close' THEN 1 ELSE 0 END) successful FROM courses c LEFT JOIN intervention_runs ir ON ir.course_id=c.id WHERE c.school_id=? GROUP BY c.id ORDER BY average_gain DESC""",(u['school_id'],)).fetchall(); c.close()
            return self.json({'by_skill':[dict(x) for x in rows],'by_course':[dict(x) for x in courses]})
        if p=='/api/teacher-availability':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            try: tid=int(b.get('teacher_id') or (u['id'] if u['role']=='teacher' else 0)); weekday=int(b.get('weekday')); start=int(b.get('start_min')); end=int(b.get('end_min'))
            except Exception:return self.json({'error':'invalid_payload'},400)
            if weekday not in range(1,6) or start<0 or end>1440 or end-start<30:return self.json({'error':'invalid_payload'},400)
            c=conn(); t=c.execute("SELECT id FROM users WHERE id=? AND school_id=? AND role='teacher'",(tid,u['school_id'])).fetchone()
            if not t:c.close();return self.json({'error':'invalid_teacher'},400)
            c.execute('INSERT OR IGNORE INTO teacher_availability(school_id,teacher_id,weekday,start_min,end_min,created_at) VALUES(?,?,?,?,?,?)',(u['school_id'],tid,weekday,start,end,now()));audit(c,u['id'],'create','teacher_availability',tid,{'weekday':weekday,'start':start,'end':end});c.commit();c.close();return self.json({'ok':True},201)
        if p=='/api/schedule-planner/auto':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            try: duration=int(b.get('duration_min') or 30); sessions_per_group=int(b.get('sessions_per_group') or 2)
            except Exception:return self.json({'error':'invalid_payload'},400)
            duration=max(20,min(90,duration)); sessions_per_group=max(1,min(4,sessions_per_group)); c=conn(); groups=c.execute("SELECT g.*,c.teacher_id FROM support_groups g JOIN courses c ON c.id=g.course_id WHERE g.school_id=? AND g.status='active' ORDER BY g.id",(u['school_id'],)).fetchall(); created=[]; conflicts=[]
            # replace only planned sessions to make auto-plan idempotent
            c.execute("DELETE FROM schedule_sessions WHERE school_id=? AND status='planned'",(u['school_id'],))
            occupied=[]
            for g in groups:
                tid=g['teacher_id']
                if not tid: conflicts.append({'group_id':g['id'],'reason':'course_without_teacher'}); continue
                av=c.execute('SELECT * FROM teacher_availability WHERE school_id=? AND teacher_id=? ORDER BY weekday,start_min',(u['school_id'],tid)).fetchall()
                placed=0
                for a in av:
                    cursor=a['start_min']
                    while cursor+duration<=a['end_min'] and placed<sessions_per_group:
                        overlap=any(x['teacher_id']==tid and x['weekday']==a['weekday'] and not(cursor+duration<=x['start_min'] or cursor>=x['start_min']+x['duration_min']) for x in occupied)
                        if not overlap:
                            cur=c.execute('INSERT INTO schedule_sessions(school_id,course_id,support_group_id,teacher_id,weekday,start_min,duration_min,status,label,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)',(u['school_id'],g['course_id'],g['id'],tid,a['weekday'],cursor,duration,'planned',g['name'],now())); rec={'id':cur.lastrowid,'group_id':g['id'],'teacher_id':tid,'weekday':a['weekday'],'start_min':cursor,'duration_min':duration};occupied.append(rec);created.append(rec);placed+=1
                        cursor+=duration
                    if placed>=sessions_per_group:break
                if placed<sessions_per_group:conflicts.append({'group_id':g['id'],'reason':'insufficient_availability','placed':placed,'required':sessions_per_group})
            audit(c,u['id'],'auto_plan','schedule','',{'created':len(created),'conflicts':len(conflicts)});c.commit();c.close();return self.json({'ok':True,'created':created,'conflicts':conflicts,'feasible':not conflicts})
        if p=='/api/commercial/license':
            if not self.require_roles(u,'admin'):return self.json({'error':'forbidden'},403)
            try: sid=int(b.get('school_id') or 0); seats=int(b.get('student_seats') or 0); teacher_seats=int(b.get('teacher_seats') or 25)
            except Exception:return self.json({'error':'invalid_payload'},400)
            plan=clean_text(b.get('plan') or 'pilot',30); expires=clean_text(b.get('expires_at'),40) or None
            if plan not in LICENSE_PLANS or seats<1 or teacher_seats<1:return self.json({'error':'invalid_payload'},400)
            c=conn(); school=c.execute('SELECT id FROM schools WHERE id=?',(sid,)).fetchone()
            if not school:c.close();return self.json({'error':'invalid_school'},400)
            c.execute("UPDATE school_licenses SET status='replaced' WHERE school_id=? AND status='active'",(sid,));cur=c.execute('INSERT INTO school_licenses(school_id,plan,status,student_seats,teacher_seats,starts_at,expires_at,created_at,created_by) VALUES(?,?,?,?,?,?,?,?,?)',(sid,plan,'active',seats,teacher_seats,now(),expires,now(),u['id']));audit(c,u['id'],'create','school_license',cur.lastrowid,{'plan':plan,'student_seats':seats});c.commit();lid=cur.lastrowid;c.close();return self.json({'ok':True,'id':lid},201)
        if p=='/api/onboarding':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            key=clean_text(b.get('item_key'),60); status=clean_text(b.get('status') or 'done',20)
            allowed={'school_profile','teacher_setup','student_import','guardian_consent','first_class','first_assignment','readiness_baseline','privacy_review'}
            if key not in allowed or status not in ('pending','done'):return self.json({'error':'invalid_payload'},400)
            c=conn();c.execute('INSERT INTO onboarding_items(school_id,item_key,status,completed_at,updated_by,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(school_id,item_key) DO UPDATE SET status=excluded.status,completed_at=excluded.completed_at,updated_by=excluded.updated_by,updated_at=excluded.updated_at',(u['school_id'],key,status,now() if status=='done' else None,u['id'],now()));audit(c,u['id'],'update','onboarding',key,{'status':status});c.commit();c.close();return self.json({'ok':True})
        if p=='/api/ops/maintenance':
            if not self.require_roles(u,'admin'):return self.json({'error':'forbidden'},403)
            c=conn(); c.execute('DELETE FROM sessions WHERE expires_at<?',(now(),)); c.execute('DELETE FROM account_tokens WHERE expires_at<?',(now(),)); audit(c,u['id'],'maintenance','system','',{}); c.commit(); c.close(); cleanup_backups(); return self.json({'ok':True,'completed_at':now()})
        if p=='/api/release-readiness/snapshot':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            # recompute through local checks without HTTP call
            c=conn(); sid=u['school_id']; lic=c.execute("SELECT * FROM school_licenses WHERE school_id=? AND status='active' ORDER BY id DESC LIMIT 1",(sid,)).fetchone(); teachers=c.execute("SELECT COUNT(*) n FROM users WHERE school_id=? AND role='teacher' AND disabled=0",(sid,)).fetchone()['n']; students=c.execute("SELECT COUNT(*) n FROM users WHERE school_id=? AND role='student' AND disabled=0",(sid,)).fetchone()['n']; courses=c.execute('SELECT COUNT(*) n FROM courses WHERE school_id=?',(sid,)).fetchone()['n']; consents=c.execute("SELECT COUNT(DISTINCT gc.student_id) n FROM guardian_consents gc JOIN users su ON su.id=gc.student_id WHERE su.school_id=? AND gc.revoked_at IS NULL",(sid,)).fetchone()['n']; c.close(); backups=sorted(BACKUP_DIR.glob('*.dump'),key=lambda x:x.stat().st_mtime,reverse=True); backup_recent=bool(backups and time.time()-backups[0].stat().st_mtime<48*3600)
            checks=[('license',bool(lic),15),('teacher',teachers>0,8),('student',students>0,8),('course',courses>0,8),('consent',students==0 or consents>=students,10),('backup',backup_recent,8),('email',email_configured() or APP_ENV!='production',8),('https',PUBLIC_BASE_URL.lower().startswith('https://') or APP_ENV!='production',10),('devmode',not DEV_MODE or APP_ENV!='production',10),('database_runtime',(APP_ENV!='production' or not REQUIRE_POSTGRES_PRODUCTION or DATABASE_ENGINE=='postgres'),15),('studio_audio',(APP_ENV!='production' or audio_quality_status()['production_ready']),12)]; score=round(sum(w for _,ok,w in checks if ok)*100/sum(w for _,_,w in checks),1); blockers=[k for k,ok,w in checks if not ok and w>=10]; warnings=[k for k,ok,w in checks if not ok and w<10]
            c=conn();cur=c.execute('INSERT INTO release_acceptance_runs(school_id,score,blockers_json,warnings_json,checks_json,created_at,created_by) VALUES(?,?,?,?,?,?,?)',(sid,score,json.dumps(blockers),json.dumps(warnings),json.dumps(checks),now(),u['id']));c.commit();rid=cur.lastrowid;c.close();return self.json({'ok':True,'id':rid,'score':score,'blockers':blockers,'warnings':warnings},201)
        if p=='/api/privacy/export':
            c=conn(); c.execute('INSERT INTO privacy_requests(user_id,request_type,status,note,requested_at,resolved_at,resolved_by) VALUES(?,?,?,?,?,?,?)',(u['id'],'export','resolved','Self-service data export',now(),now(),u['id'])); audit(c,u['id'],'privacy_export','user',u['id']); c.commit(); c.close(); return self.json(privacy_export_payload(u))
        if p=='/api/privacy/requests':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            c=conn(); rows=c.execute('SELECT pr.*,usr.name,usr.email,usr.school_id FROM privacy_requests pr JOIN users usr ON usr.id=pr.user_id WHERE usr.school_id=? ORDER BY pr.id DESC LIMIT 300',(u['school_id'],)).fetchall() if u['role']!='admin' else c.execute('SELECT pr.*,usr.name,usr.email,usr.school_id FROM privacy_requests pr JOIN users usr ON usr.id=pr.user_id ORDER BY pr.id DESC LIMIT 300').fetchall(); c.close(); return self.json({'requests':[dict(x) for x in rows]})
        if p=='/api/assignments':
            c=conn(); rows=c.execute('SELECT a.*,c.name course_name FROM assignments a JOIN courses c ON c.id=a.course_id JOIN enrollments e ON e.course_id=c.id WHERE e.user_id=? ORDER BY due_date',(u['id'],)).fetchall() if u['role']=='student' else c.execute('SELECT a.*,c.name course_name FROM assignments a JOIN courses c ON c.id=a.course_id WHERE c.school_id=? ORDER BY due_date',(u['school_id'],)).fetchall(); c.close(); return self.json({'assignments':[dict(x) for x in rows]})
        if p=='/api/questions':
            c=conn(); rows=c.execute('SELECT * FROM questions ORDER BY id DESC LIMIT 500').fetchall(); c.close(); return self.json({'questions':[dict(x) for x in rows]})
        if p=='/api/speaking-attempts':
            if u.get('role')=='student':
                student_id=u['id']
            elif self.require_roles(u,'teacher','school','admin'):
                try: student_id=int((parse_qs(urlparse(self.path).query).get('student_id') or [0])[0])
                except Exception: return self.json({'error':'invalid_student'},400)
            else: return self.json({'error':'forbidden'},403)
            c=conn(); st=c.execute('SELECT id FROM users WHERE id=? AND school_id=?',(student_id,u['school_id'])).fetchone()
            if not st: c.close(); return self.json({'error':'invalid_student'},400)
            rows=c.execute('SELECT id,part,mode,transcript,duration_ms,metrics_json,rubric_json,score_pct,audio_local_key,created_at,source FROM speaking_attempts WHERE student_id=? ORDER BY id DESC LIMIT 100',(student_id,)).fetchall(); c.close()
            out=[]
            for r in rows:
                d=dict(r); d['metrics']=safe_json(d.pop('metrics_json'),{}); d['rubric']=safe_json(d.pop('rubric_json'),{}); out.append(d)
            return self.json({'attempts':out})
        if p=='/api/speaking-interactions':
            if u.get('role')=='student': student_id=u['id']
            elif self.require_roles(u,'teacher','school','admin'):
                try: student_id=int((parse_qs(urlparse(self.path).query).get('student_id') or [0])[0])
                except Exception: return self.json({'error':'invalid_student'},400)
            else: return self.json({'error':'forbidden'},403)
            c=conn(); st=c.execute('SELECT id FROM users WHERE id=? AND school_id=?',(student_id,u['school_id'])).fetchone()
            if not st: c.close(); return self.json({'error':'invalid_student'},400)
            rows=c.execute('SELECT id,scenario_id,scenario_title,metrics_json,rubric_json,score_pct,created_at,source FROM speaking_interaction_sessions WHERE student_id=? ORDER BY id DESC LIMIT 100',(student_id,)).fetchall(); out=[]
            for rr in rows:
                d=dict(rr); d['metrics']=safe_json(d.pop('metrics_json'),{}); d['rubric']=safe_json(d.pop('rubric_json'),{}); tr=c.execute('SELECT turn_no,role,text,functions_json,created_at FROM speaking_interaction_turns WHERE session_id=? ORDER BY turn_no',(d['id'],)).fetchall(); d['turns']=[dict(x) for x in tr]
                for t in d['turns']: t['functions']=safe_json(t.pop('functions_json'),{})
                out.append(d)
            c.close(); return self.json({'sessions':out})
        if p=='/api/snapshot':
            c=conn(); r=c.execute('SELECT payload,updated_at FROM snapshots WHERE user_id=?',(u['id'],)).fetchone(); c.close(); return self.json({'snapshot':safe_json(r['payload'],{}) if r else None,'updated_at':r['updated_at'] if r else None})
        if p=='/api/report':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            return self.json({'students':self.build_report(u)})
        if p=='/api/report.csv':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            rows=self.build_report(u); buf=io.StringIO(); w=csv.DictWriter(buf,fieldnames=['id','name','attempts','accuracy','readiness','reading','listening','writing','speaking','errors','corrections','pending_errors','preparation_score','remaining','updated_at'],extrasaction='ignore'); w.writeheader(); w.writerows(rows); raw=buf.getvalue().encode('utf-8-sig'); self.send_response(200); self.send_header('Content-Type','text/csv; charset=utf-8'); self.send_header('Content-Disposition','attachment; filename="petquest_report.csv"'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw); return
        if p=='/api/audit':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            c=conn(); rows=c.execute('SELECT a.*,u.name user_name FROM audit_log a LEFT JOIN users u ON u.id=a.user_id WHERE u.school_id=? OR ?="admin" OR a.user_id IS NULL ORDER BY a.id DESC LIMIT 200',(u['school_id'],u['role'])).fetchall(); c.close(); return self.json({'events':[dict(x) for x in rows]})
        if p=='/api/users':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            c=conn();
            if u['role']=='admin' and qs.get('all')==['1']: rows=c.execute('SELECT id,email,name,role,school_id,created_at,disabled,verified_at,last_login_at FROM users ORDER BY id').fetchall()
            else: rows=c.execute('SELECT id,email,name,role,school_id,created_at,disabled,verified_at,last_login_at FROM users WHERE school_id=? ORDER BY role,name',(u['school_id'],)).fetchall()
            c.close(); return self.json({'users':[dict(x) for x in rows]})
        if p=='/api/schools':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            c=conn(); rows=c.execute('SELECT s.*,COUNT(u.id) users FROM schools s LEFT JOIN users u ON u.school_id=s.id GROUP BY s.id ORDER BY s.name').fetchall() if u['role']=='admin' else c.execute('SELECT s.*,COUNT(u.id) users FROM schools s LEFT JOIN users u ON u.school_id=s.id WHERE s.id=? GROUP BY s.id',(u['school_id'],)).fetchall(); c.close(); return self.json({'schools':[dict(x) for x in rows]})
        if p=='/api/metrics':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            cc=conn(); rr=cc.execute('SELECT pg_database_size(current_database()) bytes').fetchone(); cc.close(); return self.json({'stats':db_stats(),'db_bytes':int(rr['bytes'] or 0),'backup_count':len(list(BACKUP_DIR.glob('*.dump')))})
        if p=='/api/backups':
            if not self.require_roles(u,'admin'):return self.json({'error':'forbidden'},403)
            items=[{'name':x.name,'bytes':x.stat().st_size,'modified':datetime.datetime.fromtimestamp(x.stat().st_mtime,datetime.timezone.utc).isoformat()} for x in sorted(BACKUP_DIR.glob('*.dump'),key=lambda x:x.stat().st_mtime,reverse=True)[:30]]
            return self.json({'backups':items,'retention':BACKUP_RETENTION})
        if p=='/api/consents':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            c=conn(); rows=c.execute('SELECT gc.*,st.name student_name,st.email student_email FROM guardian_consents gc JOIN users st ON st.id=gc.student_id WHERE st.school_id=? ORDER BY gc.id DESC LIMIT 300',(u['school_id'],)).fetchall(); c.close(); return self.json({'consents':[dict(x) for x in rows],'required':REQUIRE_GUARDIAN_CONSENT})
        return super().do_GET()
    def build_report(self,u):
        c=conn(); rows=c.execute('SELECT u.id,u.name,s.payload,s.updated_at FROM users u LEFT JOIN snapshots s ON s.user_id=u.id WHERE u.school_id=? AND u.role="student"',(u['school_id'],)).fetchall(); c.close(); out=[]
        for r in rows:
            payload=safe_json(r['payload'],{}) if r['payload'] else {}; hist=payload.get('history',[]); correct=sum(1 for x in hist if x.get('correct')); acc=round(correct*100/len(hist)) if hist else 0
            wr=payload.get('writing',[]); sp=payload.get('speaking',[]); wscore=round(sum(x.get('score',0) for x in wr)/len(wr)*5) if wr else 0; sscore=round(sum(x.get('score',0) for x in sp)/len(sp)*5) if sp else 0
            readiness=round(acc*.55+wscore*.25+sscore*.20) if hist or wr or sp else 0
            
            skills=payload.get('skills',{}) if isinstance(payload.get('skills',{}),dict) else {}
            def skill_score(k):
                v=skills.get(k)
                if isinstance(v,(int,float)): return round(v)
                vals=[x for x in hist if str(x.get('skill','')).lower()==k]
                return round(sum(1 for x in vals if x.get('correct'))*100/len(vals)) if vals else 0
            prep=student_preparation_summary(r['id'],u['school_id']) or {}
            er=(prep.get('errors') or {}); pr=(prep.get('preparation') or {})
            out.append({'id':r['id'],'name':r['name'],'attempts':len(hist),'accuracy':acc,'readiness':readiness,'writing':wscore,'speaking':round(float((prep.get('skills') or {}).get('speaking',sscore) or 0),1),'reading':skill_score('reading'),'listening':skill_score('listening'),'errors':er.get('total_error_targets',0),'corrections':er.get('corrected',0),'pending_errors':er.get('pending',0),'preparation_score':pr.get('score',0),'remaining':pr.get('remaining',100),'updated_at':r['updated_at']})
        return out
    def do_POST(self):
        p=urlparse(self.path).path; b=self.body()
        if p=='/api/register':
            ip=self.client_address[0] if self.client_address else 'unknown'
            if not rate_ok('register:'+ip,8,300):return self.json({'error':'rate_limited'},429)
            name=clean_text(b.get('name',''),120); username=clean_text(b.get('username',''),32); email=clean_text(b.get('email',''),180).lower(); password=str(b.get('password',''))[:256]; confirm=str(b.get('confirm_password',password))[:256]
            profile_mode=clean_text(b.get('profile_mode','schools'),16).lower()
            if profile_mode not in {'schools','adult'}:profile_mode='schools'
            permission=bool(b.get('permission_confirmed'))
            if len(name)<2 or not valid_email(email):return self.json({'error':'invalid_payload'},400)
            if not postgres_auth.username_valid(username):return self.json({'error':'invalid_username'},400)
            if not permission:return self.json({'error':'permission_required'},400)
            if password!=confirm:return self.json({'error':'password_mismatch'},400)
            if not strong_password(password):return self.json({'error':'weak_password'},400)
            c=conn()
            try:
                if c.execute('SELECT id FROM users WHERE lower(email)=? OR lower(username)=lower(?)',(email,username)).fetchone():c.close();return self.json({'error':'username_or_email_exists'},409)
                sid=ensure_individual_school(c); pw_hash=hash_pw(password)
                uid=c.execute('INSERT INTO users(email,password_hash,name,role,school_id,created_at,username,profile_mode) VALUES(?,?,?,?,?,?,?,?)',(email,pw_hash,name,'student',sid,now(),username,profile_mode)).lastrowid
                vtoken=secrets.token_urlsafe(32); c.execute('INSERT INTO account_tokens(token,user_id,kind,created_at,expires_at) VALUES(?,?,?,?,?)',(vtoken,uid,'verify',now(),iso_after(hours=VERIFY_HOURS)))
                token=secrets.token_urlsafe(48); expires=iso_after(hours=SESSION_HOURS); c.execute('INSERT INTO sessions(token,user_id,created_at,expires_at,last_seen_at) VALUES(?,?,?,?,?)',(token,uid,now(),expires,now()))
                audit(c,uid,'self_register','user',uid,{'role':'student','username':username,'auth_store':'postgres','permission_confirmed':True}); c.commit()
                user=dict(c.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()); user.pop('password_hash',None); c.close()
            except Exception as exc:
                try:c.rollback();c.close()
                except Exception:pass
                if getattr(exc,'sqlstate',None)=='23505':return self.json({'error':'username_or_email_exists'},409)
                return self.json({'error':'registration_failed','detail':str(exc)[:180]},500)
            resp={'ok':True,'token':token,'user':user,'expires_at':expires,'verification_required':bool(email_configured())}
            if email_configured():
                link=PUBLIC_BASE_URL.rstrip('/')+'/?verify_token='+vtoken;resp['email_sent']=send_email(email,'PET Quest — Verifica tu cuenta',f'Verifica tu cuenta PET Quest usando este enlace (válido {VERIFY_HOURS} horas):\n\n{link}')
            if DEV_MODE:resp['dev_verification_token']=vtoken
            return self.json(resp,201)
        if p=='/api/login':
            ip=self.client_address[0] if self.client_address else 'unknown'
            if not rate_ok('login:'+ip,20,60):return self.json({'error':'rate_limited'},429)
            identifier=clean_text(b.get('identifier') or b.get('email',''),180).lower(); password=str(b.get('password',''))[:256]
            if not identifier:return self.json({'error':'invalid_credentials'},401)
            c=conn(); a=c.execute('SELECT * FROM login_attempts WHERE email=?',(identifier,)).fetchone()
            if a and a['locked_until']:
                try:
                    if datetime.datetime.fromisoformat(str(a['locked_until']))>now_dt():c.close();return self.json({'error':'temporarily_locked'},429)
                except Exception:pass
            ur=c.execute('SELECT * FROM users WHERE lower(username)=lower(?) OR lower(email)=lower(?) LIMIT 1',(identifier,identifier)).fetchone()
            valid=bool(ur and not ur['disabled'] and verify_pw(password,ur['password_hash']))
            if not valid:
                failures=(a['failures'] if a else 0)+1; locked=(now_dt()+datetime.timedelta(minutes=LOCK_MINUTES)).isoformat() if failures>=MAX_LOGIN_ATTEMPTS else None
                c.execute('INSERT INTO login_attempts(email,failures,locked_until,updated_at) VALUES(?,?,?,?) ON CONFLICT(email) DO UPDATE SET failures=excluded.failures,locked_until=excluded.locked_until,updated_at=excluded.updated_at',(identifier,failures,locked,now()));c.commit();c.close();time.sleep(.12);return self.json({'error':'invalid_credentials' if not locked else 'temporarily_locked'},401 if not locked else 429)
            if ur['disabled']:c.close();return self.json({'error':'account_disabled'},403)
            if password_hash_scheme(ur['password_hash'])!='pbkdf2_sha256':
                migrated_hash=hash_pw(password); c.execute('UPDATE users SET password_hash=? WHERE id=?',(migrated_hash,ur['id'])); audit(c,ur['id'],'password_hash_migrated','user',ur['id'],{'from':password_hash_scheme(ur['password_hash']),'to':'pbkdf2_sha256'})
            c.execute('DELETE FROM login_attempts WHERE lower(email) IN (?,?)',(str(ur['email'] or '').lower(),str(ur['username'] or '').lower()))
            token=secrets.token_urlsafe(48);expires=iso_after(hours=SESSION_HOURS);c.execute('INSERT INTO sessions(token,user_id,created_at,expires_at,last_seen_at) VALUES(?,?,?,?,?)',(token,ur['id'],now(),expires,now()));c.execute('UPDATE users SET last_login_at=? WHERE id=?',(now(),ur['id']));audit(c,ur['id'],'login','user',ur['id'],{'auth_store':'postgres'});c.commit();user=dict(c.execute('SELECT * FROM users WHERE id=?',(ur['id'],)).fetchone());user.pop('password_hash',None);c.close()
            return self.json({'token':token,'user':user,'expires_at':expires})
        if p=='/api/forgot-password':
            ip=self.client_address[0] if self.client_address else 'unknown'
            if not rate_ok('reset:'+ip,8,300):return self.json({'error':'rate_limited'},429)
            if not email_configured():return self.json({'error':'email_unavailable'},503)
            email=clean_text(b.get('email',''),180).lower()
            token=None
            if valid_email(email):
                token=password_recovery.issue_token(conn,email,now(),iso_after(minutes=RESET_MINUTES),audit)
            if token:
                link=PUBLIC_BASE_URL.rstrip('/')+'/?reset_token='+token
                send_email(email,'PET Quest - Restablecer contraseña',f'Usa este enlace para crear una contraseña nueva (válido {RESET_MINUTES} minutos):\n\n{link}\n\nSi no solicitaste este cambio, ignora este mensaje.')
            return self.json({'ok':True,'message':'Si la cuenta está activa, recibirás un enlace de recuperación. Revisa también la carpeta de spam.'})
        if p=='/api/reset-password':
            ip=self.client_address[0] if self.client_address else 'unknown'
            if not rate_ok('reset-submit:'+ip,15,300):return self.json({'error':'rate_limited'},429)
            token=clean_text(b.get('token'),180); password=str(b.get('password',''))
            if not strong_password(password) or len(password)>128:return self.json({'error':'weak_password'},400)
            error=password_recovery.redeem_token(conn,token,hash_pw(password),now(),audit)
            return self.json({'error':error},400) if error else self.json({'ok':True})
        if p=='/api/logout':
            token=self.bearer(); c=conn(); row=c.execute('SELECT user_id FROM sessions WHERE token=?',(token,)).fetchone(); c.execute('DELETE FROM sessions WHERE token=?',(token,));
            if row:audit(c,row['user_id'],'logout')
            c.commit();c.close();return self.json({'ok':True})
        if p=='/api/verify-email':
            token=clean_text(b.get('token'),180); c=conn(); r=c.execute('SELECT * FROM account_tokens WHERE token=? AND kind="verify" AND used_at IS NULL',(token,)).fetchone()
            if not r:c.close();return self.json({'error':'invalid_token'},400)
            try: expired=datetime.datetime.fromisoformat(r['expires_at'])<=now_dt()
            except Exception: expired=True
            if expired:c.close();return self.json({'error':'expired_token'},400)
            c.execute('UPDATE users SET verified_at=? WHERE id=?',(now(),r['user_id'])); c.execute('UPDATE account_tokens SET used_at=? WHERE token=?',(now(),token)); audit(c,r['user_id'],'email_verified'); c.commit(); c.close(); return self.json({'ok':True})
        u=self.auth()
        if not u:return self.json({'error':'unauthorized'},401)
        if p=='/api/change-password':
            old=str(b.get('current_password',''))[:256]; new=str(b.get('new_password',''))[:256]
            if not strong_password(new):return self.json({'error':'weak_password'},400)
            c=conn(); ur=c.execute('SELECT password_hash,email,username FROM users WHERE id=?',(u['id'],)).fetchone()
            if not ur or not verify_pw(old,ur['password_hash']):c.close();return self.json({'error':'invalid_current_password'},400)
            new_hash=hash_pw(new)
            c.execute('UPDATE users SET password_hash=? WHERE id=?',(new_hash,u['id'])); c.execute('DELETE FROM sessions WHERE user_id=? AND token<>?',(u['id'],self.bearer())); audit(c,u['id'],'password_changed','user',u['id'],{'auth_store':'postgres'}); c.commit(); c.close(); return self.json({'ok':True})
        if p=='/api/speaking-interactions':
            if u.get('role')!='student' and not self.require_roles(u,'teacher','school','admin'): return self.json({'error':'forbidden'},403)
            if u.get('role')=='student' and REQUIRE_GUARDIAN_CONSENT:
                c=conn(); ok=c.execute('SELECT 1 FROM guardian_consents WHERE student_id=? AND revoked_at IS NULL ORDER BY id DESC LIMIT 1',(u['id'],)).fetchone(); c.close()
                if not ok:return self.json({'error':'guardian_consent_required'},403)
            student_id=u['id'] if u.get('role')=='student' else int(b.get('student_id') or 0)
            turns=b.get('turns') if isinstance(b.get('turns'),list) else []; metrics=b.get('metrics') if isinstance(b.get('metrics'),dict) else {}; rubric=b.get('rubric') if isinstance(b.get('rubric'),dict) else {}
            if not turns or len(turns)>30:return self.json({'error':'invalid_turns'},400)
            try: score_pct=max(0.0,min(100.0,float(b.get('score_pct') or 0)))
            except Exception:return self.json({'error':'invalid_score'},400)
            raw_metrics=json.dumps(metrics,ensure_ascii=False); raw_rubric=json.dumps(rubric,ensure_ascii=False)
            c=conn(); st=c.execute('SELECT id FROM users WHERE id=? AND school_id=?',(student_id,u['school_id'])).fetchone()
            if not st:c.close();return self.json({'error':'invalid_student'},400)
            cur=c.execute('INSERT INTO speaking_interaction_sessions(student_id,scenario_id,scenario_title,metrics_json,rubric_json,score_pct,created_at,source) VALUES(?,?,?,?,?,?,?,?)',(student_id,clean_text(b.get('scenario_id'),80) or 'part3',clean_text(b.get('scenario_title'),180),raw_metrics,raw_rubric,score_pct,now(),clean_text(b.get('source'),80) or 'v46.15-part3-ai-candidate')); sid=cur.lastrowid
            student_text=[]
            for i,t in enumerate(turns,1):
                if not isinstance(t,dict): continue
                role=clean_text(t.get('role'),12); text=clean_text(t.get('text'),4000)
                if role not in ('ai','student') or not text: continue
                funcs=t.get('functions') if isinstance(t.get('functions'),dict) else {}; c.execute('INSERT INTO speaking_interaction_turns(session_id,turn_no,role,text,functions_json,created_at) VALUES(?,?,?,?,?,?)',(sid,i,role,text,json.dumps(funcs,ensure_ascii=False),clean_text(t.get('at'),60) or now()))
                if role=='student': student_text.append(text)
            # Feed Part 3 preparation with this interaction evidence.
            sp_metrics=dict(metrics); sp_metrics['interaction_session_id']=sid; sp_rubric={'grammar_vocabulary':0,'discourse_management':0,'pronunciation':0,'interactive_communication':int(rubric.get('interactive_communication') or 0),'global_achievement':int(rubric.get('interactive_communication') or 0)}
            c.execute('INSERT INTO speaking_attempts(student_id,part,mode,transcript,duration_ms,metrics_json,rubric_json,score_pct,audio_local_key,created_at,source) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(student_id,3,'interactive','\n'.join(student_text),0,json.dumps(sp_metrics,ensure_ascii=False),json.dumps(sp_rubric,ensure_ascii=False),score_pct,'',now(),'v46.15-part3-ai-candidate'))
            audit(c,u['id'],'create','speaking_interaction',sid,{'student_id':student_id,'score_pct':score_pct,'turns':len(turns)});c.commit();c.close();return self.json({'ok':True,'id':sid,'score_pct':score_pct},201)
        if p=='/api/speaking-attempts':
            if u.get('role')!='student' and not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            if u.get('role')=='student' and REQUIRE_GUARDIAN_CONSENT:
                c=conn(); ok=c.execute('SELECT 1 FROM guardian_consents WHERE student_id=? AND revoked_at IS NULL ORDER BY id DESC LIMIT 1',(u['id'],)).fetchone(); c.close()
                if not ok:return self.json({'error':'guardian_consent_required'},403)
            student_id=u['id'] if u.get('role')=='student' else int(b.get('student_id') or 0)
            try: part=int(b.get('part') or 1); duration_ms=max(0,min(600000,int(b.get('duration_ms') or 0))); score_pct=max(0.0,min(100.0,float(b.get('score_pct') or 0)))
            except Exception:return self.json({'error':'invalid_payload'},400)
            if part<1 or part>4:return self.json({'error':'invalid_part'},400)
            mode=clean_text(b.get('mode'),30) or 'practice'; transcript=clean_text(b.get('transcript'),10000); metrics=b.get('metrics') if isinstance(b.get('metrics'),dict) else {}; rubric=b.get('rubric') if isinstance(b.get('rubric'),dict) else {}
            if not transcript and duration_ms<500:return self.json({'error':'empty_attempt'},400)
            raw_metrics=json.dumps(metrics,ensure_ascii=False); raw_rubric=json.dumps(rubric,ensure_ascii=False)
            if len(raw_metrics)>20000 or len(raw_rubric)>12000:return self.json({'error':'payload_too_large'},413)
            c=conn(); st=c.execute('SELECT id FROM users WHERE id=? AND school_id=?',(student_id,u['school_id'])).fetchone()
            if not st:c.close();return self.json({'error':'invalid_student'},400)
            cur=c.execute('INSERT INTO speaking_attempts(student_id,part,mode,transcript,duration_ms,metrics_json,rubric_json,score_pct,audio_local_key,created_at,source) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(student_id,part,mode,transcript,duration_ms,raw_metrics,raw_rubric,score_pct,clean_text(b.get('audio_local_key'),180),now(),clean_text(b.get('source'),60) or 'v46.14-speaking-ai'))
            audit(c,u['id'],'create','speaking_attempt',cur.lastrowid,{'student_id':student_id,'part':part,'score_pct':score_pct}); c.commit(); rid=cur.lastrowid;c.close();return self.json({'ok':True,'id':rid,'score_pct':score_pct},201)
        if p=='/api/snapshot':
            # Core authenticated progress persistence must remain available for every user.
            # Guardian consent still protects sensitive features such as speaking/audio capture,
            # but must not prevent saving ordinary exercise progress and resume state.
            payload=b.get('snapshot',{}); raw=json.dumps(payload,ensure_ascii=False)
            if len(raw)>750000:return self.json({'error':'snapshot_too_large'},413)
            c=conn();c.execute('INSERT INTO snapshots(user_id,payload,updated_at) VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET payload=excluded.payload,updated_at=excluded.updated_at',(u['id'],raw,now()));audit(c,u['id'],'sync','snapshot',u['id'],{'bytes':len(raw)});c.commit();c.close();return self.json({'ok':True,'synced_at':now()})
        if p=='/api/courses':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            name=clean_text(b.get('name'),140)
            if not name:return self.json({'error':'invalid_payload'},400)
            teacher_id=u['id'] if u['role']=='teacher' else int(b.get('teacher_id') or 0) or None
            c=conn()
            if teacher_id:
                t=c.execute('SELECT id FROM users WHERE id=? AND school_id=? AND role="teacher"',(teacher_id,u['school_id'])).fetchone()
                if not t:c.close();return self.json({'error':'invalid_teacher'},400)
            cur=c.execute('INSERT INTO courses(school_id,name,teacher_id,created_at) VALUES(?,?,?,?)',(u['school_id'],name,teacher_id,now())); audit(c,u['id'],'create','course',cur.lastrowid,{'name':name}); c.commit(); cid=cur.lastrowid;c.close();return self.json({'ok':True,'id':cid},201)
        if p=='/api/enrollments':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            try: cid=int(b.get('course_id') or 0); sid=int(b.get('student_id') or 0)
            except Exception:return self.json({'error':'invalid_payload'},400)
            c=conn(); course=c.execute('SELECT id FROM courses WHERE id=? AND school_id=?',(cid,u['school_id'])).fetchone(); student=c.execute('SELECT id FROM users WHERE id=? AND school_id=? AND role="student"',(sid,u['school_id'])).fetchone()
            if not course or not student:c.close();return self.json({'error':'invalid_payload'},400)
            c.execute('INSERT OR IGNORE INTO enrollments(course_id,user_id) VALUES(?,?)',(cid,sid));audit(c,u['id'],'enroll','student',sid,{'course_id':cid});c.commit();c.close();return self.json({'ok':True},201)
        if p=='/api/support-groups':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            try: course_id=int(b.get('course_id') or 0)
            except Exception:return self.json({'error':'invalid_course'},400)
            name=clean_text(b.get('name'),120); skill=clean_text(b.get('skill'),20); focus=clean_text(b.get('focus'),80); members=b.get('student_ids') or []
            if not name or skill not in ALLOWED_SKILLS:return self.json({'error':'invalid_payload'},400)
            try: members=[int(x) for x in members][:100]
            except Exception:return self.json({'error':'invalid_members'},400)
            c=conn(); own=c.execute('SELECT id FROM courses WHERE id=? AND school_id=?',(course_id,u['school_id'])).fetchone()
            if not own:c.close();return self.json({'error':'invalid_course'},400)
            valid={r['user_id'] for r in c.execute('SELECT user_id FROM enrollments WHERE course_id=?',(course_id,)).fetchall()}
            selected=[sid for sid in members if sid in valid]
            cur=c.execute('INSERT INTO support_groups(school_id,course_id,name,skill,focus,created_by,created_at) VALUES(?,?,?,?,?,?,?)',(u['school_id'],course_id,name,skill,focus,u['id'],now())); gid=cur.lastrowid
            for sid in selected:c.execute('INSERT OR IGNORE INTO support_group_members(group_id,user_id) VALUES(?,?)',(gid,sid))
            report_by_id={r['id']:r for r in self.build_report(u)}
            baselines=[float(report_by_id.get(sid,{}).get(skill,0) or 0) for sid in selected]
            baseline_avg=round(sum(baselines)/len(baselines),1) if baselines else 0
            rr=c.execute('INSERT INTO intervention_runs(group_id,course_id,school_id,skill,baseline_average,current_average,delta,recommendation,success_criteria,created_at,created_by) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(gid,course_id,u['school_id'],skill,baseline_avg,baseline_avg,0,'collect_more_data',focus,now(),u['id'])); run_id=rr.lastrowid
            for sid,score in zip(selected,baselines):c.execute('INSERT INTO intervention_run_members(run_id,user_id,baseline_score,current_score,delta) VALUES(?,?,?,?,?)',(run_id,sid,score,score,0))
            audit(c,u['id'],'create','support_group',gid,{'course_id':course_id,'skill':skill,'members':len(selected),'intervention_run_id':run_id,'baseline':baseline_avg}); c.commit(); c.close(); return self.json({'ok':True,'id':gid,'members':len(selected),'intervention_run_id':run_id,'baseline_average':baseline_avg},201)
        if p=='/api/profile':
            name=clean_text(b.get('name'),120)
            if not name:return self.json({'error':'invalid_name'},400)
            c=conn(); c.execute('UPDATE users SET name=? WHERE id=?',(name,u['id'])); audit(c,u['id'],'update','profile',u['id'],{'fields':['name']}); c.commit(); c.close(); return self.json({'ok':True,'name':name})
        if p=='/api/events':
            event_type=clean_text(b.get('event_type') or b.get('type'),80); detail=b.get('detail') if isinstance(b.get('detail'),dict) else (b.get('meta') if isinstance(b.get('meta'),dict) else {})
            if not event_type:return self.json({'error':'invalid_event'},400)
            skill=clean_text(b.get('skill') or detail.get('skill'),30).lower() or None; item_id=clean_text(b.get('item_id') or detail.get('item_id') or detail.get('qid'),100) or None
            success=b.get('success',detail.get('success',detail.get('correct'))); success=None if success is None else (1 if bool(success) else 0)
            try: minutes=max(0.0,min(1440.0,float(b.get('minutes',detail.get('minutes',0)) or 0)))
            except Exception: minutes=0.0
            c=conn(); cur=c.execute('INSERT INTO learning_events(user_id,event_type,skill,item_id,success,minutes,meta_json,created_at) VALUES(?,?,?,?,?,?,?,?)',(u['id'],event_type,skill,item_id,success,minutes,json.dumps(detail,ensure_ascii=False),now())); c.commit(); eid=cur.lastrowid; c.close(); return self.json({'ok':True,'id':eid},201)
        if p=='/api/recovery/verify':
            if not self.require_roles(u,'admin'):return self.json({'error':'forbidden'},403)
            name=clean_text(b.get('name'),220)
            if not name or Path(name).name!=name or not name.endswith('.dump'):return self.json({'error':'invalid_backup'},400)
            target=BACKUP_DIR/name
            if not target.exists():return self.json({'error':'not_found'},404)
            integrity='error'; ok=False
            try:
                cp=subprocess.run(['pg_restore','--list',str(target)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=60)
                ok=(cp.returncode==0); integrity='ok' if ok else ('error:'+cp.stderr[:120])
            except Exception as exc: integrity='error:'+str(exc)[:120]
            c=conn(); cur=c.execute('INSERT INTO recovery_checks(backup_name,ok,integrity_result,checked_at,checked_by) VALUES(?,?,?,?,?)',(name,1 if ok else 0,integrity,now(),u['id'])); audit(c,u['id'],'verify','backup',cur.lastrowid,{'name':name,'integrity':integrity}); c.commit(); cid=cur.lastrowid; c.close(); return self.json({'ok':ok,'id':cid,'name':name,'integrity':integrity},200 if ok else 422)
        if p=='/api/decision-simulator/run':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            reports=self.build_report(u); skills=['reading','listening','writing','speaking']
            skill=clean_text(b.get('target_skill'),20).lower() or 'reading'; coverage=clean_text(b.get('coverage'),20).lower() or 'risk_only'; intensity=clean_text(b.get('intensity'),20).lower() or 'standard'
            if skill not in ALLOWED_SKILLS or coverage not in ('risk_only','priority','all') or intensity not in ('standard','intensive'):return self.json({'error':'invalid_payload'},400)
            try: hours=max(0,min(12,float(b.get('extra_teacher_hours',0) or 0))); weeks=max(1,min(16,int(b.get('weeks',8) or 8)))
            except Exception:return self.json({'error':'invalid_payload'},400)
            def avg(vals): return round(sum(vals)/len(vals),1) if vals else 0
            current_skill=avg([float(r.get(skill,0) or 0) for r in reports if float(r.get(skill,0) or 0)>0])
            current_readiness=avg([float(r.get('readiness',0) or 0) for r in reports if float(r.get('readiness',0) or 0)>0])
            risk=[r for r in reports if int(r.get('attempts',0) or 0)>0 and (float(r.get('readiness',0) or 0)<65 or float(r.get('accuracy',0) or 0)<60)]
            priority_students=[r for r in reports if 0<float(r.get(skill,0) or 0)<72]
            if coverage=='risk_only': covered=len(risk)
            elif coverage=='priority': covered=len(priority_students)
            else: covered=sum(1 for r in reports if int(r.get('attempts',0) or 0)>0)
            c=conn(); rows=c.execute("SELECT delta FROM intervention_runs WHERE school_id=? AND status='closed' AND delta>0 ORDER BY id DESC LIMIT 40",(u['school_id'],)).fetchall(); gains=[float(x['delta'] or 0) for x in rows]; c.close()
            n=len(gains); historic=(sum(gains)/n) if gains else 0
            confidence='high' if n>=8 else ('medium' if n>=3 else 'low')
            evidence_factor=1.0 if n>=8 else (0.78 if n>=3 else (0.55 if n else 0.32))
            # If no local intervention evidence exists, use a small explicit heuristic rather than pretending measured impact.
            base_4w=(historic*0.35) if historic>0 else 2.0
            hours_factor=min(1.45,0.55+hours/4.0)
            weeks_factor=min(2.0,weeks/4.0)
            coverage_factor={'risk_only':1.12,'priority':1.02,'all':0.82}[coverage]
            intensity_factor=1.15 if intensity=='intensive' else 1.0
            expected=max(0,min(15,base_4w*hours_factor*weeks_factor*coverage_factor*intensity_factor*evidence_factor))
            if covered==0 or current_skill<=0: expected=0.0
            uncertainty={'high':0.18,'medium':0.30,'low':0.45}[confidence]
            lo=max(0,expected*(1-uncertainty)); hi=min(18,expected*(1+uncertainty))
            total_hours=round(hours*weeks,1); efficiency=round(expected/max(1,total_hours)*10,2)
            projected_skill=min(100,current_skill+expected) if current_skill else expected
            readiness_effect=expected*0.25 if current_readiness else 0
            projected_readiness=min(100,current_readiness+readiness_effect) if current_readiness else 0
            if hours==0: recommendation='Sin horas adicionales: usar como escenario de referencia, no como plan de intervención.'
            elif covered==0: recommendation='No hay alumnos elegibles con los criterios actuales; revisar cobertura o habilidad.'
            elif efficiency>=1.5: recommendation='Alta eficiencia relativa: buen candidato para piloto y reevaluación.'
            elif efficiency>=0.8: recommendation='Eficiencia moderada: aplicar con seguimiento y criterio de salida.'
            else: recommendation='Esfuerzo alto frente al impacto estimado: comparar con una alternativa más focalizada.'
            result={'inputs':{'extra_teacher_hours':hours,'weeks':weeks,'target_skill':skill,'coverage':coverage,'intensity':intensity},'baseline':{'skill_score':current_skill,'readiness':current_readiness,'students_covered':covered},'expected':{'skill_delta':round(expected,1),'skill_delta_range':[round(lo,1),round(hi,1)],'projected_skill':round(projected_skill,1),'projected_readiness':round(projected_readiness,1)},'effort':{'teacher_hours_total':total_hours,'teacher_hours_week':hours,'weeks':weeks,'students_covered':covered},'efficiency_index':efficiency,'confidence':confidence,'historic_intervention_count':n,'historic_intervention_gain':round(historic,1),'recommendation':recommendation,'method_note':'Escenario comparativo, no prediccion garantizada. Con baja evidencia local se usa una heuristica conservadora y un rango de incertidumbre mas amplio.','generated_at':now()}; result['scenario_id']=persist_planning_scenario(u,'decision_simulator',b,result); return self.json(result)
        if p=='/api/budget-optimizer/run':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            try:
                budget=max(0,min(100000,float(b.get('budget',0) or 0))); cost=max(1,min(1000,float(b.get('cost_per_hour',1) or 1))); max_hours=max(0,min(40,float(b.get('max_hours_week',0) or 0))); weeks=max(1,min(24,int(b.get('weeks',8) or 8)))
            except Exception:return self.json({'error':'invalid_payload'},400)
            strategy=clean_text(b.get('strategy'),30).lower() or 'balanced'; forced=clean_text(b.get('target_skill'),20).lower()
            if strategy not in ('balanced','risk_first','priority_skill','max_coverage') or (forced and forced not in ALLOWED_SKILLS):return self.json({'error':'invalid_payload'},400)
            reports=self.build_report(u); skills=['reading','listening','writing','speaking']
            def avg(vals): return round(sum(vals)/len(vals),1) if vals else 0
            cur={sk:avg([float(r.get(sk,0) or 0) for r in reports if float(r.get(sk,0) or 0)>0]) for sk in skills}
            cur['readiness']=avg([float(r.get('readiness',0) or 0) for r in reports if float(r.get('readiness',0) or 0)>0])
            risk=[r for r in reports if int(r.get('attempts',0) or 0)>0 and (float(r.get('readiness',0) or 0)<65 or float(r.get('accuracy',0) or 0)<60)]
            c=conn(); rows=c.execute("SELECT delta FROM intervention_runs WHERE school_id=? AND status='closed' AND delta>0 ORDER BY id DESC LIMIT 40",(u['school_id'],)).fetchall(); gains=[float(x['delta'] or 0) for x in rows]; c.close()
            n=len(gains); historic=(sum(gains)/n) if gains else 0; confidence='high' if n>=8 else ('medium' if n>=3 else 'low'); ef=1.0 if n>=8 else (0.78 if n>=3 else (0.55 if n else 0.32)); base=(historic*0.35) if historic>0 else 2.0
            priority=min(skills,key=lambda k:cur[k] if cur[k]>0 else 999) if reports else 'reading'
            candidate_skills=[forced] if forced else ([priority]+[x for x in skills if x!=priority])
            candidates=[]
            hour_steps=sorted(set([h for h in (1,2,3,4,6,8,10,12) if h<=max_hours]+([max_hours] if max_hours>0 else [])))
            for sk in candidate_skills:
                for hours in hour_steps:
                    total=hours*weeks; spend=total*cost
                    if spend>budget+1e-9: continue
                    for coverage in ('risk_only','priority','all'):
                        if coverage=='risk_only': covered=len(risk)
                        elif coverage=='priority': covered=sum(1 for r in reports if 0<float(r.get(sk,0) or 0)<72)
                        else: covered=sum(1 for r in reports if int(r.get('attempts',0) or 0)>0)
                        if covered==0 or cur.get(sk,0)<=0: continue
                        covf={'risk_only':1.12,'priority':1.02,'all':0.82}[coverage]
                        for intensity in ('standard','intensive'):
                            intf=1.15 if intensity=='intensive' else 1.0
                            expected=max(0,min(15,base*min(1.45,0.55+hours/4.0)*min(2.0,weeks/4.0)*covf*intf*ef))
                            uncertainty={'high':0.18,'medium':0.30,'low':0.45}[confidence]
                            lo=max(0,expected*(1-uncertainty)); hi=min(18,expected*(1+uncertainty)); efficiency=expected/max(1,spend)*100
                            score=expected
                            if strategy=='risk_first': score*=1.20 if coverage=='risk_only' else 0.94
                            elif strategy=='priority_skill': score*=1.20 if sk==priority else 0.9
                            elif strategy=='max_coverage': score*=1.15 if coverage=='all' else 1.0
                            score+=min(2,efficiency*.08)
                            candidates.append({'skill':sk,'coverage':coverage,'intensity':intensity,'hours_week':round(hours,1),'weeks':weeks,'total_hours':round(total,1),'cost':round(spend,2),'students_covered':covered,'expected_delta':round(expected,1),'range':[round(lo,1),round(hi,1)],'projected_skill':round(min(100,cur[sk]+expected),1),'efficiency_per_100_currency':round(efficiency,3),'confidence':confidence,'optimization_score':round(score,3)})
            candidates.sort(key=lambda x:(x['optimization_score'],x['expected_delta'],-x['cost']),reverse=True)
            top=candidates[:8]; best=top[0] if top else None
            used=best['cost'] if best else 0; spare=max(0,budget-used)
            result={'constraints':{'budget':budget,'cost_per_hour':cost,'max_hours_week':max_hours,'weeks':weeks,'strategy':strategy,'target_skill':forced or None},'current':cur,'priority_skill':priority,'historic_intervention_count':n,'historic_intervention_gain':round(historic,1),'confidence':confidence,'best_plan':best,'alternatives':top,'budget_used':round(used,2),'budget_remaining':round(spare,2),'method_note':'Optimización heurística sobre escenarios V34 factibles. Impacto esperado y rangos son orientativos; validar mediante piloto y reevaluación.','generated_at':now()}; result['scenario_id']=persist_planning_scenario(u,'budget_optimizer',b,result); return self.json(result)
        if p=='/api/portfolio-optimizer/run':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            try:
                budget=max(0,min(200000,float(b.get('budget',0) or 0))); cost=max(1,min(1000,float(b.get('cost_per_hour',1) or 1))); max_hours=max(0,min(40,float(b.get('max_hours_week',0) or 0))); weeks=max(1,min(24,int(b.get('weeks',8) or 8))); max_interventions=max(1,min(4,int(b.get('max_interventions',3) or 3))); max_overlap=max(1,min(4,int(b.get('max_student_overlap',2) or 2)))
            except Exception:return self.json({'error':'invalid_payload'},400)
            strategy=clean_text(b.get('strategy'),30).lower() or 'balanced'
            if strategy not in ('balanced','risk_first','coverage','weak_skills'):return self.json({'error':'invalid_payload'},400)
            reports=self.build_report(u); skills=['reading','listening','writing','speaking']
            def avg(vals): return round(sum(vals)/len(vals),1) if vals else 0
            cur={sk:avg([float(r.get(sk,0) or 0) for r in reports if float(r.get(sk,0) or 0)>0]) for sk in skills}
            cur['readiness']=avg([float(r.get('readiness',0) or 0) for r in reports if float(r.get('readiness',0) or 0)>0])
            with_data=[r for r in reports if int(r.get('attempts',0) or 0)>0]
            risk=[r for r in with_data if float(r.get('readiness',0) or 0)<65 or float(r.get('accuracy',0) or 0)<60]
            c=conn(); rows=c.execute("SELECT delta FROM intervention_runs WHERE school_id=? AND status='closed' AND delta>0 ORDER BY id DESC LIMIT 40",(u['school_id'],)).fetchall(); gains=[float(x['delta'] or 0) for x in rows]; c.close()
            n=len(gains); historic=(sum(gains)/n) if gains else 0; confidence='high' if n>=8 else ('medium' if n>=3 else 'low'); ef=1.0 if n>=8 else (0.78 if n>=3 else (0.55 if n else 0.32)); base=(historic*0.35) if historic>0 else 2.0
            priority=min(skills,key=lambda k:cur[k] if cur[k]>0 else 999) if reports else 'reading'
            hour_steps=[h for h in (1,2,3,4) if h<=max_hours]
            if max_hours>0 and max_hours not in hour_steps and max_hours<4: hour_steps.append(max_hours)
            candidates=[]
            for sk in skills:
                weak=[r for r in with_data if 0<float(r.get(sk,0) or 0)<72]
                groups={'risk_only':risk,'priority':weak}
                for coverage,students in groups.items():
                    ids=sorted({int(r['id']) for r in students})
                    if not ids or cur.get(sk,0)<=0: continue
                    covf=1.12 if coverage=='risk_only' else 1.02
                    for hours in hour_steps:
                        total=hours*weeks; spend=total*cost
                        if spend>budget+1e-9: continue
                        for intensity in ('standard','intensive'):
                            intf=1.15 if intensity=='intensive' else 1.0
                            expected=max(0,min(15,base*min(1.45,0.55+hours/4.0)*min(2.0,weeks/4.0)*covf*intf*ef))
                            uncertainty={'high':0.18,'medium':0.30,'low':0.45}[confidence]
                            lo=max(0,expected*(1-uncertainty)); hi=min(18,expected*(1+uncertainty))
                            impact_points=expected*len(ids)
                            candidates.append({'skill':sk,'coverage':coverage,'intensity':intensity,'hours_week':round(hours,1),'weeks':weeks,'total_hours':round(total,1),'cost':round(spend,2),'student_ids':ids,'students_covered':len(ids),'expected_delta':round(expected,1),'range':[round(lo,1),round(hi,1)],'impact_points':round(impact_points,2),'confidence':confidence})
            # Keep a compact Pareto-ish set per skill so exhaustive combinations remain small.
            compact=[]
            for sk in skills:
                ss=[x for x in candidates if x['skill']==sk]
                ss.sort(key=lambda x:(x['impact_points']/max(1,x['cost']),x['impact_points'],-x['cost']),reverse=True)
                compact.extend(ss[:5])
            by_skill={sk:[None]+[x for x in compact if x['skill']==sk] for sk in skills}
            import itertools
            portfolios=[]; total_students=max(1,len(with_data))
            for combo in itertools.product(*[by_skill[sk] for sk in skills]):
                chosen=[x for x in combo if x]
                if not chosen or len(chosen)>max_interventions: continue
                spend=sum(x['cost'] for x in chosen); hours=sum(x['hours_week'] for x in chosen)
                if spend>budget+1e-9 or hours>max_hours+1e-9: continue
                counts={}
                for x in chosen:
                    for sid in x['student_ids']: counts[sid]=counts.get(sid,0)+1
                if counts and max(counts.values())>max_overlap: continue
                unique=len(counts); overlap_events=sum(max(0,v-1) for v in counts.values()); risk_ids={int(r['id']) for r in risk}; risk_covered=len(risk_ids.intersection(counts))
                impact=sum(x['impact_points'] for x in chosen)
                institutional=impact/(total_students*4.0)
                efficiency=impact/max(1,spend)*100
                score=impact
                if strategy=='risk_first': score+=risk_covered*2.5
                elif strategy=='coverage': score+=unique*1.8
                elif strategy=='weak_skills': score+=sum(max(0,75-cur.get(x['skill'],0))*0.15 for x in chosen)
                else: score+=unique*0.8+risk_covered*0.8
                score-=overlap_events*1.4
                portfolios.append({'plans':[{k:v for k,v in x.items() if k!='student_ids'} for x in chosen],'intervention_count':len(chosen),'budget_used':round(spend,2),'budget_remaining':round(max(0,budget-spend),2),'hours_week_used':round(hours,1),'hours_week_remaining':round(max(0,max_hours-hours),1),'unique_students':unique,'risk_students_covered':risk_covered,'overlap_events':overlap_events,'expected_impact_points':round(impact,1),'institutional_equivalent_gain':round(institutional,2),'efficiency_per_100_currency':round(efficiency,3),'optimization_score':round(score,2),'confidence':confidence})
            portfolios.sort(key=lambda x:(x['optimization_score'],x['expected_impact_points'],-x['budget_used']),reverse=True)
            top=portfolios[:6]; best=top[0] if top else None
            note='Portafolio heuristico de varias intervenciones. El impacto es orientativo y debe validarse con pilotos y resultados observados.'
            result={'constraints':{'budget':budget,'cost_per_hour':cost,'max_hours_week':max_hours,'weeks':weeks,'max_interventions':max_interventions,'max_student_overlap':max_overlap,'strategy':strategy},'current':cur,'priority_skill':priority,'historic_intervention_count':n,'historic_intervention_gain':round(historic,1),'confidence':confidence,'best_portfolio':best,'alternatives':top,'candidate_count':len(compact),'method_note':note,'generated_at':now()}; result['scenario_id']=persist_planning_scenario(u,'portfolio_optimizer',b,result); return self.json(result)
        if p=='/api/strategy-targets':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            metric=clean_text(b.get('metric'),30).lower(); allowed={'readiness','accuracy','reading','listening','writing','speaking','risk_count'}
            try: year=int(b.get('year') or datetime.date.today().year); target=float(b.get('target_value'))
            except Exception:return self.json({'error':'invalid_payload'},400)
            if metric not in allowed or year<2020 or year>2100:return self.json({'error':'invalid_payload'},400)
            owner=int(b.get('owner_user_id') or u['id']); note=clean_text(b.get('note'),500)
            c=conn(); cur=c.execute('INSERT INTO strategic_targets(school_id,year,metric,target_value,owner_user_id,status,note,created_at,updated_at,created_by) VALUES(?,?,?,?,?,?,?,?,?,?)',(u['school_id'],year,metric,target,owner,'active',note,now(),now(),u['id'])); audit(c,u['id'],'create','strategic_target',cur.lastrowid,{'year':year,'metric':metric,'target':target}); c.commit(); tid=cur.lastrowid;c.close();return self.json({'ok':True,'id':tid},201)
        if p=='/api/governance/goals':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            title=clean_text(b.get('title'),160); metric=clean_text(b.get('metric'),30).lower(); due=clean_text(b.get('due_date'),20)
            allowed={'readiness','accuracy','reading','listening','writing','speaking','risk_count'}
            try: target=float(b.get('target_value'))
            except Exception:return self.json({'error':'invalid_target'},400)
            if not title or metric not in allowed:return self.json({'error':'invalid_payload'},400)
            reports=self.build_report(u)
            def goal_avg(vals): return round(sum(vals)/len(vals),1) if vals else 0
            if metric=='risk_count': baseline=sum(1 for r in reports if int(r.get('attempts',0) or 0)>0 and (float(r.get('readiness',0) or 0)<65 or float(r.get('accuracy',0) or 0)<60))
            elif metric=='accuracy': baseline=goal_avg([float(r.get('accuracy',0) or 0) for r in reports if int(r.get('attempts',0) or 0)>0])
            else: baseline=goal_avg([float(r.get(metric,0) or 0) for r in reports if float(r.get(metric,0) or 0)>0])
            owner=int(b.get('owner_user_id') or u['id']); c=conn(); cur=c.execute('INSERT INTO governance_goals(school_id,title,metric,target_value,baseline_value,current_value,owner_user_id,due_date,status,created_at,updated_at,created_by) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(u['school_id'],title,metric,target,baseline,baseline,owner,due,'active',now(),now(),u['id'])); audit(c,u['id'],'create','governance_goal',cur.lastrowid,{'metric':metric,'target':target,'baseline':baseline}); c.commit(); gid=cur.lastrowid;c.close();return self.json({'ok':True,'id':gid,'baseline_value':baseline},201)
        if p=='/api/governance/actions':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            try: goal_id=int(b.get('goal_id') or 0)
            except Exception:return self.json({'error':'invalid_goal'},400)
            title=clean_text(b.get('title'),180); due=clean_text(b.get('due_date'),20); expected=clean_text(b.get('expected_impact'),500)
            if not title:return self.json({'error':'invalid_payload'},400)
            c=conn(); goal=c.execute('SELECT id FROM governance_goals WHERE id=? AND school_id=?',(goal_id,u['school_id'])).fetchone()
            if not goal:c.close();return self.json({'error':'invalid_goal'},400)
            owner=int(b.get('owner_user_id') or u['id']); cur=c.execute('INSERT INTO governance_actions(goal_id,school_id,title,owner_user_id,due_date,status,expected_impact,created_at,updated_at,created_by) VALUES(?,?,?,?,?,?,?,?,?,?)',(goal_id,u['school_id'],title,owner,due,'open',expected,now(),now(),u['id'])); audit(c,u['id'],'create','governance_action',cur.lastrowid,{'goal_id':goal_id}); c.commit(); aid=cur.lastrowid;c.close();return self.json({'ok':True,'id':aid},201)
        if p=='/api/governance/review':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            try: goal_id=int(b.get('goal_id') or 0); observed=float(b.get('observed_value'))
            except Exception:return self.json({'error':'invalid_payload'},400)
            decision=clean_text(b.get('decision'),30).lower(); note=clean_text(b.get('note'),1000)
            if decision not in ('continue','close','adjust','escalate'):return self.json({'error':'invalid_decision'},400)
            c=conn(); goal=c.execute('SELECT * FROM governance_goals WHERE id=? AND school_id=?',(goal_id,u['school_id'])).fetchone()
            if not goal:c.close();return self.json({'error':'invalid_goal'},400)
            status='closed' if decision=='close' else 'active'; c.execute('UPDATE governance_goals SET current_value=?,status=?,updated_at=? WHERE id=?',(observed,status,now(),goal_id)); cur=c.execute('INSERT INTO governance_reviews(goal_id,school_id,observed_value,decision,note,created_at,created_by) VALUES(?,?,?,?,?,?,?)',(goal_id,u['school_id'],observed,decision,note,now(),u['id'])); audit(c,u['id'],'review','governance_goal',goal_id,{'observed':observed,'decision':decision}); c.commit(); rid=cur.lastrowid;c.close();return self.json({'ok':True,'review_id':rid,'goal_id':goal_id,'status':status})
        if p=='/api/governance/actions/status':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            try: aid=int(b.get('action_id') or 0)
            except Exception:return self.json({'error':'invalid_action'},400)
            status=clean_text(b.get('status'),20).lower()
            if status not in ('open','done','cancelled'):return self.json({'error':'invalid_status'},400)
            c=conn(); row=c.execute('SELECT id FROM governance_actions WHERE id=? AND school_id=?',(aid,u['school_id'])).fetchone()
            if not row:c.close();return self.json({'error':'not_found'},404)
            c.execute('UPDATE governance_actions SET status=?,updated_at=? WHERE id=?',(status,now(),aid)); audit(c,u['id'],'update','governance_action',aid,{'status':status}); c.commit(); c.close();return self.json({'ok':True,'id':aid,'status':status})
        if p=='/api/executive-review/snapshot':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            label=clean_text(b.get('period_label'),80) or now()[:10]; window=clean_text(b.get('window_type'),20).lower() or 'monthly'
            if window not in ('monthly','quarterly'):return self.json({'error':'invalid_window'},400)
            reports=self.build_report(u); skills=['reading','listening','writing','speaking']
            def avg(vals): return round(sum(vals)/len(vals),1) if vals else 0
            school={'students_total':len(reports),'students_with_data':sum(1 for r in reports if int(r.get('attempts',0) or 0)>0),'readiness':avg([float(r.get('readiness',0) or 0) for r in reports if float(r.get('readiness',0) or 0)>0]),'accuracy':avg([float(r.get('accuracy',0) or 0) for r in reports if int(r.get('attempts',0) or 0)>0])}
            for sk in skills:school[sk]=avg([float(r.get(sk,0) or 0) for r in reports if float(r.get(sk,0) or 0)>0])
            school['risk_count']=sum(1 for r in reports if int(r.get('attempts',0) or 0)>0 and (float(r.get('readiness',0) or 0)<65 or float(r.get('accuracy',0) or 0)<60))
            c=conn(); by_id={r['id']:r for r in reports}; classes=[]
            for cr in c.execute("SELECT c.id,c.name,c.teacher_id,u.name teacher_name FROM courses c LEFT JOIN users u ON u.id=c.teacher_id WHERE c.school_id=? ORDER BY c.name",(u['school_id'],)).fetchall():
                ids={x['user_id'] for x in c.execute('SELECT user_id FROM enrollments WHERE course_id=?',(cr['id'],)).fetchall()}; reps=[by_id[i] for i in ids if i in by_id]
                cm={'id':cr['id'],'name':cr['name'],'teacher':cr['teacher_name'] or 'Sin profesor','students':len(reps),'readiness':avg([float(r.get('readiness',0) or 0) for r in reps if float(r.get('readiness',0) or 0)>0]),'accuracy':avg([float(r.get('accuracy',0) or 0) for r in reps if int(r.get('attempts',0) or 0)>0])}
                for sk in skills:cm[sk]=avg([float(r.get(sk,0) or 0) for r in reps if float(r.get(sk,0) or 0)>0])
                cm['risk_count']=sum(1 for r in reps if int(r.get('attempts',0) or 0)>0 and (float(r.get('readiness',0) or 0)<65 or float(r.get('accuracy',0) or 0)<60)); classes.append(cm)
            payload={'school':school,'classes':classes}; cur=c.execute('INSERT INTO academic_review_snapshots(school_id,period_label,window_type,payload_json,created_at,created_by) VALUES(?,?,?,?,?,?)',(u['school_id'],label,window,json.dumps(payload,ensure_ascii=False),now(),u['id'])); audit(c,u['id'],'create','academic_review_snapshot',cur.lastrowid,{'period_label':label,'window_type':window}); c.commit(); sid=cur.lastrowid;c.close();return self.json({'ok':True,'id':sid,'period_label':label,'window_type':window,'payload':payload},201)
        if p=='/api/school-impact/snapshot':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            label=clean_text(b.get('period_label') or now()[:10],80)
            reports=self.build_report(u); skills=['reading','listening','writing','speaking']
            def avg(vals): return round(sum(vals)/len(vals),1) if vals else 0
            m={'students_with_data':sum(1 for r in reports if int(r.get('attempts',0) or 0)>0),'students_total':len(reports),'readiness':avg([float(r.get('readiness',0) or 0) for r in reports if float(r.get('readiness',0) or 0)>0]),'accuracy':avg([float(r.get('accuracy',0) or 0) for r in reports if int(r.get('attempts',0) or 0)>0])}
            for sk in skills:m[sk]=avg([float(r.get(sk,0) or 0) for r in reports if float(r.get(sk,0) or 0)>0])
            m['risk_count']=sum(1 for r in reports if int(r.get('attempts',0) or 0)>0 and (float(r.get('readiness',0) or 0)<65 or float(r.get('accuracy',0) or 0)<60))
            c=conn(); cur=c.execute('INSERT INTO school_quality_snapshots(school_id,period_label,metrics_json,created_at,created_by) VALUES(?,?,?,?,?)',(u['school_id'],label,json.dumps(m,ensure_ascii=False),now(),u['id'])); audit(c,u['id'],'create','school_quality_snapshot',cur.lastrowid,{'period_label':label}); c.commit(); sid=cur.lastrowid;c.close();return self.json({'ok':True,'id':sid,'period_label':label,'metrics':m},201)
        if p=='/api/interventions/evaluate':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            try: gid=int(b.get('group_id') or 0)
            except Exception:return self.json({'error':'invalid_group'},400)
            c=conn(); run=c.execute('SELECT ir.*,g.name group_name FROM intervention_runs ir JOIN support_groups g ON g.id=ir.group_id WHERE ir.group_id=? AND ir.school_id=?',(gid,u['school_id'])).fetchone()
            if not run:c.close();return self.json({'error':'not_found'},404)
            members=c.execute('SELECT * FROM intervention_run_members WHERE run_id=?',(run['id'],)).fetchall(); c.close()
            reports={r['id']:r for r in self.build_report(u)}; deltas=[]; currents=[]
            c=conn()
            for m in members:
                current=float(reports.get(m['user_id'],{}).get(run['skill'],0) or 0); delta=round(current-float(m['baseline_score'] or 0),1); currents.append(current); deltas.append(delta)
                c.execute('UPDATE intervention_run_members SET current_score=?,delta=? WHERE run_id=? AND user_id=?',(current,delta,run['id'],m['user_id']))
            current_avg=round(sum(currents)/len(currents),1) if currents else 0; rec,reason=intervention_decision(float(run['baseline_average'] or 0),current_avg,deltas); status='closed' if rec=='close' else 'active'; closed=now() if status=='closed' else None
            c.execute('UPDATE intervention_runs SET current_average=?,delta=?,recommendation=?,status=?,last_evaluated_at=?,closed_at=? WHERE id=?',(current_avg,round(current_avg-float(run['baseline_average'] or 0),1),rec,status,now(),closed,run['id']))
            c.execute('UPDATE support_groups SET status=? WHERE id=?',('closed' if status=='closed' else 'active',gid)); audit(c,u['id'],'evaluate','intervention_run',run['id'],{'group_id':gid,'recommendation':rec,'reason':reason,'current_average':current_avg}); c.commit(); c.close()
            return self.json({'ok':True,'group_id':gid,'run_id':run['id'],'baseline_average':run['baseline_average'],'current_average':current_avg,'delta':round(current_avg-float(run['baseline_average'] or 0),1),'recommendation':rec,'reason':reason,'status':status})
        if p=='/api/teacher-availability':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            try: tid=int(b.get('teacher_id') or (u['id'] if u['role']=='teacher' else 0)); weekday=int(b.get('weekday')); start=int(b.get('start_min')); end=int(b.get('end_min'))
            except Exception:return self.json({'error':'invalid_payload'},400)
            if weekday not in range(1,6) or start<0 or end>1440 or end-start<30:return self.json({'error':'invalid_payload'},400)
            c=conn(); t=c.execute("SELECT id FROM users WHERE id=? AND school_id=? AND role='teacher'",(tid,u['school_id'])).fetchone()
            if not t:c.close();return self.json({'error':'invalid_teacher'},400)
            c.execute('INSERT OR IGNORE INTO teacher_availability(school_id,teacher_id,weekday,start_min,end_min,created_at) VALUES(?,?,?,?,?,?)',(u['school_id'],tid,weekday,start,end,now()));audit(c,u['id'],'create','teacher_availability',tid,{'weekday':weekday,'start':start,'end':end});c.commit();c.close();return self.json({'ok':True},201)
        if p=='/api/schedule-planner/auto':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            try: duration=int(b.get('duration_min') or 30); sessions_per_group=int(b.get('sessions_per_group') or 2)
            except Exception:return self.json({'error':'invalid_payload'},400)
            duration=max(20,min(90,duration)); sessions_per_group=max(1,min(4,sessions_per_group)); c=conn(); groups=c.execute("SELECT g.*,c.teacher_id FROM support_groups g JOIN courses c ON c.id=g.course_id WHERE g.school_id=? AND g.status='active' ORDER BY g.id",(u['school_id'],)).fetchall(); created=[]; conflicts=[]
            # replace only planned sessions to make auto-plan idempotent
            c.execute("DELETE FROM schedule_sessions WHERE school_id=? AND status='planned'",(u['school_id'],))
            occupied=[]
            for g in groups:
                tid=g['teacher_id']
                if not tid: conflicts.append({'group_id':g['id'],'reason':'course_without_teacher'}); continue
                av=c.execute('SELECT * FROM teacher_availability WHERE school_id=? AND teacher_id=? ORDER BY weekday,start_min',(u['school_id'],tid)).fetchall()
                placed=0
                for a in av:
                    cursor=a['start_min']
                    while cursor+duration<=a['end_min'] and placed<sessions_per_group:
                        overlap=any(x['teacher_id']==tid and x['weekday']==a['weekday'] and not(cursor+duration<=x['start_min'] or cursor>=x['start_min']+x['duration_min']) for x in occupied)
                        if not overlap:
                            cur=c.execute('INSERT INTO schedule_sessions(school_id,course_id,support_group_id,teacher_id,weekday,start_min,duration_min,status,label,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)',(u['school_id'],g['course_id'],g['id'],tid,a['weekday'],cursor,duration,'planned',g['name'],now())); rec={'id':cur.lastrowid,'group_id':g['id'],'teacher_id':tid,'weekday':a['weekday'],'start_min':cursor,'duration_min':duration};occupied.append(rec);created.append(rec);placed+=1
                        cursor+=duration
                    if placed>=sessions_per_group:break
                if placed<sessions_per_group:conflicts.append({'group_id':g['id'],'reason':'insufficient_availability','placed':placed,'required':sessions_per_group})
            audit(c,u['id'],'auto_plan','schedule','',{'created':len(created),'conflicts':len(conflicts)});c.commit();c.close();return self.json({'ok':True,'created':created,'conflicts':conflicts,'feasible':not conflicts})
        if p=='/api/commercial/license':
            if not self.require_roles(u,'admin'):return self.json({'error':'forbidden'},403)
            try: sid=int(b.get('school_id') or 0); seats=int(b.get('student_seats') or 0); teacher_seats=int(b.get('teacher_seats') or 25)
            except Exception:return self.json({'error':'invalid_payload'},400)
            plan=clean_text(b.get('plan') or 'pilot',30); expires=clean_text(b.get('expires_at'),40) or None
            if plan not in LICENSE_PLANS or seats<1 or teacher_seats<1:return self.json({'error':'invalid_payload'},400)
            c=conn(); school=c.execute('SELECT id FROM schools WHERE id=?',(sid,)).fetchone()
            if not school:c.close();return self.json({'error':'invalid_school'},400)
            c.execute("UPDATE school_licenses SET status='replaced' WHERE school_id=? AND status='active'",(sid,));cur=c.execute('INSERT INTO school_licenses(school_id,plan,status,student_seats,teacher_seats,starts_at,expires_at,created_at,created_by) VALUES(?,?,?,?,?,?,?,?,?)',(sid,plan,'active',seats,teacher_seats,now(),expires,now(),u['id']));audit(c,u['id'],'create','school_license',cur.lastrowid,{'plan':plan,'student_seats':seats});c.commit();lid=cur.lastrowid;c.close();return self.json({'ok':True,'id':lid},201)
        if p=='/api/onboarding':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            key=clean_text(b.get('item_key'),60); status=clean_text(b.get('status') or 'done',20)
            allowed={'school_profile','teacher_setup','student_import','guardian_consent','first_class','first_assignment','readiness_baseline','privacy_review'}
            if key not in allowed or status not in ('pending','done'):return self.json({'error':'invalid_payload'},400)
            c=conn();c.execute('INSERT INTO onboarding_items(school_id,item_key,status,completed_at,updated_by,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(school_id,item_key) DO UPDATE SET status=excluded.status,completed_at=excluded.completed_at,updated_by=excluded.updated_by,updated_at=excluded.updated_at',(u['school_id'],key,status,now() if status=='done' else None,u['id'],now()));audit(c,u['id'],'update','onboarding',key,{'status':status});c.commit();c.close();return self.json({'ok':True})
        if p=='/api/ops/maintenance':
            if not self.require_roles(u,'admin'):return self.json({'error':'forbidden'},403)
            c=conn(); c.execute('DELETE FROM sessions WHERE expires_at<?',(now(),)); c.execute('DELETE FROM account_tokens WHERE expires_at<?',(now(),)); audit(c,u['id'],'maintenance','system','',{}); c.commit(); c.close(); cleanup_backups(); return self.json({'ok':True,'completed_at':now()})
        if p=='/api/calibration/anonymous-candidates':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            try: pred=float(b.get('predicted_readiness')); score=float(b.get('actual_scale_score'))
            except Exception:return self.json({'error':'invalid_payload'},400)
            if pred<0 or pred>100 or score<102 or score>170:return self.json({'error':'invalid_payload'},400)
            source=clean_text(b.get('source') or 'official_exam',30).lower();
            if source not in ('official_exam','external_mock'):return self.json({'error':'invalid_source'},400)
            anon=clean_text(b.get('anon_id'),80)
            c=conn()
            if not anon:
                n=c.execute('SELECT COUNT(*) n FROM anonymous_calibration_candidates WHERE school_id=?',(u['school_id'],)).fetchone()['n']+1; anon=f'Student-{n:06d}'
            band=_cambridge_band(score); exam=clean_text(b.get('exam_date'),20) or None; cohort=clean_text(b.get('cohort_label'),80) or None; notes=clean_text(b.get('notes'),500)
            c.execute('INSERT INTO anonymous_calibration_candidates(school_id,anon_id,predicted_readiness,actual_scale_score,cambridge_band,source,exam_date,cohort_label,recorded_at,recorded_by,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(school_id,anon_id) DO UPDATE SET predicted_readiness=excluded.predicted_readiness,actual_scale_score=excluded.actual_scale_score,cambridge_band=excluded.cambridge_band,source=excluded.source,exam_date=excluded.exam_date,cohort_label=excluded.cohort_label,recorded_at=excluded.recorded_at,recorded_by=excluded.recorded_by,notes=excluded.notes',(u['school_id'],anon,pred,score,band,source,exam,cohort,now(),u['id'],notes)); audit(c,u['id'],'upsert','anonymous_calibration_candidate',anon,{'band':band,'source':source}); c.commit(); c.close(); return self.json({'ok':True,'anon_id':anon,'cambridge_band':band},201)
        if p=='/api/calibration/anonymous-candidates/import':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            rows=b.get('rows') if isinstance(b.get('rows'),list) else []
            if not rows or len(rows)>2000:return self.json({'error':'invalid_payload'},400)
            c=conn(); inserted=0; errors=[]
            for i,r in enumerate(rows):
                try:
                    pred=float(r.get('predicted_readiness')); score=float(r.get('actual_scale_score')); source=clean_text(r.get('source') or 'official_exam',30).lower(); anon=clean_text(r.get('anon_id'),80) or f'Import-{int(time.time())}-{i+1:05d}'
                    if pred<0 or pred>100 or score<102 or score>170 or source not in ('official_exam','external_mock'):raise ValueError()
                    band=_cambridge_band(score); c.execute('INSERT INTO anonymous_calibration_candidates(school_id,anon_id,predicted_readiness,actual_scale_score,cambridge_band,source,exam_date,cohort_label,recorded_at,recorded_by,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(school_id,anon_id) DO UPDATE SET predicted_readiness=excluded.predicted_readiness,actual_scale_score=excluded.actual_scale_score,cambridge_band=excluded.cambridge_band,source=excluded.source,exam_date=excluded.exam_date,cohort_label=excluded.cohort_label,recorded_at=excluded.recorded_at,recorded_by=excluded.recorded_by,notes=excluded.notes',(u['school_id'],anon,pred,score,band,source,clean_text(r.get('exam_date'),20) or None,clean_text(r.get('cohort_label'),80) or None,now(),u['id'],clean_text(r.get('notes'),500))); inserted+=1
                except Exception: errors.append(i+1)
            audit(c,u['id'],'import','anonymous_calibration_candidates','',{'inserted':inserted,'errors':len(errors)}); c.commit(); c.close(); return self.json({'ok':True,'inserted':inserted,'error_rows':errors},201)
        if p=='/api/calibration/outcomes':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            try:
                student_id=int(b.get('student_id') or 0); pred=float(b.get('predicted_readiness')); score=b.get('actual_scale_score'); score=None if score in (None,'') else float(score)
            except Exception:return self.json({'error':'invalid_payload'},400)
            source=clean_text(b.get('source'),30).lower(); allowed={'official_exam','teacher_mock','external_mock'}
            if source not in allowed or pred<0 or pred>100 or (score is not None and (score<0 or score>230)):return self.json({'error':'invalid_payload'},400)
            ap=b.get('actual_pass'); actual_pass=None if ap is None else (1 if bool(ap) else 0)
            c=conn(); st=c.execute('SELECT id FROM users WHERE id=? AND school_id=? AND role="student"',(student_id,u['school_id'])).fetchone()
            if not st:c.close();return self.json({'error':'invalid_student'},400)
            cur=c.execute('INSERT INTO calibration_outcomes(school_id,student_id,source,predicted_readiness,actual_scale_score,actual_pass,exam_date,recorded_at,recorded_by,notes) VALUES(?,?,?,?,?,?,?,?,?,?)',(u['school_id'],student_id,source,pred,score,actual_pass,clean_text(b.get('exam_date'),20) or None,now(),u['id'],clean_text(b.get('notes'),500)))
            audit(c,u['id'],'create','calibration_outcome',cur.lastrowid,{'student_id':student_id,'source':source}); c.commit(); oid=cur.lastrowid;c.close();return self.json({'ok':True,'id':oid},201)
        if p=='/api/calibration/review':
            if not self.require_roles(u,'academic_reviewer','admin'):return self.json({'error':'forbidden'},403)
            name=clean_text(b.get('reviewer_name'),120); org=clean_text(b.get('organization'),160); cred=clean_text(b.get('credentials'),240); evidence=clean_text(b.get('evidence_ref'),500); decision=clean_text(b.get('decision'),20).lower(); independent=1 if b.get('independent') is True else 0
            if not name or not org or not cred or not evidence or decision not in ('approved','rejected') or not independent:return self.json({'error':'invalid_payload'},400)
            c=conn();cur=c.execute('INSERT INTO psychometric_reviews(school_id,reviewer_name,organization,credentials,independent,decision,evidence_ref,reviewed_at,recorded_by,notes) VALUES(?,?,?,?,?,?,?,?,?,?)',(u['school_id'],name,org,cred,independent,decision,evidence,now(),u['id'],clean_text(b.get('notes'),1000)));audit(c,u['id'],'create','psychometric_review',cur.lastrowid,{'decision':decision,'organization':org});c.commit();rid=cur.lastrowid;c.close();return self.json({'ok':True,'id':rid},201)
        if p=='/api/academic-errors':
            if u.get('role')!='student' and not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            student_id=u['id'] if u.get('role')=='student' else int(b.get('student_id') or 0)
            events=b.get('events') if isinstance(b.get('events'),list) else []
            if not events or len(events)>100:return self.json({'error':'invalid_payload'},400)
            c=conn(); st=c.execute('SELECT id FROM users WHERE id=? AND school_id=?',(student_id,u['school_id'])).fetchone()
            if not st:c.close();return self.json({'error':'invalid_student'},400)
            inserted=0
            for e in events:
                c.execute('INSERT INTO academic_error_events(student_id,skill,part,competence,subcompetence,error_code,severity,original_text,correction,mastery_proxy,occurred_at,source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(student_id,clean_text(e.get('skill'),20),int(e.get('part') or 0),clean_text(e.get('competence'),60),clean_text(e.get('subcompetence'),80),clean_text(e.get('error_code'),80),clean_text(e.get('severity'),20),clean_text(e.get('original_text'),500),clean_text(e.get('correction'),500),float(e.get('mastery_proxy') or 0),clean_text(e.get('occurred_at'),40) or now(),clean_text(e.get('source'),60)))
                inserted+=1
            audit(c,u['id'],'create','academic_error_events',student_id,{'count':inserted}); c.commit(); c.close();return self.json({'ok':True,'inserted':inserted},201)
        if p=='/api/mock-attempts':
            if u.get('role')!='student' and not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            student_id=u['id'] if u.get('role')=='student' else int(b.get('student_id') or 0); pack=clean_text(b.get('pack_id'),80); skill=clean_text(b.get('skill'),20); items=b.get('items') or []
            if not pack or skill not in ('reading','listening') or not isinstance(items,list) or not items:return self.json({'error':'invalid_payload'},400)
            c=conn(); st=c.execute('SELECT id FROM users WHERE id=? AND school_id=?',(student_id,u['school_id'])).fetchone()
            if not st:c.close();return self.json({'error':'invalid_student'},400)
            total=len(items); correct=sum(1 for x in items if bool(x.get('is_correct'))); pct=round(correct*100/total,1)
            cur=c.execute('INSERT INTO mock_attempts(student_id,pack_id,skill,total_items,correct_items,pct,started_at,finished_at,source) VALUES(?,?,?,?,?,?,?,?,?)',(student_id,pack,skill,total,correct,pct,clean_text(b.get('started_at'),40),now(),clean_text(b.get('source'),60) or 'v44')); aid=cur.lastrowid
            for x in items:c.execute('INSERT INTO mock_item_responses(attempt_id,student_id,pack_id,skill,part,item_id,answer_text,answer_option,is_correct,response_ms,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(aid,student_id,pack,skill,int(x.get('part') or 0),clean_text(x.get('item_id'),120),clean_text(x.get('answer_text'),300),x.get('answer_option') if isinstance(x.get('answer_option'),int) else None,1 if bool(x.get('is_correct')) else 0,int(x.get('response_ms') or 0),now()))
            audit(c,u['id'],'create','mock_attempt',aid,{'pack_id':pack,'skill':skill,'pct':pct}); c.commit(); c.close(); return self.json({'ok':True,'id':aid,'correct':correct,'total':total,'pct':pct},201)
        if p=='/api/academic-remediation':
            if u.get('role')!='student' and not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            student_id=u['id'] if u.get('role')=='student' else int(b.get('student_id') or 0)
            code=clean_text(b.get('error_code'),80); prompt=clean_text(b.get('prompt'),500); answer=clean_text(b.get('answer'),300); correct=1 if bool(b.get('correct')) else 0
            if not code or not prompt:return self.json({'error':'invalid_payload'},400)
            c=conn(); st=c.execute('SELECT id FROM users WHERE id=? AND school_id=?',(student_id,u['school_id'])).fetchone()
            if not st:c.close();return self.json({'error':'invalid_student'},400)
            cur=c.execute('INSERT INTO academic_remediation_attempts(student_id,error_code,prompt,answer,correct,attempted_at,source) VALUES(?,?,?,?,?,?,?)',(student_id,code,prompt,answer,correct,now(),clean_text(b.get('source'),60) or 'v43-remediation'))
            audit(c,u['id'],'create','academic_remediation_attempt',cur.lastrowid,{'student_id':student_id,'error_code':code,'correct':bool(correct)}); c.commit(); rid=cur.lastrowid;c.close();return self.json({'ok':True,'id':rid},201)
        if p=='/api/release-readiness/snapshot':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            # recompute through local checks without HTTP call
            c=conn(); sid=u['school_id']; lic=c.execute("SELECT * FROM school_licenses WHERE school_id=? AND status='active' ORDER BY id DESC LIMIT 1",(sid,)).fetchone(); teachers=c.execute("SELECT COUNT(*) n FROM users WHERE school_id=? AND role='teacher' AND disabled=0",(sid,)).fetchone()['n']; students=c.execute("SELECT COUNT(*) n FROM users WHERE school_id=? AND role='student' AND disabled=0",(sid,)).fetchone()['n']; courses=c.execute('SELECT COUNT(*) n FROM courses WHERE school_id=?',(sid,)).fetchone()['n']; consents=c.execute("SELECT COUNT(DISTINCT gc.student_id) n FROM guardian_consents gc JOIN users su ON su.id=gc.student_id WHERE su.school_id=? AND gc.revoked_at IS NULL",(sid,)).fetchone()['n']; c.close(); backups=sorted(BACKUP_DIR.glob('*.dump'),key=lambda x:x.stat().st_mtime,reverse=True); backup_recent=bool(backups and time.time()-backups[0].stat().st_mtime<48*3600)
            checks=[('license',bool(lic),15),('teacher',teachers>0,8),('student',students>0,8),('course',courses>0,8),('consent',students==0 or consents>=students,10),('backup',backup_recent,8),('email',email_configured() or APP_ENV!='production',8),('https',PUBLIC_BASE_URL.lower().startswith('https://') or APP_ENV!='production',10),('devmode',not DEV_MODE or APP_ENV!='production',10),('database_runtime',(APP_ENV!='production' or not REQUIRE_POSTGRES_PRODUCTION or DATABASE_ENGINE=='postgres'),15),('studio_audio',(APP_ENV!='production' or audio_quality_status()['production_ready']),12)]; score=round(sum(w for _,ok,w in checks if ok)*100/sum(w for _,_,w in checks),1); blockers=[k for k,ok,w in checks if not ok and w>=10]; warnings=[k for k,ok,w in checks if not ok and w<10]
            c=conn();cur=c.execute('INSERT INTO release_acceptance_runs(school_id,score,blockers_json,warnings_json,checks_json,created_at,created_by) VALUES(?,?,?,?,?,?,?)',(sid,score,json.dumps(blockers),json.dumps(warnings),json.dumps(checks),now(),u['id']));c.commit();rid=cur.lastrowid;c.close();return self.json({'ok':True,'id':rid,'score':score,'blockers':blockers,'warnings':warnings},201)
        if p=='/api/assignments':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            try: course_id=int(b.get('course_id') or 0)
            except Exception:return self.json({'error':'invalid_course'},400)
            title=clean_text(b.get('title'),120); skill=clean_text(b.get('skill'),20); due=clean_text(b.get('due_date'),20)
            if not title or skill not in ALLOWED_SKILLS:return self.json({'error':'invalid_payload'},400)
            c=conn(); own=c.execute('SELECT id FROM courses WHERE id=? AND school_id=?',(course_id,u['school_id'])).fetchone()
            if not own:c.close();return self.json({'error':'invalid_course'},400)
            cur=c.execute('INSERT INTO assignments(course_id,title,skill,due_date,created_at) VALUES(?,?,?,?,?)',(course_id,title,skill,due,now()));audit(c,u['id'],'create','assignment',cur.lastrowid,{'title':title});c.commit(); aid=cur.lastrowid;c.close();return self.json({'ok':True,'id':aid},201)
        if p=='/api/questions':
            if not self.require_roles(u,'teacher','school','admin'):return self.json({'error':'forbidden'},403)
            skill=clean_text(b.get('skill'),20); prompt=clean_text(b.get('prompt'),2000); options=b.get('options') or []
            if skill not in ('reading','listening') or not prompt or len(options)<2:return self.json({'error':'invalid_payload'},400)
            opts=[clean_text(x,500) for x in options[:5]]
            try: ans=int(b.get('answer_index',0)); part=int(b.get('part',1)); level=int(b.get('level',1))
            except Exception:return self.json({'error':'invalid_payload'},400)
            max_part=6 if skill=='reading' else 4
            if ans<0 or ans>=len(opts) or part<1 or part>max_part or level<1 or level>3:return self.json({'error':'invalid_payload'},400)
            c=conn();cur=c.execute('INSERT INTO questions(skill,part,level,focus,prompt,options_json,answer_index,explanation,tip,status,created_by,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(skill,part,level,clean_text(b.get('focus'),80),prompt,json.dumps(opts,ensure_ascii=False),ans,clean_text(b.get('explanation'),1200),clean_text(b.get('tip'),600),clean_text(b.get('status') or 'draft',20),u['id'],now()));audit(c,u['id'],'create','question',cur.lastrowid,{'skill':skill,'part':part});c.commit();qid=cur.lastrowid;c.close();return self.json({'ok':True,'id':qid},201)
        if p=='/api/users':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            email=clean_text(b.get('email'),180).lower(); name=clean_text(b.get('name'),120); role=clean_text(b.get('role'),20); password=str(b.get('password',''))[:256]
            try: school_id=int(b.get('school_id') or u['school_id'] or 0)
            except Exception: school_id=0
            if not valid_email(email) or not name or role not in ALLOWED_ROLES or not strong_password(password):return self.json({'error':'invalid_payload'},400)
            if u['role']=='school' and school_id!=u['school_id']:return self.json({'error':'forbidden'},403)
            if u['role']=='school' and role=='admin':return self.json({'error':'forbidden'},403)
            c=conn(); school=c.execute('SELECT id FROM schools WHERE id=?',(school_id,)).fetchone()
            if not school:c.close();return self.json({'error':'invalid_school'},400)
            lic=c.execute("SELECT * FROM school_licenses WHERE school_id=? AND status='active' ORDER BY id DESC LIMIT 1",(school_id,)).fetchone()
            if lic and role in ('student','teacher'):
                current=c.execute('SELECT COUNT(*) n FROM users WHERE school_id=? AND role=? AND disabled=0',(school_id,role)).fetchone()['n']; limit=lic['student_seats'] if role=='student' else lic['teacher_seats']
                if current>=limit:c.close();return self.json({'error':'license_seat_limit','role':role,'limit':limit},409)
            try:
                cur=c.execute('INSERT INTO users(email,password_hash,name,role,school_id,created_at) VALUES(?,?,?,?,?,?)',(email,hash_pw(password),name,role,school_id,now())); uid=cur.lastrowid
            except Exception as exc:c.rollback();c.close();return self.json({'error':'email_exists' if getattr(exc,'sqlstate',None)=='23505' else 'create_user_failed','detail':str(exc)[:180]},409 if getattr(exc,'sqlstate',None)=='23505' else 500)
            vtoken=secrets.token_urlsafe(32); c.execute('INSERT INTO account_tokens(token,user_id,kind,created_at,expires_at) VALUES(?,?,?,?,?)',(vtoken,uid,'verify',now(),iso_after(hours=VERIFY_HOURS))); audit(c,u['id'],'create','user',uid,{'role':role}); c.commit(); c.close(); resp={'ok':True,'id':uid};
            if email_configured():
                link=PUBLIC_BASE_URL.rstrip('/')+'/?verify_token='+vtoken
                resp['email_sent']=send_email(email,'PET Quest — Verifica tu cuenta',f'Verifica tu cuenta PET Quest usando este enlace (válido {VERIFY_HOURS} horas):\n\n{link}')
            if DEV_MODE:resp['dev_verification_token']=vtoken
            return self.json(resp,201)
        if p=='/api/verify-email':
            token=clean_text(b.get('token'),180); c=conn(); r=c.execute('SELECT * FROM account_tokens WHERE token=? AND kind="verify" AND used_at IS NULL',(token,)).fetchone()
            if not r:c.close();return self.json({'error':'invalid_token'},400)
            try: expired=datetime.datetime.fromisoformat(r['expires_at'])<=now_dt()
            except Exception: expired=True
            if expired:c.close();return self.json({'error':'expired_token'},400)
            c.execute('UPDATE users SET verified_at=? WHERE id=?',(now(),r['user_id'])); c.execute('UPDATE account_tokens SET used_at=? WHERE token=?',(now(),token)); audit(c,r['user_id'],'email_verified'); c.commit(); c.close(); return self.json({'ok':True})
        if p=='/api/schools':
            if not self.require_roles(u,'admin'):return self.json({'error':'forbidden'},403)
            name=clean_text(b.get('name'),160)
            if not name:return self.json({'error':'invalid_payload'},400)
            c=conn();cur=c.execute('INSERT INTO schools(name,created_at) VALUES(?,?)',(name,now()));audit(c,u['id'],'create','school',cur.lastrowid,{'name':name});c.commit();sid=cur.lastrowid;c.close();return self.json({'ok':True,'id':sid},201)
        if p=='/api/backup':
            if not self.require_roles(u,'admin'):return self.json({'error':'forbidden'},403)
            path=create_backup(); c=conn(); audit(c,u['id'],'backup_created','database',path.name,{'bytes':path.stat().st_size}); c.commit(); c.close(); return self.json({'ok':True,'name':path.name,'bytes':path.stat().st_size,'retention':BACKUP_RETENTION})
        if p=='/api/privacy/delete-request':
            note=clean_text(b.get('note'),600); c=conn(); existing=c.execute("SELECT id FROM privacy_requests WHERE user_id=? AND request_type='delete' AND status='open'",(u['id'],)).fetchone()
            if existing:c.close();return self.json({'ok':True,'id':existing['id'],'already_open':True})
            cur=c.execute('INSERT INTO privacy_requests(user_id,request_type,status,note,requested_at) VALUES(?,?,?,?,?)',(u['id'],'delete','open',note,now())); audit(c,u['id'],'privacy_delete_requested','user',u['id']); c.commit(); rid=cur.lastrowid; c.close(); return self.json({'ok':True,'id':rid},201)
        if p=='/api/privacy/rectify':
            name=clean_text(b.get('name'),120)
            if not name:return self.json({'error':'invalid_payload'},400)
            c=conn(); c.execute('UPDATE users SET name=? WHERE id=?',(name,u['id'])); cur=c.execute('INSERT INTO privacy_requests(user_id,request_type,status,note,requested_at,resolved_at,resolved_by) VALUES(?,?,?,?,?,?,?)',(u['id'],'rectify','resolved','Self-service name rectification',now(),now(),u['id'])); audit(c,u['id'],'privacy_rectified','user',u['id'],{'field':'name'}); c.commit(); rid=cur.lastrowid; c.close(); return self.json({'ok':True,'request_id':rid})
        if p=='/api/consents/revoke':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            try: student_id=int(b.get('student_id') or 0)
            except Exception:return self.json({'error':'invalid_student'},400)
            c=conn(); st=c.execute('SELECT id,school_id,role FROM users WHERE id=?',(student_id,)).fetchone()
            if not st or st['role']!='student' or (u['role']=='school' and st['school_id']!=u['school_id']):c.close();return self.json({'error':'invalid_student'},400)
            cur=c.execute('UPDATE guardian_consents SET revoked_at=? WHERE student_id=? AND revoked_at IS NULL',(now(),student_id)); audit(c,u['id'],'guardian_consent_revoked','student',student_id,{'count':cur.rowcount}); c.commit(); n=cur.rowcount; c.close(); return self.json({'ok':True,'revoked':n})
        if p=='/api/privacy/resolve':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            try: rid=int(b.get('request_id') or 0)
            except Exception:return self.json({'error':'invalid_request'},400)
            action=clean_text(b.get('action'),30); c=conn(); r=c.execute('SELECT pr.*,usr.school_id FROM privacy_requests pr JOIN users usr ON usr.id=pr.user_id WHERE pr.id=?',(rid,)).fetchone()
            if not r or (u['role']=='school' and r['school_id']!=u['school_id']):c.close();return self.json({'error':'not_found'},404)
            if r['status']!='open':c.close();return self.json({'error':'already_resolved'},409)
            if action=='approve_delete':
                uid=r['user_id'];
                c.execute('DELETE FROM snapshots WHERE user_id=?',(uid,)); c.execute('DELETE FROM guardian_consents WHERE student_id=?',(uid,)); c.execute('DELETE FROM sessions WHERE user_id=?',(uid,)); c.execute('DELETE FROM account_tokens WHERE user_id=?',(uid,)); c.execute('DELETE FROM enrollments WHERE user_id=?',(uid,)); c.execute('DELETE FROM support_group_members WHERE user_id=?',(uid,)); c.execute('DELETE FROM intervention_run_members WHERE user_id=?',(uid,)); c.execute('DELETE FROM academic_remediation_attempts WHERE student_id=?',(uid,)); c.execute('DELETE FROM academic_error_events WHERE student_id=?',(uid,)); c.execute('DELETE FROM mock_item_responses WHERE student_id=?',(uid,)); c.execute('DELETE FROM mock_attempts WHERE student_id=?',(uid,)); c.execute('DELETE FROM speaking_attempts WHERE student_id=?',(uid,)); c.execute('DELETE FROM speaking_interaction_sessions WHERE student_id=?',(uid,)); c.execute('DELETE FROM calibration_outcomes WHERE student_id=?',(uid,)); c.execute('DELETE FROM learning_events WHERE user_id=?',(uid,)); c.execute('DELETE FROM planning_scenarios WHERE created_by=?',(uid,)); c.execute("UPDATE users SET name='Deleted User',email='deleted-'||id||'@invalid.local',disabled=1,verified_at=NULL,last_login_at=NULL WHERE id=?",(uid,)); status='resolved'; note='Approved deletion/anonymization with educational evidence purge'
            elif action=='reject': status='rejected'; note='Deletion request rejected with documented reason'
            else:c.close();return self.json({'error':'invalid_action'},400)
            c.execute("UPDATE privacy_requests SET status=?,note=COALESCE(note,'')||?,resolved_at=?,resolved_by=? WHERE id=?",(status,' | '+note,now(),u['id'],rid)); audit(c,u['id'],'privacy_request_resolved','privacy_request',rid,{'action':action}); c.commit(); c.close(); return self.json({'ok':True,'status':status})
        if p=='/api/consents':
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            try: student_id=int(b.get('student_id') or 0)
            except Exception:return self.json({'error':'invalid_student'},400)
            guardian_name=clean_text(b.get('guardian_name'),120); guardian_email=clean_text(b.get('guardian_email'),180).lower(); version=clean_text(b.get('consent_version') or '2026-08',40)
            if not guardian_name or not valid_email(guardian_email):return self.json({'error':'invalid_payload'},400)
            c=conn(); st=c.execute('SELECT id,school_id,role FROM users WHERE id=?',(student_id,)).fetchone()
            if not st or st['role']!='student' or (u['role']=='school' and st['school_id']!=u['school_id']):c.close();return self.json({'error':'invalid_student'},400)
            c.execute('UPDATE guardian_consents SET revoked_at=? WHERE student_id=? AND revoked_at IS NULL',(now(),student_id))
            cur=c.execute('INSERT INTO guardian_consents(student_id,guardian_name,guardian_email,consent_version,accepted_at,recorded_by) VALUES(?,?,?,?,?,?)',(student_id,guardian_name,guardian_email,version,now(),u['id']))
            audit(c,u['id'],'guardian_consent_recorded','student',student_id,{'consent_id':cur.lastrowid,'version':version}); c.commit(); cid=cur.lastrowid;c.close();return self.json({'ok':True,'id':cid},201)
        return self.json({'error':'not_found'},404)
    def do_PATCH(self):
        p=urlparse(self.path).path; b=self.body(); u=self.auth()
        if not u:return self.json({'error':'unauthorized'},401)
        m=re.fullmatch(r'/api/users/(\d+)',p)
        if m:
            if not self.require_roles(u,'school','admin'):return self.json({'error':'forbidden'},403)
            uid=int(m.group(1)); c=conn(); target=c.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()
            if not target:c.close();return self.json({'error':'not_found'},404)
            if u['role']=='school' and target['school_id']!=u['school_id']:c.close();return self.json({'error':'forbidden'},403)
            if target['role']=='admin' and u['role']!='admin':c.close();return self.json({'error':'forbidden'},403)
            updates=[]; vals=[]
            if 'disabled' in b: updates.append('disabled=?'); vals.append(1 if b.get('disabled') else 0)
            if 'name' in b: updates.append('name=?'); vals.append(clean_text(b.get('name'),120))
            if 'role' in b:
                role=clean_text(b.get('role'),20)
                if role not in ALLOWED_ROLES or (u['role']=='school' and role=='admin'):c.close();return self.json({'error':'invalid_role'},400)
                updates.append('role=?'); vals.append(role)
            if not updates:c.close();return self.json({'error':'no_changes'},400)
            vals.append(uid); c.execute('UPDATE users SET '+','.join(updates)+' WHERE id=?',vals); audit(c,u['id'],'update','user',uid,{'fields':[x.split('=')[0] for x in updates]}); c.commit(); c.close(); return self.json({'ok':True})
        return self.json({'error':'not_found'},404)

def main():
    errors=production_startup_checks()
    if errors:
        raise SystemExit('PET Quest production startup blocked: '+ ' | '.join(errors))
    init_db()
    print('PostgreSQL runtime: primary/only database')
    if APP_ENV=='production' and known_demo_accounts_present():
        raise SystemExit('PET Quest production startup blocked: known demo account detected')
    print(f'PET Quest V{APP_VERSION} server on http://{HOST}:{PORT} [{APP_ENV}]'); ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
if __name__=='__main__':main()
