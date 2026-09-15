"""Shared visual system, navigation components, and reusable application fields."""
from datetime import date
from html import escape
import hmac
import os
import streamlit as st
from .config import APP_TITLE,APP_SUBTITLE,STATUS_LABELS,STATUS_DESCRIPTIONS,STATUS_COLORS
from .schema import FIELDS,TABS,FIELD_MAP,blank_application
from .storage import get_settings

CSS='''
<style>
.block-container {max-width:1360px;padding-top:2rem;padding-bottom:3rem;}
h1,h2,h3 {letter-spacing:-.025em;}
h1 {font-size:2.4rem!important;font-weight:650!important;line-height:1.16!important;}
h2 {font-size:1.5rem!important;} h3 {font-size:1.08rem!important;}
[data-testid="stMetric"] {background:white;border:1px solid #E3DFE8;border-radius:12px;padding:1.1rem 1.25rem;}
[data-testid="stMetricLabel"] {color:#656173;font-size:.82rem;}
[data-testid="stMetricValue"] {font-size:1.85rem;color:#292238;}
[data-testid="stForm"] {border:1px solid #E3DFE8;border-radius:14px;background:#fff;padding:1.4rem;}
[data-testid="stExpander"] {border:1px solid #E3DFE8;border-radius:10px;background:#fff;}
.stButton>button,.stDownloadButton>button {border-radius:8px;min-height:2.65rem;font-weight:600;}
[data-baseweb="tab-list"] {gap:1.5rem;border-bottom:1px solid #E3DFE8;}
[data-baseweb="tab"] {font-weight:600;padding:0 .1rem;}
.hg-eyebrow {font-size:.72rem;letter-spacing:.13em;font-weight:750;text-transform:uppercase;color:#785388;margin-bottom:.7rem;}
.hg-lead {font-size:1.08rem;line-height:1.65;color:#696275;max-width:780px;margin-bottom:1.7rem;}
.hg-card {border:1px solid #E3DFE8;border-radius:14px;background:#fff;padding:1.6rem;height:100%;}
.hg-card h3 {margin-top:0;font-size:1.05rem!important;color:#312541;}
.hg-card p {color:#6B6577;font-size:.93rem;line-height:1.65;margin-bottom:0;}
.hg-hero {border-radius:18px;background:linear-gradient(110deg,#EFE7F3,#F9F6FA 70%);padding:2.5rem;border:1px solid #E2D5EA;margin-bottom:1.5rem;}
.hg-hero h1 {max-width:750px;font-size:3rem!important;}
.hg-badge {display:inline-block;border-radius:24px;font-weight:650;font-size:.82rem;padding:.45rem .8rem;margin-bottom:.75rem;}
.hg-rule {border-left:3px solid #9270A2;padding-left:1rem;margin:.9rem 0;}
.hg-footer {border-top:1px solid #E3DFE8;color:#797184;font-size:.77rem;padding-top:1rem;margin-top:2.5rem;}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {color:#CEBDD8;}
@media(max-width:700px){.block-container{padding:1rem;}h1{font-size:2rem!important;}.hg-hero{padding:1.4rem;}.hg-hero h1{font-size:2.1rem!important;}}
</style>
'''

def shell():
    st.markdown(CSS,unsafe_allow_html=True)
    with st.sidebar:
        st.markdown('## HomeGuard')
        st.caption('PERSONAL LINES · HOMEOWNERS')
        st.markdown('---')

def heading(title,description='',eyebrow='Homeowners underwriting'):
    st.markdown(f'<div class="hg-eyebrow">{escape(eyebrow)}</div>',unsafe_allow_html=True)
    st.title(title)
    if description: st.markdown(f'<div class="hg-lead">{escape(description)}</div>',unsafe_allow_html=True)

def card(title,text):
    st.markdown(f'<div class="hg-card"><h3>{escape(title)}</h3><p>{escape(text)}</p></div>',unsafe_allow_html=True)

def badge(status):
    color=STATUS_COLORS.get(status,'#686173')
    st.markdown(f'<span class="hg-badge" style="background:{color}14;color:{color};border:1px solid {color}35">{escape(status)} · {escape(STATUS_LABELS.get(status,status))}</span>',unsafe_allow_html=True)

def footer():
    st.markdown('<div class="hg-footer">HomeGuard demonstration workspace · Synthetic model · Recommendations do not bind coverage</div>',unsafe_allow_html=True)

def require_staff():
    if not get_settings()['require_dashboard_auth'] or st.session_state.get('staff_authenticated'): return
    heading('Underwriting workspace','Sign in to review submissions and record underwriting actions.','Staff access')
    login_form()
    st.stop()

def login_form():
    with st.form('staff_login'):
        username=st.text_input('Username')
        password=st.text_input('Password',type='password')
        submitted=st.form_submit_button('Sign in',type='primary')
    if submitted:
        expected_user=os.environ.get('HOMEGUARD_USERNAME','admin')
        expected_password=os.environ.get('HOMEGUARD_PASSWORD','admin123')
        if hmac.compare_digest(username,expected_user) and hmac.compare_digest(password,expected_password):
            st.session_state.staff_authenticated=True; st.session_state.staff_name=username; st.rerun()
        else: st.error('The username or password was not recognized.')
    if not os.environ.get('HOMEGUARD_PASSWORD'):
        st.caption('Demo sign-in: admin / admin123. Use synthetic applications in this workspace.')

def render_fields(record,prefix,sections=None):
    """Explicit widget keys and an independent draft preserve submitted values."""
    values={}
    for section in sections or TABS:
        st.markdown('### '+section)
        fields=[f for f in FIELDS if f.section==section]
        columns=st.columns(2,gap='large')
        for i,f in enumerate(fields):
            with columns[i%2]:
                key=prefix+f.key
                title=f.label+(' *' if f.required else '')
                value=record.get(f.key)
                if f.kind=='select':
                    index=f.options.index(value) if value in f.options else 0
                    values[f.key]=st.selectbox(title,f.options,index=index,key=key,help=f.help or None)
                elif f.kind in ('integer','number','money'):
                    integer=f.kind in ('integer','money')
                    cast=int if integer else float
                    try: current=cast(value) if value is not None else None
                    except (ValueError,TypeError,OverflowError): current=None
                    if current is not None and (current<f.minimum or (f.maximum is not None and current>f.maximum)): current=None
                    values[f.key]=st.number_input(title,min_value=cast(f.minimum),max_value=cast(f.maximum) if f.maximum is not None else None,value=current,step=cast(1000 if f.kind=='money' else 1 if integer else .1),key=key,help=f.help or None)
                elif f.kind=='date':
                    try: current=date.fromisoformat(str(value)[:10]) if value else None
                    except ValueError: current=None
                    value=st.date_input(title,value=current,min_value=date(1900,1,1),max_value=date(date.today().year+5,12,31),key=key,help=f.help or None)
                    values[f.key]=value.isoformat() if value else None
                elif f.kind=='textarea':
                    values[f.key]=st.text_area(title,value=str(value or ''),height=100,key=key,help=f.help or None)
                else:
                    values[f.key]=st.text_input(title,value=str(value or ''),key=key,help=f.help or None)
    return values

def render_questionnaire(record,prefix):
    values=dict(record)
    tabs=st.tabs(list(TABS))
    for tab,section in zip(tabs,TABS):
        with tab: values.update(render_fields(record,prefix,[section]))
    return values

def clear_widgets(prefix):
    for key in list(st.session_state):
        if key.startswith(prefix): del st.session_state[key]

def show_assessment(result):
    badge(result['status'])
    st.write(STATUS_DESCRIPTIONS[result['status']])
    cols=st.columns(3)
    cols[0].metric('Model recommendation',result['model_status'])
    cols[1].metric('Model class support',f'{result["confidence"]:.0%}')
    cols[2].metric('Evidence / data gaps',result.get('evidence_gap_count',0))
    st.caption('Model support is not calibrated real-world confidence. Evidence and model disagreements can hold a case in B.')
    if result.get('probabilities'):
        st.caption(' · '.join(f'{k}: {v:.1%}' for k,v in result['probabilities'].items()))
    if result.get('flags'):
        st.dataframe([{'Type':f['category'],'Finding':f['reason'],'Next action':f['action']} for f in result['flags']],hide_index=True,width='stretch')
    else: st.success('Evidence is complete and the model supports the next pricing step.')
