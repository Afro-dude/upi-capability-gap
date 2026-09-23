"""Exploratory classified transaction comparisons; no causal diagnosis or forecast."""
import numpy as np
import pandas as pd
from scipy import stats
from cmst import load_person, rate_table, PROCESSED
from validation import official_state_check
from npci import load_npci, unclassified_share, quarter_totals, allocate

METHODS = ['excluded', 'proportional', 'by_adults', 'by_capable', 'by_gap']

def capability_by_state():
    p = load_person()
    a = p[p.age >= 15]
    cap = rate_table(a, ['state', 'state_code'], 's7_upi_capable').rename(columns={
        'rate':'upi_capable_rate', 'pop_weighted':'adult_pop', 'count_weighted':'upi_capable_pop'})
    check = official_state_check(a)
    return cap.merge(check[['state_code', 'matches_published_precision', 'review_status']],
                     on='state_code', validate='one_to_one')

def sensitivity(merged, unclassified_volume):
    """Assumption demonstrations on all states, not evidence of unbiased coverage."""
    base = allocate(merged, unclassified_volume, 'excluded').set_index('state').txn_per_adult
    rows=[]
    for method in METHODS:
        d = allocate(merged, unclassified_volume, method)
        order = d.set_index('state').txn_per_adult.reindex(base.index)
        rows.append({'method': method,
                     'pearson_r_vs_capability': d.upi_capable_rate.corr(d.txn_per_adult),
                     'spearman_vs_capability': stats.spearmanr(d.upi_capable_rate, d.txn_per_adult).statistic,
                     'rank_corr_vs_excluded': stats.spearmanr(order, base).statistic,
                     'top_state': d.loc[d.txn_per_adult.idxmax(), 'state'],
                     'interpretation': 'Hypothetical allocation; not an estimate of missing state data',
                     'invariant_by_construction': method in ['excluded','proportional','by_adults'],
                     'uses_capability_in_allocation': method in ['by_capable','by_gap'],
                     'state_count': len(d)})
    return pd.DataFrame(rows)

def regression(d):
    """Descriptive OLS; omit unresolved source discrepancies from the fit."""
    out=d.copy()
    out['included_in_fit'] = out.matches_published_precision & ~out.unreliable
    eligible=out[out.included_in_fit]
    if len(eligible)<3 or eligible.upi_capable_rate.nunique()<2:
        raise ValueError('Insufficient validated variation for a descriptive fit')
    fit=stats.linregress(eligible.upi_capable_rate, eligible.txn_per_adult)
    out['fitted_classified_txn_per_adult']=np.nan
    out.loc[out.included_in_fit,'fitted_classified_txn_per_adult'] = fit.intercept + fit.slope*eligible.upi_capable_rate
    out['residual']=out.txn_per_adult-out.fitted_classified_txn_per_adult
    out['comparison_label']='Excluded from fit: source discrepancy or small sample'
    out.loc[out.included_in_fit & out.residual.ge(0),'comparison_label']='Above descriptive fitted line'
    out.loc[out.included_in_fit & out.residual.lt(0),'comparison_label']='Below descriptive fitted line'
    return out,fit

def main():
    PROCESSED.mkdir(parents=True,exist_ok=True)
    cap=capability_by_state()
    npci=load_npci()
    unc=unclassified_share(npci)
    unc.to_csv(PROCESSED/'npci_unclassified_share.csv',index=False)
    qt,unc_vol,_=quarter_totals(npci)
    merged=qt.merge(cap,on='state',how='outer',validate='one_to_one',indicator=True)
    if not merged._merge.eq('both').all():
        raise ValueError('Survey/NPCI join would lose states')
    merged=merged.drop(columns='_merge')
    sensitivity(merged,unc_vol).to_csv(PROCESSED/'npci_allocation_sensitivity.csv',index=False)
    d,fit=regression(allocate(merged,unc_vol,'excluded'))
    d['transaction_scope']='Classified only; unknown state coverage'
    d.to_csv(PROCESSED/'state_capability_vs_usage.csv',index=False)
    total=qt.volume_mn.sum()+unc_vol
    summary={'period':'Jan-Mar 2025','total_volume_mn':total,
             'classified_volume_mn':qt.volume_mn.sum(),'unclassified_volume_mn':unc_vol,
             'unclassified_share_volume':unc_vol/total,
             'national_volume_per_survey_capable_person':total*1e6/cap.upi_capable_pop.sum(),
             'classified_volume_per_survey_capable_person':qt.volume_mn.sum()*1e6/cap.upi_capable_pop.sum(),
             'benchmark_interpretation':'Aggregate ratios, not observed user frequency or new-user forecasts'}
    pd.DataFrame([summary]).to_csv(PROCESSED/'npci_national_summary.csv',index=False)
    pd.DataFrame([{'fit_scope':'Source-validated states; classified transactions only',
                   'states_in_fit':int(d.included_in_fit.sum()),'pearson_r':fit.rvalue,
                   'r_squared':fit.rvalue**2,'slope':fit.slope,'intercept':fit.intercept,
                   'interpretation':'Descriptive association; no causal or intervention interpretation'}]
                ).to_csv(PROCESSED/'descriptive_fit.csv',index=False)
    print(f'Joined {len(d)} states; {unc_vol/total:.2%} of national volume unclassified.')
    print(f'Descriptive fit on {d.included_in_fit.sum()} states: R2={fit.rvalue**2:.3f}.')
    print('Allocation invariance is not evidence that real state rankings are robust.')

if __name__=='__main__':
    main()
