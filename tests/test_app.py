from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from homeguard.storage import load_applications,load_decisions,get_settings
from homeguard.schema import VERIFICATION_FIELDS

ROOT=Path(__file__).resolve().parent.parent

def app(page=None,staff=False):
    at=AppTest.from_file(str(ROOT/'streamlit_app.py'),default_timeout=40)
    if staff:
        at.session_state.staff_authenticated=True
        at.session_state.staff_name='Demo reviewer'
    at.run()
    if page: at.switch_page(page).run()
    return at

def button(at,label): return next(b for b in at.button if b.label==label)

@pytest.mark.parametrize('page',[
    None,'pages/1_New_Application.py','pages/2_Settings.py','pages/3_Dashboard.py',
    'pages/4_Industry.py','pages/5_User_Guide.py','pages/6_Model_Lab.py',
])
def test_all_pages_render(page):
    at=app(page,True)
    assert not at.exception

def test_workbench_requires_staff_by_default():
    at=app('pages/3_Dashboard.py')
    assert not at.exception
    assert any(t.label=='Password' for t in at.text_input)
    assert not at.get('dataframe')

def test_end_to_end_evidence_review_and_decision():
    at=app('pages/1_New_Application.py',True)
    button(at,'B · missing evidence').click().run()
    # Edit different tabs together to catch overwriting during collection.
    at.text_input(key='intake_applicant_name').set_value('Demo insured edited')
    at.number_input(key='intake_all_peril_deductible').set_value(2500)
    button(at,'Save draft').click().run()
    at.switch_page('pages/0_Overview.py').run()
    at.switch_page('pages/1_New_Application.py').run()
    assert at.text_input(key='intake_applicant_name').value=='Demo insured edited'
    assert at.number_input(key='intake_all_peril_deductible').value==2500
    button(at,'Analyze & submit application').click().run()
    assert not at.exception
    saved=load_applications()[0]
    assert saved['applicant_name']=='Demo insured edited'
    assert saved['last_assessment']['status']=='B'
    button(at,'View the underwriting workbench').click().run()
    assert not at.exception
    assert any(t.value=='Underwriting workbench' for t in at.title)
    # AppTest does not update its next-run page hash after in-app switch_page.
    # Pin the destination for subsequent simulated widget interactions.
    at.switch_page('pages/3_Dashboard.py').run()
    prefix=f'review_{saved["app_id"]}_1_'
    at.selectbox(key=prefix+'hazard_verification').select('Verified')
    at.text_input(key=prefix+'hazard_document_reference').set_value('DEMO-ONLY/reviewed')
    button(at,'Save evidence & reassess').click().run()
    assert not at.exception
    saved=load_applications()[0]
    assert saved['_revision']==2
    assert saved['last_assessment']['status']=='A' and saved['initial_status']=='B'
    assert any(m.label=='B → A after updates' and m.value=='1' for m in at.metric)
    at.selectbox(key='decision_status_'+saved['app_id']).select('A')
    at.text_area(key='decision_notes_'+saved['app_id']).set_value('Synthetic evidence reviewed; staff disposition recorded.')
    button(at,'Record decision').click().run()
    assert not at.exception and load_decisions()[saved['app_id']]['status']=='A'
    # New browser session reads the same decision.
    other=app('pages/3_Dashboard.py',True)
    assert not other.exception
    assert any('Staff' in str(frame.value) for frame in other.dataframe)

def test_public_submission_cannot_self_verify():
    at=app('pages/1_New_Application.py')
    button(at,'STP-ready home').click().run()
    next(c for c in at.checkbox if c.label=='Save as a demo application').uncheck()
    button(at,'Analyze & submit application').click().run()
    assert not at.exception
    saved=load_applications()[0]
    assert all(saved[k]=='Not checked' for k in VERIFICATION_FIELDS)
    assert saved['last_assessment']['status']=='B'
    assert not at.metric

def test_empty_source_selection_keeps_filters():
    at=app('pages/3_Dashboard.py',True)
    at.multiselect(key='portfolio_sources').set_value([]).run()
    assert not at.exception
    assert at.multiselect(key='portfolio_sources').value==[]
    assert any('No applications match' in x.value for x in at.info)
    at.multiselect(key='portfolio_sources').set_value(['Demo portfolio']).run()
    assert not at.exception and at.metric

def test_settings_survive_navigation_and_new_session():
    at=app('pages/2_Settings.py',True)
    at.toggle[0].set_value(False)
    at.slider[0].set_value(.8)
    button(at,'Save workspace settings').click().run()
    at.switch_page('pages/0_Overview.py').run()
    at.switch_page('pages/2_Settings.py').run()
    assert at.toggle[0].value is False and at.slider[0].value==.8
    other=app('pages/2_Settings.py',True)
    assert not other.exception and other.toggle[0].value is False
    assert get_settings()['model_confidence_threshold']==.8
