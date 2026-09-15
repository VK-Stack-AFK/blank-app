import gzip
import hashlib
import json
import numpy as np
import pandas as pd
from homeguard.model import load_model,DATASET_PATH,MODEL_DIR,feature_frame,FEATURES,predict_many
from homeguard.synthetic import generate_dataset,synthetic_application
from sklearn.metrics import accuracy_score,confusion_matrix


def test_committed_dataset_and_holdout_measurements_match():
    raw=gzip.decompress(DATASET_PATH.read_bytes())
    data=pd.read_csv(DATASET_PATH,dtype={'zip_code':str})
    estimator,metadata=load_model()
    assert len(data)==10000 and data.app_id.nunique()==10000
    assert data.dataset_split.value_counts().to_dict()=={'train':8000,'test':2000}
    assert hashlib.sha256(raw).hexdigest()==metadata['dataset_sha256']
    assert hashlib.sha256((MODEL_DIR/'homeowners_demo.joblib').read_bytes()).hexdigest()==metadata['artifact_sha256']
    heldout=data[data.dataset_split=='test']
    predictions=estimator.predict(feature_frame(heldout.to_dict('records')))
    assert accuracy_score(heldout.reference_label,predictions)==metadata['accuracy']
    assert confusion_matrix(heldout.reference_label,predictions,labels=['A','B','F']).tolist()==metadata['confusion_matrix']
    assert sum(metadata['class_counts'].values())==10000
    assert set(data.state)==set('AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC'.split())

def test_features_exclude_identity_labels_and_split(complete_home):
    altered={**complete_home,'applicant_name':'Different','applicant_email':'other@example.com','zip_code':'99999','state':'AK','reference_label':'F','dataset_split':'test','app_id':'SECRET'}
    assert feature_frame([complete_home]).equals(feature_frame([altered]))
    assert predict_many([complete_home])==predict_many([altered])
    assert not {'applicant_name','applicant_email','zip_code','state','reference_label','dataset_split','app_id'} & set(FEATURES)

def test_synthetic_generation_is_deterministic():
    assert generate_dataset(100,42).equals(generate_dataset(100,42))
    assert not generate_dataset(100,42).equals(generate_dataset(100,43))
    assert synthetic_application(5,'B',42)==synthetic_application(5,'B',42)
