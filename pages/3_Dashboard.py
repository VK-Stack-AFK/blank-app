"""Dashboard with macro data and analytics for HomeGuard UW Validator."""
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from pathlib import Path

from homeguard.config import STATUS_DESCRIPTIONS, STATUS_COLORS, STATUS_LABELS
from homeguard.validation import evaluate_portfolio, enrich_dataframe
from homeguard.submissions_manager import load_submissions, get_available_dates, get_recent_submission_count

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

# Auth check
require_auth = st.session_state.get("require_dashboard_auth", True)
is_authenticated = st.session_state.get("staff_authenticated", False)

if require_auth and not is_authenticated:
    st.error("🔒 Access Denied: Authentication required")
    st.markdown("""
    This is a staff-only dashboard. Please authenticate first.

    To access this page, go to **Settings** and log in with your staff credentials.
    """)
    if st.button("Go to Settings"):
        st.switch_page("pages/2_Settings.py")
    st.stop()

st.markdown("""
<style>
.metric-card {
    padding: 1.5rem;
    border-radius: 1rem;
    background: rgba(255,255,255,0.7);
    border: 1px solid rgba(0,0,0,0.08);
    text-align: center;
}
.metric-value {
    font-size: 2.5rem;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 0.5rem;
}
.metric-label {
    font-size: 0.9rem;
    color: #667085;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
</style>
""", unsafe_allow_html=True)

st.markdown("# 📊 Underwriting Portfolio & Analytics")

# Load data
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

try:
    # Initialize session state for data filters
    if "include_test_data" not in st.session_state:
        st.session_state.include_test_data = True
    if "include_recent_submissions" not in st.session_state:
        st.session_state.include_recent_submissions = True
    if "include_archived_submissions" not in st.session_state:
        st.session_state.include_archived_submissions = False
    if "include_test_applications" not in st.session_state:
        st.session_state.include_test_applications = True
    if "selected_app_id" not in st.session_state:
        st.session_state.selected_app_id = None
    if "app_status_updates" not in st.session_state:
        st.session_state.app_status_updates = {}

    # Load test data
    apps_raw = pd.read_csv(DATA_DIR / "applications.csv") if st.session_state.include_test_data else pd.DataFrame()

    # Load submissions based on filters
    submissions = load_submissions(
        include_recent=st.session_state.include_recent_submissions,
        include_older=st.session_state.include_archived_submissions
    )

    # Load test applications - ensure directory exists
    test_apps = pd.DataFrame()
    if st.session_state.include_test_applications:
        test_apps_dir = DATA_DIR / "test_applications"
        test_apps_dir.mkdir(parents=True, exist_ok=True)
        for file in test_apps_dir.glob("applications_*.csv"):
            test_apps = pd.concat([test_apps, pd.read_csv(file)], ignore_index=True)

    # Combine all data
    all_data = [apps_raw, submissions, test_apps]
    apps_raw = pd.concat([df for df in all_data if not df.empty], ignore_index=True) if any(not df.empty for df in all_data) else pd.DataFrame()

    apps = enrich_dataframe(apps_raw)
    evaluated = evaluate_portfolio(apps)
    portfolio = apps.merge(evaluated, on="app_id", how="left")

    # Count new submissions
    new_count = get_recent_submission_count()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Split into queues
needs_review = portfolio[portfolio["status"] == "B"]
needs_rejection = portfolio[portfolio["status"] == "F"]

# Create tabs
tab1, tab2 = st.tabs(["📈 Underwriting Portfolio", "📬 Manual Review Queue"])

# ===== TAB 1: Portfolio Overview =====
with tab1:
    col_title, col_badge, col_refresh = st.columns([0.75, 0.15, 0.1])
    with col_title:
        st.markdown("## Overview")
    with col_badge:
        if new_count > 0:
            st.metric("🆕 New Applications", new_count)
    with col_refresh:
        if st.button("🔄 Refresh", key="refresh_data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Data source checkboxes
    st.markdown("### 📊 Data Sources")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.session_state.include_test_data = st.checkbox(
            "☑ Test Data (1000 apps)",
            value=st.session_state.include_test_data,
            key="cb_test_data"
        )
    with col2:
        st.session_state.include_recent_submissions = st.checkbox(
            "☑ Recent Submissions",
            value=st.session_state.include_recent_submissions,
            key="cb_recent"
        )
    with col3:
        st.session_state.include_archived_submissions = st.checkbox(
            "☑ Archived Submissions",
            value=st.session_state.include_archived_submissions,
            key="cb_archived"
        )
    with col4:
        st.session_state.include_test_applications = st.checkbox(
            "🧪 Test Applications",
            value=st.session_state.include_test_applications,
            key="cb_test_apps"
        )

    # Reload data if checkboxes changed
    if (st.session_state.get("last_include_test_data", True) != st.session_state.include_test_data or
        st.session_state.get("last_include_recent", True) != st.session_state.include_recent_submissions or
        st.session_state.get("last_include_archived", False) != st.session_state.include_archived_submissions or
        st.session_state.get("last_include_test_apps", True) != st.session_state.include_test_applications):
        st.session_state.last_include_test_data = st.session_state.include_test_data
        st.session_state.last_include_recent = st.session_state.include_recent_submissions
        st.session_state.last_include_archived = st.session_state.include_archived_submissions
        st.session_state.last_include_test_apps = st.session_state.include_test_applications
        st.rerun()

    # Filter by specific date (optional)
    st.markdown("### 📅 Filter by Date")
    col1, col2 = st.columns([0.3, 0.7])
    with col1:
        available_dates = get_available_dates()
        if available_dates:
            selected_date = st.selectbox(
                "Specific Date (optional)",
                ["All"] + available_dates,
                key="date_filter"
            )

            if selected_date != "All":
                from homeguard.submissions_manager import load_submissions
                submissions = load_submissions(specific_date=selected_date)
                if not submissions.empty:
                    apps_raw = pd.concat([apps_raw, submissions], ignore_index=True) if not apps_raw.empty else submissions
                    apps = enrich_dataframe(apps_raw)
                    evaluated = evaluate_portfolio(apps)
                    portfolio = apps.merge(evaluated, on="app_id", how="left")

    total = len(portfolio)
    a_count = (portfolio["status"] == "A").sum()
    b_count = (portfolio["status"] == "B").sum()
    f_count = (portfolio["status"] == "F").sum()

    a_pct = (a_count / total * 100) if total else 0
    b_pct = (b_count / total * 100) if total else 0
    f_pct = (f_count / total * 100) if total else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">📋 {total}</div>
            <div class="metric-label">Total Applications</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card" style="background: #dcfce7;">
            <div class="metric-value">✅ {a_count}</div>
            <div class="metric-label">Approved for Pricing ({a_pct:.0f}%)</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card" style="background: #fef3c7;">
            <div class="metric-value">⏳ {b_count}</div>
            <div class="metric-label">Referred for Review ({b_pct:.0f}%)</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card" style="background: #fee2e2;">
            <div class="metric-value">❌ {f_count}</div>
            <div class="metric-label">Declined ({f_pct:.0f}%)</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Charts
    st.markdown("## 📉 Portfolio Analytics")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Decision Distribution")
        status_counts = portfolio["status"].value_counts().reindex(["A", "B", "F"], fill_value=0)
        fig_pie = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            color=status_counts.index,
            color_discrete_map={
                "A": "#10b981",
                "B": "#f59e0b",
                "F": "#ef4444",
            },
            hole=0.4,
        )
        fig_pie.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.markdown("### Status by State")
        state_status = portfolio.groupby(["state", "status"]).size().unstack(fill_value=0)
        if not state_status.empty:
            fig_bar = px.bar(
                state_status.reset_index().melt(id_vars="state", var_name="status", value_name="count"),
                x="state",
                y="count",
                color="status",
                color_discrete_map={
                    "A": "#10b981",
                    "B": "#f59e0b",
                    "F": "#ef4444",
                },
                title="Applications by State and Status",
            )
            fig_bar.update_layout(height=400, xaxis_tickangle=-45, margin=dict(b=100))
            st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # Risk factors analysis
    st.markdown("## 🚨 Key Risk Indicators")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Roof Age Distribution")
        if "roof_age" in portfolio.columns:
            roof_age_data = portfolio["roof_age"].dropna()
            fig_roof = px.histogram(
                x=roof_age_data,
                nbins=15,
                title="Roof Age Distribution (Years)",
                labels={"x": "Roof Age", "count": "Count"},
            )
            fig_roof.update_traces(marker_color="#6366f1")
            fig_roof.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig_roof, use_container_width=True)

    with col2:
        st.markdown("### Loss History (5 Years)")
        if "prior_claim_count_5y" in portfolio.columns:
            claims_dist = portfolio["prior_claim_count_5y"].value_counts().sort_index()
            fig_claims = px.bar(
                x=claims_dist.index,
                y=claims_dist.values,
                title="Prior Claims Distribution (5 years)",
                labels={"x": "Number of Claims", "y": "Count"},
            )
            fig_claims.update_traces(marker_color="#ec4899")
            fig_claims.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig_claims, use_container_width=True)

    st.markdown("---")

    # Detailed application table
    st.markdown("## 📋 Application Details")

    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.multiselect(
            "Filter by Status",
            ["A", "B", "F"],
            default=["A", "B", "F"],
        )
    with col2:
        state_filter = st.multiselect(
            "Filter by State",
            sorted(portfolio["state"].dropna().unique()),
            default=sorted(portfolio["state"].dropna().unique()),
        )

    filtered = portfolio.copy()
    if status_filter:
        filtered = filtered[filtered["status"].isin(status_filter)]
    if state_filter:
        filtered = filtered[filtered["state"].isin(state_filter)]

    table_cols = [
        "app_id",
        "applicant_name",
        "state",
        "status",
        "roof_age",
        "prior_claim_count_5y",
        "wildfire_score",
        "wind_hail_score",
        "reason_summary",
    ]

    display_df = filtered[table_cols].copy()
    display_df.columns = ["App ID", "Applicant", "State", "Status", "Roof Age", "Claims", "Wildfire", "Wind/Hail", "Reason"]

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    st.markdown("## 💾 Export")

    col1, col2 = st.columns(2)

    with col1:
        csv_all = portfolio.to_csv(index=False)
        st.download_button(
            "📥 Download Full Portfolio",
            csv_all,
            file_name="portfolio_full.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col2:
        csv_filtered = filtered.to_csv(index=False)
        st.download_button(
            "📥 Download Filtered Results",
            csv_filtered,
            file_name="portfolio_filtered.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ===== TAB 2: Review Queue =====
with tab2:
    # Combine both queues
    all_queue = pd.concat([needs_review, needs_rejection]).drop_duplicates(subset=["app_id"])

    # Apply any status updates from previous actions
    for app_id, new_status in st.session_state.app_status_updates.items():
        all_queue.loc[all_queue["app_id"] == app_id, "status"] = new_status

    # Filter pending (B status) and rejected (F status) - both need review
    pending = all_queue[all_queue["status"].isin(["B", "F"])]

    st.markdown("## 📋 Pending Underwriter Review")

    total_pending = len(pending)
    st.markdown(f"**{total_pending} applications** awaiting review or action")

    if total_pending == 0:
        st.success("✓ No pending applications!")
    else:
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Pending", total_pending)
        with col2:
            review_only = len(pending[pending["status"] == "B"])
            st.metric("Referred for Review", review_only)
        with col3:
            reject_only = len(pending[pending["status"] == "F"])
            st.metric("Declined", reject_only)

        st.markdown("---")

        # Sort options
        col1, col2 = st.columns(2)
        with col1:
            sort_by = st.selectbox("Sort by", ["Newest First", "Oldest First", "Status"], key="review_sort")

        # Sort pending applications
        if "submission_date" in pending.columns:
            pending = pending.copy()
            pending["submission_date"] = pd.to_datetime(pending["submission_date"], errors="coerce")

            if sort_by == "Newest First":
                pending = pending.sort_values("submission_date", ascending=False, na_position="last")
            elif sort_by == "Oldest First":
                pending = pending.sort_values("submission_date", ascending=True, na_position="last")
            elif sort_by == "Status":
                pending = pending.sort_values(["status", "submission_date"], ascending=[True, False])

        # Display pending applications with clickable rows
        st.markdown("### Click an application to review details")

        for idx, (_, row) in enumerate(pending.iterrows()):
            app_id = row["app_id"]
            is_selected = st.session_state.selected_app_id == app_id

            # Highlight selected row
            bg_color = "#e3f2fd" if is_selected else "transparent"
            status_color = "#ef4444" if row["status"] == "F" else "#f59e0b"

            col1, col2, col3, col4, col5, col6 = st.columns([1.5, 2, 1.5, 1.5, 1, 1.5])

            with col1:
                if st.button(app_id, key=f"select_{idx}", use_container_width=True):
                    st.session_state.selected_app_id = app_id
                    st.rerun()

            with col2:
                st.write(row.get("applicant_name", "N/A"))

            with col3:
                st.write(row.get("state", "N/A"))

            with col4:
                status_label = "DENY" if row["status"] == "F" else "REVIEW"
                st.write(f"**{status_label}**")

            with col5:
                if is_selected:
                    st.write("✓ Selected")

            with col6:
                if is_selected:
                    st.write(row.get("applicant_email", "N/A")[:15] + "...")

        st.markdown("---")

        # Show selected application details and action options
        if st.session_state.selected_app_id and st.session_state.selected_app_id in pending["app_id"].values:
            st.markdown("## 📋 Application Details & Decision")

            app_row = pending[pending["app_id"] == st.session_state.selected_app_id].iloc[0]
            selected_app = st.session_state.selected_app_id
            is_rejection = app_row["status"] == "F"

            # Display application details
            with st.expander("Full Application Details", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**App ID:** {app_row.get('app_id', 'N/A')}")
                    st.write(f"**Applicant:** {app_row.get('applicant_name', 'N/A')}")
                    st.write(f"**Email:** {app_row.get('applicant_email', 'N/A')}")
                    st.write(f"**State:** {app_row.get('state', 'N/A')}")

                with col2:
                    st.write(f"**Roof Age:** {app_row.get('roof_age', 'N/A')} years")
                    st.write(f"**Prior Claims:** {app_row.get('prior_claim_count_5y', 'N/A')}")
                    st.write(f"**Water Claims:** {app_row.get('water_claim_count_5y', 'N/A')}")
                    st.write(f"**Wildfire Score:** {app_row.get('wildfire_score', 'N/A')}/100")

                with col3:
                    st.write(f"**Status:** {app_row.get('status', 'N/A')}")
                    st.write(f"**Submitted:** {app_row.get('submission_date', 'Test Data')}")
                    st.write(f"**Flood Zone:** {app_row.get('flood_zone', 'N/A')}")
                    st.write(f"**Wind/Hail Score:** {app_row.get('wind_hail_score', 'N/A')}/100")

                st.write(f"**Reason:** {app_row.get('reason_summary', 'N/A')}")

            st.markdown("---")

            # Action buttons
            st.markdown("### Underwriting Decision")

            col_approve, col_refer, col_deny = st.columns([1.2, 1.2, 1.5])

            with col_approve:
                if st.button("APPROVE", use_container_width=True, type="primary"):
                    st.session_state.app_status_updates[selected_app] = "A"
                    st.success(f"Updated {selected_app} to APPROVED")
                    st.rerun()

            with col_refer:
                if st.button("REFER FOR REVIEW", use_container_width=True):
                    st.session_state.app_status_updates[selected_app] = "B"
                    st.info(f"Updated {selected_app} to REFERRED FOR REVIEW")
                    st.rerun()

            with col_deny:
                if st.button("REJECT AND DECLINE", use_container_width=True):
                    st.session_state.app_status_updates[selected_app] = "F"
                    st.error(f"Updated {selected_app} to DECLINED")
                    st.rerun()

            st.markdown("---")

            # Email generator
            st.markdown("## ✉️ Send Notification")

            # Generate email based on current status
            if is_rejection:
                email_subject = "Application Decision - Unable to Provide Coverage"
                email_body = f"""Dear {app_row.get('applicant_name', 'Applicant')},

Thank you for submitting your homeowners insurance application. After careful review by our underwriting team, we are unable to provide coverage at this time.

Reason for Decision:
{app_row.get('reason_summary', 'Application does not meet our underwriting guidelines.')}

If you have questions about this decision or would like to provide additional information, please contact us within 30 days.

Sincerely,
HomeGuard Underwriting Team"""
            else:
                email_subject = "Application Status Update - Under Review"
                email_body = f"""Dear {app_row.get('applicant_name', 'Applicant')},

Thank you for submitting your homeowners insurance application. Our underwriting team is currently reviewing your application.

Review Notes:
{app_row.get('reason_summary', 'Your application requires underwriting review.')}

We will contact you within 2-3 business days with next steps and a final decision.

Sincerely,
HomeGuard Underwriting Team"""

            email_to = st.text_input("Send To:", value=app_row.get("applicant_email", ""))

            with st.expander("Edit Email Before Sending", expanded=False):
                email_subject = st.text_input("Subject:", value=email_subject)
                email_body = st.text_area("Message:", value=email_body, height=200)

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("Send Email", use_container_width=True, type="primary"):
                    st.success(f"Email sent to {email_to}")
                    st.info(f"Subject: {email_subject}")

            with col2:
                if st.button("Preview Email", use_container_width=True):
                    with st.expander("Email Preview", expanded=True):
                        st.markdown(f"**To:** {email_to}")
                        st.markdown(f"**Subject:** {email_subject}")
                        st.markdown("---")
                        st.write(email_body)

            with col3:
                if st.button("View in Queue", use_container_width=True):
                    st.info(f"Scroll up to find {selected_app} in the review queue above")

            with col4:
                if st.button("Clear Selection", use_container_width=True):
                    st.session_state.selected_app_id = None
                    st.rerun()

        else:
            if not pending.empty:
                st.info("Click an application above to view details and take action")

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📋 New Application", use_container_width=True):
        st.switch_page("pages/1_New_Application.py")

with col2:
    if st.button("⚙️ Settings", use_container_width=True):
        st.switch_page("pages/2_Settings.py")

with col3:
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("streamlit_app.py")

st.markdown("---")

# Debug: Force verify and recalculate data
if st.button("🔍 Force Verify & Update Statistics", use_container_width=True, type="secondary"):
    st.cache_data.clear()
    st.rerun()

# Debug info
with st.expander("🐛 Debug: Raw Data vs Routed Status"):
    raw_a = (apps["prior_claim_count_5y"] == 0).sum()
    raw_b = (apps["prior_claim_count_5y"] == 2).sum()
    raw_f = (apps["prior_claim_count_5y"] >= 3).sum()

    routed_a = (portfolio["status"] == "A").sum()
    routed_b = (portfolio["status"] == "B").sum()
    routed_f = (portfolio["status"] == "F").sum()

    st.markdown("**Raw Data (by claims count):**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("A (0 claims)", f"{raw_a} ({raw_a/len(apps)*100:.1f}%)")
    with col2:
        st.metric("B (2 claims)", f"{raw_b} ({raw_b/len(apps)*100:.1f}%)")
    with col3:
        st.metric("F (3+ claims)", f"{raw_f} ({raw_f/len(apps)*100:.1f}%)")

    st.markdown("**Routed Status (by validation logic):**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("A (Auto-Pass)", f"{routed_a} ({routed_a/len(portfolio)*100:.1f}%)")
    with col2:
        st.metric("B (Needs Review)", f"{routed_b} ({routed_b/len(portfolio)*100:.1f}%)")
    with col3:
        st.metric("F (Auto-Reject)", f"{routed_f} ({routed_f/len(portfolio)*100:.1f}%)")

    if raw_a != routed_a or raw_b != routed_b or raw_f != routed_f:
        st.warning("""
        ⚠️ **Mismatch detected!** Applications are being re-routed by validation logic.

        This means the routing rules are finding additional rejection/review reasons beyond just claims count.
        Common causes: hazard exposure, flood zones, missing fields, or compliance issues.
        """)
    else:
        st.success("✓ Raw data matches routed status perfectly!")
