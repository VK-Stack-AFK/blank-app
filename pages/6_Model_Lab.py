"""Visible provenance, held-out measurements, and model/field documentation."""
import json
from dataclasses import asdict
import pandas as pd
import plotly.express as px
import streamlit as st
from homeguard.model import load_model,DATASET_PATH
from homeguard.schema import FIELDS,label
from homeguard.ui import heading,require_staff

require_staff()
heading('Model lab','Inspect the prediction prototype, its inputs, and what its test results actually measure.','Homeowners prediction research')
try: _,metadata=load_model()
except (RuntimeError,OSError,ValueError) as exc:
    st.error(str(exc));st.stop()
st.info('Demonstration model · 10,000 synthetic applications · Reference-rule labels. These results do not measure performance on real insureds or predict claim cost.')
cols=st.columns(4)
cols[0].metric('Synthetic applications',f'{metadata["dataset_rows"]:,}')
cols[1].metric('Training / held-out',f'{metadata["train_rows"]:,} / {metadata["test_rows"]:,}')
cols[2].metric('Synthetic test agreement',f'{metadata["accuracy"]:.2%}')
cols[3].metric('Synthetic macro F1',f'{metadata["macro_f1"]:.3f}')
st.caption(f'{metadata["algorithm"]} · {metadata["model_version"]} · Label policy {metadata["rule_version"]} · Seed {metadata["seed"]}')
performance,inputs,provenance=st.tabs(['Held-out evaluation','Inputs & explanations','Data & model record'])
with performance:
    c1,c2=st.columns(2)
    with c1:
        st.subheader('Confusion matrix')
        st.dataframe(pd.DataFrame(metadata['confusion_matrix'],index=['Actual '+c for c in metadata['classes']],columns=['Predicted '+c for c in metadata['classes']]),width='stretch')
        st.caption('Rows are reference labels; columns are model predictions. The 2,000 test rows are excluded from model fitting and preprocessing fitting.')
    with c2:
        st.subheader('Per-class synthetic results')
        report=pd.DataFrame({c:metadata['classification_report'][c] for c in metadata['classes']}).T
        st.dataframe(report.style.format({'precision':'{:.3f}','recall':'{:.3f}','f1-score':'{:.3f}','support':'{:.0f}'}),width='stretch')
    st.write('The generated scenarios share the same label policy in training and testing. High agreement mainly demonstrates the model’s ability to learn that policy. Production performance needs independent, representative, time-separated outcomes and a clearly defined prediction target.')
with inputs:
    st.subheader('Global feature importance')
    importance=pd.DataFrame([{'Input':label(k),'Importance':v} for k,v in list(metadata['feature_importance'].items())[:12]])
    fig=px.bar(importance,x='Importance',y='Input',orientation='h',color_discrete_sequence=['#754185'])
    fig.update_layout(yaxis=dict(autorange='reversed'),height=410,margin=dict(l=0,r=0,t=10,b=0))
    st.plotly_chart(fig,width='stretch')
    st.caption('Random-forest impurity importance is global and can be biased toward certain feature types. It is not a causal or per-application explanation.')
    st.markdown('**Excluded from prediction:** '+', '.join(metadata['excluded_inputs'])+'.')
    with st.expander('Exact model feature list'):
        st.dataframe([{'Model input':key,'Label':label(key)} for key in metadata['features']],hide_index=True,width='stretch')
    with st.expander('Complete questionnaire dictionary'):
        dictionary=pd.DataFrame([{'Field':f.key,'Question':f.label,'Section':f.section,'Required':f.required,'Use':f.role,'Model input':f.key in metadata['features'],'Choices':' | '.join(f.options)} for f in FIELDS])
        st.dataframe(dictionary,hide_index=True,width='stretch')
        st.download_button('Download field dictionary',dictionary.to_csv(index=False),'homeguard-field-dictionary.csv','text/csv')
with provenance:
    st.write(metadata['data_provenance'])
    st.dataframe([{'Class':k,'All synthetic records':v} for k,v in metadata['class_counts'].items()],hide_index=True,width='stretch')
    st.write('The download includes all 10,000 rows, the reference label, and a train/test split column. The separate 1,000-home demonstration portfolio uses a different seed. Industry statistics are educational context and are not training data.')
    st.download_button('Download 10,000 synthetic applications (CSV.gz)',DATASET_PATH.read_bytes(),DATASET_PATH.name,'application/gzip')
    st.download_button('Download model metadata',json.dumps(metadata,indent=2),'homeguard-model-metadata.json','application/json')
    with st.expander('Version and integrity record'):
        st.json({k:metadata[k] for k in ['model_version','rule_version','sklearn_version','seed','dataset_sha256','artifact_sha256']})
    st.caption('Model rebuilding is a deliberate developer operation, documented in the README. It does not run during intake or a portfolio refresh.')
    st.markdown('[Model reference: scikit-learn random forests](https://scikit-learn.org/stable/modules/ensemble.html#forest) · [Evaluation reference](https://scikit-learn.org/stable/modules/model_evaluation.html)')
