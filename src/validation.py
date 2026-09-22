"""Reconcile survey estimates with an explicit, versioned official reference."""
import pandas as pd
from cmst import BASE, wmean

def official_state_check(adults):
    reference = pd.read_csv(BASE / 'data/reference/official_online_capability.csv',
                            dtype={'state_code': str})
    computed = adults.groupby('state_code').apply(
        lambda d: wmean(d, 's6_can_bank_online') * 100, include_groups=False
    ).rename('computed_pct').reset_index()
    out = reference.merge(computed, on='state_code', how='outer', validate='one_to_one')
    if out[['computed_pct', 'official_pct']].isna().any().any():
        raise ValueError('Official reference and survey state coverage differ')
    out['difference_pp'] = out.computed_pct - out.official_pct
    out['matches_published_precision'] = out.difference_pp.abs() <= 0.0500001
    # Do not bless new discrepancies just because Himachal is already known.
    unexpected = out[~out.matches_published_precision & ~out.state_code.eq('02')]
    if not unexpected.empty:
        raise ValueError('New state discrepancies: ' + ', '.join(unexpected.state_code))
    out['review_status'] = out.matches_published_precision.map({
        True: 'Matches official online-banking rate at published precision',
        False: 'Unresolved discrepancy with official online-banking rate'})
    return out
