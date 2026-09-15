"""Legacy sample helpers now use the complete deterministic questionnaire."""
from .synthetic import synthetic_application,evidence_gap_example


def generate_test_data_a(): return synthetic_application(3,'A',900)
def generate_test_data_b(): return evidence_gap_example()
def generate_test_data_f(): return synthetic_application(3,'F',900)
