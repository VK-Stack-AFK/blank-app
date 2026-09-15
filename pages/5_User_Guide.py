"""The complete, downloadable application guide."""
from pathlib import Path
import streamlit as st
from homeguard.ui import heading
heading('Your HomeGuard guide','From the first application to a supported underwriting recommendation.','Workspace help')
path=Path(__file__).resolve().parent.parent/'docs'/'USER_GUIDE.md'
content=path.read_text()
parts=content.split('\n## ')[1:]
labels=[p.split('\n',1)[0] for p in parts]
selected=st.selectbox('Guide section',labels)
st.markdown(parts[labels.index(selected)].split('\n',1)[1])
st.download_button('Download the complete user guide',content,'HomeGuard-User-Guide.md','text/markdown')
