"""Detailed, stable homeowners application intake."""
import streamlit as st
from homeguard.schema import blank_application,CONTACT_FIELDS,FIELDS,VERIFICATION_FIELDS,label
from homeguard.validation import _is_missing,input_issues,normalize_record
from homeguard.prediction import assess_application
from homeguard.storage import get_settings,save_application,new_application_id
from homeguard.synthetic import synthetic_application,evidence_gap_example
from homeguard.ui import heading,render_questionnaire,clear_widgets,show_assessment

heading('New homeowners application','Capture the home and the supporting evidence. Save an in-session draft at any point, or analyze and submit the record.','Application intake')
settings=get_settings()
if 'application_draft' not in st.session_state: st.session_state.application_draft=blank_application()
if settings['test_mode_enabled']:
    with st.expander('Start from a synthetic example',expanded=False):
        st.caption('Examples include synthetic evidence references. They are not verified real properties.')
        cols=st.columns(4)
        for col,caption,category in zip(cols,['STP-ready home','B · missing evidence','F · review recommendation','Blank application'],['A','B','F',None]):
            if col.button(caption,width='stretch'):
                record=evidence_gap_example() if category=='B' else synthetic_application(3,category,900) if category else blank_application()
                for key in ('app_id','submission_date','data_source','initial_status'): record.pop(key,None)
                st.session_state.application_draft=record
                st.session_state.pop('submission_result',None)
                clear_widgets('intake_'); st.rerun()
st.caption(f'{len(FIELDS)} fields across five sections. * identifies information needed for complete evaluation. Unknown information creates a review task; it is never treated as zero risk. Evidence & consent is completed by the underwriting team.')
with st.form('homeowners_application',clear_on_submit=False):
    values=render_questionnaire(st.session_state.application_draft,'intake_')
    st.markdown('---')
    demo=st.checkbox('Save as a demo application',value=True,help='Keep synthetic exercises separate from submitted applications.')
    c1,c2=st.columns(2)
    save_draft=c1.form_submit_button('Save draft',width='stretch')
    submit=c2.form_submit_button('Analyze & submit application',type='primary',width='stretch')
if save_draft or submit:
    st.session_state.application_draft=values
if save_draft: st.success('Draft saved for this browser session. Submit the record to keep it after the session ends.')
if submit:
    contact_errors=[label(k) for k in CONTACT_FIELDS if _is_missing(values.get(k))]
    quality=input_issues(values)
    malformed=[i['reason'] for i in quality if i['code'].startswith('invalid_') or i['code'] in {'email_format','zip_format','claims_consistency','paid_without_claim','future_verification'}]
    if contact_errors: st.error('Complete the identifying fields: '+', '.join(contact_errors))
    elif malformed: st.error('Correct the following before saving: '+' '.join(malformed))
    else:
        record=normalize_record(values)
        if not demo and not st.session_state.get('staff_authenticated'):
            # Applicant declarations cannot establish staff verification.
            for field in VERIFICATION_FIELDS: record[field]='Not checked'
            record['verification_reviewer']=''
            record['verification_date']=None
        record['app_id']=new_application_id()
        result=assess_application(record,settings['model_confidence_threshold'])
        saved=save_application(record,'Demo application' if demo else 'Submission',st.session_state.get('staff_name','Intake'),result)
        st.session_state.submission_result={'application':saved,'assessment':result}
if st.session_state.get('submission_result'):
    result=st.session_state.submission_result
    st.markdown('---'); st.success('Application received · '+result['application']['app_id'])
    if st.session_state.get('staff_authenticated') or settings['show_results_to_applicants']:
        show_assessment(result['assessment'])
    else: st.write('Your submission is available to the underwriting team for review. No coverage decision has been issued.')
    if st.button('View the underwriting workbench',type='primary'):
        st.session_state.open_app_id=result['application']['app_id']; st.switch_page('pages/3_Dashboard.py')
