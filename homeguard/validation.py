"""Input quality, evidence readiness, and transparent POC reference rules.

The prediction service makes model recommendations. This module supplies the
synthetic label policy and guardrails; it never issues an insurance decision.
"""
from __future__ import annotations
from datetime import date, datetime, timezone
from pathlib import Path
import math
import re
import pandas as pd
from .config import RULE_VERSION, FEATURE_FLAGS
from .schema import FIELDS, FIELD_MAP, REQUIRED_FIELDS, VERIFICATION_FIELDS, REFERENCE_FIELDS, label

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
QUESTIONNAIRE_FIELDS = list(REQUIRED_FIELDS)

def _is_missing(value):
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {'', 'unknown', 'none', 'null', 'nan', 'nat'}
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False

def _to_float(value, default=float('nan')):
    try:
        value = float(value)
        return value if math.isfinite(value) else default
    except (TypeError, ValueError):
        return default

def normalize_yes_no(value):
    if _is_missing(value):
        return 'Unknown'
    text = str(value).strip().lower()
    if text in {'yes','true','y','1'}: return 'Yes'
    if text in {'no','false','n','0'}: return 'No'
    return 'Unknown'

def normalize_record(row):
    out = dict(row)
    for f in FIELDS:
        v = out.get(f.key)
        valid_none_choice = f.kind=='select' and isinstance(v,str) and v=='None' and v in f.options
        if _is_missing(v) and not valid_none_choice:
            out[f.key] = None
        elif f.kind in ('integer','number','money'):
            out[f.key] = _to_float(v, None)
        else:
            out[f.key] = str(v).strip()
    out['state'] = str(out.get('state') or '').upper()
    aliases = {'Architectural Shingle':'Architectural shingle', '3-tab Shingle':'Asphalt / 3-tab shingle', 'Wood Shake':'Wood shake', 'Asphalt':'Asphalt / 3-tab shingle'}
    out['roof_material'] = aliases.get(out.get('roof_material'), out.get('roof_material'))
    rc = _to_float(out.get('estimated_replacement_cost'), 0)
    paid = _to_float(out.get('claim_total_paid_5y'), 0)
    coverage = _to_float(out.get('requested_dwelling_limit'), 0)
    out['loss_ratio'] = paid / rc if rc > 0 else None
    out['coverage_to_rc_ratio'] = coverage / rc if rc > 0 else None
    return out

def enrich_dataframe(df):
    return pd.DataFrame([normalize_record(r) for r in df.to_dict('records')])

def get_missing_fields(row):
    return [key for key in REQUIRED_FIELDS if _is_missing(row.get(key))]

def issue(code, field, reason, action, category='Risk', severity='B'):
    return {'code':code,'factor':field,'reason':reason,'action':action,'category':category,'severity':severity}

def input_issues(row,as_of=None):
    as_of=as_of or date.today()
    r = normalize_record(row)
    out = [issue('missing_'+key,key,f'{label(key)} is missing.',f'Confirm and record {label(key).lower()}.','Data quality') for key in get_missing_fields(r)]
    for f in FIELDS:
        raw = row.get(f.key)
        v = r.get(f.key)
        if _is_missing(raw): continue
        if f.kind in ('integer','number','money'):
            if v is None or v < f.minimum or (f.maximum is not None and v > f.maximum) or (f.kind=='integer' and v != int(v)):
                out.append(issue('invalid_'+f.key,f.key,f'{f.label} is outside the accepted range or format.','Correct the value using the source record.','Data quality'))
        elif f.kind == 'select' and v not in f.options:
            out.append(issue('invalid_'+f.key,f.key,f'{f.label} has an unrecognized value.','Choose a supported response or leave it unknown.','Data quality'))
        elif f.kind == 'date':
            try: date.fromisoformat(str(v)[:10])
            except (ValueError, TypeError): out.append(issue('invalid_'+f.key,f.key,f'{f.label} is not a valid date.','Record an ISO date.','Data quality'))
    if r.get('applicant_email') and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',r['applicant_email']):
        out.append(issue('email_format','applicant_email','Contact email format is invalid.','Confirm the insured contact email.','Data quality'))
    if r.get('zip_code') and not re.fullmatch(r'\d{5}(-\d{4})?',r['zip_code']):
        out.append(issue('zip_format','zip_code','ZIP code format is invalid.','Enter a five-digit ZIP or ZIP+4.','Data quality'))
    claims = _to_float(r.get('prior_claim_count_5y'),0)
    if _to_float(r.get('water_claim_count_5y'),0)>claims or _to_float(r.get('open_claims'),0)>claims:
        out.append(issue('claims_consistency','prior_claim_count_5y','Water or open claims exceed the total claim count.','Reconcile the five-year loss history.','Data quality'))
    if claims==0 and _to_float(r.get('claim_total_paid_5y'),0)>0:
        out.append(issue('paid_without_claim','claim_total_paid_5y','Payments are recorded with zero claims.','Reconcile claims and total paid.','Data quality'))
    roof_year = r.get('roof_replacement_year')
    if roof_year and r.get('roof_age') is not None and abs(as_of.year-roof_year-r['roof_age'])>1:
        out.append(issue('roof_date_consistency','roof_age','Roof age and replacement year disagree.','Confirm the roof invoice date and update the age.','Data quality'))
    if r.get('roof_age') is not None and r.get('year_built') and r['roof_age']>as_of.year-r['year_built']+1:
        out.append(issue('roof_house_consistency','roof_age','Roof age exceeds the age of the dwelling.','Check construction and roof dates.','Data quality'))
    if r.get('verification_date'):
        try:
            if date.fromisoformat(r['verification_date'][:10])>as_of:
                out.append(issue('future_verification','verification_date','Evidence review date is in the future.','Record the actual completed review date.','Evidence'))
        except ValueError: pass
    return out

def evidence_issues(row):
    r = normalize_record(row)
    out=[]
    for key in VERIFICATION_FIELDS:
        if r.get(key)!='Verified':
            out.append(issue(key,key,f'{label(key)} is {r.get(key) or "not checked"}.',f'Check the source and record {label(REFERENCE_FIELDS[key]).lower()}.','Evidence'))
        elif _is_missing(r.get(REFERENCE_FIELDS[key])):
            out.append(issue('reference_'+key,REFERENCE_FIELDS[key],f'{label(key)} has no source reference.','Record the document or provider report reference.','Evidence'))
    if any(r.get(k)=='Verified' for k in VERIFICATION_FIELDS):
        for k in ('verification_reviewer','verification_date'):
            if _is_missing(r.get(k)): out.append(issue('evidence_'+k,k,f'{label(k)} is missing.','Record who reviewed the evidence and when.','Evidence'))
    for k in ('applicant_attestation','verification_consent'):
        if r.get(k)!='Yes': out.append(issue(k,k,f'{label(k)} is not confirmed.','Obtain and record the required confirmation.','Evidence'))
    if _to_float(r.get('prior_claim_count_5y'),0)>0 and _is_missing(r.get('loss_details')):
        out.append(issue('loss_details','loss_details','Loss details are missing.','Summarize loss dates, causes, payments, and repair completion.','Evidence'))
    stated=_to_float(r.get('square_footage'),0)
    verified=_to_float(r.get('reported_square_footage_verified'),0)
    if stated and verified and abs(stated-verified)/verified>.15:
        out.append(issue('area_mismatch','square_footage','Reported living area differs from verified area by more than 15%.','Reconcile property records and the replacement-cost estimate.','Evidence'))
    if r.get('external_consumer_data_used')=='Yes' and r.get('ai_governance_docs_ready')!='Yes':
        out.append(issue('governance','ai_governance_docs_ready','External-data governance has not been documented.','Complete the applicable carrier/state data-use review.','Governance'))
    for k in ('social_media_used','device_data_used','biometric_used','credit_score_used'):
        if normalize_yes_no(row.get(k))=='Yes':
            out.append(issue('restricted_'+k,k,'A restricted consumer-data factor needs governance review.','Remove unsupported decision inputs and obtain staff governance review.','Governance'))
    return out

def risk_issues(row, feature_overrides=None):
    r=normalize_record(row)
    flags={**FEATURE_FLAGS,**(feature_overrides or {})}
    out=[]
    def add(code,key,reason,action,severity='B'):
        out.append(issue(code,key,reason,action,'Risk',severity))
    if flags['use_loss_ratio']:
        ratio=_to_float(r.get('loss_ratio'),0)
        if ratio>.75: add('high_claims_to_value','loss_ratio',f'Five-year claims / replacement cost is {ratio:.0%}, above the 75% POC threshold.','Check loss severity and replacement cost before a final underwriting decision.','F')
        elif ratio>=.25: add('moderate_claims_to_value','loss_ratio',f'Five-year claims / replacement cost is {ratio:.0%}.','Confirm loss circumstances, recovery, and completed repairs.')
    if flags['check_claims_count']:
        claims=_to_float(r.get('prior_claim_count_5y'),0)
        if claims>=3: add('claim_frequency','prior_claim_count_5y',f'{int(claims)} claims in five years exceeds the POC frequency threshold.','Review the loss run and document the underwriting decision.','F')
        elif claims==2: add('two_claims','prior_claim_count_5y','Two claims are recorded in five years.','Assess causes and whether repairs reduce recurrence.')
        if _to_float(r.get('open_claims'),0)>0: add('open_claim','open_claims','An unresolved claim is recorded.','Confirm claim status and outstanding repairs.','F')
        if _to_float(r.get('water_claim_count_5y'),0)>0: add('water_loss','water_claim_count_5y','Prior water loss requires context.','Review repair records and leak-prevention measures.')
    if flags['check_roof_age']:
        age=_to_float(r.get('roof_age'),0)
        if age>25 and r.get('roof_condition_ai')=='Poor': add('old_poor_roof','roof_age','Roof is over 25 years old and reported in poor condition.','Obtain an inspection and replacement or repair plan.','F')
        elif age>=20: add('aging_roof','roof_age',f'Roof is {age:.0f} years old.','Confirm condition, remaining useful life, and replacement evidence.')
        if r.get('roof_condition_ai')=='Poor': add('poor_roof','roof_condition_ai','Poor roof condition is reported.','Review the inspection and repair evidence.')
    if flags['check_hazard_exposure']:
        for k,start,severe,name in [('wildfire_score',50,85,'Wildfire'),('wind_hail_score',50,80,'Wind / hail')]:
            value=_to_float(r.get(k),0)
            if value>=start: add(k,k,f'{name} exposure is {value:.0f}/100.','Verify the hazard report and review mitigation / placement options.','F' if value>=severe else 'B')
        if r.get('flood_zone') in {'A','AE','AH','AO','V','VE'}: add('flood_zone','flood_zone',f'Flood zone {r["flood_zone"]} needs coverage review.','Confirm flood mapping and any separate flood coverage.')
    if flags['check_occupancy'] and r.get('occupancy') in {'Seasonal','Investment','Vacant'}:
        add('occupancy','occupancy',f'Occupancy is {r["occupancy"].lower()}.','Confirm eligibility for the intended homeowners product.')
    if _to_float(r.get('coverage_to_rc_ratio'),1)<.8: add('underinsurance','requested_dwelling_limit','Dwelling coverage is below 80% of estimated replacement cost.','Reconcile the estimate and requested Coverage A with the insured.')
    checks=[('roof_leaks','Yes','Active roof leakage'),('unrepaired_damage','Yes','Unrepaired damage'),('short_term_rental','Yes','Short-term rental use'),('business_use','Yes','Business activity'),('renovation_in_progress','Yes','Structural renovation'),('trampoline','Yes','Trampoline exposure'),('animal_bite_history','Yes','Animal liability history'),('prior_flooding','Yes','Prior flooding'),('prior_nonrenewal','Yes','Prior nonrenewal / cancellation')]
    for key,value,name in checks:
        if r.get(key)==value: add(key,key,name+' requires underwriter review.','Confirm the circumstances and supporting evidence.')
    if r.get('electrical_type') in {'Aluminum','Knob and tube'} or r.get('electrical_panel')=='Fuses': add('electrical','electrical_type','Electrical system needs an inspection review.','Obtain electrical inspection / upgrade evidence.')
    if r.get('plumbing_type') in {'Galvanized','Polybutylene'}: add('plumbing','plumbing_type','Plumbing material needs condition review.','Obtain condition and replacement documentation.')
    if r.get('smoke_alarms')=='No': add('smoke_alarms','smoke_alarms','Operational smoke alarms are not confirmed.','Confirm functioning alarms before reassessment.')
    if r.get('pool')=='Yes' and r.get('pool_fenced')!='Yes': add('pool_barrier','pool_fenced','Pool barrier information is incomplete.','Confirm the barrier and premises safeguards.')
    if r.get('diving_board')=='Yes': add('pool_features','diving_board','Pool diving equipment is reported.','Review premises liability requirements.')
    if r.get('solid_fuel_stove')=='Yes' and r.get('stove_professional_install')!='Yes': add('stove','stove_professional_install','Solid-fuel installation needs verification.','Obtain installation and inspection documentation.')
    if r.get('dwelling_type') in {'Condominium','Manufactured home'} or r.get('policy_form')=='Other / needs placement': add('product_fit','dwelling_type','The requested risk needs product-placement review.','Confirm the correct personal-lines product.')
    if r.get('ownership_type')=='LLC / other entity': add('ownership','ownership_type','Entity ownership needs product eligibility review.','Confirm the named-insured interest and product eligibility.')
    if _to_float(r.get('vacant_days'),0)>30: add('vacancy','vacant_days','The home has been unoccupied for more than 30 days.','Confirm occupancy dates and property monitoring.')
    if _to_float(r.get('coverage_lapse_days'),0)>30: add('coverage_gap','coverage_lapse_days','A coverage gap exceeds 30 days.','Document the reason and verify the current property condition.')
    if _to_float(r.get('distance_fire_station'),0)>5: add('fire_response','distance_fire_station','Fire station distance exceeds the 5-mile POC referral threshold.','Verify responding fire protection.')
    if _to_float(r.get('water_heater_age'),0)>15: add('water_heater','water_heater_age','Water heater is over 15 years old.','Confirm condition and leak mitigation.')
    return out

def reference_recommendation(row, include_evidence=True, feature_overrides=None,as_of=None):
    risk=risk_issues(row,feature_overrides)
    guards=input_issues(row,as_of)+(evidence_issues(row) if include_evidence else [])
    status='F' if any(f['severity']=='F' for f in risk) else 'B' if risk else 'A'
    if guards: status='B'
    return {'status':status,'flags':guards+risk,'reasons':[x['reason'] for x in guards+risk] or ['The reference checks are clear.'],'rule_version':RULE_VERSION}

def route_application(row, feature_overrides=None):
    from .prediction import assess_application
    return assess_application(dict(row),feature_overrides=feature_overrides)

def evaluate_portfolio(df):
    from .prediction import assess_many
    return pd.DataFrame(assess_many(df.to_dict('records')))

def build_audit_log(df):
    return evaluate_portfolio(df)

def load_csv(name):
    return pd.read_csv(DATA_DIR/name,dtype={'app_id':str,'zip_code':str})
