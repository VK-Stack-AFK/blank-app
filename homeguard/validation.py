"""Simplified routing engine for HomeGuard UW Validator.

Three outcomes: GREEN LIGHT (auto-proceed), NEEDS UNDERWRITER (manual review),
REJECT (blocked/critical issues).
"""
from __future__ import annotations

import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from .config import (
    BLOCKED_BEHAVIORAL_FACTORS,
    QUESTIONNAIRE_FIELDS,
    ROUTING_STATUSES,
    STATE_COMPLIANCE_RULES,
    LOSS_RATIO_THRESHOLDS,
    FEATURE_FLAGS,
)

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"


def load_csv(name: str) -> pd.DataFrame:
    """Load a CSV from the data directory."""
    return pd.read_csv(DATA_DIR / name)


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and value.strip().lower() in {"", "nan", "none", "null", "unknown"}:
        return True
    return False


def _to_float(value: Any, default: float = np.nan) -> float:
    try:
        if _is_missing(value):
            return default
        return float(value)
    except Exception:
        return default


def normalize_yes_no(value: Any) -> str:
    if _is_missing(value):
        return "No"
    text = str(value).strip().lower()
    if text in {"yes", "y", "true", "1"}:
        return "Yes"
    return "No"


def enrich_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Add calculated fields used by validation and dashboards."""
    out = df.copy()

    for col in ["requested_dwelling_limit", "estimated_replacement_cost"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    for col in [
        "year_built",
        "roof_age",
        "roof_condition_confidence",
        "prior_claim_count_5y",
        "water_claim_count_5y",
        "claim_total_paid_5y",
        "open_claims",
        "wildfire_score",
        "wind_hail_score",
    ]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    for col in [
        "social_media_used",
        "device_data_used",
        "biometric_used",
        "external_consumer_data_used",
        "ai_governance_docs_ready",
    ]:
        if col in out.columns:
            out[col] = out[col].apply(normalize_yes_no)

    out["coverage_to_rc_ratio"] = (
        out["requested_dwelling_limit"] / out["estimated_replacement_cost"]
        if "requested_dwelling_limit" in out.columns and "estimated_replacement_cost" in out.columns
        else np.nan
    )

    return out


def get_missing_fields(row: pd.Series) -> List[str]:
    """Return list of missing required questionnaire fields."""
    return [field for field in QUESTIONNAIRE_FIELDS if field in row.index and _is_missing(row[field])]


def get_reject_reasons(row: pd.Series) -> List[str]:
    """Check for REJECT conditions. Returns list of rejection reasons."""
    reasons = []
    state = str(row.get("state", "")).upper().strip()

    # Check blocked behavioral factors
    for factor in BLOCKED_BEHAVIORAL_FACTORS:
        if normalize_yes_no(row.get(factor)) == "Yes":
            reasons.append(f"Declined: {factor.replace('_', ' ')} not permitted in underwriting")

    # State-specific compliance issues
    if state in STATE_COMPLIANCE_RULES:
        rule = STATE_COMPLIANCE_RULES[state]
        if "blocked_factors" in rule:
            for blocked_factor in rule["blocked_factors"]:
                if normalize_yes_no(row.get(blocked_factor)) == "Yes":
                    reasons.append(f"Declined ({state} compliance): {rule['rule']}")

    # Missing critical fields
    missing = get_missing_fields(row)
    if missing:
        reasons.append(f"Incomplete application: Missing {', '.join(missing[:3])}")

    # Loss ratio check (if enabled)
    if FEATURE_FLAGS.get("use_loss_ratio", True):
        loss_ratio = _to_float(row.get("loss_ratio"), default=0)
        if loss_ratio > LOSS_RATIO_THRESHOLDS.get("underwriter_max", 0.75):
            reasons.append(f"Declined: Loss ratio of {loss_ratio:.1%} exceeds underwriting guidelines")

    # Auto-reject high-severity underwriting flags
    if FEATURE_FLAGS.get("check_claims_count", True):
        open_claims = _to_float(row.get("open_claims"), default=0)
        if open_claims > 0:
            reasons.append("Declined: Active claim on record—cannot underwrite")

        claims = _to_float(row.get("prior_claim_count_5y"), default=0)
        if claims >= 3:
            reasons.append(f"Declined: Loss frequency of {int(claims)} claims in 5 years exceeds guidelines")

    return reasons


def get_underwriter_flags(row: pd.Series) -> List[Dict[str, str]]:
    """Check for NEEDS UNDERWRITER conditions. Returns list of flag details."""
    flags = []
    state = str(row.get("state", "")).upper().strip()

    # Loss ratio check (if enabled) - mid-range
    if FEATURE_FLAGS.get("use_loss_ratio", True):
        loss_ratio = _to_float(row.get("loss_ratio"), default=0)
        if (loss_ratio >= LOSS_RATIO_THRESHOLDS.get("green_light_max", 0.25) and
            loss_ratio <= LOSS_RATIO_THRESHOLDS.get("underwriter_max", 0.75)):
            flags.append({
                "factor": "loss_ratio_moderate",
                "reason": f"Moderate loss ratio ({loss_ratio:.1%})—requires underwriter review",
            })

    # Governance requirements
    if FEATURE_FLAGS.get("check_governance", True):
        if normalize_yes_no(row.get("external_consumer_data_used")) == "Yes":
            if normalize_yes_no(row.get("ai_governance_docs_ready")) != "Yes":
                if state in STATE_COMPLIANCE_RULES and STATE_COMPLIANCE_RULES[state].get("requires_governance"):
                    flags.append({
                        "factor": "governance_requirement",
                        "reason": f"{state} compliance: External data source requires governance documentation",
                    })

    # Roof concerns
    if FEATURE_FLAGS.get("check_roof_age", True):
        roof_age = _to_float(row.get("roof_age"))
        if not np.isnan(roof_age) and roof_age >= 20:
            flags.append({
                "factor": "roof_age",
                "reason": f"Property age: Roof is {int(roof_age)} years old (inspection recommended)",
            })

        roof_condition = str(row.get("roof_condition_ai", "")).strip().lower()
        if roof_condition == "poor":
            flags.append({
                "factor": "roof_condition",
                "reason": "Roof condition: Poor condition assessment requires underwriter review",
            })

    # Claims concerns (not auto-reject, but flag for review)
    if FEATURE_FLAGS.get("check_claims_count", True):
        claims = _to_float(row.get("prior_claim_count_5y"), default=0)
        if claims == 2:
            flags.append({
                "factor": "claims_history",
                "reason": f"Loss history: {int(claims)} claims filed in last 5 years",
            })

        water_claims = _to_float(row.get("water_claim_count_5y"), default=0)
        if water_claims >= 1:
            flags.append({
                "factor": "water_claims",
                "reason": f"Water loss pattern: {int(water_claims)} water-related claim(s)—assess maintenance history",
            })

    # Hazard exposure
    if FEATURE_FLAGS.get("check_hazard_exposure", True):
        wildfire = _to_float(row.get("wildfire_score"), default=0)
        if wildfire >= 70:
            flags.append({
                "factor": "wildfire_exposure",
                "reason": f"Wildfire exposure: Score {int(wildfire)}/100—requires hazard review",
            })

        wind_hail = _to_float(row.get("wind_hail_score"), default=0)
        if wind_hail >= 70:
            flags.append({
                "factor": "wind_hail_exposure",
                "reason": f"Wind/hail exposure: Score {int(wind_hail)}/100—requires hazard review",
            })

        flood_zone = str(row.get("flood_zone", "")).strip().upper()
        if flood_zone in {"A", "AE", "V", "VE"}:
            flags.append({
                "factor": "flood_zone",
                "reason": f"Flood zone {flood_zone}: Special hazard designation—verify coverage requirements",
            })

    # Coverage concerns
    coverage_to_rc_ratio = _to_float(row.get("coverage_to_rc_ratio"))
    if not np.isnan(coverage_to_rc_ratio) and coverage_to_rc_ratio < 0.80:
        flags.append({
            "factor": "underinsurance",
            "reason": f"Underinsurance: Coverage is {coverage_to_rc_ratio:.0%} of estimated replacement cost",
        })

    return flags


def route_application(row: pd.Series, feature_overrides: Dict[str, bool] = None) -> Dict[str, Any]:
    """Route application to one of 3 statuses: GREEN LIGHT, NEEDS UNDERWRITER, or REJECT."""
    # Apply feature flag overrides (from settings)
    if feature_overrides:
        for key, value in feature_overrides.items():
            FEATURE_FLAGS[key] = value

    enriched = enrich_dataframe(row.to_frame().T).iloc[0]

    # Check for REJECT conditions
    reject_reasons = get_reject_reasons(enriched)
    if reject_reasons:
        return {
            "app_id": enriched.get("app_id"),
            "status": "F",
            "reasons": reject_reasons,
            "flags": [],
            "evaluated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    # Check for NEEDS UNDERWRITER flags
    underwriter_flags = get_underwriter_flags(enriched)
    if underwriter_flags:
        flag_reasons = [f["reason"] for f in underwriter_flags[:3]]
        return {
            "app_id": enriched.get("app_id"),
            "status": "B",
            "reasons": flag_reasons,
            "flags": underwriter_flags,
            "evaluated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    # Otherwise: A (Auto-Pass)
    return {
        "app_id": enriched.get("app_id"),
        "status": "A",
        "reasons": ["Complete application, meets underwriting criteria"],
        "flags": [],
        "evaluated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def evaluate_portfolio(df: pd.DataFrame) -> pd.DataFrame:
    """Route all applications in portfolio."""
    enriched = enrich_dataframe(df)
    records = []
    for _, row in enriched.iterrows():
        routed = route_application(row)
        records.append({
            "app_id": routed["app_id"],
            "status": routed["status"],
            "reason_summary": "; ".join(routed["reasons"]),
            "flag_count": len(routed["flags"]),
            "evaluated_at": routed["evaluated_at"],
        })
    return pd.DataFrame(records)


def build_audit_log(df: pd.DataFrame) -> pd.DataFrame:
    """Create audit trail for all applications."""
    enriched = enrich_dataframe(df)
    rows = []
    for _, row in enriched.iterrows():
        routed = route_application(row)
        rows.append({
            "app_id": routed["app_id"],
            "state": row.get("state"),
            "applicant": row.get("applicant_name"),
            "status": routed["status"],
            "routing_reason": "; ".join(routed["reasons"]),
            "human_review_required": "Yes" if routed["status"] in {"NEEDS UNDERWRITER", "REJECT"} else "No",
            "evaluated_at": routed["evaluated_at"],
        })
    return pd.DataFrame(rows)
