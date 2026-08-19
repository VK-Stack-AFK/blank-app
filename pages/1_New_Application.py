"""Application questionnaire form for HomeGuard UW Validator."""
import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

from homeguard.config import QUESTIONNAIRE_FIELDS, STATUS_DESCRIPTIONS, STATUS_COLORS, STATUS_LABELS
from homeguard.validation import route_application, enrich_dataframe
from homeguard.submissions_manager import save_submission
from homeguard.test_data_generator import generate_test_data_a, generate_test_data_b, generate_test_data_f

st.set_page_config(page_title="New Application", page_icon="📋", layout="wide")

# Custom styling
st.markdown("""
<style>
.form-section {
    background: rgba(255,255,255,0.7);
    border-radius: 1rem;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(0,0,0,0.08);
}
.form-header {
    font-size: 1.3rem;
    font-weight: 600;
    margin-bottom: 1rem;
    color: #0f172a;
}
.result-badge {
    padding: 1rem;
    border-radius: 0.75rem;
    font-weight: 600;
    text-align: center;
    font-size: 1.2rem;
}
.status-green { background: #dcfce7; color: #166534; }
.status-yellow { background: #fef3c7; color: #92400e; }
.status-red { background: #fee2e2; color: #991b1b; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
# 📋 Application Questionnaire

Complete this form to submit your homeowners insurance application for underwriting evaluation.
""")

st.info("All fields marked with * are required for underwriting assessment.")

# Test mode templates
test_mode = st.session_state.get("test_mode_enabled", True)
if test_mode:
    st.markdown("### 🧪 Sample Applications (Auto-fill for Testing)")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Sample: Approved for Pricing", use_container_width=True, type="secondary"):
            st.session_state.test_template = "A"
            st.rerun()

    with col2:
        if st.button("Sample: Referred for Review", use_container_width=True, type="secondary"):
            st.session_state.test_template = "B"
            st.rerun()

    with col3:
        if st.button("Sample: Declined", use_container_width=True, type="secondary"):
            st.session_state.test_template = "F"
            st.rerun()

    st.markdown("---")

# Generate test data if template was selected
test_data = None
if test_mode and st.session_state.get("test_template"):
    if st.session_state.test_template == "A":
        test_data = generate_test_data_a()
    elif st.session_state.test_template == "B":
        test_data = generate_test_data_b()
    elif st.session_state.test_template == "F":
        test_data = generate_test_data_f()

# Create form sections
with st.form(key="application_form"):
    # Section 1: Applicant Information
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown('<div class="form-header">👤 Applicant Information</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        applicant_name = st.text_input("Applicant Name *", placeholder="John Doe", value=test_data.get("applicant_name", "") if test_data else "")
    with col2:
        state_list = sorted([
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
        ])
        state_default = test_data.get("state", "") if test_data else ""
        state_index = state_list.index(state_default) if state_default in state_list else 0
        state = st.selectbox("State *", [""] + state_list, index=state_index + 1 if state_default else 0, label_visibility="visible")

    email = st.text_input("Email *", placeholder="john@example.com", value=test_data.get("applicant_email", "") if test_data else "")

    st.markdown("</div>", unsafe_allow_html=True)

    # Section 2: Property Address
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown('<div class="form-header">🏠 Property Address</div>', unsafe_allow_html=True)

    address = st.text_input("Street Address *", placeholder="123 Main St", value=test_data.get("address", "") if test_data else "")

    col1, col2, col3 = st.columns(3)
    with col1:
        city = st.text_input("City *", placeholder="Springfield", value=test_data.get("city", "") if test_data else "")
    with col2:
        zip_code = st.text_input("ZIP Code *", placeholder="12345", value=test_data.get("zip_code", "") if test_data else "")
    with col3:
        occupancy_default = test_data.get("occupancy", "Owner-occupied") if test_data else "Owner-occupied"
        occupancy = st.selectbox("Occupancy *", ["Owner-occupied", "Seasonal", "Investment"], index=["Owner-occupied", "Seasonal", "Investment"].index(occupancy_default))

    st.markdown("</div>", unsafe_allow_html=True)

    # Section 3: Property Characteristics
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown('<div class="form-header">🏗️ Property Characteristics</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        year_built = st.number_input("Year Built *", min_value=1800, max_value=2025, step=1, value=int(test_data.get("year_built", 2000)) if test_data else 2000)
    with col2:
        roof_age = st.number_input("Roof Age (years) *", min_value=0, max_value=100, step=1, value=int(test_data.get("roof_age", 0)) if test_data else 0)
    with col3:
        roof_materials = ["Architectural Shingle", "3-tab Shingle", "Metal", "Tile", "Wood Shake", "Other"]
        roof_material_default = test_data.get("roof_material", "Architectural Shingle") if test_data else "Architectural Shingle"
        roof_material_idx = roof_materials.index(roof_material_default) if roof_material_default in roof_materials else 0
        roof_material = st.selectbox("Roof Material *", roof_materials, index=roof_material_idx)

    roof_conditions = ["Good", "Fair", "Poor", "Unknown"]
    roof_condition_default = test_data.get("roof_condition_ai", "Good") if test_data else "Good"
    roof_condition_idx = roof_conditions.index(roof_condition_default) if roof_condition_default in roof_conditions else 0
    roof_condition_ai = st.selectbox("Roof Condition *", roof_conditions, index=roof_condition_idx)

    st.markdown("</div>", unsafe_allow_html=True)

    # Section 4: Coverage & Risk Assessment
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown('<div class="form-header">💰 Coverage & Risk Assessment</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        requested_dwelling_limit = st.number_input("Requested Dwelling Limit ($) *", min_value=0, step=10000, value=int(test_data.get("requested_dwelling_limit", 500000)) if test_data else 500000)
    with col2:
        estimated_replacement_cost = st.number_input("Estimated Replacement Cost ($) *", min_value=0, step=10000, value=int(test_data.get("estimated_replacement_cost", 500000)) if test_data else 500000)

    st.markdown("</div>", unsafe_allow_html=True)

    # Section 5: Loss History
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown('<div class="form-header">📋 Loss History (Last 5 Years)</div>', unsafe_allow_html=True)

    st.markdown("_How many insurance claims have you filed in the past 5 years?_")
    col1, col2, col3 = st.columns(3)
    with col1:
        prior_claim_count_5y = st.number_input("Total Claims *", min_value=0, max_value=20, step=1, value=int(test_data.get("prior_claim_count_5y", 0)) if test_data else 0)
    with col2:
        st.markdown("_Water-related claims include: roof leaks, burst pipes, water heater failures, flooding_")
        water_claim_count_5y = st.number_input("Water Claims *", min_value=0, max_value=20, step=1, value=int(test_data.get("water_claim_count_5y", 0)) if test_data else 0)
    with col3:
        claim_total_paid_5y = st.number_input("Total Paid ($) *", min_value=0, step=1000, value=int(test_data.get("claim_total_paid_5y", 0)) if test_data else 0)

    open_claims = st.number_input("Open/Pending Claims *", min_value=0, max_value=20, step=1, value=int(test_data.get("open_claims", 0)) if test_data else 0)
    st.caption("Claims currently under review or awaiting settlement")

    st.markdown("</div>", unsafe_allow_html=True)

    # Section 6: Geographic Risk Factors
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown('<div class="form-header">⚠️ Geographic Risk Factors</div>', unsafe_allow_html=True)

    st.markdown("_If you don't know your scores, enter 0. If you have FEMA flood maps, check your zone._")

    col1, col2 = st.columns(2)
    with col1:
        wildfire_score = st.slider("Wildfire Exposure Score (0-100) *", 0, 100, int(test_data.get("wildfire_score", 50)) if test_data else 50)
        st.caption("Based on proximity to wildland fire risk areas")
    with col2:
        wind_hail_score = st.slider("Wind/Hail Exposure Score (0-100) *", 0, 100, int(test_data.get("wind_hail_score", 50)) if test_data else 50)
        st.caption("Based on area's historical severe weather")

    st.markdown("_Select your flood zone. If unsure, check FEMA Flood Map Service online._")
    flood_zone_options = ["X - No special flood hazard zone (most common)",
                          "A - Special flood hazard zone (1% annual chance)",
                          "AE - Special flood hazard zone (specified BFE)",
                          "V - Coastal flood hazard with velocity",
                          "VE - Coastal flood hazard with specified BFE and velocity",
                          "Other/Unsure"]
    flood_zone_default = test_data.get("flood_zone", "X") if test_data else "X"
    flood_zone_map_reverse = {
        "X": "X - No special flood hazard zone (most common)",
        "A": "A - Special flood hazard zone (1% annual chance)",
        "AE": "AE - Special flood hazard zone (specified BFE)",
        "V": "V - Coastal flood hazard with velocity",
        "VE": "VE - Coastal flood hazard with specified BFE and velocity",
    }
    flood_zone_default_opt = flood_zone_map_reverse.get(flood_zone_default, "X - No special flood hazard zone (most common)")
    flood_zone_idx = flood_zone_options.index(flood_zone_default_opt) if flood_zone_default_opt in flood_zone_options else 0
    flood_zone_opt = st.selectbox(
        "Flood Zone *",
        flood_zone_options,
        index=flood_zone_idx
    )

    # Map display options to codes
    flood_zone_map = {
        "X - No special flood hazard zone (most common)": "X",
        "A - Special flood hazard zone (1% annual chance)": "A",
        "AE - Special flood hazard zone (specified BFE)": "AE",
        "V - Coastal flood hazard with velocity": "V",
        "VE - Coastal flood hazard with specified BFE and velocity": "VE",
        "Other/Unsure": "X",
    }
    flood_zone = flood_zone_map[flood_zone_opt]

    st.markdown("</div>", unsafe_allow_html=True)

    # Section 7: Data Source & Governance
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown('<div class="form-header">📄 Data Source & Governance Documentation</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        external_consumer_data_default = test_data.get("external_consumer_data_used", "No") if test_data else "No"
        external_consumer_data_idx = ["No", "Yes"].index(external_consumer_data_default) if external_consumer_data_default in ["No", "Yes"] else 0
        external_consumer_data_used = st.selectbox(
            "Using External Consumer Data? *",
            ["No", "Yes"],
            index=external_consumer_data_idx,
            help="External data = credit reports, claims databases, third-party verification services"
        )
    with col2:
        ai_governance_docs_default = test_data.get("ai_governance_docs_ready", "Yes") if test_data else "Yes"
        ai_governance_docs_idx = ["Yes", "No"].index(ai_governance_docs_default) if ai_governance_docs_default in ["Yes", "No"] else 0
        ai_governance_docs_ready = st.selectbox(
            "Governance Documentation Ready? *",
            ["Yes", "No"],
            index=ai_governance_docs_idx,
            help="Documentation showing compliance with fair lending and data use regulations"
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # Submit button
    submitted = st.form_submit_button("Submit Application", use_container_width=True, type="primary")

if submitted:
    # Validate all required fields are filled
    missing_fields = []
    if not applicant_name:
        missing_fields.append("Applicant Name")
    if not email:
        missing_fields.append("Email")
    if not state:
        missing_fields.append("State")
    if not address:
        missing_fields.append("Street Address")
    if not city:
        missing_fields.append("City")
    if not zip_code:
        missing_fields.append("ZIP Code")

    if missing_fields:
        st.error(f"Please fill in all required fields: {', '.join(missing_fields)}")
    else:
        # Create application record
        app_data = {
            "app_id": f"APP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "applicant_name": applicant_name,
            "applicant_email": email,
            "state": state,
            "address": address,
            "city": city,
            "zip_code": zip_code,
            "occupancy": occupancy,
            "year_built": year_built,
            "roof_age": roof_age,
            "roof_material": roof_material,
            "roof_condition_ai": roof_condition_ai,
            "requested_dwelling_limit": requested_dwelling_limit,
            "estimated_replacement_cost": estimated_replacement_cost,
            "prior_claim_count_5y": prior_claim_count_5y,
            "water_claim_count_5y": water_claim_count_5y,
            "claim_total_paid_5y": claim_total_paid_5y,
            "open_claims": open_claims,
            "wildfire_score": wildfire_score,
            "wind_hail_score": wind_hail_score,
            "flood_zone": flood_zone,
            "external_consumer_data_used": external_consumer_data_used,
            "ai_governance_docs_ready": ai_governance_docs_ready,
        }

        # Route application
        app_series = pd.Series(app_data)
        result = route_application(app_series)

        # Save to appropriate location
        app_data["submission_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        app_data["routed_status"] = result["status"]

        is_test = test_mode and st.session_state.get("test_template") is not None

        if is_test:
            # Save to test_applications folder
            test_dir = BASE_DIR / "data" / "test_applications"
            test_dir.mkdir(parents=True, exist_ok=True)
            today = datetime.now().strftime("%Y-%m-%d")
            test_file = test_dir / f"applications_{today}.csv"

            if test_file.exists():
                df_existing = pd.read_csv(test_file)
                df_new = pd.DataFrame([app_data])
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            else:
                df_combined = pd.DataFrame([app_data])

            df_combined.to_csv(test_file, index=False)
            st.toast(f"🧪 Test application saved (not in production data)", icon="🧪")
        else:
            # Save to normal submissions
            save_submission(app_data)
            st.toast(f"✓ Application {app_data['app_id']} submitted! Status: {result['status']}", icon="✅")

        # Clear test template
        st.session_state.test_template = None

        # Store in session state
        st.session_state.last_application = app_data
        st.session_state.last_result = result

        # Show result
        st.markdown("---")

        show_results = st.session_state.get("show_results_to_applicants", False)

        if show_results:
            # Mode 1: Show immediate results to applicant
            st.markdown("## 🔍 Underwriting Decision")
            status = result["status"]
            status_label = STATUS_LABELS.get(status, status)
            color_class = "status-green" if status == "A" else "status-yellow" if status == "B" else "status-red"
            emoji = "✅" if status == "A" else "⏳" if status == "B" else "❌"
            st.markdown(f'<div class="result-badge {color_class}">{emoji} {status_label}</div>', unsafe_allow_html=True)
            st.markdown(f"**Decision Rationale:**\n{STATUS_DESCRIPTIONS.get(status, '')}")

            if result["reasons"]:
                st.markdown("**Details:**")
                for reason in result["reasons"]:
                    st.markdown(f"• {reason}")

        else:
            # Mode 2: Legal-safe mode - generic acknowledgment
            st.markdown("## ✅ Application Received")
            st.success("""
            Thank you for submitting your application. We've received your information and our underwriting team will review it shortly.

            We'll contact you at **{email}** within 1-2 business days with next steps.
            """.format(email=email))

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 View Dashboard", use_container_width=True):
                st.switch_page("pages/3_Dashboard.py")
        with col2:
            if st.button("➕ New Application", use_container_width=True):
                st.rerun()
