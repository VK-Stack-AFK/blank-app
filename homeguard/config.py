"""Configuration for simplified HomeGuard UW Validator."""
from __future__ import annotations

APP_TITLE = "HomeGuard UW Validator"
APP_SUBTITLE = "Homeowners Insurance Pre-Pricing Underwriting Assistant"

# Loss Ratio Thresholds (for POC testing)
# Loss ratio = total claims paid / estimated replacement cost
LOSS_RATIO_THRESHOLDS = {
    "green_light_max": 0.25,      # < 25% = GREEN LIGHT (great)
    "underwriter_max": 0.75,      # 25-75% = NEEDS UNDERWRITER (refer)
    # > 75% = REJECT (auto-recommend rejection)
}

# Feature toggles for POC testing
FEATURE_FLAGS = {
    "use_loss_ratio": True,
    "check_roof_age": True,
    "check_claims_count": True,
    "check_hazard_exposure": True,
    "check_governance": True,
    "check_occupancy": True,
}

# Questionnaire fields (what we ask the applicant)
QUESTIONNAIRE_FIELDS = [
    "applicant_name",
    "state",
    "address",
    "city",
    "zip_code",
    "occupancy",
    "year_built",
    "roof_age",
    "roof_material",
    "roof_condition_ai",
    "requested_dwelling_limit",
    "estimated_replacement_cost",
    "prior_claim_count_5y",
    "water_claim_count_5y",
    "claim_total_paid_5y",
    "open_claims",
    "wildfire_score",
    "flood_zone",
    "wind_hail_score",
    "external_consumer_data_used",
    "ai_governance_docs_ready",
]

# Three simple routing statuses
ROUTING_STATUSES = [
    "A",
    "B",
    "F",
]

STATUS_DESCRIPTIONS = {
    "A": "Approved for Pricing. Application meets underwriting criteria and is ready for downstream pricing workflow.",
    "B": "Referred for Manual Review. Application requires underwriter assessment due to complexity or risk factors.",
    "F": "Declined. Application does not meet underwriting criteria.",
}

STATUS_LABELS = {
    "A": "Approved for Pricing",
    "B": "Referred for Manual Review",
    "F": "Declined",
}

STATUS_COLORS = {
    "A": "#10b981",
    "B": "#f59e0b",
    "F": "#ef4444",
}

# Compliance-blocked factors (auto-REJECT if present)
BLOCKED_BEHAVIORAL_FACTORS = [
    "social_media_used",
    "device_data_used",
    "biometric_used",
]

# State-specific compliance rules
STATE_COMPLIANCE_RULES = {
    "MD": {
        "rule": "Credit score cannot be sole reason for refusal to underwrite.",
        "blocked_factors": ["credit_score_used"],
    },
    "NY": {
        "rule": "External consumer data requires AI governance documentation.",
        "requires_governance": True,
    },
    "CO": {
        "rule": "SB21-169: Controls required against discrimination in algorithms.",
        "requires_governance": True,
    },
    "CA": {
        "rule": "External data/AI models may create proxy discrimination concerns.",
        "requires_governance": True,
    },
}
