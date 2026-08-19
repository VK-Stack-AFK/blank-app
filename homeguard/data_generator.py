"""Generate synthetic homeowners insurance applications for testing."""
import pandas as pd
import numpy as np
from datetime import datetime
import random

# Sample realistic data
FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "Michael", "Jennifer", "William", "Linda",
    "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah",
    "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa", "Matthew", "Betty",
    "Mark", "Margaret", "Donald", "Sandra", "Steven", "Ashley", "Paul", "Kimberly",
    "Andrew", "Emily", "Joshua", "Donna", "Kenneth", "Michelle", "Kevin", "Carol",
    "Brian", "Amanda", "George", "Melissa", "Edward", "Deborah", "Ronald", "Stephanie"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Young",
    "Allen", "King", "Wright", "Scott", "Torres", "Peterson", "Phillips", "Campbell",
    "Parker", "Evans", "Edwards", "Collins", "Reeves", "Stewart", "Morris", "Morales"
]

STREETS = [
    "Main", "Oak", "Elm", "Maple", "Pine", "Cedar", "Birch", "Ash", "Willow",
    "Cherry", "Apple", "Walnut", "Ash", "Spruce", "Fir", "Hemlock", "Juniper",
    "Beach", "Mountain", "Forest", "River", "Lake", "Creek", "Valley", "Hill",
    "Park", "Garden", "Court", "Drive", "Lane", "Street", "Avenue", "Boulevard"
]

CITIES_BY_STATE = {
    "CA": ["Los Angeles", "San Francisco", "San Diego", "Sacramento", "Fresno"],
    "TX": ["Houston", "Dallas", "San Antonio", "Austin", "Fort Worth"],
    "FL": ["Miami", "Tampa", "Orlando", "Jacksonville", "Naples"],
    "NY": ["New York", "Buffalo", "Rochester", "Albany", "Syracuse"],
    "IL": ["Chicago", "Springfield", "Peoria", "Rockford", "Naperville"],
    "PA": ["Philadelphia", "Pittsburgh", "Allentown", "Erie", "Reading"],
    "OH": ["Columbus", "Cleveland", "Cincinnati", "Toledo", "Akron"],
    "GA": ["Atlanta", "Augusta", "Savannah", "Athens", "Macon"],
    "NC": ["Charlotte", "Raleigh", "Greensboro", "Durham", "Winston-Salem"],
    "MI": ["Detroit", "Grand Rapids", "Lansing", "Ann Arbor", "Flint"],
    "NJ": ["Newark", "Jersey City", "Paterson", "Elizabeth", "Trenton"],
    "VA": ["Richmond", "Virginia Beach", "Arlington", "Alexandria", "Roanoke"],
    "WA": ["Seattle", "Spokane", "Tacoma", "Vancouver", "Bellevue"],
    "AZ": ["Phoenix", "Mesa", "Scottsdale", "Glendale", "Gilbert"],
    "CO": ["Denver", "Colorado Springs", "Aurora", "Fort Collins", "Lakewood"],
    "MD": ["Baltimore", "Annapolis", "Frederick", "Gaithersburg", "Rockville"],
}

ROOF_MATERIALS = ["Architectural Shingle", "3-tab Shingle", "Metal", "Tile", "Wood Shake", "Asphalt"]
ROOF_CONDITIONS = ["Good", "Fair", "Poor", "Unknown"]
OCCUPANCIES = ["Owner-occupied", "Seasonal", "Investment"]

ALL_STATES = list(CITIES_BY_STATE.keys()) + ["AL", "AK", "AR", "CT", "DE", "HI", "ID", "IN", "IA", "KS", "KY", "LA", "ME", "MA", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NM", "OK", "OR", "RI", "SC", "SD", "TN", "UT", "VT", "WI", "WY", "WV"]


def generate_applications(count: int = 1000) -> pd.DataFrame:
    """Generate synthetic homeowners insurance applications."""
    np.random.seed(42)
    random.seed(42)

    records = []

    for i in range(count):
        app_id = f"APP-{i+1:05d}"
        state = random.choice(ALL_STATES)

        # Personal info
        applicant_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

        # Address
        street_num = random.randint(1, 9999)
        street_name = random.choice(STREETS)
        city = random.choice(CITIES_BY_STATE.get(state, ["City"]))
        zip_code = f"{random.randint(10000, 99999)}"
        address = f"{street_num} {street_name} St"

        occupancy = np.random.choice(OCCUPANCIES, p=[0.85, 0.10, 0.05])

        # Property details
        year_built = random.randint(1960, 2023)
        roof_age = random.randint(0, 40)
        roof_material = random.choice(ROOF_MATERIALS)
        roof_condition_ai = np.random.choice(ROOF_CONDITIONS, p=[0.50, 0.30, 0.10, 0.10])

        # Coverage
        replacement_cost = random.choice([350000, 400000, 450000, 500000, 550000, 600000, 650000, 700000, 750000, 800000, 900000, 1000000])
        coverage_pct = np.random.choice([0.70, 0.80, 0.85, 0.90, 0.95, 1.00, 1.05, 1.10], p=[0.05, 0.10, 0.15, 0.30, 0.25, 0.10, 0.04, 0.01])
        requested_dwelling_limit = int(replacement_cost * coverage_pct)

        # Claims (weighted to generate realistic distribution)
        claims_probability = np.random.random()
        if claims_probability < 0.70:  # 70% no claims
            prior_claim_count_5y = 0
            water_claim_count_5y = 0
            claim_total_paid_5y = 0
            open_claims = 0
        elif claims_probability < 0.90:  # 20% have 1-2 claims
            prior_claim_count_5y = random.choice([1, 2])
            water_claim_count_5y = 1 if random.random() < 0.4 else 0
            claim_total_paid_5y = random.randint(5000, 30000)
            open_claims = 0
        else:  # 10% have 3+ claims or open claims
            prior_claim_count_5y = random.choice([3, 4, 5])
            water_claim_count_5y = random.choice([1, 2])
            claim_total_paid_5y = random.randint(20000, 80000)
            open_claims = 1 if random.random() < 0.3 else 0

        # Loss ratio = total paid / replacement cost
        loss_ratio = claim_total_paid_5y / replacement_cost if replacement_cost > 0 else 0

        # Hazards (vary by state)
        if state == "CA":
            wildfire_score = random.randint(40, 100)
        elif state in ["FL", "LA"]:
            wildfire_score = random.randint(10, 50)
        else:
            wildfire_score = random.randint(10, 70)

        wind_hail_score = random.randint(20, 95)

        flood_zone_choices = ["X", "X", "X", "X", "X", "X", "A", "AE", "VE"]
        flood_zone = random.choice(flood_zone_choices)

        # Governance
        external_consumer_data_used = "Yes" if random.random() < 0.60 else "No"
        ai_governance_docs_ready = "Yes" if random.random() < 0.70 else "No"

        record = {
            "app_id": app_id,
            "applicant_name": applicant_name,
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
            "estimated_replacement_cost": replacement_cost,
            "prior_claim_count_5y": prior_claim_count_5y,
            "water_claim_count_5y": water_claim_count_5y,
            "claim_total_paid_5y": claim_total_paid_5y,
            "open_claims": open_claims,
            "loss_ratio": loss_ratio,
            "wildfire_score": wildfire_score,
            "wind_hail_score": wind_hail_score,
            "flood_zone": flood_zone,
            "external_consumer_data_used": external_consumer_data_used,
            "ai_governance_docs_ready": ai_governance_docs_ready,
        }

        records.append(record)

    df = pd.DataFrame(records)
    return df


if __name__ == "__main__":
    # Generate and save
    df = generate_applications(1000)
    df.to_csv("data/applications_1k.csv", index=False)
    print(f"✓ Generated {len(df)} applications")
    print(f"✓ Saved to: data/applications_1k.csv")
    print(f"\nSample row:")
    print(df.iloc[0])
    print(f"\nStatus distribution (before routing):")
    print(f"  Loss ratio < 0.25: {(df['loss_ratio'] < 0.25).sum()} apps")
    print(f"  Loss ratio 0.25-0.75: {((df['loss_ratio'] >= 0.25) & (df['loss_ratio'] <= 0.75)).sum()} apps")
    print(f"  Loss ratio > 0.75: {(df['loss_ratio'] > 0.75).sum()} apps")
