from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import pytest
from homeguard.prediction import assess_application
from homeguard.storage import save_application,load_applications,save_decision,load_decisions,load_events,new_application_id,get_settings,save_settings,RevisionConflict,safe_csv
from homeguard.portfolio import load_portfolio,evaluate_records,portfolio_metrics
from homeguard.synthetic import evidence_gap_example


def test_unique_ids_and_zero_preserving_roundtrip(complete_home):
    assert len({new_application_id() for _ in range(2000)})==2000
    complete_home.update(app_id=None,zip_code='06067')
    saved=save_application(complete_home,assessment=assess_application(complete_home))
    loaded=load_applications()[0]
    assert loaded['zip_code']=='06067' and loaded['app_id']==saved['app_id']
    assert len(load_events(saved['app_id']))==1

def test_evidence_recovery_and_manual_decisions_are_distinct():
    home=evidence_gap_example()
    first=save_application(home,assessment=assess_application(home))
    first.update(hazard_verification='Verified',hazard_document_reference='DEMO-ONLY/reviewed')
    second=save_application(first,assessment=assess_application(first),expected_revision=1)
    rows=evaluate_records(load_portfolio(['Submission']))
    metrics=portfolio_metrics(rows)
    assert metrics['stp_ready']==1 and metrics['evidence_recovered']==1
    save_decision(second['app_id'],'A','Demo underwriter','Evidence reviewed',2)
    rows=evaluate_records(load_portfolio(['Submission']))
    assert rows[0]['effective_status']=='A' and rows[0]['decision']['reviewer']=='Demo underwriter'
    metrics=portfolio_metrics(rows)
    assert metrics['stp_ready']==0 and metrics['staff_cleared']==1 and metrics['evidence_recovered']==0
    record=load_applications()[0]
    assert record['_revision']==3
    save_application(record,assessment=assess_application(record),expected_revision=3)
    assert not load_decisions()
    assert any(e['event_type']=='underwriter_decision' for e in load_events(second['app_id']))

def test_stale_edits_and_decisions_do_not_overwrite(complete_home):
    home=save_application(complete_home)
    save_decision(home['app_id'],'B','Reviewer','Need an inspection',1)
    with pytest.raises(RevisionConflict): save_application(home,expected_revision=1)
    with pytest.raises(RevisionConflict): save_decision(home['app_id'],'A','Other reviewer','Outdated review',1)
    assert load_decisions()[home['app_id']]['status']=='B'

def test_concurrent_new_submissions_and_optimistic_edits(complete_home):
    def create(index): return save_application({**complete_home,'app_id':f'CONCURRENT-{index}'})
    with ThreadPoolExecutor(max_workers=4) as pool: list(pool.map(create,range(12)))
    assert len(load_applications())==12
    def edit(index):
        try:
            save_application({**complete_home,'app_id':'CONCURRENT-0','underwriting_notes':str(index)},expected_revision=1)
            return True
        except RevisionConflict: return False
    with ThreadPoolExecutor(max_workers=4) as pool: successes=list(pool.map(edit,range(4)))
    assert sum(successes)==1

def test_source_date_filtering_and_overlay_dedup(tmp_path,complete_home):
    data=tmp_path/'data';data.mkdir()
    sample={**complete_home,'app_id':'SAMPLE-1','submission_date':'2026-08-10T12:00:00Z'}
    pd.DataFrame([sample,sample]).to_csv(data/'applications.csv',index=False)
    save_application({**sample,'underwriting_notes':'Overlay'},'Demo portfolio')
    save_application({**complete_home,'app_id':'S2','submission_date':'2026-09-14T12:00:00Z'},'Submission')
    assert load_portfolio([],root=tmp_path)==[]
    rows=load_portfolio(['Demo portfolio'],root=tmp_path)
    assert len(rows)==1 and rows[0]['underwriting_notes']=='Overlay'
    from datetime import date
    filtered=load_portfolio(['Demo portfolio','Submission'],date(2026,9,1),date(2026,9,15),tmp_path)
    assert [r['app_id'] for r in filtered]==['S2']

def test_settings_are_persistent_and_validated():
    save_settings({'test_mode_enabled':False,'model_confidence_threshold':.8},'Demo admin')
    assert get_settings()['test_mode_enabled'] is False
    assert get_settings()['model_confidence_threshold']==.8
    with pytest.raises(ValueError): save_settings({'model_confidence_threshold':1.2},'Demo admin')

def test_csv_formula_injection_is_escaped():
    csv=safe_csv(pd.DataFrame({'name':['=cmd()','+SUM(A1)','@hello','normal'],'zip':['06067']*4}))
    assert "'=cmd()" in csv and "'+SUM(A1)" in csv and '06067' in csv
