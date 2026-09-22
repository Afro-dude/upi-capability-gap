"""Survey capability explorer with explicitly exploratory NPCI comparisons.

Run: streamlit run app.py. Reads committed aggregates; no raw microdata required.
"""
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).resolve().parent / 'data' / 'processed'
BLUE, ORANGE = '#2c6e91', '#c1440e'
st.set_page_config(page_title='India’s UPI capability gap', page_icon='◐', layout='wide')

@st.cache_data
def load(name):
    return pd.read_csv(DATA / name)

def chart(fig, height=400):
    fig.update_layout(height=height, margin=dict(l=10,r=20,t=25,b=10),
                      legend=dict(orientation='h'), paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, width='stretch')

def table(df, key):
    st.dataframe(df, hide_index=True, width='stretch')
    st.download_button('Download this table', df.to_csv(index=False),
                       file_name=f'{key}.csv', mime='text/csv', key=key)

national = load('national_summary.csv').iloc[0]
conditional = load('conditional_national.csv').iloc[0]
states = load('state_level.csv')
validation = load('official_state_validation.csv')
npci = load('npci_national_summary.csv').iloc[0]

st.title('India’s UPI capability gap')
st.write('Explore who reports being able to use UPI, using the NSS Comprehensive Modular '
         'Survey: Telecom, January–March 2025. NPCI transaction data is shown separately '
         'because capability and recorded transactions measure different things.')
st.caption('Survey population: persons aged 15+. Weighted point estimates; confidence '
           'intervals are unavailable. This is a historical snapshot, not live monitoring.')
overview, explore, transactions, scenario, methods = st.tabs([
    'Survey findings', 'Explore capability', 'NPCI: exploratory', 'What-if calculator', 'Methods & checks'])

with overview:
    a,b,c = st.columns(3)
    a.metric('UPI-capable, age 15+', f'{national.upi_capable_rate:.1%}')
    b.metric('Estimated not UPI-capable', f'{national.gap_pop/1e7:.1f} crore')
    c.metric('Recent internet users unable to transact online',
             f'{conditional.internet_users_not_online_capable/1e7:.1f} crore')
    st.subheader('Access, use and capability')
    indicators = load('funnel_national.csv')
    fig=go.Figure(go.Bar(y=indicators.stage, x=indicators.pct_of_adults,
                         orientation='h', marker_color=BLUE,
                         text=indicators.pct_of_adults.map(lambda x:f'{x:.1%}'),
                         textposition='outside'))
    fig.update_yaxes(autorange='reversed')
    fig.update_xaxes(tickformat='.0%', range=[0,1.08], title='Share of persons aged 15+')
    chart(fig)
    st.caption('These are separate indicators, not a sequential funnel. A computer user '
               'may use the internet without a smartphone; capability does not require recent use.')
    st.subheader('Online-banking capability among recent internet users')
    groups=load('conditional_sector_gender.csv')
    fig=go.Figure()
    for sex,color in [('Female',ORANGE),('Male',BLUE)]:
        g=groups[groups.gender_name.eq(sex)]
        fig.add_bar(x=g.sector_name,y=g.conditional_rate,name=sex,marker_color=color,
                    text=g.conditional_rate.map(lambda x:f'{x:.1%}'),textposition='outside')
    fig.update_yaxes(tickformat='.0%',range=[0,1])
    chart(fig,330)
    st.caption('Numerator: respondents who both used the internet and can transact online. '
               'Denominator: recent internet users in the same group. Observed differences '
               'do not identify their causes. Small third-category cells are omitted from this chart.')
    st.subheader('Reported reasons for no internet at home')
    barriers=load('barriers_household.csv').groupby('reason_no_internet_hh').households.sum().sort_values()
    fig=go.Figure(go.Bar(y=barriers.index,x=barriers/barriers.sum(),orientation='h',marker_color=BLUE))
    fig.update_xaxes(tickformat='.0%')
    chart(fig,440)
    st.caption('Households without home internet, by their stated main reason. These are not '
               'UPI-specific barriers and do not measure the return on an intervention.')

with explore:
    view=st.radio('Population view',['National segments','State / UT'],horizontal=True)
    st.info('Sample counts describe coverage. The minimum display size of 30 is not a '
            'precision guarantee. Do not interpret close point estimates as significant differences.')
    if view=='National segments':
        segments=load('national_segments.csv')
        sector=st.multiselect('Sector',sorted(segments.sector_name.unique()),default=['Rural','Urban'])
        gender=st.multiselect('Sex',sorted(segments.gender_name.unique()),default=['Female','Male'])
        sub=segments[segments.sector_name.isin(sector)&segments.gender_name.isin(gender)&~segments.unreliable].copy()
        if sub.empty:
            st.info('No groups meet these selections and the display threshold.')
        else:
            fig=go.Figure()
            for (sec,sex),g in sub.groupby(['sector_name','gender_name']):
                fig.add_scatter(x=g.age_band,y=g.rate,mode='lines+markers',name=f'{sec} · {sex}')
            fig.update_yaxes(tickformat='.0%',range=[0,1])
            fig.update_xaxes(categoryorder='array',categoryarray=['15-24','25-34','35-44','45-59','60+'])
            chart(fig)
            table(sub[['sector_name','age_band','gender_name','rate','pop_weighted',
                       'gap_pop','n_unweighted','uncertainty_status']], 'national_segments')
    else:
        pick=st.selectbox('State or union territory',sorted(states.state))
        row=states[states.state.eq(pick)].iloc[0]
        if not row.matches_published_precision:
            st.warning('Source discrepancy: the supplied microdata gives 64.4% online-banking '
                       'capability for Himachal Pradesh; official Table 12 gives 66.2%. '
                       'UPI-specific estimates below remain provisional. No values have been overwritten.')
        a,b,c=st.columns(3)
        a.metric('UPI-capable',f'{row.upi_capable_rate:.1%}')
        b.metric('Survey respondents aged 15+',f'{row.n_unweighted:,.0f}')
        c.metric('Sampled first-stage units',f'{row.n_fsu:,.0f}')
        fig=go.Figure(go.Bar(x=['Female','Male'],y=[row.female_rate,row.male_rate],marker_color=[ORANGE,BLUE]))
        fig.update_yaxes(tickformat='.0%',range=[0,1],title='UPI capability')
        chart(fig,300)
        table(states[['state','upi_capable_rate','female_rate','male_rate','n_unweighted',
                      'n_fsu','review_status','uncertainty_status']], 'state_capability')
        st.caption('Alphabetical order. Online-banking reconciliation is a validation check, '
                   'not proof that every derived statistic or population total is correct.')

with transactions:
    st.warning(f'{npci.unclassified_share_volume:.1%} of Q1 2025 transaction volume has no state '
               'classification. State-specific coverage is unknown, so complete-volume rankings '
               'and behavioural diagnoses cannot be inferred from this view.')
    a,b,c=st.columns(3)
    a.metric('National volume, including unclassified',f'{npci.total_volume_mn/1000:.2f} billion')
    b.metric('Classified volume',f'{npci.classified_volume_mn/1000:.2f} billion')
    c.metric('Unclassified volume',f'{npci.unclassified_volume_mn/1000:.2f} billion')
    d=load('state_capability_vs_usage.csv')
    fit=load('descriptive_fit.csv').iloc[0]
    eligible=d[d.included_in_fit].sort_values('upi_capable_rate')
    fig=go.Figure(go.Scatter(x=eligible.upi_capable_rate,y=eligible.txn_per_adult,
                             text=eligible.state,mode='markers',name='Classified data',
                             marker=dict(color=BLUE,size=9),
                             hovertemplate='%{text}<br>UPI-capable: %{x:.1%}<br>Classified transactions per resident aged 15+: %{y:.1f}<extra></extra>'))
    fig.add_scatter(x=eligible.upi_capable_rate,y=eligible.fitted_classified_txn_per_adult,
                    mode='lines',name='Descriptive fit',line=dict(dash='dash',color=ORANGE))
    fig.update_xaxes(tickformat='.0%',title='Survey UPI-capability rate')
    fig.update_yaxes(title='Classified transactions / resident aged 15+, Q1 2025')
    chart(fig,460)
    st.caption(f'Descriptive R² = {fit.r_squared:.3f}; {fit.states_in_fit:.0f} states/UTs. '
               'Himachal Pradesh is excluded from the fit pending source reconciliation. '
               'Transaction location need not equal payer residence. Residuals do not identify '
               'merchant acceptance, user behaviour, or an intervention effect.')
    table(d[['state','volume_mn','txn_per_adult','included_in_fit','transaction_scope','review_status']],
          'classified_state_transactions')
    st.subheader('What allocation assumptions do')
    st.write('Proportional and population-based allocations preserve per-adult rankings by '
             'construction. That does not validate the real missing-data pattern. Allocations '
             'using capability or the capability gap also build the tested relationship into the data.')
    table(load('npci_allocation_sensitivity.csv'), 'allocation_assumptions')
    st.caption('The assumption demonstration retains all 36 states to reproduce the earlier '
               'comparison; it is distinct from the 35-state descriptive fit above.')

with scenario:
    st.subheader('A population-based what-if')
    st.write('Specify an assumed share of the estimated excluded population becoming UPI-capable. '
             'The result is arithmetic, not a predicted response to a programme. No ML is used.')
    scope=st.selectbox('Scenario population',['All persons aged 15+','National demographic segment'])
    gap=float(national.gap_pop)
    if scope=='National demographic segment':
        segments=load('national_segments.csv')
        segments=segments[~segments.unreliable].copy()
        segments['label']=segments.sector_name+' · '+segments.gender_name+' · '+segments.age_band
        label=st.selectbox('Select segment',sorted(segments.label))
        gap=float(segments.loc[segments.label.eq(label),'gap_pop'].iloc[0])
    assumed=st.slider('Assumed share becoming capable (%)',0,100,10)
    a,b=st.columns(2)
    a.metric('Baseline excluded population estimate',f'{gap:,.0f}')
    b.metric('Hypothetical newly capable population',f'{gap*assumed/100:,.0f}')
    st.caption('Calculation: baseline excluded population × assumed share. Baseline sampling '
               'uncertainty remains unresolved. This calculator estimates neither additional '
               'transactions nor a programme’s cost, effectiveness or causal impact.')

with methods:
    st.subheader('Survey source checks')
    st.write('State codes are the first two characters of NSS-Region. Weights are MLT/100, '
             'as specified in the official README. Q12 codes 1 and 3 indicate UPI capability. '
             'Eligible adults with missing or invalid Q12 responses stop the build; structural '
             'skips outside the internet-capability routing are counted as not capable.')
    table(validation,'official_state_validation')
    st.subheader('Sampling uncertainty remains unresolved')
    st.write('The official two-stage variance formula requires frame FSU counts, listed '
             'household counts and subdivision factors not supplied in the person/household '
             'files. Confidence intervals and significance rankings are withheld. The previous '
             'claim that the available identifiers alone suffice has been corrected.')
    st.subheader('Indicator overlap checks')
    table(load('indicator_overlap_checks.csv'),'indicator_overlap_checks')
    st.write('Conditional rates use actual respondent intersections. Successive prevalence '
             'totals are not treated as retention probabilities.')
    st.subheader('Scope and provenance')
    st.write('The survey covers January–March 2025 and excludes some inaccessible Andaman '
             'and Nicobar villages. Household internet barriers do not establish UPI barriers. '
             'The state join is ecological: it does not attach transactions to survey respondents.')
    st.markdown('[Official survey materials](https://microdata.gov.in/NADA/index.php/catalog/239/related-materials) '
                ' · [Methodology and source audit](https://github.com/Afro-dude/upi-capability-gap/blob/main/DATA_NOTES.md)')
