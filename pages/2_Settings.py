"""POC Settings - Application display preferences and authentication."""
import streamlit as st

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

st.markdown("# ⚙️ Settings")

# Check if user is authenticated
is_staff = st.session_state.get("staff_authenticated", False)

if not is_staff:
    st.warning("🔒 You must be authenticated as staff to access settings. Use the login form below.")

    with st.form("staff_login"):
        st.markdown("### Staff Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", use_container_width=True, type="primary")

        if submit:
            # Default credentials (change these in production!)
            if username == "admin" and password == "admin123":
                st.session_state.staff_authenticated = True
                st.success("✓ Authenticated! Reloading...")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

    st.markdown("---")
    st.info("**Demo credentials:** Username: `admin` | Password: `admin123`")
    st.stop()

# Staff authenticated - show settings
st.success("✓ Authenticated as staff")

st.markdown("---")

st.markdown("## Demonstration & Testing")

# Initialize session state
if "test_mode_enabled" not in st.session_state:
    st.session_state.test_mode_enabled = True

test_mode = st.toggle(
    "🧪 Enable Sample Applications (auto-fill for testing)",
    value=st.session_state.test_mode_enabled,
    key="test_mode_enabled",
    help="Show sample application templates on Application page for testing workflows",
)

if test_mode != st.session_state.test_mode_enabled:
    st.session_state.test_mode_enabled = test_mode

st.markdown("---")

st.markdown("## Applicant Communication")

# Initialize session state
if "show_results_to_applicants" not in st.session_state:
    st.session_state.show_results_to_applicants = False

show_results = st.toggle(
    "Display underwriting decision immediately after submission?",
    value=st.session_state.show_results_to_applicants,
    key="show_results_to_applicants",
    help="If OFF: Applicants see 'Application received' message. If ON: Applicants see underwriting decision.",
)

if show_results != st.session_state.show_results_to_applicants:
    st.session_state.show_results_to_applicants = show_results
    st.success("✓ Setting saved")

st.markdown("---")

st.markdown("## Staff Portal Access Control")

# Initialize backend auth setting
if "require_dashboard_auth" not in st.session_state:
    st.session_state.require_dashboard_auth = False

require_auth = st.toggle(
    "🔒 Require authentication to access Portfolio & Review Queue?",
    value=st.session_state.require_dashboard_auth,
    key="require_dashboard_auth",
    help="If ON: Only authenticated staff can access underwriting portfolio. If OFF: Dashboard is public (testing only).",
)

if require_auth != st.session_state.require_dashboard_auth:
    st.session_state.require_dashboard_auth = require_auth
    st.success("✓ Setting saved")

if require_auth:
    st.info("""
    ✅ **Secure Mode**: Dashboard and Review Queue require staff login.
    - Applicants cannot access backend data
    - Only authenticated staff can see application details
    """)
else:
    st.warning("""
    ⚠️ **Public Mode**: Dashboard is accessible without login.
    - Use only for testing/demos
    - Not secure for production
    """)

st.markdown("---")

st.markdown("## Sample Data Management")

col1, col2 = st.columns(2)

with col1:
    if st.button("Regenerate Sample Portfolio", use_container_width=True, type="secondary"):
        from pathlib import Path
        from homeguard.data_generator_stratified import generate_stratified_dataset

        BASE_DIR = Path(__file__).parent.parent
        DATA_DIR = BASE_DIR / "data"

        try:
            # Generate new data
            with st.spinner("Generating 1000 stratified applications..."):
                df = generate_stratified_dataset(total=1000, pct_a=0.70, pct_b=0.20, pct_f=0.10)

            # Save to CSV
            output_path = DATA_DIR / "applications.csv"
            df.to_csv(output_path, index=False)

            st.success("✓ Sample portfolio regenerated! Refresh Dashboard to view updated data.")
            st.balloons()
        except Exception as e:
            st.error(f"Error regenerating portfolio: {str(e)}")

with col2:
    if st.button("📊 View Current Distribution", use_container_width=True, type="secondary"):
        import pandas as pd
        from pathlib import Path

        BASE_DIR = Path(__file__).parent.parent
        DATA_DIR = BASE_DIR / "data"

        try:
            df = pd.read_csv(DATA_DIR / "applications.csv")
            a = (df["prior_claim_count_5y"] == 0).sum()
            b = (df["prior_claim_count_5y"] == 2).sum()
            f = (df["prior_claim_count_5y"] >= 3).sum()
            total = len(df)

            col_a, col_b, col_f = st.columns(3)
            with col_a:
                st.metric("Category A", f"{a} ({a/total*100:.1f}%)", "Auto-Pass")
            with col_b:
                st.metric("Category B", f"{b} ({b/total*100:.1f}%)", "Needs Review")
            with col_f:
                st.metric("Category F", f"{f} ({f/total*100:.1f}%)", "Auto-Reject")
        except Exception as e:
            st.error(f"Error loading data: {e}")

st.markdown("---")

st.markdown("## Staff Credentials")

st.markdown("_Demo credentials for testing:_")
st.code("""
Username: admin
Password: admin123
""")

st.markdown("""
**In production:** Replace these with secure credentials stored in environment variables.
""")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    if st.button("📊 Go to Dashboard", use_container_width=True):
        st.switch_page("pages/3_Dashboard.py")

with col2:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.staff_authenticated = False
        st.rerun()
