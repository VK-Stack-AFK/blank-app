import streamlit as st
from homeguard.ui import heading,card
from homeguard.schema import FIELDS
st.markdown('''<div class="hg-hero"><div class="hg-eyebrow">PERSONAL HOMEOWNERS · UNDERWRITING WORKSPACE</div><h1>A clearer path<br>from submission to pricing.</h1><p class="hg-lead">Bring the dwelling, loss history, and supporting evidence into one view. Use model-assisted recommendations to focus underwriting attention where it matters.</p></div>''',unsafe_allow_html=True)
left,right=st.columns([1.1,1],gap='large')
with left:
    st.markdown('### Start with a complete picture of the home')
    st.write('Capture the insured interest, construction, roof and systems, coverage, prior losses, and verification evidence. The workbench explains what is ready and what still needs attention.')
    if st.button('Start a homeowners application',type='primary',width='stretch'): st.switch_page('pages/1_New_Application.py')
    if st.button('Open underwriting workbench',width='stretch'): st.switch_page('pages/3_Dashboard.py')
with right:
    card('Designed for the grey area','B cases become an actionable worklist: missing facts, evidence to verify, and risk questions to resolve. Update the record, reassess, and track model-cleared readiness separately from staff overrides.')
st.markdown('')
a,b,c=st.columns(3,gap='large')
with a: card('A · STP ready','Complete evidence and sufficient model support for the next pricing step. This does not quote a premium or bind coverage.')
with b: card('B · Underwriter review','An evidence gap, uncertainty, or risk question needs attention. Clear the facts before reassessing.')
with c: card('F · Rejection recommendation','A model-supported recommendation for staff review. The underwriter owns the final decision.')
st.markdown('---')
a,b,c=st.columns(3)
a.metric('Application fields',len(FIELDS))
b.metric('Synthetic model dataset','10,000')
c.metric('Held-out test records','2,000')
st.caption('Demonstration scope: application intake, prediction, evidence tracking, underwriting review, and explanations. External verification, pricing, policy issuance, and email delivery are future integrations.')
col1,col2=st.columns(2)
with col1:
    st.page_link('pages/4_Industry.py',label='Explore the homeowners industry',icon=':material/monitoring:')
with col2:
    st.page_link('pages/5_User_Guide.py',label='Read the complete application guide',icon=':material/menu_book:')
