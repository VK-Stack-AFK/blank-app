"""Persisted POC settings with a staff-only save boundary."""
import streamlit as st
from homeguard.storage import get_settings,save_settings
from homeguard.ui import heading,login_form

heading('Workspace settings','Manage the demonstration workflow and model review threshold.','Administration')
if not st.session_state.get('staff_authenticated'):
    login_form(); st.stop()
current=get_settings()
with st.form('workspace_settings'):
    st.subheader('Application experience')
    demo=st.toggle('Offer synthetic examples in application intake',value=current['test_mode_enabled'])
    results=st.toggle('Show recommendations to applicants after submission',value=current['show_results_to_applicants'])
    auth=st.toggle('Require staff sign-in for the workbench and Model Lab',value=current['require_dashboard_auth'])
    st.subheader('Prediction review')
    threshold=st.slider('Minimum model class support for routing without a model-support hold',min_value=.5,max_value=.99,value=float(current['model_confidence_threshold']),step=.01,format='%.2f')
    st.caption('Missing information, evidence gaps, and model/reference disagreements still route to B. Model support is not a calibrated probability of a real underwriting outcome.')
    saved=st.form_submit_button('Save workspace settings',type='primary')
if saved:
    save_settings({'test_mode_enabled':demo,'show_results_to_applicants':results,'require_dashboard_auth':auth,'model_confidence_threshold':threshold},st.session_state.get('staff_name','Staff'))
    st.success('Settings saved. These settings persist across pages and sessions.')
st.caption('Authentication here is a local POC login. Configure HOMEGUARD_USERNAME and HOMEGUARD_PASSWORD for a private demonstration; a production system needs managed identity, authorization, and operational controls.')
if st.button('Sign out'):
    st.session_state.pop('staff_authenticated',None);st.session_state.pop('staff_name',None);st.rerun()
