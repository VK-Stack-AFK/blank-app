"""Original homeowners POC questionnaire shared by intake, review, and exports.

Informed by public homeowners coverage/application guidance; not an ACORD form
or a carrier-approved application. Unknown information stays unknown.
"""
from dataclasses import dataclass
from datetime import date

STATES = tuple("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split())
UNKNOWN = "Unknown"
YES_NO = (UNKNOWN, "No", "Yes")
VERIFICATION = ("Not checked", "Verified", "Discrepancy", "Not available")
TABS = ("Insured & dwelling", "Roof & systems", "Protection & hazards", "Coverage & losses", "Evidence & consent")

@dataclass(frozen=True)
class Field:
    key: str
    label: str
    section: str
    kind: str = "text"
    required: bool = False
    options: tuple = ()
    minimum: float = 0
    maximum: float | None = None
    help: str = ""
    role: str = "Context"

FIELDS: list[Field] = []
def add(section, key, label, kind="text", required=False, options=(), minimum=0, maximum=None, help="", role="Context"):
    FIELDS.append(Field(key, label, section, kind, required, tuple(options), minimum, maximum, help, role))

s = TABS[0]
add(s,"applicant_name","Named insured",required=True)
add(s,"co_applicant_name","Additional named insured")
add(s,"applicant_email","Contact email",required=True)
add(s,"applicant_phone","Contact phone",required=True)
add(s,"producer_name","Producer / agency")
add(s,"effective_date","Requested effective date","date",True)
add(s,"ownership_type","Ownership interest","select",True,(UNKNOWN,"Individual","Joint owners","Trust","LLC / other entity"),role="Referral")
add(s,"mailing_address","Mailing address, if different")
add(s,"address","Insured property street address",required=True)
add(s,"city","City",required=True)
add(s,"state","State / jurisdiction","select",True,(UNKNOWN,)+STATES,role="Governance")
add(s,"zip_code","ZIP code",required=True,help="Keep leading zeroes. Use 5 digits or ZIP+4.")
add(s,"county","County")
add(s,"occupancy","Occupancy","select",True,(UNKNOWN,"Owner-occupied","Seasonal","Investment","Vacant"),role="Model / referral")
add(s,"primary_residence","Insured's primary residence?","select",True,YES_NO)
add(s,"dwelling_type","Dwelling type","select",True,(UNKNOWN,"Detached single family","Townhouse","Two-to-four family","Condominium","Manufactured home"),role="Referral")
add(s,"number_of_units","Number of dwelling units","integer",True,minimum=1,maximum=4,role="Referral")
add(s,"year_built","Year built","integer",True,minimum=1800,maximum=date.today().year,role="Model")
add(s,"square_footage","Finished living area (sq ft)","integer",True,minimum=100,maximum=30000,role="Model / verification")
add(s,"stories","Number of stories","integer",True,minimum=1,maximum=6)
add(s,"construction_type","Exterior construction","select",True,(UNKNOWN,"Frame","Masonry veneer","Solid masonry","Concrete / steel","Other"),role="Model")
add(s,"foundation_type","Foundation","select",True,(UNKNOWN,"Slab","Crawl space","Basement","Elevated / pilings","Other"),role="Model")
add(s,"basement_finished","Finished basement?","select",False,YES_NO)
add(s,"purchase_date","Purchase / closing date","date")
add(s,"renovation_in_progress","Structural renovation in progress?","select",True,YES_NO,role="Referral")
add(s,"vacant_days","Consecutive days unoccupied","integer",True,maximum=365,role="Model / referral")
add(s,"short_term_rental","Any short-term rental use?","select",True,YES_NO,role="Model / referral")
add(s,"business_use","Business activity beyond a home office?","select",True,YES_NO,role="Referral")
add(s,"business_details","Business / rental / renovation details","textarea")
add(s,"mortgagee_name","Mortgage lender / additional interest",help="Name only; do not enter account numbers.")

s = TABS[1]
add(s,"roof_age","Roof age (years)","integer",True,maximum=100,role="Model")
add(s,"roof_material","Roof covering","select",True,(UNKNOWN,"Architectural shingle","Asphalt / 3-tab shingle","Metal","Tile","Slate","Wood shake","Other"),role="Model")
add(s,"roof_shape","Roof shape","select",True,(UNKNOWN,"Gable","Hip","Flat / low slope","Mixed"),role="Model")
add(s,"roof_condition_ai","Reported roof condition","select",True,(UNKNOWN,"Good","Fair","Poor"),help="Record reported or inspected condition. No image AI is connected.",role="Model / verification")
add(s,"roof_replacement_year","Last full roof replacement year","integer",False,minimum=1900,maximum=date.today().year,role="Consistency")
add(s,"roof_layers","Roof covering layers","integer",False,minimum=1,maximum=5)
add(s,"roof_leaks","Active roof leak or unrepaired roof damage?","select",True,YES_NO,role="Referral")
add(s,"roof_document_reference","Roof invoice / inspection reference",help="A reference is not a completed verification.")
add(s,"electrical_type","Electrical wiring","select",True,(UNKNOWN,"Copper","Aluminum","Knob and tube","Mixed / other"),role="Model / referral")
add(s,"electrical_panel","Electrical panel","select",True,(UNKNOWN,"Circuit breakers","Fuses","Other"),role="Referral")
add(s,"electrical_update_year","Electrical update year","integer",False,minimum=1900,maximum=date.today().year)
add(s,"service_amps","Electrical service (amps)","integer",False,minimum=30,maximum=600)
add(s,"plumbing_type","Supply plumbing","select",True,(UNKNOWN,"Copper","PEX / PVC / CPVC","Galvanized","Polybutylene","Mixed / other"),role="Model / referral")
add(s,"plumbing_update_year","Plumbing update year","integer",False,minimum=1900,maximum=date.today().year)
add(s,"water_heater_age","Water heater age (years)","integer",True,maximum=80,role="Model / referral")
add(s,"water_heater_location","Water heater location","select",False,(UNKNOWN,"Garage","Utility room","Attic","Basement","Other"))
add(s,"heating_type","Primary heating","select",True,(UNKNOWN,"Central gas","Central electric","Heat pump","Oil","Wood / solid fuel","Other"),role="Model / referral")
add(s,"heating_update_year","Heating update year","integer",False,minimum=1900,maximum=date.today().year)
add(s,"solid_fuel_stove","Supplemental wood / solid-fuel stove?","select",True,YES_NO,role="Referral")
add(s,"stove_professional_install","Stove professionally installed / inspected?","select",False,YES_NO,role="Referral")
add(s,"unrepaired_damage","Other unrepaired property damage?","select",True,YES_NO,role="Model / referral")
add(s,"damage_details","Damage and completed repair details","textarea")
add(s,"solar_panels","Solar panels installed?","select",False,YES_NO)

s = TABS[2]
add(s,"smoke_alarms","Operational smoke alarms?","select",True,YES_NO,role="Referral")
add(s,"carbon_monoxide_alarms","Operational carbon monoxide alarms?","select",False,YES_NO)
add(s,"burglar_alarm","Burglar alarm","select",False,(UNKNOWN,"None","Local","Centrally monitored"))
add(s,"fire_alarm","Fire alarm","select",False,(UNKNOWN,"None","Local","Centrally monitored"))
add(s,"sprinkler_system","Automatic fire sprinklers?","select",False,YES_NO)
add(s,"water_leak_detection","Automatic water leak detection?","select",False,YES_NO)
add(s,"automatic_water_shutoff","Automatic water shutoff?","select",False,YES_NO)
add(s,"distance_fire_station","Distance to responding fire station (miles)","number",True,maximum=100,role="Model / referral")
add(s,"distance_hydrant","Distance to fire hydrant (feet)","integer",False,maximum=50000)
add(s,"protection_class","Reported protection class (1–10)","integer",False,minimum=1,maximum=10,help="Leave blank if not verified.")
add(s,"pool","Pool or spa on the premises?","select",True,YES_NO,role="Referral")
add(s,"pool_fenced","Pool protected by a fence / approved barrier?","select",False,YES_NO,role="Referral")
add(s,"diving_board","Diving board or slide?","select",False,YES_NO,role="Referral")
add(s,"trampoline","Trampoline on the premises?","select",True,YES_NO,role="Referral")
add(s,"dog_declared","Dogs kept at the property?","select",True,YES_NO)
add(s,"animal_bite_history","Any animal bite / liability incident?","select",True,YES_NO,role="Referral")
add(s,"liability_details","Premises liability details","textarea")
add(s,"wildfire_score","Verified wildfire exposure score (0–100)","integer",True,maximum=100,help="Leave blank if unknown. Missing is not zero risk.",role="Model / verification")
add(s,"wind_hail_score","Verified wind / hail exposure score (0–100)","integer",True,maximum=100,role="Model / verification")
add(s,"flood_zone","Flood zone","select",True,(UNKNOWN,"X","A","AE","AH","AO","V","VE","Other"),role="Model / verification")
add(s,"distance_to_coast","Distance to coast (miles)","number",False,maximum=2000)
add(s,"defensible_space","Documented defensible space?","select",False,YES_NO)
add(s,"wind_mitigation","Documented roof / opening wind mitigation?","select",False,YES_NO)
add(s,"prior_flooding","Prior flooding / surface-water intrusion?","select",True,YES_NO,role="Referral")
add(s,"hazard_notes","Hazard and mitigation notes","textarea")

s = TABS[3]
add(s,"policy_form","Requested policy form","select",True,(UNKNOWN,"HO-3","HO-5","HO-2","Other / needs placement"),role="Referral")
add(s,"requested_dwelling_limit","Coverage A · dwelling ($)","money",True,minimum=1,role="Model")
add(s,"estimated_replacement_cost","Estimated dwelling replacement cost ($)","money",True,minimum=1,help="Rebuilding cost, not purchase price or market value.",role="Model / verification")
add(s,"other_structures_limit","Coverage B · other structures ($)","money",True)
add(s,"personal_property_limit","Coverage C · personal property ($)","money",True)
add(s,"loss_of_use_limit","Coverage D · loss of use ($)","money",True)
add(s,"personal_liability_limit","Coverage E · personal liability ($)","money",True,minimum=1)
add(s,"medical_payments_limit","Coverage F · medical payments to others ($)","money",True,help="Coverage F is distinct from routing class F.")
add(s,"all_peril_deductible","All-peril deductible ($)","money",True)
add(s,"wind_deductible_pct","Wind / hurricane deductible (%)","number",False,maximum=20)
add(s,"replacement_cost_contents","Replacement cost on contents requested?","select",False,YES_NO)
add(s,"water_backup_requested","Water backup endorsement requested?","select",False,YES_NO)
add(s,"ordinance_law_requested","Ordinance or law coverage requested?","select",False,YES_NO)
add(s,"scheduled_property","Scheduled valuables requested?","select",False,YES_NO)
add(s,"separate_flood_policy","Separate flood coverage","select",False,(UNKNOWN,"In force","Requested","Not requested"))
add(s,"earthquake_requested","Earthquake coverage requested?","select",False,YES_NO)
add(s,"prior_carrier","Current / prior homeowners carrier")
add(s,"prior_policy_expiration","Current policy expiration","date")
add(s,"coverage_lapse_days","Days without homeowners coverage","integer",True,maximum=3650,role="Referral")
add(s,"prior_nonrenewal","Prior cancellation / nonrenewal?","select",True,YES_NO,role="Referral")
add(s,"prior_nonrenewal_reason","Reason and date, if applicable","textarea")
add(s,"prior_claim_count_5y","Total claims in the past 5 years","integer",True,maximum=50,role="Model")
add(s,"water_claim_count_5y","Water-related claims in the past 5 years","integer",True,maximum=50,role="Model")
add(s,"claim_total_paid_5y","Total paid for claims in the past 5 years ($)","money",True,role="Model")
add(s,"open_claims","Open / unresolved claims","integer",True,maximum=50,role="Model")
add(s,"loss_details","Loss dates, causes, payments, and completed repairs","textarea",help="Summarize each loss separately. No claims database is connected.",role="Evidence")

s = TABS[4]
add(s,"property_verification","Property record verification","select",True,VERIFICATION,role="STP evidence")
add(s,"roof_verification","Roof condition verification","select",True,VERIFICATION,role="STP evidence")
add(s,"claims_verification","Claims history verification","select",True,VERIFICATION,role="STP evidence")
add(s,"hazard_verification","Hazard report verification","select",True,VERIFICATION,role="STP evidence")
add(s,"replacement_cost_verification","Replacement-cost estimate verification","select",True,VERIFICATION,role="STP evidence")
add(s,"property_document_reference","Property record reference",role="Evidence")
add(s,"claims_document_reference","Loss-run / claims report reference",role="Evidence")
add(s,"hazard_document_reference","Hazard / flood report reference",role="Evidence")
add(s,"replacement_cost_reference","Replacement-cost estimate reference",role="Evidence")
add(s,"verification_reviewer","Evidence reviewed by",role="Evidence")
add(s,"verification_date","Evidence review date","date",role="Evidence")
add(s,"reported_square_footage_verified","Verified living area (sq ft)","integer",False,minimum=100,maximum=30000,role="Consistency")
add(s,"external_consumer_data_used","External consumer reports used?","select",True,YES_NO,role="Governance")
add(s,"ai_governance_docs_ready","Required external-data governance documented?","select",True,YES_NO,role="Governance")
add(s,"applicant_attestation","Responses confirmed with insured?","select",True,YES_NO,role="STP evidence")
add(s,"verification_consent","Required verification authorization recorded?","select",True,YES_NO,role="STP evidence")
add(s,"underwriting_notes","Underwriting notes and outstanding questions","textarea")

FIELD_MAP = {f.key: f for f in FIELDS}
REQUIRED_FIELDS = tuple(f.key for f in FIELDS if f.required)
CONTACT_FIELDS = ("applicant_name", "applicant_email", "address", "city", "state", "zip_code")
VERIFICATION_FIELDS = ("property_verification", "roof_verification", "claims_verification", "hazard_verification", "replacement_cost_verification")
REFERENCE_FIELDS = dict(zip(VERIFICATION_FIELDS,("property_document_reference","roof_document_reference","claims_document_reference","hazard_document_reference","replacement_cost_reference")))

def blank_application():
    return {f.key: (f.options[0] if f.kind == "select" else None if f.kind in ("integer","number","money","date") else "") for f in FIELDS}

def label(key):
    return FIELD_MAP[key].label if key in FIELD_MAP else key.replace("_", " ").capitalize()
