"""Transactional POC records, review decisions, settings, and audit events."""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import sqlite3
import uuid
import pandas as pd
from .config import DEFAULT_SETTINGS, SCHEMA_VERSION

class RevisionConflict(ValueError): pass

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def new_application_id(): return 'HG-'+uuid.uuid4().hex[:16].upper()
def data_dir(): return Path(os.environ.get('HOMEGUARD_DATA_DIR',Path(__file__).resolve().parent.parent/'data'/'runtime'))

@contextmanager
def connection():
    folder=data_dir(); folder.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(folder/'homeguard.sqlite3',timeout=20)
    con.row_factory=sqlite3.Row
    try:
        con.execute('PRAGMA journal_mode=WAL')
        con.executescript('''
        CREATE TABLE IF NOT EXISTS applications(app_id TEXT PRIMARY KEY, payload TEXT NOT NULL, source TEXT NOT NULL, revision INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS decisions(app_id TEXT PRIMARY KEY, status TEXT NOT NULL, reviewer TEXT NOT NULL, rationale TEXT NOT NULL, decided_at TEXT NOT NULL, revision INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS events(event_id TEXT PRIMARY KEY, app_id TEXT NOT NULL, event_type TEXT NOT NULL, actor TEXT NOT NULL, at TEXT NOT NULL, detail TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        ''')
        with con: yield con
    finally: con.close()

def _json(value): return json.dumps(value,default=str,allow_nan=False)
def _event(con,app_id,kind,actor,detail):
    con.execute('INSERT INTO events VALUES(?,?,?,?,?,?)',(uuid.uuid4().hex,app_id,kind,actor,now(),_json(detail)))

def save_application(payload,source='Submission',actor='Intake',assessment=None,expected_revision=None):
    record=dict(payload)
    app_id=record.get('app_id') or new_application_id()
    record['app_id']=app_id
    record['schema_version']=SCHEMA_VERSION
    record.pop('_revision',None)
    with connection() as con:
        con.execute('BEGIN IMMEDIATE')
        old=con.execute('SELECT * FROM applications WHERE app_id=?',(app_id,)).fetchone()
        revision=old['revision'] if old else 0
        if expected_revision is not None and expected_revision!=revision:
            raise RevisionConflict('This application was updated in another session. Refresh and review the latest version.')
        previous=json.loads(old['payload']) if old else {}
        record['submission_date']=previous.get('submission_date') or record.get('submission_date') or now()
        record['initial_status']=previous.get('initial_status') or record.get('initial_status') or (assessment or {}).get('status','B')
        record['data_source']=old['source'] if old else source
        if assessment: record['last_assessment']=assessment
        con.execute('INSERT INTO applications VALUES(?,?,?,?) ON CONFLICT(app_id) DO UPDATE SET payload=excluded.payload,source=excluded.source,revision=excluded.revision',(app_id,_json(record),record['data_source'],revision+1))
        con.execute('DELETE FROM decisions WHERE app_id=?',(app_id,))
        changed={k:{'before':previous.get(k),'after':v} for k,v in record.items() if previous.get(k)!=v and k not in {'last_assessment'}}
        _event(con,app_id,'application_updated' if old else 'application_created',actor,{'changes':changed,'assessment':assessment,'revision':revision+1})
    return {**record,'_revision':revision+1}

def load_applications():
    with connection() as con:
        return [{**json.loads(r['payload']),'_revision':r['revision']} for r in con.execute('SELECT * FROM applications')]

def save_decision(app_id,status,reviewer,rationale,expected_revision):
    if status not in {'A','B','F'}: raise ValueError('Unsupported decision.')
    if not reviewer.strip() or not rationale.strip(): raise ValueError('Reviewer and decision rationale are required.')
    with connection() as con:
        con.execute('BEGIN IMMEDIATE')
        row=con.execute('SELECT revision FROM applications WHERE app_id=?',(app_id,)).fetchone()
        if not row or row['revision']!=expected_revision: raise RevisionConflict('Refresh the application before recording a decision.')
        revision=expected_revision+1
        con.execute('UPDATE applications SET revision=? WHERE app_id=?',(revision,app_id))
        con.execute('INSERT INTO decisions VALUES(?,?,?,?,?,?) ON CONFLICT(app_id) DO UPDATE SET status=excluded.status,reviewer=excluded.reviewer,rationale=excluded.rationale,decided_at=excluded.decided_at,revision=excluded.revision',(app_id,status,reviewer.strip(),rationale.strip(),now(),revision))
        _event(con,app_id,'underwriter_decision',reviewer.strip(),{'status':status,'rationale':rationale.strip(),'application_revision':revision})

def load_decisions():
    with connection() as con: return {r['app_id']:dict(r) for r in con.execute('SELECT * FROM decisions')}

def load_events(app_id=None):
    with connection() as con:
        rows=con.execute('SELECT * FROM events WHERE app_id=? ORDER BY at DESC,rowid DESC',(app_id,)) if app_id else con.execute('SELECT * FROM events ORDER BY at DESC,rowid DESC LIMIT 2000')
        return [{**dict(r),'detail':json.loads(r['detail'])} for r in rows]

def get_settings():
    with connection() as con: return {**DEFAULT_SETTINGS,**{r['key']:json.loads(r['value']) for r in con.execute('SELECT * FROM settings')}}

def save_settings(values,actor):
    allowed={k:v for k,v in values.items() if k in DEFAULT_SETTINGS}
    for key,value in allowed.items():
        if key=='model_confidence_threshold':
            if not isinstance(value,(float,int)) or isinstance(value,bool) or not .5 <= value <= .99:
                raise ValueError('Model support threshold must be between 0.50 and 0.99.')
        elif not isinstance(value,bool): raise ValueError(f'{key} must be a boolean.')
    with connection() as con:
        for key,value in allowed.items(): con.execute('INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(key,_json(value)))
        _event(con,'SYSTEM','settings_updated',actor,allowed)

def safe_csv(df):
    out=df.copy()
    for col in out.columns:
        out[col]=out[col].map(lambda v: "'"+v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@','\t','\r')) else v)
    return out.to_csv(index=False)
