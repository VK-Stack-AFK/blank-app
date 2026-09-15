"""Reproducible random-forest prototype, synthetic labels and held-out evaluation."""
from functools import lru_cache
from pathlib import Path
import gzip
import hashlib
import json
import os
import time
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score,classification_report,confusion_matrix,f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from .config import MODEL_VERSION,RULE_VERSION
from .validation import normalize_record,reference_recommendation

ROOT=Path(__file__).resolve().parent.parent
MODEL_DIR=ROOT/'models'
DATASET_PATH=ROOT/'data'/'ml'/'homeowners_synthetic_10000.csv.gz'
NUMERIC=['year_built','square_footage','roof_age','water_heater_age','distance_fire_station','vacant_days','coverage_lapse_days','prior_claim_count_5y','water_claim_count_5y','open_claims','wildfire_score','wind_hail_score','loss_ratio','coverage_to_rc_ratio']
CATEGORICAL=['occupancy','roof_material','roof_shape','roof_condition_ai','construction_type','foundation_type','electrical_type','electrical_panel','plumbing_type','heating_type','roof_leaks','unrepaired_damage','short_term_rental','business_use','renovation_in_progress','trampoline','animal_bite_history','prior_flooding','prior_nonrenewal','smoke_alarms','pool','pool_fenced','diving_board','solid_fuel_stove','stove_professional_install','dwelling_type','policy_form','ownership_type','flood_zone']
FEATURES=NUMERIC+CATEGORICAL
CLASSES=['A','B','F']

def feature_frame(records):
    df=pd.DataFrame([normalize_record(r) for r in records]).reindex(columns=FEATURES)
    for key in NUMERIC: df[key]=pd.to_numeric(df[key],errors='coerce').replace([np.inf,-np.inf],np.nan)
    for key in CATEGORICAL: df[key]=df[key].fillna('Unknown').astype(str)
    return df

def train_model():
    from .synthetic import generate_dataset,AS_OF
    started=time.monotonic()
    data=generate_dataset(10000,42)
    labels=[reference_recommendation(r,include_evidence=False,as_of=AS_OF)['status'] for r in data.to_dict('records')]
    data['reference_label']=labels
    X=feature_frame(data.to_dict('records')); y=pd.Series(labels)
    train,test=train_test_split(np.arange(len(data)),test_size=.2,random_state=42,stratify=y)
    data['dataset_split']='train'; data.loc[test,'dataset_split']='test'
    prep=ColumnTransformer([('numeric',SimpleImputer(strategy='median'),NUMERIC),('category',OneHotEncoder(handle_unknown='ignore',sparse_output=False),CATEGORICAL)])
    estimator=Pipeline([('prepare',prep),('forest',RandomForestClassifier(n_estimators=160,max_depth=None,min_samples_leaf=2,max_features=.75,class_weight='balanced',random_state=42,n_jobs=1))])
    estimator.fit(X.iloc[train],y.iloc[train])
    predictions=estimator.predict(X.iloc[test])
    names=estimator.named_steps['prepare'].get_feature_names_out()
    importance={key:0. for key in FEATURES}
    for name,value in zip(names,estimator.named_steps['forest'].feature_importances_):
        stripped=name.split('__',1)[1]
        key=next((k for k in sorted(FEATURES,key=len,reverse=True) if stripped==k or stripped.startswith(k+'_')),None)
        if key: importance[key]+=float(value)
    raw=data.to_csv(index=False).encode()
    DATASET_PATH.parent.mkdir(parents=True,exist_ok=True); DATASET_PATH.write_bytes(gzip.compress(raw,mtime=0))
    MODEL_DIR.mkdir(parents=True,exist_ok=True)
    metadata={'model_version':MODEL_VERSION,'rule_version':RULE_VERSION,'algorithm':'RandomForestClassifier','dataset_rows':10000,'train_rows':len(train),'test_rows':len(test),'seed':42,
        'scenario_as_of':AS_OF.isoformat(),'hyperparameters':estimator.named_steps['forest'].get_params(),
        'data_provenance':'Synthetic scenarios. Labels generated from HomeGuard POC reference rules; not historical underwriting outcomes.',
        'confidence_note':'Class probabilities are model support, not calibrated real-world underwriting confidence.',
        'accuracy':float(accuracy_score(y.iloc[test],predictions)),'macro_f1':float(f1_score(y.iloc[test],predictions,average='macro')),
        'classification_report':classification_report(y.iloc[test],predictions,labels=CLASSES,output_dict=True,zero_division=0),
        'confusion_matrix':confusion_matrix(y.iloc[test],predictions,labels=CLASSES).tolist(),'classes':CLASSES,'class_counts':y.value_counts().to_dict(),
        'feature_importance':dict(sorted(importance.items(),key=lambda x:x[1],reverse=True)),'features':FEATURES,
        'excluded_inputs':['name','email','phone','street address','ZIP code','state','protected characteristics','reference label','dataset split','application ID','verification status'],
        'dataset_sha256':hashlib.sha256(raw).hexdigest(),'sklearn_version':sklearn.__version__,'training_seconds':round(time.monotonic()-started,3)}
    joblib.dump(estimator,MODEL_DIR/'homeowners_demo.joblib',compress=3)
    metadata['artifact_sha256']=hashlib.sha256((MODEL_DIR/'homeowners_demo.joblib').read_bytes()).hexdigest()
    (MODEL_DIR/'metadata.json').write_text(json.dumps(metadata,indent=2))
    _load_model.cache_clear()
    return metadata

def load_model():
    model_path=MODEL_DIR/'homeowners_demo.joblib'; metadata_path=MODEL_DIR/'metadata.json'
    if not model_path.exists() or not metadata_path.exists():
        raise RuntimeError('Demo model is unavailable. Run python -m homeguard.model to rebuild it.')
    return _load_model(model_path.stat().st_mtime_ns,metadata_path.stat().st_mtime_ns)

@lru_cache(maxsize=1)
def _load_model(artifact_modified,metadata_modified):
    model_path=MODEL_DIR/'homeowners_demo.joblib'; metadata_path=MODEL_DIR/'metadata.json'
    metadata=json.loads(metadata_path.read_text())
    if not isinstance(metadata,dict) or not {'sklearn_version','artifact_sha256','model_version'}<=metadata.keys():
        raise RuntimeError('Model metadata is incomplete. Rebuild the demo model.')
    if metadata['sklearn_version']!=sklearn.__version__:
        raise RuntimeError('Model/library versions differ. Install the pinned requirements or rebuild the demo model.')
    if hashlib.sha256(model_path.read_bytes()).hexdigest()!=metadata['artifact_sha256']:
        raise RuntimeError('Model artifact checksum does not match its metadata. Rebuild the model.')
    return joblib.load(model_path),metadata

def predict_many(records):
    if not records: return []
    estimator,metadata=load_model()
    probability=estimator.predict_proba(feature_frame(records))
    classes=estimator.classes_
    return [{'model_status':str(classes[np.argmax(p)]),'confidence':float(max(p)),'probabilities':{str(c):float(v) for c,v in zip(classes,p)},'model_artifact_sha256':metadata['artifact_sha256']} for p in probability]

if __name__=='__main__':
    m=train_model(); print(json.dumps({k:m[k] for k in ['dataset_rows','train_rows','test_rows','class_counts','accuracy','macro_f1','training_seconds']},indent=2))
