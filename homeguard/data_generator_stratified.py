"""Generate 1000 stratified test applications across all 50 US states."""
import pandas as pd
import numpy as np
import random
from datetime import datetime

# US state populations (2024 estimate) - for proportional distribution
STATE_POPULATIONS = {
    "CA": 39538223, "TX": 30033928, "FL": 22610726, "NY": 19571216, "PA": 12961683,
    "IL": 12549689, "OH": 11785869, "GA": 10912876, "NC": 10439388, "MI": 9986857,
    "NJ": 9290841, "VA": 8715698, "WA": 7705281, "AZ": 7431344, "MA": 7001399,
    "TN": 7126489, "IN": 6862199, "MD": 6177224, "MO": 6196911, "WI": 5910726,
    "CO": 5773714, "MN": 5737915, "SC": 5373555, "AL": 5108468, "LA": 4635315,
    "KY": 4505836, "OR": 4233358, "OK": 4053824, "CT": 3626205, "UT": 3417734,
    "NM": 2117522, "NV": 3194176, "AR": 3067732, "MS": 2939690, "KS": 2940546,
    "NE": 1920076, "ID": 1964726, "HI": 1435138, "NH": 1454674, "ME": 1385340,
    "MT": 1122867, "RI": 1095962, "DE": 1031890, "SD": 887770, "ND": 780588,
    "AK": 733406, "VT": 643077, "WY": 576851
}

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "Michael", "Jennifer", "William", "Linda",
    "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah",
    "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa", "Matthew", "Betty",
    "Mark", "Margaret", "Donald", "Sandra", "Steven", "Ashley", "Paul", "Kimberly",
    "Andrew", "Emily", "Joshua", "Donna", "Kenneth", "Michelle", "Kevin", "Carol",
    "Brian", "Amanda", "George", "Melissa", "Edward", "Deborah", "Ronald", "Stephanie",
    "Anthony", "Rebecca", "Frank", "Sharon", "Ryan", "Laura", "Gary", "Cynthia"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Young",
    "Allen", "King", "Wright", "Scott", "Torres", "Peterson", "Phillips", "Campbell",
    "Parker", "Evans", "Edwards", "Collins", "Reeves", "Stewart", "Morris", "Morales",
    "Ortiz", "Murphy", "Cook", "Rogers", "Gutierrez", "Ortega", "Morgan", "Peterson"
]

STREETS = ["Main", "Oak", "Elm", "Maple", "Pine", "Cedar", "Birch", "Ash", "Willow", "Cherry",
           "Apple", "Walnut", "Beach", "Mountain", "Forest", "River", "Lake", "Creek", "Valley",
           "Hill", "Park", "Garden", "Court", "Drive", "Lane", "Street", "Avenue", "Boulevard"]

ROOF_MATERIALS = ["Architectural Shingle", "3-tab Shingle", "Metal", "Tile", "Wood Shake", "Asphalt"]
ROOF_CONDITIONS = ["Good", "Fair", "Poor"]
OCCUPANCIES = ["Owner-occupied", "Seasonal", "Investment"]


def get_category_a_data(state: str, app_id: str) -> dict:
    """Generate Category A (AUTO PASS) application - must have loss_ratio < 0.25."""
    roof_age = random.randint(5, 15)  # Young roof
    roof_condition = "Good"
    prior_claims = 0  # No claims
    water_claims = 0
    replacement_cost = random.randint(450000, 550000)
    claim_paid = 0  # Zero claims = zero paid
    loss_ratio = 0

    # State-specific hazards (lower for A category)
    hazard_profiles = {
        "CA": {"wildfire": random.randint(10, 35), "wind_hail": random.randint(15, 40)},
        "FL": {"wildfire": random.randint(5, 20), "wind_hail": random.randint(35, 60)},
        "TX": {"wildfire": random.randint(15, 35), "wind_hail": random.randint(50, 75)},
        "default": {"wildfire": random.randint(10, 30), "wind_hail": random.randint(20, 50)}
    }
    hazard = hazard_profiles.get(state, hazard_profiles["default"])

    return {
        "app_id": app_id,
        "applicant_name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
        "applicant_email": f"applicant{app_id}@example.com",
        "state": state,
        "address": f"{random.randint(1, 9999)} {random.choice(STREETS)} St",
        "city": "City",
        "zip_code": f"{random.randint(10000, 99999)}",
        "occupancy": "Owner-occupied",
        "year_built": random.randint(2000, 2022),
        "roof_age": roof_age,
        "roof_material": random.choice(ROOF_MATERIALS),
        "roof_condition_ai": roof_condition,
        "requested_dwelling_limit": int(replacement_cost * 0.9),
        "estimated_replacement_cost": replacement_cost,
        "prior_claim_count_5y": prior_claims,
        "water_claim_count_5y": water_claims,
        "claim_total_paid_5y": claim_paid,
        "open_claims": 0,
        "loss_ratio": loss_ratio,
        "wildfire_score": hazard["wildfire"],
        "wind_hail_score": hazard["wind_hail"],
        "flood_zone": "X",
        "external_consumer_data_used": "No",
        "ai_governance_docs_ready": "Yes",
    }


def get_category_b_data(state: str, app_id: str) -> dict:
    """Generate Category B (NEEDS UNDERWRITER) - must have 0.25 < loss_ratio < 0.75."""
    roof_age = random.randint(20, 25)  # Aging roof
    roof_condition = random.choice(["Fair", "Fair", "Fair"])
    prior_claims = 2  # Exactly 2 claims
    water_claims = 0
    replacement_cost = random.randint(450000, 550000)
    # Generate claim amount in 0.25-0.75 range
    claim_paid = random.randint(int(replacement_cost * 0.30), int(replacement_cost * 0.65))
    loss_ratio = claim_paid / replacement_cost

    hazard_profiles = {
        "CA": {"wildfire": random.randint(40, 60), "wind_hail": random.randint(25, 45)},
        "FL": {"wildfire": random.randint(10, 25), "wind_hail": random.randint(45, 65)},
        "TX": {"wildfire": random.randint(20, 40), "wind_hail": random.randint(50, 65)},
        "default": {"wildfire": random.randint(30, 50), "wind_hail": random.randint(35, 60)}
    }
    hazard = hazard_profiles.get(state, hazard_profiles["default"])

    return {
        "app_id": app_id,
        "applicant_name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
        "applicant_email": f"applicant{app_id}@example.com",
        "state": state,
        "address": f"{random.randint(1, 9999)} {random.choice(STREETS)} St",
        "city": "City",
        "zip_code": f"{random.randint(10000, 99999)}",
        "occupancy": random.choice(["Owner-occupied", "Owner-occupied", "Seasonal"]),
        "year_built": random.randint(1990, 2010),
        "roof_age": roof_age,
        "roof_material": random.choice(ROOF_MATERIALS),
        "roof_condition_ai": roof_condition,
        "requested_dwelling_limit": 550000,
        "estimated_replacement_cost": 650000,
        "prior_claim_count_5y": prior_claims,
        "water_claim_count_5y": water_claims,
        "claim_total_paid_5y": claim_paid,
        "open_claims": 0,
        "loss_ratio": loss_ratio,
        "wildfire_score": hazard["wildfire"],
        "wind_hail_score": hazard["wind_hail"],
        "flood_zone": "X",
        "external_consumer_data_used": "No",
        "ai_governance_docs_ready": "Yes",
    }


def get_category_f_data(state: str, app_id: str) -> dict:
    """Generate Category F (AUTO REJECT) - must have loss_ratio > 0.75 OR claims >= 3."""
    roof_age = random.randint(5, 15)
    roof_condition = "Good"
    prior_claims = random.choice([3, 4, 5])  # 3+ claims = auto-reject
    water_claims = 0
    replacement_cost = random.randint(450000, 550000)
    # Generate high claims to hit > 0.75 loss ratio
    claim_paid = random.randint(int(replacement_cost * 0.80), int(replacement_cost * 1.10))
    loss_ratio = claim_paid / replacement_cost

    hazard_profiles = {
        "CA": {"wildfire": random.randint(60, 80), "wind_hail": random.randint(35, 55)},
        "FL": {"wildfire": random.randint(15, 30), "wind_hail": random.randint(65, 80)},
        "TX": {"wildfire": random.randint(30, 50), "wind_hail": random.randint(70, 85)},
        "default": {"wildfire": random.randint(50, 75), "wind_hail": random.randint(50, 75)}
    }
    hazard = hazard_profiles.get(state, hazard_profiles["default"])

    return {
        "app_id": app_id,
        "applicant_name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
        "applicant_email": f"applicant{app_id}@example.com",
        "state": state,
        "address": f"{random.randint(1, 9999)} {random.choice(STREETS)} St",
        "city": "City",
        "zip_code": f"{random.randint(10000, 99999)}",
        "occupancy": "Owner-occupied",
        "year_built": random.randint(1975, 2015),
        "roof_age": roof_age,
        "roof_material": random.choice(ROOF_MATERIALS),
        "roof_condition_ai": roof_condition,
        "requested_dwelling_limit": 400000,
        "estimated_replacement_cost": 700000,
        "prior_claim_count_5y": prior_claims,
        "water_claim_count_5y": water_claims,
        "claim_total_paid_5y": claim_paid,
        "open_claims": 0,
        "loss_ratio": loss_ratio,
        "wildfire_score": hazard["wildfire"],
        "wind_hail_score": hazard["wind_hail"],
        "flood_zone": "X",
        "external_consumer_data_used": "No",
        "ai_governance_docs_ready": "Yes",
    }


def generate_stratified_dataset(total: int = 1000, pct_a: float = 0.70, pct_b: float = 0.20, pct_f: float = 0.10) -> pd.DataFrame:
    """Generate stratified dataset with population-weighted state distribution."""
    np.random.seed(42)
    random.seed(42)

    # Calculate exact target counts
    target_a = int(total * pct_a)
    target_b = int(total * pct_b)
    target_f = total - target_a - target_b

    # Build weighted state list for sampling
    total_pop = sum(STATE_POPULATIONS.values())
    state_weights = [STATE_POPULATIONS[state] / total_pop for state in sorted(STATE_POPULATIONS.keys())]
    states_sorted = sorted(STATE_POPULATIONS.keys())

    records = []
    app_counter = 0

    # Generate Category A (exactly 700)
    for i in range(target_a):
        state = np.random.choice(states_sorted, p=state_weights)
        app_id = f"APP-{app_counter + 1:05d}"
        records.append(get_category_a_data(state, app_id))
        app_counter += 1

    # Generate Category B (exactly 200)
    for i in range(target_b):
        state = np.random.choice(states_sorted, p=state_weights)
        app_id = f"APP-{app_counter + 1:05d}"
        records.append(get_category_b_data(state, app_id))
        app_counter += 1

    # Generate Category F (exactly 100)
    for i in range(target_f):
        state = np.random.choice(states_sorted, p=state_weights)
        app_id = f"APP-{app_counter + 1:05d}"
        records.append(get_category_f_data(state, app_id))
        app_counter += 1

    df = pd.DataFrame(records)

    # Shuffle
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    return df


if __name__ == "__main__":
    print("Generating 1000 stratified applications (70% A, 20% B, 10% F)...")
    df = generate_stratified_dataset(total=1000, pct_a=0.70, pct_b=0.20, pct_f=0.10)

    # Save
    df.to_csv("data/applications.csv", index=False)

    print(f"\n[OK] Generated {len(df)} applications")
    print(f"  Distribution across all 50 states")
    print(f"\nState distribution sample:")
    print(df["state"].value_counts().head(10))
    print(f"\n[OK] Saved to: data/applications.csv")
