"""HomeGuard UW Validator - Home Page."""
import streamlit as st
from homeguard.config import APP_TITLE, APP_SUBTITLE

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.hero {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 45%, #0f766e 100%);
    color: white;
    padding: 3rem 2rem;
    border-radius: 1.5rem;
    margin-bottom: 2rem;
    text-align: center;
    box-shadow: 0 20px 55px rgba(15, 23, 42, 0.18);
}
.hero h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
    font-weight: 800;
}
.hero p {
    font-size: 1.1rem;
    opacity: 0.95;
    margin: 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="hero">
    <div style="font-size: 3rem; margin-bottom: 1rem;">🏠</div>
    <h1>{APP_TITLE}</h1>
    <p>{APP_SUBTITLE}</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
## Overview

HomeGuard Underwriting Decision Engine is an automated pre-pricing underwriting assistant for personal homeowners insurance.
It evaluates applications and routes them to one of three clear outcomes:

✅ **Approved for Pricing** — Application meets underwriting criteria, ready for pricing
⏳ **Referred for Manual Review** — Requires underwriter assessment for complexity or risk factors
❌ **Declined** — Application does not meet underwriting criteria

---

## For Applicants

""")

st.markdown("### 📋 Submit Application")
st.markdown("Complete the questionnaire to submit a homeowners insurance application for underwriting evaluation.")
if st.button("Submit Application →", use_container_width=True, type="primary"):
    st.switch_page("pages/1_New_Application.py")

st.markdown("---")

st.markdown("""
## Underwriting Staff Portal 🔒

Access to the underwriting dashboard and review queue requires authentication. Go to **Settings** to log in with staff credentials.
""")

st.markdown("""
### 📊 Underwriting Portfolio

View portfolio analytics, review underwriting decisions, and access the manual review queue.
""")
if st.button("Go to Dashboard →", use_container_width=True, type="primary"):
    st.switch_page("pages/3_Dashboard.py")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### ⚙️ Settings

    Configure system, manage authentication, customize experience.
    """)
    if st.button("Go to Settings →", use_container_width=True):
        st.switch_page("pages/2_Settings.py")

with col2:
    st.markdown("""
    ### ℹ️ About

    Learn about this tool.
    """)
    st.markdown("[View on GitHub](https://github.com)")

st.markdown("---")

st.markdown("""
## Security

- **Public access**: Only questionnaire is accessible to applicants
- **Staff access**: Dashboard and Review Queue require authentication
- **Demo credentials**: Username `admin` / Password `admin123`
- **Production**: Replace demo credentials with secure credentials

---

## Next Steps

1. Submit a new application to see the decision flow
2. Go to Settings and authenticate as staff
3. View Review Queue and Dashboard
4. Try toggling "password protection" in Settings to test public vs. staff modes

---

*This is a proof-of-concept tool. Any real deployment requires compliance, legal, and actuarial review.*
""")

