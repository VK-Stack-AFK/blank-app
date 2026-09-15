"""Generate the standalone demo portfolio, separate from ML train/test data."""
from pathlib import Path
import pandas as pd
from .synthetic import generate_dataset
from .prediction import assess_many


def generate_applications(count=1000):
    data=generate_dataset(count,seed=2026)
    # Include otherwise-clear homes with resolvable verification gaps.
    for index in range(0,count,10):
        data.loc[index,'hazard_verification']='Not checked'
        data.loc[index,'hazard_document_reference']=''
    records=data.to_dict('records')
    assessments=assess_many(records)
    data['initial_status']=[r['status'] for r in assessments]
    return data

if __name__=='__main__':
    path=Path(__file__).resolve().parent.parent/'data'/'applications.csv'
    frame=generate_applications();frame.to_csv(path,index=False)
    print(f'Saved {len(frame):,} synthetic portfolio records; initial routes: {frame.initial_status.value_counts().to_dict()}')
