"""HomeGuard multipage entry point."""
import streamlit as st
from homeguard.ui import shell,footer
st.set_page_config(page_title='HomeGuard · Homeowners underwriting',page_icon=':material/home_work:',layout='wide',initial_sidebar_state='expanded')
shell()
page=st.navigation({
    'Workspace':[
        st.Page('pages/0_Overview.py',title='Overview',icon=':material/home_work:'),
        st.Page('pages/1_New_Application.py',title='New application',icon=':material/post_add:'),
        st.Page('pages/3_Dashboard.py',title='Underwriting workbench',icon=':material/dashboard:')],
    'Knowledge & model':[
        st.Page('pages/4_Industry.py',title='Industry background',icon=':material/monitoring:'),
        st.Page('pages/5_User_Guide.py',title='User guide',icon=':material/menu_book:'),
        st.Page('pages/6_Model_Lab.py',title='Model lab',icon=':material/model_training:')],
    'Administration':[st.Page('pages/2_Settings.py',title='Settings',icon=':material/settings:')]
})
with st.sidebar:
    st.markdown('---')
    st.caption('PROOF OF CONCEPT')
    st.caption('10,000 synthetic training / test scenarios. Human ownership of underwriting decisions.')
page.run()
footer()
