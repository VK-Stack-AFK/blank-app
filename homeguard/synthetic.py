"""Deterministic, explicitly synthetic homeowners scenarios; no real consumers."""
from datetime import date, timedelta
import random
import pandas as pd
from .schema import FIELDS, STATES, VERIFICATION_FIELDS, REFERENCE_FIELDS, blank_application
from .config import SCHEMA_VERSION

AS_OF = date(2026, 9, 15)

def synthetic_application(index=0, category='A', seed=42):
    rng=random.Random(seed+index*1009)
    r=blank_application()
    for f in FIELDS:
        if f.kind=='select': r[f.key]='No' if 'No' in f.options else f.options[1]
        elif f.kind in ('integer','number','money'): r[f.key]=max(f.minimum,1) if f.required else None
        elif f.kind=='date': r[f.key]=AS_OF.isoformat() if f.required else None
        elif f.required: r[f.key]='Synthetic example'
    rc=rng.randrange(200000,1500000,1000)
    roof_age=rng.randint(1,18)
    r.update(app_id=f'DEMO-{seed:04d}-{index+1:05d}',schema_version=SCHEMA_VERSION,
        applicant_name=f'{rng.choice(["Alex","Jordan","Morgan","Taylor","Casey","Sam"])} {rng.choice(["Reed","Brooks","Ellis","Parker","Lane","Hayes"])} · Demo {index+1}',
        applicant_email=f'homeowner{index+1}@example.com',applicant_phone='202-555-0100',producer_name='HomeGuard Demo Agency',
        address=f'{100+index} Example Lane',city='Sample City',county='Sample County',state=STATES[index%len(STATES)],zip_code=f'{1000+index%98000:05d}',
        ownership_type='Individual',occupancy='Owner-occupied',primary_residence='Yes',dwelling_type='Detached single family',number_of_units=1,
        year_built=rng.randint(1950,AS_OF.year-roof_age),square_footage=rng.randrange(1000,5500,50),stories=rng.choice([1,2,3]),
        construction_type=rng.choice(['Frame','Masonry veneer','Solid masonry']),foundation_type=rng.choice(['Slab','Crawl space','Basement']),
        roof_age=roof_age,roof_material=rng.choice(['Architectural shingle','Metal','Tile','Slate']),roof_shape=rng.choice(['Gable','Hip','Mixed']),roof_condition_ai=rng.choice(['Good','Fair']),
        roof_replacement_year=AS_OF.year-roof_age,roof_layers=1,electrical_type='Copper',electrical_panel='Circuit breakers',service_amps=200,
        plumbing_type=rng.choice(['Copper','PEX / PVC / CPVC']),water_heater_age=rng.randint(1,14),heating_type=rng.choice(['Central gas','Central electric','Heat pump']),
        smoke_alarms='Yes',carbon_monoxide_alarms='Yes',distance_fire_station=round(rng.uniform(.1,4.9),1),distance_hydrant=rng.randrange(100,1000,50),
        pool='No',pool_fenced='No',wildfire_score=rng.randint(0,49),wind_hail_score=rng.randint(0,49),flood_zone='X',policy_form=rng.choice(['HO-3','HO-5']),
        requested_dwelling_limit=round(rc*rng.uniform(.82,1.15)),estimated_replacement_cost=rc,
        other_structures_limit=round(rc*.1),personal_property_limit=round(rc*.6),loss_of_use_limit=round(rc*.2),personal_liability_limit=rng.choice([100000,300000,500000]),
        medical_payments_limit=5000,all_peril_deductible=rng.choice([1000,2500,5000]),wind_deductible_pct=2,
        prior_carrier='Example Mutual (synthetic)',coverage_lapse_days=0,vacant_days=rng.randint(0,20),
        prior_claim_count_5y=0,water_claim_count_5y=0,claim_total_paid_5y=0,open_claims=0,
        applicant_attestation='Yes',verification_consent='Yes',external_consumer_data_used='No',ai_governance_docs_ready='Yes',
        verification_reviewer='Synthetic evidence scenario',verification_date=AS_OF.isoformat(),
        data_source='Demo portfolio',submission_date=(AS_OF-timedelta(days=rng.randrange(0,60))).isoformat()+'T12:00:00+00:00')
    for key in VERIFICATION_FIELDS:
        r[key]='Verified'; r[REFERENCE_FIELDS[key]]=f'DEMO-ONLY/{index+1}/{key}'
    if category=='A' and index%4==0:
        r.update(prior_claim_count_5y=1,claim_total_paid_5y=round(rc*rng.uniform(.001,.20)))
    if category=='A' and index%7==0: r.update(pool='Yes',pool_fenced='Yes')
    if category=='B':
        case=index%31
        if case==0: r.update(roof_age=rng.randint(20,25),roof_replacement_year=None,year_built=1980)
        elif case==1: r.update(prior_claim_count_5y=2,claim_total_paid_5y=round(rc*rng.uniform(.01,.2)))
        elif case==2: r.update(prior_claim_count_5y=1,claim_total_paid_5y=round(rc*rng.uniform(.26,.70)))
        elif case==3: r['wind_hail_score']=rng.randint(50,79)
        elif case==4: r['wildfire_score']=rng.randint(50,84)
        elif case==5: r['occupancy']='Seasonal'
        elif case==6: r['flood_zone']=rng.choice(['AE','A','V','VE'])
        elif case==7: r['requested_dwelling_limit']=round(rc*rng.uniform(.5,.79))
        elif case==8: r.update(pool='Yes',pool_fenced='No')
        elif case==9: r['electrical_type']=rng.choice(['Aluminum','Knob and tube'])
        elif case==10: r['plumbing_type']=rng.choice(['Galvanized','Polybutylene'])
        elif case==11: r['short_term_rental']='Yes'
        elif case==12: r.update(prior_claim_count_5y=1,water_claim_count_5y=1,claim_total_paid_5y=10000)
        elif case==13: r['water_heater_age']=rng.randint(16,25)
        elif case==14: r['distance_fire_station']=round(rng.uniform(5.1,10),1)
        elif case==15: r['roof_leaks']='Yes'
        elif case==16: r['unrepaired_damage']='Yes'
        elif case==17: r['business_use']='Yes'
        elif case==18: r['renovation_in_progress']='Yes'
        elif case==19: r[rng.choice(['trampoline','animal_bite_history'])]='Yes'
        elif case==20: r['prior_flooding']='Yes'
        elif case==21: r['prior_nonrenewal']='Yes'
        elif case==22: r['electrical_panel']='Fuses'
        elif case==23: r['smoke_alarms']='No'
        elif case==24: r.update(solid_fuel_stove='Yes',stove_professional_install='No')
        elif case==25: r['dwelling_type']=rng.choice(['Condominium','Manufactured home'])
        elif case==26: r['ownership_type']='LLC / other entity'
        elif case==27: r['vacant_days']=rng.randint(31,90)
        elif case==28: r['coverage_lapse_days']=rng.randint(31,120)
        elif case==29: r.update(pool='Yes',pool_fenced='Yes',diving_board='Yes')
        else: r['roof_condition_ai']='Poor'
    elif category=='F':
        case=index%5
        if case==0: r.update(prior_claim_count_5y=rng.randint(3,6),claim_total_paid_5y=round(rc*rng.uniform(.03,.6)))
        elif case==1: r.update(prior_claim_count_5y=1,claim_total_paid_5y=round(rc*rng.uniform(.78,1.2)))
        elif case==2: r.update(prior_claim_count_5y=1,open_claims=1,claim_total_paid_5y=10000)
        elif case==3: r.update(roof_age=rng.randint(26,40),roof_condition_ai='Poor',roof_replacement_year=None,year_built=1960)
        else: r[rng.choice(['wildfire_score','wind_hail_score'])]=rng.randint(85,100)
    if r['prior_claim_count_5y']:
        r['loss_details']=f'Synthetic loss-run example: {r["prior_claim_count_5y"]} claim(s), {r["open_claims"]} open; total paid ${r["claim_total_paid_5y"]:,.0f}. Not a real claims report.'
    r['loss_ratio']=r['claim_total_paid_5y']/rc
    return r

def generate_dataset(count=10000,seed=42):
    rng=random.Random(seed)
    categories=['A']*int(count*.65)+['B']*int(count*.25)
    categories+=['F']*(count-len(categories)); rng.shuffle(categories)
    return pd.DataFrame([synthetic_application(i,c,seed) for i,c in enumerate(categories)])

def evidence_gap_example():
    r=synthetic_application(1,'A',seed=700)
    r.update(app_id=None,applicant_name='Morgan Ellis · Evidence review demo',hazard_verification='Not checked',hazard_document_reference='')
    return r
