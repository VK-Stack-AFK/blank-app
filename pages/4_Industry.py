"""Dated market context and homeowners coverage education."""
import pandas as pd
import plotly.express as px
import streamlit as st
from homeguard.industry import III_URL,NAIC_URL,COVERAGE_URL,CHECKED,CLAIMS_TREND,LOSS_CAUSES
from homeguard.ui import heading,card

heading('The homeowners landscape','Understand the home, its coverage, and the loss patterns behind the underwriting questions.','Industry background')
st.caption(f'Historical reporting periods are shown below. Sources checked {CHECKED}; these are not live market indicators.')
cols=st.columns(4)
cols[0].metric('Average HO-3 premium · 2022','$1,569')
cols[1].metric('Claim frequency · 2023','5.33',help='Claims per 100 house-years; not the percentage of unique households filing a claim.')
cols[2].metric('Average claim · 2023','$20,062')
cols[3].metric('HO-3 exposure share · 2022','78.99%',help='Share of owner-occupied exposures in the NAIC report.')
st.markdown(f'Premium and claims: [Triple-I, citing NAIC and ISO/Verisk]({III_URL}). HO-3 exposure share: [NAIC 2022 report announcement, published May 2025]({NAIC_URL}).')
market,coverage,operations=st.tabs(['Loss patterns','Coverage foundations','Why evidence matters'])
with market:
    c1,c2=st.columns(2)
    with c1:
        st.subheader('Cost per claim, 2019–2023')
        fig=px.line(pd.DataFrame(CLAIMS_TREND),x='Year',y='Average claim ($)',markers=True,color_discrete_sequence=['#754185'])
        fig.update_layout(xaxis=dict(dtick=1),height=330,yaxis_tickprefix='$',yaxis_range=[0,23000])
        st.plotly_chart(fig,width='stretch')
    with c2:
        st.subheader('Share of homeowners losses, 2023')
        fig=px.bar(pd.DataFrame(LOSS_CAUSES),y='Cause',x='Share of 2023 losses (%)',orientation='h',text='Share of 2023 losses (%)',color_discrete_sequence=['#217C77'])
        fig.update_traces(texttemplate='%{text}%');fig.update_layout(height=330,yaxis=dict(autorange='reversed'),xaxis_range=[0,50])
        st.plotly_chart(fig,width='stretch')
    st.markdown(f'[Source: Triple-I / ISO, a Verisk business]({III_URL}). Severity is incurred indemnity per claim, excluding loss-adjustment expenses. Frequency uses house-years of exposure. Claims data cover HO-2, HO-3, HO-5 and North Carolina HE-7, excluding Alaska, Texas, Puerto Rico, renters and condominium forms. Cause shares measure losses, not claim counts; “other” combines the remaining categories.')
    with st.expander('View the underlying annual figures'):
        st.dataframe(CLAIMS_TREND,hide_index=True,width='stretch')
    st.caption('Use this context to prioritize evidence collection. It does not establish carrier appetite, a rate indication, or a target STP percentage.')
with coverage:
    st.subheader('What the application is asking you to protect')
    st.dataframe([
        {'Coverage':'A · Dwelling','Purpose':'The home and attached structures','Capture':'Rebuilding estimate and requested limit'},
        {'Coverage':'B · Other structures','Purpose':'Detached structures','Capture':'Separate structure limits'},
        {'Coverage':'C · Personal property','Purpose':'Household belongings','Capture':'Limit, settlement basis, valuables'},
        {'Coverage':'D · Loss of use','Purpose':'Eligible additional living expenses','Capture':'Requested limit'},
        {'Coverage':'E · Personal liability','Purpose':'Covered injury or damage liability','Capture':'Limit and premises exposures'},
        {'Coverage':'F · Medical payments','Purpose':'Eligible medical payments to others','Capture':'Requested limit'},
    ],hide_index=True,width='stretch')
    st.write('Rebuilding cost differs from market value. Flood and earthquake damage generally need separate coverage arrangements; water-backup coverage is a distinct consideration. Actual protection depends on the policy wording, exclusions, limits, and jurisdiction.')
    st.markdown(f'[Coverage background: Travelers homeowners coverage guide]({COVERAGE_URL}). HomeGuard’s questionnaire is an original POC design; carrier-specific applications and eligibility requirements still need to be configured.')
    st.info('Coverage letters A–F describe policy protections. HomeGuard routing classes A, B and F describe an application recommendation. They are separate concepts.')
with operations:
    columns=st.columns(3)
    with columns[0]: card('Property facts','Reconcile construction, occupancy, roof condition, systems, and rebuilding cost before relying on a risk assessment.')
    with columns[1]: card('Loss context','Understand cause, amount, open status, repairs, and mitigation. An incomplete loss run creates an actionable review task.')
    with columns[2]: card('Evidence readiness','Connect each verified fact to a source and a reviewer. Completing a missing report can resolve a B hold when the model and reference checks support A.')
    st.markdown('### HomeGuard’s automation goal')
    st.write('Increase the share of complete, supported applications that can reach pricing with less manual handling. Separate data gaps from risk questions, preserve the original recommendation, and measure evidence-driven improvement independently from staff dispositions.')
    st.caption('No external industry STP benchmark is assumed. Workbench percentages come only from the applications and filters you select.')
    st.page_link('pages/5_User_Guide.py',label='Follow the full application-to-review guide',icon=':material/menu_book:')
