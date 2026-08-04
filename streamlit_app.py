from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from homeguard.config import APP_SUBTITLE, APP_TITLE, DISPLAY_STATUS_ORDER, STATUS_DESCRIPTIONS
from homeguard.validation import (
    build_audit_log,
    completeness_score,
    enrich_dataframe,
    evaluate_portfolio,
    explode_flags,
    route_application,
    verification_tools_dataframe,
)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
:root {
  --card-bg: rgba(255,255,255,0.75);
  --card-border: rgba(0,0,0,0.08);
  --muted: #667085;
}
.block-container {padding-top: 1.2rem; padding-bottom: 3rem;}
.hero {
  padding: 1.4rem 1.6rem;
  border-radius: 1.25rem;
  background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 45%, #0f766e 100%);
  color: white;
  margin-bottom: 1rem;
  box-shadow: 0 20px 55px rgba(15, 23, 42, .18);
}
.hero h1 {font-size: 2.2rem; margin-bottom: .25rem;}
.hero p {font-size: 1.05rem; opacity: .92; margin-bottom: 0;}
.metric-card {
  padding: 1rem 1rem;
  border: 1px solid var(--card-border);
  border-radius: 1rem;
  background: var(--card-bg);
  box-shadow: 0 8px 25px rgba(16, 24, 40, .08);
}
.metric-label {font-size: .78rem; color: #667085; margin-bottom: .25rem; text-transform: uppercase; letter-spacing: .04em;}
.metric-value {font-size: 1.8rem; font-weight: 800; line-height: 1.1;}
.metric-help {font-size: .78rem; color: #667085; margin-top: .3rem;}
.status-pill {
  padding: .4rem .7rem;
  border-radius: 999px;
  font-weight: 800;
  display: inline-block;
  color: #0f172a;
}
.good {background: #dcfce7; color: #166534;}
.info {background: #dbeafe; color: #1d4ed8;}
.warn {background: #fef3c7; color: #92400e;}
.bad {background: #fee2e2; color: #991b1b;}
.small-note {color: #667085; font-size: .88rem;}
.section-card {
  border: 1px solid rgba(0,0,0,.08);
  border-radius: 1rem;
  padding: 1rem;
  background: rgba(255,255,255,.7);
  margin-bottom: 1rem;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / name)


@st.cache_data(show_spinner=False)
def load_sample_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    apps = load_csv("applications.csv")
    state_rules = load_csv("state_ai_rules.csv")
    factor_matrix = load_csv("factor_permissions.csv")
    carrier_rules = load_csv("carrier_appetite_rules.csv")
    return apps, state_rules, factor_matrix, carrier_rules


def metric_card(label: str, value: str, help_text: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value}</div>
          <div class="metric-help">{help_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_class(status: str) -> str:
    if status == "STP-ready":
        return "good"
    if status == "Request Info":
        return "info"
    if status == "Refer to Underwriter":
        return "warn"
    return "bad"


def status_pill(status: str) -> str:
    return f'<span class="status-pill {status_class(status)}">{status}</span>'


def as_percent(num: float) -> str:
    if pd.isna(num):
        return "—"
    return f"{num:.1%}"


def readable_table(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if col.endswith("_pct") or col.endswith("_ratio") or col == "completeness_score":
            out[col] = out[col].apply(lambda x: f"{x:.1%}" if pd.notna(x) else "—")
    return out


apps_sample, state_rules, factor_matrix, carrier_rules = load_sample_data()

st.sidebar.title("🏠 HomeGuard UW")
st.sidebar.caption("Pre-pricing homeowners underwriting validation POC")

uploaded_file = st.sidebar.file_uploader("Upload applications CSV", type=["csv"])
if uploaded_file is not None:
    try:
        apps_raw = pd.read_csv(uploaded_file)
        st.sidebar.success("Uploaded CSV loaded")
    except Exception as exc:
        st.sidebar.error(f"Could not load uploaded CSV: {exc}")
        apps_raw = apps_sample.copy()
else:
    apps_raw = apps_sample.copy()

apps = enrich_dataframe(apps_raw)
evaluated = evaluate_portfolio(apps)
portfolio = apps.merge(evaluated, on="app_id", how="left")
flags = explode_flags(apps)
audit = build_audit_log(apps)

state_options = ["All"] + sorted([x for x in portfolio["state"].dropna().unique()])
status_options = ["All"] + DISPLAY_STATUS_ORDER
state_filter = st.sidebar.selectbox("State filter", state_options)
status_filter = st.sidebar.selectbox("Routing status filter", status_options)

filtered = portfolio.copy()
if state_filter != "All":
    filtered = filtered[filtered["state"] == state_filter]
if status_filter != "All":
    filtered = filtered[filtered["status"] == status_filter]

st.markdown(
    f"""
    <div class="hero">
      <h1>{APP_TITLE}</h1>
      <p>{APP_SUBTITLE}. This demo validates applications, property data, claims indicators, hazard factors, and AI/compliance guardrails before any pricing workflow.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.info(
    "Scope note: this POC does **not** set premiums, bind coverage, or auto-deny homeowners policies. "
    "It prepares a validated, auditable pre-pricing underwriting file and routes exceptions to humans."
)

tabs = st.tabs(
    [
        "1 · Executive Overview",
        "2 · Application Validator",
        "3 · Verification Tools",
        "4 · Rules & Regulation Matrix",
        "5 · Human Review Queue",
        "6 · Audit Log",
        "7 · Data / GitHub Notes",
    ]
)

with tabs[0]:
    total = len(filtered)
    status_counts = filtered["status"].value_counts().to_dict()
    stp_pct = status_counts.get("STP-ready", 0) / total if total else 0
    request_pct = status_counts.get("Request Info", 0) / total if total else 0
    refer_pct = status_counts.get("Refer to Underwriter", 0) / total if total else 0
    hold_pct = status_counts.get("Compliance Hold", 0) / total if total else 0
    avg_completeness = filtered["completeness_score"].mean() if total else 0
    match_rate = (filtered["property_match_status"] == "Matched").mean() if total else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Applications", str(total), "Filtered portfolio count")
    with c2:
        metric_card("% STP-ready", as_percent(stp_pct), "Clean enough for downstream pricing workflow")
    with c3:
        metric_card("Avg. completeness", as_percent(avg_completeness), "Required field completion")
    with c4:
        metric_card("Property match rate", as_percent(match_rate), "Exact property/parcel match")

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        metric_card("Request-info rate", as_percent(request_pct), "Needs missing/corrected data")
    with c6:
        metric_card("Referral rate", as_percent(refer_pct), "Needs human underwriting judgment")
    with c7:
        metric_card("Compliance holds", as_percent(hold_pct), "Restricted factor or governance issue")
    with c8:
        avg_flags = filtered["flag_count"].mean() if total else 0
        metric_card("Avg. flags / app", f"{avg_flags:.1f}", "Risk, validation, or compliance flags")

    st.divider()

    left, right = st.columns([1.1, 1])
    with left:
        st.subheader("Routing Outcomes")
        routing_df = (
            filtered["status"]
            .value_counts()
            .reindex(DISPLAY_STATUS_ORDER, fill_value=0)
            .reset_index()
        )
        routing_df.columns = ["status", "count"]
        fig = px.bar(
            routing_df,
            x="status",
            y="count",
            text="count",
            title="Pre-pricing routing distribution",
        )
        fig.update_layout(height=390, margin=dict(l=20, r=20, t=55, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Why Files Are Not STP-ready")
        if flags.empty:
            st.success("No flags in current filter.")
        else:
            flag_counts = flags[flags["app_id"].isin(filtered["app_id"])]
            factor_counts = flag_counts["factor"].value_counts().head(10).reset_index()
            factor_counts.columns = ["factor", "count"]
            fig2 = px.bar(
                factor_counts,
                x="count",
                y="factor",
                orientation="h",
                text="count",
                title="Top validation/risk/compliance flags",
            )
            fig2.update_layout(height=390, margin=dict(l=20, r=20, t=55, b=20))
            st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Portfolio View")
    cols = [
        "app_id",
        "applicant_name",
        "state",
        "city",
        "status",
        "completeness_score",
        "property_match_status",
        "roof_age",
        "roof_condition_ai",
        "prior_claim_count_5y",
        "wildfire_score",
        "flood_zone",
        "wind_hail_score",
        "reason_summary",
    ]
    st.dataframe(readable_table(filtered[cols]), use_container_width=True, hide_index=True)

with tabs[1]:
    st.subheader("Single Application Validator")
    selected_app = st.selectbox(
        "Select application",
        options=portfolio["app_id"].tolist(),
        format_func=lambda app_id: f"{app_id} — {portfolio.loc[portfolio['app_id'] == app_id, 'applicant_name'].iloc[0]}",
    )
    row = apps[apps["app_id"] == selected_app].iloc[0]
    routed = route_application(row)
    score, missing_required, missing_critical = completeness_score(row)

    left, right = st.columns([1, 1])
    with left:
        st.markdown("### Validation Result")
        st.markdown(status_pill(routed["status"]), unsafe_allow_html=True)
        st.caption(STATUS_DESCRIPTIONS.get(routed["status"], ""))
        st.progress(score, text=f"Data completeness: {score:.1%}")
        st.write("**Reason summary:**")
        st.write(routed["reason_summary"])

    with right:
        st.markdown("### Application Snapshot")
        snapshot = pd.DataFrame(
            [
                ["Applicant", row.get("applicant_name")],
                ["State", row.get("state")],
                ["Address", f"{row.get('address')}, {row.get('city')} {row.get('zip_code')}"],
                ["Occupancy", row.get("occupancy")],
                ["Property Match", row.get("property_match_status")],
                ["Roof", f"{row.get('roof_age')} yrs · {row.get('roof_material')} · {row.get('roof_condition_ai')}"],
                ["Claims 5Y", f"{row.get('prior_claim_count_5y')} claim(s), ${row.get('claim_total_paid_5y'):,.0f} paid"],
                ["Hazards", f"Wildfire {row.get('wildfire_score')} · Wind/Hail {row.get('wind_hail_score')} · Flood {row.get('flood_zone')}"],
            ],
            columns=["Field", "Value"],
        )
        st.dataframe(snapshot, use_container_width=True, hide_index=True)

    st.markdown("### Verification Flags")
    flag_df = pd.DataFrame(routed["flags"])
    if flag_df.empty:
        st.success("No validation, risk, or compliance flags detected for this application.")
    else:
        st.dataframe(flag_df, use_container_width=True, hide_index=True)

    st.markdown("### Suggested Next Actions")
    if routed["status"] == "STP-ready":
        st.success("Proceed to downstream rating/pricing workflow. No manual pre-pricing validation required in this POC.")
    elif routed["status"] == "Request Info":
        st.warning("Request corrected or missing data from customer/agent before pricing workflow.")
        if missing_required:
            st.write("Missing required fields:", ", ".join(missing_required))
    elif routed["status"] == "Refer to Underwriter":
        st.warning("Prepare underwriter packet and route for manual review.")
    else:
        st.error("Send to compliance/legal governance queue before the file proceeds.")

    st.markdown("### Pre-Pricing Validation Math")
    calc_table = pd.DataFrame(
        [
            ["Coverage-to-replacement-cost ratio", f"{row.get('coverage_to_rc_ratio'):.1%}" if pd.notna(row.get("coverage_to_rc_ratio")) else "—"],
            ["Square footage variance", f"{row.get('sqft_variance_pct'):.1%}" if pd.notna(row.get("sqft_variance_pct")) else "—"],
            ["Roof condition confidence", f"{row.get('roof_condition_confidence'):.1%}" if pd.notna(row.get("roof_condition_confidence")) else "—"],
            ["Completeness score", f"{score:.1%}"],
        ],
        columns=["Metric", "Value"],
    )
    st.dataframe(calc_table, use_container_width=True, hide_index=True)

with tabs[2]:
    st.subheader("Verification Tools for Personal Homeowners Insurance")
    st.write(
        "These are the tools/modules this POC is meant to represent. The design goal is to validate, enrich, flag, and route the file before pricing."
    )
    tools_df = verification_tools_dataframe()
    st.dataframe(tools_df, use_container_width=True, hide_index=True)

    st.markdown("### AI-driven vs. human-governed split")
    ai_col, human_col = st.columns(2)
    with ai_col:
        st.markdown("""
        **AI / automation should handle:**
        - Missing-field detection
        - Address normalization and property matching
        - Public/vendor data comparison
        - Claims summarization
        - Hazard flagging
        - Roof-condition assistance
        - State-factor permission checks
        - Routing recommendation
        - Audit-log drafting
        """)
    with human_col:
        st.markdown("""
        **Humans should govern:**
        - Final underwriting authority
        - Carrier appetite thresholds
        - Exceptions and adverse decisions
        - State-specific compliance interpretation
        - Fairness/proxy-bias review
        - Model changes and overrides
        - Customer/agent adverse explanations
        - Final pricing and binding workflows
        """)

with tabs[3]:
    st.subheader("Regulatory & Factor Rules Explorer")
    st.caption("Starter matrix only. Treat this as POC reference content, not legal advice or final compliance approval.")

    rule_tab, factor_tab, carrier_tab = st.tabs(["Regulatory Matrix", "Factor Permission Matrix", "Mock Carrier Appetite Rules"])
    with rule_tab:
        jurisdiction_filter = st.multiselect(
            "Filter jurisdiction",
            sorted(state_rules["jurisdiction"].unique()),
            default=sorted(state_rules["jurisdiction"].unique()),
        )
        st.dataframe(state_rules[state_rules["jurisdiction"].isin(jurisdiction_filter)], use_container_width=True, hide_index=True)

    with factor_tab:
        factor_status = st.multiselect(
            "Filter factor status",
            sorted(factor_matrix["poc_status"].unique()),
            default=sorted(factor_matrix["poc_status"].unique()),
        )
        st.dataframe(factor_matrix[factor_matrix["poc_status"].isin(factor_status)], use_container_width=True, hide_index=True)

    with carrier_tab:
        st.write(
            "This is a fictional homeowners carrier appetite ruleset. Replace these rows with approved real carrier rules after compliance/legal review."
        )
        st.dataframe(carrier_rules, use_container_width=True, hide_index=True)

with tabs[4]:
    st.subheader("Human Review Queue")
    queue = filtered[filtered["status"].isin(["Refer to Underwriter", "Compliance Hold", "Request Info"])]
    st.write(
        "This queue shows applications that should not go straight through the pre-pricing workflow."
    )
    if queue.empty:
        st.success("No items in the current review queue.")
    else:
        queue_cols = [
            "app_id",
            "applicant_name",
            "state",
            "status",
            "completeness_score",
            "property_match_status",
            "roof_age",
            "roof_condition_ai",
            "prior_claim_count_5y",
            "claim_total_paid_5y",
            "wildfire_score",
            "flood_zone",
            "wind_hail_score",
            "reason_summary",
        ]
        st.dataframe(readable_table(queue[queue_cols]), use_container_width=True, hide_index=True)

        selected_queue_app = st.selectbox("Open review item", queue["app_id"].tolist())
        queue_row = apps[apps["app_id"] == selected_queue_app].iloc[0]
        review_flags = pd.DataFrame(route_application(queue_row)["flags"])
        st.markdown("### Underwriter Packet")
        st.json(
            {
                "app_id": selected_queue_app,
                "applicant": queue_row.get("applicant_name"),
                "state": queue_row.get("state"),
                "recommended_route": route_application(queue_row)["status"],
                "reason_summary": route_application(queue_row)["reason_summary"],
                "questions_to_agent_or_customer": [
                    "Confirm roof age and most recent roof update/inspection.",
                    "Confirm owner-occupied status and intended use of property.",
                    "Provide documentation for any prior water loss repairs.",
                    "Confirm whether flood coverage should be quoted separately if applicable.",
                ],
            }
        )
        st.dataframe(review_flags, use_container_width=True, hide_index=True)

with tabs[5]:
    st.subheader("Audit Log")
    st.write(
        "Every evaluated application creates an audit record with data sources, AI tools used, model/rule versions, routing status, and reason codes."
    )
    audit_filtered = audit[audit["app_id"].isin(filtered["app_id"])]
    st.dataframe(audit_filtered, use_container_width=True, hide_index=True)

    csv_buffer = io.StringIO()
    audit_filtered.to_csv(csv_buffer, index=False)
    st.download_button(
        "Download audit log CSV",
        csv_buffer.getvalue(),
        file_name="homeguard_audit_log.csv",
        mime="text/csv",
    )

with tabs[6]:
    st.subheader("Data Upload + GitHub Notes")
    st.markdown(
        """
        ### Expected application CSV columns
        Upload a CSV that follows the sample data schema in `data/applications.csv`. The app will calculate:
        - `coverage_to_rc_ratio`
        - `sqft_variance_pct`
        - completeness score
        - validation flags
        - compliance flags
        - final pre-pricing route

        ### Local run command
        ```bash
        pip install -r requirements.txt
        streamlit run app.py
        ```

        ### GitHub upload flow
        ```bash
        git init
        git add .
        git commit -m "Initial HomeGuard UW Validator POC"
        git branch -M main
        git remote add origin https://github.com/YOUR-USERNAME/homeguard-uw-validator.git
        git push -u origin main
        ```

        ### What to customize next
        1. Replace mock applications with approved synthetic/demo data.
        2. Replace `carrier_appetite_rules.csv` with real carrier-approved rules.
        3. Add API connectors for property, geocoding, hazard, and claims vendors.
        4. Add authentication if this ever touches real customer data.
        5. Add legal/compliance review before using any AI output in regulated decisions.
        """
    )

    st.markdown("### Current loaded dataset")
    st.dataframe(apps_raw, use_container_width=True, hide_index=True)
