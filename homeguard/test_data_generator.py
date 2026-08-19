"""Generate test application data for validation testing."""
import random
from pathlib import Path


TEST_NAMES = [
    "alex", "morgan", "jordan", "casey", "taylor", "riley", "dakota", "skylar",
    "sage", "raven", "quinn", "ash", "blake", "drew", "hayden", "reese"
]

TEST_LAST_NAMES = [
    "smith", "johnson", "williams", "brown", "jones", "garcia", "miller", "davis"
]

STREETS = ["Main", "Oak", "Elm", "Maple", "Pine", "Cedar", "Birch", "Ash"]
ROOF_MATERIALS = ["Architectural Shingle", "3-tab Shingle", "Metal", "Tile"]


def get_test_name_counter():
    """Get and increment test name counter."""
    counter_file = Path(__file__).parent.parent / "data" / ".test_counter"

    if counter_file.exists():
        with open(counter_file, "r") as f:
            counter = int(f.read().strip())
    else:
        counter = 0

    counter += 1

    with open(counter_file, "w") as f:
        f.write(str(counter))

    return f"{random.choice(TEST_NAMES)}{random.choice(TEST_LAST_NAMES)}_test_{counter:03d}"


def generate_test_data_a() -> dict:
    """Generate test data that routes to Category A."""
    return {
        "applicant_name": get_test_name_counter(),
        "applicant_email": f"test{random.randint(1000, 9999)}@example.com",
        "state": random.choice(["CA", "TX", "FL", "NY", "PA", "IL", "OH", "GA"]),
        "address": f"{random.randint(1, 9999)} {random.choice(STREETS)} St",
        "city": random.choice(["Springfield", "Shelbyville", "Capital City", "Metropolis"]),
        "zip_code": f"{random.randint(10000, 99999)}",
        "occupancy": "Owner-occupied",
        "year_built": random.randint(2000, 2023),
        "roof_age": random.randint(5, 15),
        "roof_material": random.choice(ROOF_MATERIALS),
        "roof_condition_ai": "Good",
        "requested_dwelling_limit": random.randint(400000, 550000),
        "estimated_replacement_cost": random.randint(450000, 550000),
        "prior_claim_count_5y": 0,  # Category A: no claims
        "water_claim_count_5y": 0,
        "claim_total_paid_5y": 0,
        "open_claims": 0,
        "wildfire_score": random.randint(20, 60),
        "wind_hail_score": random.randint(20, 60),
        "flood_zone": "X",
        "external_consumer_data_used": "No",
        "ai_governance_docs_ready": "Yes",
    }


def generate_test_data_b() -> dict:
    """Generate test data that routes to Category B."""
    replacement_cost = random.randint(450000, 550000)
    claim_paid = random.randint(int(replacement_cost * 0.30), int(replacement_cost * 0.65))

    return {
        "applicant_name": get_test_name_counter(),
        "applicant_email": f"test{random.randint(1000, 9999)}@example.com",
        "state": random.choice(["CA", "TX", "FL", "NY", "PA", "IL", "OH", "GA"]),
        "address": f"{random.randint(1, 9999)} {random.choice(STREETS)} St",
        "city": random.choice(["Springfield", "Shelbyville", "Capital City", "Metropolis"]),
        "zip_code": f"{random.randint(10000, 99999)}",
        "occupancy": random.choice(["Owner-occupied", "Owner-occupied", "Seasonal"]),
        "year_built": random.randint(1990, 2010),
        "roof_age": random.randint(18, 25),
        "roof_material": random.choice(ROOF_MATERIALS),
        "roof_condition_ai": random.choice(["Good", "Fair"]),
        "requested_dwelling_limit": random.randint(400000, 550000),
        "estimated_replacement_cost": replacement_cost,
        "prior_claim_count_5y": 2,  # Category B: exactly 2 claims
        "water_claim_count_5y": random.choice([0, 1]),
        "claim_total_paid_5y": claim_paid,
        "open_claims": 0,
        "wildfire_score": random.randint(40, 70),
        "wind_hail_score": random.randint(40, 70),
        "flood_zone": "X",
        "external_consumer_data_used": "No",
        "ai_governance_docs_ready": "Yes",
    }


def generate_test_data_f() -> dict:
    """Generate test data that routes to Category F."""
    replacement_cost = random.randint(450000, 550000)
    claim_paid = random.randint(int(replacement_cost * 0.80), int(replacement_cost * 1.10))

    return {
        "applicant_name": get_test_name_counter(),
        "applicant_email": f"test{random.randint(1000, 9999)}@example.com",
        "state": random.choice(["CA", "TX", "FL", "NY", "PA", "IL", "OH", "GA"]),
        "address": f"{random.randint(1, 9999)} {random.choice(STREETS)} St",
        "city": random.choice(["Springfield", "Shelbyville", "Capital City", "Metropolis"]),
        "zip_code": f"{random.randint(10000, 99999)}",
        "occupancy": "Owner-occupied",
        "year_built": random.randint(1975, 2015),
        "roof_age": random.randint(10, 20),
        "roof_material": random.choice(ROOF_MATERIALS),
        "roof_condition_ai": "Good",
        "requested_dwelling_limit": random.randint(350000, 500000),
        "estimated_replacement_cost": replacement_cost,
        "prior_claim_count_5y": random.choice([3, 4, 5]),  # Category F: 3+ claims
        "water_claim_count_5y": 0,
        "claim_total_paid_5y": claim_paid,
        "open_claims": 0,
        "wildfire_score": random.randint(30, 70),
        "wind_hail_score": random.randint(30, 70),
        "flood_zone": "X",
        "external_consumer_data_used": "No",
        "ai_governance_docs_ready": "Yes",
    }
