"""A single, filtered portfolio with durable application/decision overlays."""
from datetime import date
from pathlib import Path
import pandas as pd
from .config import STATUS_LABELS
from .prediction import assess_many
from .storage import load_applications, load_decisions
from .validation import normalize_record

ROOT=Path(__file__).resolve().parent.parent
SOURCES=('Demo portfolio','Demo application','Submission','Legacy submission')

def csv_records(path,source):
    if not path.exists(): return []
    frame=pd.read_csv(path,dtype={'app_id':str,'zip_code':str}).astype(object)
    frame=frame.where(pd.notna(frame),None)
    records=[]
    for index,row in enumerate(frame.to_dict('records')):
        r=normalize_record(row)
        r.update(data_source=source,_revision=0)
        r['app_id']=r.get('app_id') or f'LEGACY-{path.stem}-{index+1}'
        # Original rule-only approval is not evidence of model/STP readiness.
        r['initial_status']=r.get('initial_status') or 'B'
        records.append(r)
    return records

def load_portfolio(sources=None,start_date=None,end_date=None,root=ROOT):
    selected=set(SOURCES if sources is None else sources)
    records={}
    if 'Demo portfolio' in selected:
        for r in csv_records(root/'data'/'applications.csv','Demo portfolio'): records[r['app_id']]=r
    if 'Legacy submission' in selected:
        for path in sorted((root/'data'/'submissions').glob('*/applications_*.csv')):
            for r in csv_records(path,'Legacy submission'): records[r['app_id']]=r
    for r in load_applications():
        if r['data_source'] in selected: records[r['app_id']]=r
        else: records.pop(r['app_id'],None)
    result=[]
    for r in records.values():
        timestamp=pd.to_datetime(r.get('submission_date'),utc=True,errors='coerce')
        day=None if pd.isna(timestamp) else timestamp.date()
        if (start_date or end_date) and day is None: continue
        if start_date and day<start_date: continue
        if end_date and day>end_date: continue
        result.append(r)
    return sorted(result,key=lambda r:str(r.get('submission_date') or ''),reverse=True)

def evaluate_records(records,threshold=.75):
    decisions=load_decisions()
    results=assess_many(records,threshold)
    evaluated=[]
    for record,result in zip(records,results):
        decision=decisions.get(record['app_id'])
        if decision and decision['revision']!=record.get('_revision',0): decision=None
        evaluated.append({**record,**result,'decision':decision,'effective_status':decision['status'] if decision else result['status'],
                          'initial_status':record.get('initial_status') or result['status']})
    return evaluated

def portfolio_metrics(rows):
    """Current automation excludes every case with a human disposition."""
    count=len(rows)
    stp=sum(r['status']=='A' and not r.get('decision') for r in rows)
    return {'applications':count,'stp_ready':stp,'stp_rate':stp/count if count else 0,
            'evidence_recovered':sum(r.get('initial_status')=='B' and r.get('_revision',0)>0 and r['status']=='A' and not r.get('decision') for r in rows),
            'staff_cleared':sum(bool(r.get('decision')) and r['decision']['status']=='A' for r in rows),
            'review':sum(r['effective_status']=='B' for r in rows),
            'rejection_recommendations':sum(r['status']=='F' and not r.get('decision') for r in rows)}

def summary_frame(rows):
    return pd.DataFrame([{'Application ID':r['app_id'],'Named insured':r.get('applicant_name',''),
        'State':r.get('state',''),'Source':r['data_source'],'Submitted':str(r.get('submission_date') or '')[:10],
        'Current outcome':('Staff · ' if r.get('decision') else '')+STATUS_LABELS[r['effective_status']],
        'Model class':r['model_status'],'Model support':round(r['confidence'],3),
        'Evidence / data gaps':r['evidence_gap_count'],'Findings':r['flag_count'],
        'Roof age':r.get('roof_age'),'Dwelling limit':r.get('requested_dwelling_limit')} for r in rows])
