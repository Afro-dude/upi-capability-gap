from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from build_analysis import conditional_table, build_funnel, transition_checks, FUNNEL
from build_npci_analysis import regression
from npci import allocate, load_npci
from validation import official_state_check

ROOT = Path(__file__).resolve().parents[1]

def test_conditionals_use_respondent_intersections():
    # An online-capable non-user must not enter the conditional numerator.
    d=pd.DataFrame({'weight':[2.,3.,5.], 's5_used_internet':[True,True,False],
                    's6_can_bank_online':[True,False,True]})
    result=conditional_table(d).iloc[0]
    assert result.conditional_rate == pytest.approx(2/5)
    assert result.internet_users_not_online_capable == 3
    assert result.online_capable_internet_users == 2

def test_non_nested_indicators_do_not_publish_retention():
    d=pd.DataFrame({col:[True,False] for col,_ in FUNNEL})
    d['weight']=[2.,3.]
    d['s4_can_use_internet']=[True,True]
    f=build_funnel(d)
    assert not {'retention_from_prev','lost_here_crore'} & set(f.columns)
    check=transition_checks(d)
    assert check.iloc[2].current_outside_previous_n == 1
    assert check.iloc[2].current_outside_previous_population == 3

@pytest.fixture
def state_data():
    return pd.DataFrame({'state':['A','B','C'], 'volume_mn':[100.,90.,10.],
                         'adult_pop':[100.,100.,100.], 'upi_capable_pop':[90.,40.,20.]})

def test_allocations_conserve_known_and_unknown_separately(state_data):
    for method in ['proportional','by_adults','by_capable','by_gap']:
        d=allocate(state_data,40.,method)
        assert d.allocated_mn.sum()==pytest.approx(40.)
        assert d.total_volume_mn.sum()==pytest.approx(240.)
        pd.testing.assert_series_equal(d.volume_mn,state_data.volume_mn)
    d=allocate(state_data,40.,'excluded')
    assert d.allocated_mn.sum()==0
    assert d.total_volume_mn.sum()==200

def test_invariant_allocations_do_not_prove_true_rankings(state_data):
    base=allocate(state_data,40.,'excluded').txn_per_adult
    for method in ['proportional','by_adults']:
        assert base.rank().equals(allocate(state_data,40.,method).txn_per_adult.rank())
    # A feasible alternative with the same unknown national total reverses A/B.
    actual=(state_data.volume_mn+pd.Series([0.,40.,0.]))/state_data.adult_pop
    assert base[0]>base[1] and actual[0]<actual[1]

def test_regression_excludes_unresolved_source_without_inventing_values():
    d=pd.DataFrame({'upi_capable_rate':[.2,.4,.6,.8], 'txn_per_adult':[2.,4.,6.,1000.],
                    'matches_published_precision':[True,True,True,False], 'unreliable':[False]*4})
    result,fit=regression(d)
    assert fit.slope==pytest.approx(10.)
    assert result.included_in_fit.sum()==3
    assert np.isnan(result.loc[3,'residual'])
    assert result.loc[3,'txn_per_adult']==1000

def test_incomplete_quarter_rejected(tmp_path,monkeypatch):
    import npci
    (tmp_path/'upi_statewise_2025-Jan.xlsx').touch()
    monkeypatch.setattr(npci,'NPCI_DIR',tmp_path)
    with pytest.raises(ValueError,match='exactly Jan'):load_npci()

def test_new_official_discrepancy_fails(monkeypatch):
    import validation
    reference=pd.DataFrame({'state_code':['01','02'],'official_pct':[50.,66.2]})
    monkeypatch.setattr(validation.pd,'read_csv',lambda *a,**k:reference)
    d=pd.DataFrame({'state_code':['01','02'],'weight':[1.,1.],
                    's6_can_bank_online':[True,True]})
    with pytest.raises(ValueError,match='New state discrepancies'):official_state_check(d)

def test_committed_totals_and_validation():
    p=ROOT/'data/processed'
    national=pd.read_csv(p/'national_summary.csv').iloc[0]
    segments=pd.read_csv(ROOT/'data/powerbi/fct_segment.csv')
    assert segments.adults.sum()==pytest.approx(national.adult_pop)
    assert segments.capable_adults.sum()==pytest.approx(national.upi_capable_pop)
    c=pd.read_csv(p/'conditional_national.csv').iloc[0]
    assert c.online_capable_internet_users+c.internet_users_not_online_capable==pytest.approx(c.internet_users)
    monthly=pd.read_csv(p/'npci_unclassified_share.csv')
    totals=pd.read_csv(p/'npci_national_summary.csv').iloc[0]
    assert totals.total_volume_mn==pytest.approx(monthly.total_volume_mn.sum())
    assert totals.classified_volume_mn+totals.unclassified_volume_mn==pytest.approx(totals.total_volume_mn)
    assert totals.unclassified_share_volume==pytest.approx(totals.unclassified_volume_mn/totals.total_volume_mn)
    state=pd.read_csv(p/'state_capability_vs_usage.csv')
    assert state.allocated_mn.eq(0).all()
    assert state.volume_mn.sum()==pytest.approx(totals.classified_volume_mn)
    assert not state.loc[state.state.eq('Himachal Pradesh'),'included_in_fit'].any()
    validation=pd.read_csv(p/'official_state_validation.csv',dtype={'state_code':str})
    assert validation.loc[~validation.matches_published_precision,'state_code'].tolist()==['02']

@pytest.mark.skipif(not (ROOT/'data/raw/CMST80PER.dta').exists(),reason='Licensed raw inputs are not committed')
def test_raw_reproduction():
    from cmst import load_person
    p=load_person();a=p[p.age>=15]
    result=official_state_check(a)
    assert len(result)==36 and result.matches_published_precision.sum()==35
    saved=pd.read_csv(ROOT/'data/processed/conditional_national.csv')
    pd.testing.assert_frame_equal(conditional_table(a),saved,check_dtype=False)
