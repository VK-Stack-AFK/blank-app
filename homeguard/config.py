"""Configuration for HomeGuard UW Validator demo."""
from __future__ import annotations

APP_TITLE = "HomeGuard UW Validator"
APP_SUBTITLE = "Personal Homeowners Pre-Pricing Underwriting Validation POC"

REQUIRED_FIELDS = [
    "applicant_name",
    "state",
    "address",
    "city",
    "zip_code",
    "occupancy",
    "prior_insurance",
    "year_built",
    "roof_age",
    "roof_material",
    "square_feet_reported",
    "construction_type",
    "protection_class",
    "prior_claim_count_5y",
    "wildfire_score",
    "flood_zone",
    "wind_hail_score",
    "requested_dwelling_limit",
    "estimated_replacement_cost",
]

CRITICAL_FIELDS = [
    "state",
    "address",
    "occupancy",
    "year_built",
    "roof_age",
    "square_feet_reported",
    "roof_material",
    "construction_type",
    "requested_dwelling_limit",
    "estimated_replacement_cost",
]

BLOCKED_BEHAVIORAL_FACTORS = [
    "social_media_used",
    "device_data_used",
    "biometric_used",
]

DISPLAY_STATUS_ORDER = [
    "STP-ready",
    "Request Info",
    "Refer to Underwriter",
    "Compliance Hold",
]

STATUS_DESCRIPTIONS = {
    "STP-ready": "Complete and consistent enough to proceed to downstream rating/pricing workflow.",
    "Request Info": "Required data is missing or inconsistent; customer/agent input needed.",
    "Refer to Underwriter": "Risk complexity, hazard flags, or ambiguity requires manual underwriting review.",
    "Compliance Hold": "Potential restricted factor, state rule issue, or missing AI governance control.",
}

VERIFICATION_TOOLS = [
    {
        "tool": "Application Completeness Checker",
        "what_it_verifies": "Required homeowners fields are present before pre-pricing.",
        "ai_role": "Detect missing fields and generate request-info list.",
        "human_role": "Approve final carrier-required field list.",
    },
    {
        "tool": "Address Normalization + Geocoding",
        "what_it_verifies": "Address is valid, standardized, and can be matched to a property record.",
        "ai_role": "Normalize strings, find likely matches, flag low-confidence matches.",
        "human_role": "Review unmatched or conflicting address/property records.",
    },
    {
        "tool": "Parcel/Public Property Data Matcher",
        "what_it_verifies": "Year built, square footage, property type, construction indicators, and parcel match.",
        "ai_role": "Compare application values against external property records.",
        "human_role": "Decide what to request when public records conflict with applicant data.",
    },
    {
        "tool": "Replacement Cost Plausibility Check",
        "what_it_verifies": "Requested dwelling coverage is not obviously below estimated replacement cost.",
        "ai_role": "Flag underinsurance/coverage-to-RCV gaps.",
        "human_role": "Confirm replacement-cost assumptions and coverage requirements.",
    },
    {
        "tool": "Roof Age + Roof Condition Review",
        "what_it_verifies": "Roof age/material/condition risk before rating or inspection.",
        "ai_role": "Use provided data or vendor/image outputs to flag old, poor, or low-confidence roof records.",
        "human_role": "Make adverse decisions or inspection requirements for roof concerns.",
    },
    {
        "tool": "Claims History Summarizer",
        "what_it_verifies": "Frequency, severity, water loss patterns, and open claims.",
        "ai_role": "Summarize claims and identify repeated loss patterns.",
        "human_role": "Interpret context and handle adverse actions/notices when needed.",
    },
    {
        "tool": "Hazard Exposure Checker",
        "what_it_verifies": "Wildfire, flood, wind/hail, coastal, and freeze exposure.",
        "ai_role": "Score direct physical hazard exposure and produce reason flags.",
        "human_role": "Review high-severity/peril-specific exceptions.",
    },
    {
        "tool": "Liability Feature Validator",
        "what_it_verifies": "Pool, trampoline, dog disclosure, and other liability-relevant property features.",
        "ai_role": "Flag exposures using carrier/state rules.",
        "human_role": "Apply state-specific and sensitive liability rules.",
    },
    {
        "tool": "State Factor Permission Checker",
        "what_it_verifies": "Whether a factor is allowed, blocked, state-gated, or needs review.",
        "ai_role": "Route restricted/sensitive factors to compliance hold.",
        "human_role": "Maintain legal rules and approve factor inventory.",
    },
    {
        "tool": "AI Governance/Audit Log Generator",
        "what_it_verifies": "What data and models were used and why the file was routed.",
        "ai_role": "Create reason codes, model versions, data lineage, and decision trail.",
        "human_role": "Approve model changes, overrides, and regulatory reporting.",
    },
]
