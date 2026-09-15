from copy import deepcopy
from datetime import date,timedelta
import pytest
from homeguard.config import FEATURE_FLAGS
from homeguard.schema import REQUIRED_FIELDS
from homeguard.validation import input_issues,risk_issues,normalize_record,reference_recommendation
from homeguard.prediction import assess_application,combine
from homeguard.synthetic import evidence_gap_example,synthetic_application

@pytest.mark.parametrize('key',REQUIRED_FIELDS)
def test_absent_required_field_never_clears_stp(complete_home,key):
    complete_home.pop(key)
    assert assess_application(complete_home)['status']=='B'

@pytest.mark.parametrize('key,value',[
    ('roof_age',-1),('roof_age',1.5),('roof_age',float('inf')),('wind_hail_score',101),
    ('estimated_replacement_cost',0),('prior_claim_count_5y','garbage'),('roof_age','nan'),
    ('year_built',4000),('zip_code','123'),('applicant_email','bademail'),('state','ZZ'),
    ('verification_date',(date.today()+timedelta(days=1)).isoformat()),
])
def test_invalid_inputs_hold_review(complete_home,key,value):
    complete_home[key]=value
    assert input_issues(complete_home)
    assert assess_application(complete_home)['status']=='B'

@pytest.mark.parametrize('ratio,expected',[(.2499,'A'),(.25,'B'),(.75,'B'),(.7501,'F')])
def test_claims_ratio_reference_boundaries(complete_home,ratio,expected):
    complete_home.update(prior_claim_count_5y=1,estimated_replacement_cost=1000000,requested_dwelling_limit=1000000,claim_total_paid_5y=ratio*1000000,loss_details='Synthetic loss reviewed')
    assert reference_recommendation(complete_home)['status']==expected

def test_supplied_derived_ratio_cannot_override_paid_claims(complete_home):
    complete_home.update(prior_claim_count_5y=1,claim_total_paid_5y=1000000,estimated_replacement_cost=500000,loss_ratio=0,loss_details='Reviewed')
    assert normalize_record(complete_home)['loss_ratio']==2
    assert reference_recommendation(complete_home)['status']=='F'

def test_none_alarm_response_is_a_known_choice(complete_home):
    complete_home['burglar_alarm']='None'
    assert normalize_record(complete_home)['burglar_alarm']=='None'

def test_independent_feature_overrides(complete_home):
    before=deepcopy(FEATURE_FLAGS)
    complete_home.update(prior_claim_count_5y=4,claim_total_paid_5y=1000,loss_details='Reviewed')
    assert any(f['severity']=='F' for f in risk_issues(complete_home))
    assert not any(f['code']=='claim_frequency' for f in risk_issues(complete_home,{'check_claims_count':False}))
    assert FEATURE_FLAGS==before

def test_evidence_gap_can_resolve_to_a():
    home=evidence_gap_example()
    initial=assess_application(home)
    assert initial['status']=='B' and initial['model_status']=='A'
    home.update(hazard_verification='Verified',hazard_document_reference='DEMO-ONLY/reviewed')
    assert assess_application(home)['status']=='A'

def test_verification_requires_reference_reviewer_and_date(complete_home):
    for key in ['property_document_reference','verification_reviewer','verification_date']:
        record={**complete_home,key:None}
        assert assess_application(record)['status']=='B'

def test_disagreement_and_low_support_hold_b(complete_home):
    assert combine(complete_home,{'model_status':'F','confidence':.99,'probabilities':{'F':.99}})['status']=='B'
    assert combine(complete_home,{'model_status':'A','confidence':.5,'probabilities':{'A':.5}})['status']=='B'

def test_f_is_recommendation_with_reference_evidence():
    result=assess_application(synthetic_application(3,'F',900))
    assert result['status']=='F'
    assert result['stp_eligible'] is False
    assert result['reference_status']=='F'

def test_model_failure_never_approves(monkeypatch,complete_home):
    def broken(_): raise RuntimeError('Model is unavailable')
    monkeypatch.setattr('homeguard.prediction.predict_many',broken)
    result=assess_application(complete_home)
    assert result['status']=='B' and result['model_status']=='Unavailable'
