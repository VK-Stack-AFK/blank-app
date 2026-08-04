"""Validation and routing engine for the HomeGuard UW Validator demo.

This is intentionally deterministic. It is a POC pre-pricing validator, not a
premium model and not a final underwriting authority system.
"""
from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from .config import (
    BLOCKED_BEHAVIORAL_FACTORS,
    CRITICAL_FIELDS,
    REQUIRED_FIELDS,
    VERIFICATION_TOOLS,
)


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

    for col in ["requested_dwelling_limit", "estimated_replacement_cost", "square_feet_reported", "square_feet_public"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    out["coverage_to_rc_ratio"] = out["requested_dwelling_limit"] / out["estimated_replacement_cost"]
    out["sqft_variance_pct"] = (
        (out["square_feet_reported"] - out["square_feet_public"]).abs() / out["square_feet_public"]
    )
    out.loc[out["square_feet_public"].isna(), "sqft_variance_pct"] = np.nan

    for col in [
        "year_built",
        "roof_age",
        "roof_condition_confidence",
        "electrical_age",
        "plumbing_age",
        "heating_age",
        "protection_class",
        "distance_fire_station_miles",
        "distance_hydrant_ft",
        "prior_claim_count_5y",
        "water_claim_count_5y",
        "claim_total_paid_5y",
        "open_claims",
        "wildfire_score",
        "wind_hail_score",
        "coastal_distance_miles",
    ]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    for col in [
        "pool",
        "trampoline",
        "dog_declared",
        "credit_score_used",
        "social_media_used",
        "device_data_used",
        "biometric_used",
        "external_consumer_data_used",
        "ai_governance_docs_ready",
    ]:
        if col in out.columns:
            out[col] = out[col].apply(normalize_yes_no)

    return out


def completeness_score(row: pd.Series) -> Tuple[float, List[str], List[str]]:
    missing_required = [field for field in REQUIRED_FIELDS if field in row.index and _is_missing(row[field])]
    missing_critical = [field for field in CRITICAL_FIELDS if field in row.index and _is_missing(row[field])]
    present = len(REQUIRED_FIELDS) - len(missing_required)
    score = present / len(REQUIRED_FIELDS) if REQUIRED_FIELDS else 1.0
    return score, missing_required, missing_critical


def compliance_flags(row: pd.Series) -> List[Dict[str, str]]:
    flags: List[Dict[str, str]] = []
    state = str(row.get("state", "")).upper().strip()

    for factor in BLOCKED_BEHAVIORAL_FACTORS:
        if normalize_yes_no(row.get(factor)) == "Yes":
            flags.append(
                {
                    "severity": "blocked",
                    "factor": factor,
                    "reason": "Behavioral/sensitive data is blocked in this POC because it creates privacy, proxy-discrimination, and actuarial-nexus risk.",
                }
            )

    if state == "MD" and normalize_yes_no(row.get("credit_score_used")) == "Yes":
        flags.append(
            {
                "severity": "blocked",
                "factor": "credit_score_used",
                "reason": "Maryland homeowners rule: credit history cannot be used to refuse to underwrite, cancel, or refuse to renew based wholly or partly on credit history.",
            }
        )

    if state == "NY" and normalize_yes_no(row.get("external_consumer_data_used")) == "Yes" and normalize_yes_no(row.get("ai_governance_docs_ready")) != "Yes":
        flags.append(
            {
                "severity": "caution",
                "factor": "external_consumer_data_used",
                "reason": "New York AIS/ECDIS use needs documentation showing no unfair or unlawful discrimination.",
            }
        )

    if state == "CO" and normalize_yes_no(row.get("external_consumer_data_used")) == "Yes" and normalize_yes_no(row.get("ai_governance_docs_ready")) != "Yes":
        flags.append(
            {
                "severity": "caution",
                "factor": "external_consumer_data_used",
                "reason": "Colorado SB21-169 requires controls against unfair discrimination in external consumer data, algorithms, and predictive models.",
            }
        )

    if state == "CA" and normalize_yes_no(row.get("external_consumer_data_used")) == "Yes" and normalize_yes_no(row.get("ai_governance_docs_ready")) != "Yes":
        flags.append(
            {
                "severity": "caution",
                "factor": "external_consumer_data_used",
                "reason": "California CDI has warned that AI/big data and certain external inputs can create proxy discrimination and actuarial-nexus concerns.",
            }
        )

    return flags


def validation_flags(row: pd.Series) -> List[Dict[str, str]]:
    flags: List[Dict[str, str]] = []
    score, missing_required, missing_critical = completeness_score(row)

    if missing_critical:
        flags.append(
            {
                "severity": "medium",
                "factor": "missing_critical_fields",
                "reason": f"Critical field(s) missing: {', '.join(missing_critical)}.",
            }
        )
    elif missing_required:
        flags.append(
            {
                "severity": "low",
                "factor": "missing_required_fields",
                "reason": f"Non-critical field(s) missing: {', '.join(missing_required)}.",
            }
        )

    match_status = str(row.get("property_match_status", "")).strip()
    if match_status == "Unmatched":
        flags.append({"severity": "medium", "factor": "property_match_status", "reason": "Property address could not be matched to external property records."})
    elif match_status == "Partial Match":
        flags.append({"severity": "low", "factor": "property_match_status", "reason": "Partial property match creates data confidence concern."})

    roof_age = _to_float(row.get("roof_age"))
    if not np.isnan(roof_age) and roof_age > 25:
        flags.append({"severity": "high", "factor": "roof_age", "reason": "Roof age exceeds 25-year appetite threshold."})

    roof_condition = str(row.get("roof_condition_ai", "")).strip().lower()
    roof_conf = _to_float(row.get("roof_condition_confidence"), default=0)
    if roof_condition == "poor":
        flags.append({"severity": "high", "factor": "roof_condition_ai", "reason": "AI/vendor roof condition indicates poor condition; human review required before adverse use."})
    elif roof_conf < 0.60:
        flags.append({"severity": "medium", "factor": "roof_condition_confidence", "reason": "Roof condition confidence is low; request photos or inspection."})

    coverage_to_rc_ratio = _to_float(row.get("coverage_to_rc_ratio"))
    if not np.isnan(coverage_to_rc_ratio) and coverage_to_rc_ratio < 0.80:
        flags.append({"severity": "medium", "factor": "coverage_to_rc_ratio", "reason": "Requested Coverage A appears below 80% of estimated replacement cost."})

    sqft_variance_pct = _to_float(row.get("sqft_variance_pct"))
    if not np.isnan(sqft_variance_pct) and sqft_variance_pct > 0.15:
        flags.append({"severity": "medium", "factor": "sqft_variance_pct", "reason": "Reported square footage differs from public/property data by more than 15%."})

    if str(row.get("occupancy", "")).strip() != "Owner-occupied":
        flags.append({"severity": "medium", "factor": "occupancy", "reason": "POC scope is owner-occupied homeowners; non-owner/seasonal occupancy needs review."})

    claims = _to_float(row.get("prior_claim_count_5y"), default=0)
    water_claims = _to_float(row.get("water_claim_count_5y"), default=0)
    paid = _to_float(row.get("claim_total_paid_5y"), default=0)
    open_claims = _to_float(row.get("open_claims"), default=0)

    if claims >= 3:
        flags.append({"severity": "high", "factor": "prior_claim_count_5y", "reason": "Three or more claims in the last five years."})
    if water_claims >= 2:
        flags.append({"severity": "medium", "factor": "water_claim_count_5y", "reason": "Repeated water claims in the last five years."})
    if paid >= 25000:
        flags.append({"severity": "medium", "factor": "claim_total_paid_5y", "reason": "Total paid claims exceed $25,000 in the last five years."})
    if open_claims > 0:
        flags.append({"severity": "high", "factor": "open_claims", "reason": "Open claim requires manual review."})

    wildfire = _to_float(row.get("wildfire_score"), default=0)
    wind_hail = _to_float(row.get("wind_hail_score"), default=0)
    flood_zone = str(row.get("flood_zone", "")).strip().upper()

    if wildfire >= 85:
        flags.append({"severity": "high", "factor": "wildfire_score", "reason": "Severe wildfire exposure score."})
    elif wildfire >= 70:
        flags.append({"severity": "medium", "factor": "wildfire_score", "reason": "Elevated wildfire exposure score."})

    if wind_hail >= 80:
        flags.append({"severity": "high", "factor": "wind_hail_score", "reason": "High wind/hail exposure score."})
    elif wind_hail >= 70:
        flags.append({"severity": "medium", "factor": "wind_hail_score", "reason": "Elevated wind/hail exposure score."})

    if flood_zone in {"A", "AE", "V", "VE"}:
        flags.append({"severity": "medium", "factor": "flood_zone", "reason": "Special flood hazard zone; standard homeowners coverage typically excludes flood."})

    if normalize_yes_no(row.get("trampoline")) == "Yes":
        flags.append({"severity": "low", "factor": "trampoline", "reason": "Trampoline liability exposure requires carrier/state rule check."})
    if normalize_yes_no(row.get("dog_declared")) == "Yes":
        flags.append({"severity": "low", "factor": "dog_declared", "reason": "Dog-related liability question requires human/state-rule review."})

    return flags


def route_application(row: pd.Series) -> Dict[str, Any]:
    score, missing_required, missing_critical = completeness_score(row)
    comp_flags = compliance_flags(row)
    val_flags = validation_flags(row)

    blocked = [flag for flag in comp_flags if flag["severity"] == "blocked"]
    caution = [flag for flag in comp_flags if flag["severity"] == "caution"]
    request_info_factors = {"missing_critical_fields", "property_match_status", "coverage_to_rc_ratio", "sqft_variance_pct", "roof_condition_confidence"}
    high_val = [flag for flag in val_flags if flag["severity"] == "high"]
    request_info = [flag for flag in val_flags if flag["factor"] in request_info_factors and flag["severity"] in {"medium", "low"}]

    if blocked or caution:
        route = "Compliance Hold"
    elif missing_critical or request_info:
        route = "Request Info"
    elif high_val or val_flags:
        route = "Refer to Underwriter"
    else:
        route = "STP-ready"

    all_flags = comp_flags + val_flags
    reason_summary = "; ".join([flag["reason"] for flag in all_flags[:5]]) or "No material validation, risk, or compliance flags detected."

    return {
        "app_id": row.get("app_id"),
        "status": route,
        "completeness_score": round(score, 3),
        "missing_required_count": len(missing_required),
        "missing_critical_count": len(missing_critical),
        "flag_count": len(all_flags),
        "high_flag_count": len(high_val),
        "compliance_flag_count": len(comp_flags),
        "reason_summary": reason_summary,
        "flags": all_flags,
        "evaluated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def evaluate_portfolio(df: pd.DataFrame) -> pd.DataFrame:
    enriched = enrich_dataframe(df)
    records = []
    for _, row in enriched.iterrows():
        routed = route_application(row)
        records.append({k: v for k, v in routed.items() if k != "flags"})
    return pd.DataFrame(records)


def build_audit_log(df: pd.DataFrame) -> pd.DataFrame:
    enriched = enrich_dataframe(df)
    rows = []
    for _, row in enriched.iterrows():
        routed = route_application(row)
        data_sources = ["Application", "Mock property record", "Mock hazard score"]
        if row.get("property_match_status") in {"Matched", "Partial Match"}:
            data_sources.append("Parcel/property match")
        if _to_float(row.get("prior_claim_count_5y"), default=0) > 0:
            data_sources.append("Claims/loss history")
        if normalize_yes_no(row.get("external_consumer_data_used")) == "Yes":
            data_sources.append("External consumer data flag")

        rows.append(
            {
                "app_id": row.get("app_id"),
                "state": row.get("state"),
                "status": routed["status"],
                "data_sources_used": ", ".join(data_sources),
                "ai_tools_used": "Completeness checker, property matcher, claims summarizer, hazard checker, factor rules engine",
                "model_versions": "rule_engine_v0.3; roof_assist_v0.1_mock; hazard_flags_v0.1_mock",
                "human_review_required": "Yes" if routed["status"] in {"Refer to Underwriter", "Compliance Hold"} else "No",
                "reason_summary": routed["reason_summary"],
                "evaluated_at": routed["evaluated_at"],
            }
        )
    return pd.DataFrame(rows)


def explode_flags(df: pd.DataFrame) -> pd.DataFrame:
    enriched = enrich_dataframe(df)
    rows = []
    for _, row in enriched.iterrows():
        routed = route_application(row)
        for flag in routed["flags"]:
            rows.append(
                {
                    "app_id": row.get("app_id"),
                    "state": row.get("state"),
                    "status": routed["status"],
                    "severity": flag.get("severity"),
                    "factor": flag.get("factor"),
                    "reason": flag.get("reason"),
                }
            )
    return pd.DataFrame(rows)


def verification_tools_dataframe() -> pd.DataFrame:
    return pd.DataFrame(VERIFICATION_TOOLS)
