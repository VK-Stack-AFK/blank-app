"""Compatibility adapters; new writes are transactional and CSVs stay read-only."""
from datetime import datetime,timedelta,timezone
import pandas as pd
from .portfolio import load_portfolio
from .prediction import assess_application
from .storage import save_application,get_settings
from .validation import normalize_record


def save_submission(app_data):
    record=normalize_record(app_data)
    return save_application(record,'Submission','Intake',assess_application(record,get_settings()['model_confidence_threshold']))

def load_submissions(include_recent=True,include_older=False,specific_date=None):
    if not (include_recent or include_older or specific_date): return pd.DataFrame()
    rows=load_portfolio(['Submission','Legacy submission'])
    cutoff=datetime.now(timezone.utc).date()-timedelta(days=30)
    result=[]
    for row in rows:
        time=pd.to_datetime(row.get('submission_date'),utc=True,errors='coerce')
        if pd.isna(time): continue
        day=time.date()
        if specific_date:
            if day.isoformat()!=str(specific_date)[:10]: continue
        elif not ((include_recent and day>=cutoff) or (include_older and day<cutoff)): continue
        result.append(row)
    return pd.DataFrame(result)

def get_available_dates():
    frame=load_submissions(True,True)
    return sorted(set(str(x)[:10] for x in frame.get('submission_date',[])),reverse=True)

def get_recent_submission_count(): return len(load_submissions())
