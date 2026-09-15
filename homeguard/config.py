"""Shared product vocabulary and versioned demonstration settings."""
APP_TITLE = "HomeGuard"
APP_SUBTITLE = "Personal homeowners underwriting"
RULE_VERSION = "homeowners-reference-2.0"
MODEL_VERSION = "homeguard-rf-demo-1.0"
SCHEMA_VERSION = 2
STATUS_LABELS = {"A": "STP ready", "B": "Underwriter review", "F": "Recommended for rejection"}
STATUS_DESCRIPTIONS = {
    "A": "Ready for the next pricing step under this demonstration's decision policy. Coverage is not bound.",
    "B": "Resolve the evidence gaps or risk questions below, then reassess the application.",
    "F": "Recommended for rejection. An underwriter must make and document the final decision.",
}
STATUS_COLORS = {"A": "#117467", "B": "#9B650F", "F": "#A83F58"}
ROUTING_STATUSES = ["A", "B", "F"]
LOSS_RATIO_THRESHOLDS = {"green_light_max": .25, "underwriter_max": .75}
FEATURE_FLAGS = {"use_loss_ratio": True, "check_roof_age": True, "check_claims_count": True,
                 "check_hazard_exposure": True, "check_governance": True, "check_occupancy": True}
DEFAULT_SETTINGS = {"test_mode_enabled": True, "show_results_to_applicants": False,
                    "require_dashboard_auth": True, "model_confidence_threshold": .75}
