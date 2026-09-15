"""Model-first recommendations with explicit evidence and disagreement holds."""
from datetime import datetime,timezone
from .config import MODEL_VERSION,RULE_VERSION
from .model import predict_many
from .validation import input_issues,evidence_issues,risk_issues,issue


def combine(record,prediction,threshold=.75,feature_overrides=None):
    guards=input_issues(record)+evidence_issues(record)
    risks=risk_issues(record,feature_overrides)
    reference='F' if any(f['severity']=='F' for f in risks) else 'B' if risks else 'A'
    model_status=prediction['model_status']
    if prediction['confidence']<threshold:
        guards.append(issue('model_confidence','model_confidence','Model support is below the review threshold.','Review the evidence and document an underwriting assessment.','Model review'))
    if model_status!=reference:
        guards.append(issue('model_disagreement','model_prediction',f'Model class {model_status} differs from reference class {reference}.','Review the differences before a staff decision.','Model review'))
    status='B' if guards else model_status
    flags=guards+risks
    reasons=[f['reason'] for f in flags] or [f'The demo model recommends STP readiness with {prediction["confidence"]:.0%} class support; evidence checks are complete.']
    return {'app_id':record.get('app_id'),'status':status,**prediction,'reference_status':reference,'reasons':reasons,'flags':flags,
        'reason_summary':'; '.join(reasons),'flag_count':len(flags),'evidence_gap_count':sum(f['category'] in {'Evidence','Data quality','Governance'} for f in guards),
        'stp_eligible':status=='A','model_version':MODEL_VERSION,'rule_version':RULE_VERSION,
        'evaluated_at':datetime.now(timezone.utc).isoformat(timespec='seconds')}

def assess_many(records,threshold=.75,feature_overrides=None):
    if not records:return []
    try: predictions=predict_many(records)
    except (RuntimeError,OSError,ValueError) as exc:
        return [{'app_id':r.get('app_id'),'status':'B','model_status':'Unavailable','confidence':0.,'probabilities':{},'reference_status':'Not evaluated','reasons':[str(exc)],'flags':[issue('model_unavailable','model',str(exc),'Restore the model before evaluating this application.','Model review')],'reason_summary':str(exc),'flag_count':1,'evidence_gap_count':0,'stp_eligible':False,'model_version':MODEL_VERSION,'rule_version':RULE_VERSION,'evaluated_at':datetime.now(timezone.utc).isoformat(timespec='seconds')} for r in records]
    return [combine(r,p,threshold,feature_overrides) for r,p in zip(records,predictions)]

def assess_application(record,threshold=.75,feature_overrides=None):
    return assess_many([record],threshold,feature_overrides)[0]
