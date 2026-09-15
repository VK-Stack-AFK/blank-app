"""Persistent homeowners portfolio and evidence-led underwriting workbench."""
import json
import pandas as pd
import plotly.express as px
import streamlit as st
from homeguard.config import STATUS_LABELS,STATUS_COLORS
from homeguard.portfolio import SOURCES,load_portfolio,evaluate_records,portfolio_metrics,summary_frame
from homeguard.prediction import assess_application
from homeguard.schema import FIELDS,TABS,label
from homeguard.storage import get_settings,save_application,save_decision,load_events,safe_csv,RevisionConflict
from homeguard.validation import normalize_record,input_issues
from homeguard.ui import require_staff,heading,show_assessment,render_questionnaire,clear_widgets

require_staff()
heading('Underwriting workbench','Review the home, resolve the evidence, and document the next step.','Personal lines operations')
settings=get_settings()
with st.expander('Portfolio filters',expanded=True):
    selected=st.multiselect('Application sources',SOURCES,default=list(SOURCES),key='portfolio_sources')
    c1,c2=st.columns(2)
    start=c1.date_input('Submitted on or after',value=None,key='portfolio_start')
    end=c2.date_input('Submitted on or before',value=None,key='portfolio_end')
    if st.button('Refresh portfolio'): st.rerun()
if start and end and start>end:
    st.error('The end date must be on or after the start date.'); st.stop()
records=load_portfolio(selected,start,end)
rows=evaluate_records(records,settings['model_confidence_threshold'])
if not rows:
    st.info('No applications match these filters. Choose another source or date range, or create a homeowners application.')
    st.page_link('pages/1_New_Application.py',label='Create an application',icon=':material/add_home:')
    st.stop()
metrics=portfolio_metrics(rows)
cols=st.columns(4)
cols[0].metric('Applications in view',metrics['applications'])
cols[1].metric('STP readiness',f'{metrics["stp_rate"]:.1%}',help='Current engine A with no staff decision ÷ all applications in this filtered view. This is readiness, not issued policies.')
cols[2].metric('Open B reviews',metrics['review'])
cols[3].metric('B → A after updates',metrics['evidence_recovered'],help='Initially B, now engine A after saved application/evidence updates, with no staff decision.')
st.caption(f'{metrics["stp_ready"]} model-cleared cases · {metrics["staff_cleared"]} separately cleared by staff · {metrics["rejection_recommendations"]} rejection recommendations awaiting staff action. Metrics follow the selected sources and dates.')
queue_tab,overview_tab,export_tab,history_tab=st.tabs(['Review a home','Portfolio overview','Application register','Decision history'])
with overview_tab:
    counts=pd.DataFrame([{'Outcome':STATUS_LABELS[k],'Applications':sum(r['effective_status']==k for r in rows),'Class':k} for k in STATUS_LABELS])
    c1,c2=st.columns([1,1])
    with c1:
        st.subheader('Current application outcomes')
        fig=px.bar(counts,x='Outcome',y='Applications',color='Class',color_discrete_map=STATUS_COLORS,text='Applications')
        fig.update_layout(showlegend=False,plot_bgcolor='rgba(0,0,0,0)',paper_bgcolor='rgba(0,0,0,0)',margin=dict(l=0,r=0,t=10,b=0),height=320)
        st.plotly_chart(fig,width='stretch')
    with c2:
        st.subheader('Where review work is concentrated')
        findings={}
        for r in rows:
            if r['effective_status']=='B':
                for factor in set(f['factor'] for f in r['flags']): findings[factor]=findings.get(factor,0)+1
        if findings: st.dataframe([{'Review topic':label(k),'Applications':v} for k,v in sorted(findings.items(),key=lambda x:x[1],reverse=True)[:8]],hide_index=True,width='stretch')
        else: st.info('No unresolved B cases in this view.')
    st.info('To improve STP readiness, complete missing evidence or correct supported facts and reassess. A staff decision is tracked separately and does not increase automated STP readiness.')
with export_tab:
    st.subheader('Application register')
    frame=summary_frame(rows)
    st.dataframe(frame,hide_index=True,width='stretch',column_config={'Model support':st.column_config.NumberColumn(format='percent')})
    st.download_button('Download register (CSV)',safe_csv(frame),'homeguard-application-register.csv','text/csv')
    flat=pd.DataFrame([{k:v for k,v in r.items() if k not in {'flags','reasons','last_assessment','probabilities','decision'}} for r in rows])
    st.download_button('Download questionnaire & assessments (CSV)',safe_csv(flat),'homeguard-applications.csv','text/csv')
    st.caption('Exports include the filtered records. Synthetic and submitted sources remain labeled; leading-zero ZIP codes are preserved in the CSV text.')
with history_tab:
    st.subheader('Recorded application and decision events')
    visible_ids={r['app_id'] for r in rows}
    events=[e for e in load_events() if e['app_id'] in visible_ids]
    if events:
        st.dataframe([{'Time (UTC)':e['at'],'Application':e['app_id'],'Action':e['event_type'].replace('_',' '),'Staff / source':e['actor']} for e in events],hide_index=True,width='stretch')
        st.download_button('Download visible audit events (JSON)',json.dumps(events,indent=2,default=str),'homeguard-audit-events.json','application/json')
    else: st.info('No saved events for these applications yet. Evidence edits and staff decisions create an audit record.')
with queue_tab:
    open_id=st.session_state.pop('open_app_id',None)
    ids=[r['app_id'] for r in rows]
    if open_id in ids: st.session_state.review_selected=open_id
    elif st.session_state.get('review_selected') not in ids: st.session_state.review_selected=ids[0]
    by_id={r['app_id']:r for r in rows}
    chosen=st.selectbox('Choose a homeowners application',ids,format_func=lambda k:f'{by_id[k].get("applicant_name",k)} · {k} · {STATUS_LABELS[by_id[k]["effective_status"]]}',key='review_selected')
    record=next(r for r in records if r['app_id']==chosen)
    case=by_id[chosen]
    c1,c2=st.columns([3,1])
    with c1:
        st.subheader(record.get('applicant_name','Homeowners application'))
        st.write(f'{record.get("address") or "Address pending"} · {record.get("city") or ""}, {record.get("state") or ""} {record.get("zip_code") or ""}')
        st.caption(f'{chosen} · {record["data_source"]} · Application revision {record.get("_revision",0)}')
    with c2:
        value=record.get('requested_dwelling_limit')
        st.metric('Requested dwelling limit',f'${value:,.0f}' if isinstance(value,(float,int)) else 'Pending')
    show_assessment(case)
    if case.get('decision'):
        decision=case['decision']
        st.info(f'Staff disposition: {STATUS_LABELS[decision["status"]]} · {decision["reviewer"]} · {decision["decided_at"]}\n\n{decision["rationale"]}')
    details,edit,decide,case_history=st.tabs(['Application details','Update evidence & reassess','Record staff decision','Case history'])
    with details:
        for section in TABS:
            with st.expander(section):
                st.dataframe([{'Question':f.label,'Response':str(record.get(f.key)) if record.get(f.key) is not None else 'Not provided','Use':f.role} for f in FIELDS if f.section==section],hide_index=True,width='stretch')
        st.caption('Findings explain the POC reference checks and evidence gaps. They are not causal explanations of the random forest. Model Lab shows global feature importance.')
    with edit:
        st.write('Record the source-supported facts. Mark evidence verified only after a staff review. Saving updates runs the model again and retires any earlier staff disposition.')
        prefix=f'review_{chosen}_{record.get("_revision",0)}_'
        with st.form('edit_'+chosen):
            changed=render_questionnaire(record,prefix)
            updated=st.form_submit_button('Save evidence & reassess',type='primary')
        if updated:
            malformed=[x['reason'] for x in input_issues(changed) if x['code'].startswith('invalid_') or x['code'] in {'email_format','zip_format','claims_consistency','paid_without_claim','future_verification'}]
            if malformed: st.error('Correct before saving: '+' '.join(malformed))
            else:
                try:
                    revised=normalize_record(changed)
                    revised['initial_status']=case['initial_status']
                    result=assess_application(revised,settings['model_confidence_threshold'])
                    save_application(revised,record['data_source'],st.session_state.get('staff_name','Demo staff'),result,record.get('_revision',0))
                    st.session_state.review_notice='Application evidence saved and reassessed.'
                    clear_widgets(prefix); st.rerun()
                except RevisionConflict as exc: st.error(str(exc))
    with decide:
        st.write('A staff disposition is a recorded review action. It does not bind coverage, issue a policy, or send a notice. F remains a recommendation for rejection.')
        with st.form('decision_'+chosen):
            disposition=st.selectbox('Staff disposition',list(STATUS_LABELS),format_func=lambda k:f'{k} · {STATUS_LABELS[k]}',index=1,key='decision_status_'+chosen)
            reviewer=st.text_input('Reviewing underwriter',value=st.session_state.get('staff_name',''),key='decision_reviewer_'+chosen)
            rationale=st.text_area('Decision rationale and supporting evidence',key='decision_notes_'+chosen)
            applied=st.form_submit_button('Record decision',type='primary')
        if applied:
            if not reviewer.strip() or not rationale.strip(): st.error('Enter the reviewing underwriter and a decision rationale.')
            else:
                try:
                    revision=record.get('_revision',0)
                    if not revision:
                        saved=save_application({**record,'initial_status':case['initial_status']},record['data_source'],reviewer,assess_application(record,settings['model_confidence_threshold']),0)
                        revision=saved['_revision']
                    save_decision(chosen,disposition,reviewer,rationale,revision)
                    st.session_state.review_notice='Staff decision recorded. Portfolio totals now reflect this disposition.'; st.rerun()
                except (RevisionConflict,ValueError) as exc: st.error(str(exc))
        note=f'HomeGuard application {chosen}\nNamed insured: {record.get("applicant_name","")}\n\nYour homeowners application is with our underwriting team. We will confirm any additional information needed and communicate the next step. No coverage is bound by this message.\n'
        st.download_button('Download insured update draft',note,f'{chosen}-insured-update.txt','text/plain')
        st.caption('Draft only. No email or messaging service is connected.')
    with case_history:
        events=load_events(chosen)
        if not events: st.info('No saved changes or decisions yet.')
        for event in events[:30]:
            with st.expander(f'{event["at"]} · {event["event_type"].replace("_"," ")} · {event["actor"]}'):
                st.json(event['detail'])
        if len(events)>30: st.caption('Showing the most recent 30 events. The JSON download includes the complete case history.')
        st.download_button('Download complete case history',json.dumps(events,indent=2,default=str),f'{chosen}-history.json','application/json')
if st.session_state.get('review_notice'): st.success(st.session_state.pop('review_notice'))
