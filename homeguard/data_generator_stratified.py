"""Compatibility entry point for explicitly synthetic scenario mixtures.

All 50 states and DC are cycled for coverage, not population-weighted sampling.
This generator is not the ML dataset builder; use python -m homeguard.model.
"""
import random
import pandas as pd
from .synthetic import synthetic_application


def _category(category,state,app_id):
    result=synthetic_application(0,category,2026)
    result.update(state=state,app_id=app_id)
    return result

def get_category_a_data(state,app_id): return _category('A',state,app_id)
def get_category_b_data(state,app_id): return _category('B',state,app_id)
def get_category_f_data(state,app_id): return _category('F',state,app_id)

def generate_stratified_dataset(total=1000,pct_a=.70,pct_b=.20,pct_f=.10):
    if total<1 or any(p<0 for p in (pct_a,pct_b,pct_f)) or abs(pct_a+pct_b+pct_f-1)>1e-9:
        raise ValueError('Provide a positive count and class fractions summing to one.')
    categories=['A']*int(total*pct_a)+['B']*int(total*pct_b)
    categories+=['F']*(total-len(categories));random.Random(2026).shuffle(categories)
    return pd.DataFrame([synthetic_application(i,category,2026) for i,category in enumerate(categories)])
