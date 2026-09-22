"""Render corrected figures from the same committed tables used by the app."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from cmst import PROCESSED, OUTPUTS

BLUE,ORANGE='#2c6e91','#c1440e'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,
                     'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':140})

def save(fig,name,note):
    fig.text(.02,.015,note,ha='left',va='bottom',fontsize=8,color='#555555')
    fig.tight_layout(rect=(0,.075,1,1))
    fig.savefig(OUTPUTS/name,bbox_inches='tight')
    plt.close(fig)

def main():
    OUTPUTS.mkdir(exist_ok=True)
    f=pd.read_csv(PROCESSED/'funnel_national.csv')
    fig,ax=plt.subplots(figsize=(10,5.2))
    ax.barh(f.stage,f.pct_of_adults,color=BLUE)
    ax.invert_yaxis();ax.set_xlim(0,1)
    ax.xaxis.set_major_formatter(lambda x,_:f'{x:.0%}')
    ax.set_title('Digital access, use and capability | India, Jan–Mar 2025',loc='left')
    ax.set_xlabel('Share of persons aged 15+')
    save(fig,'fig1_funnel.png','Separate prevalence indicators, not a sequential funnel. Weighted point estimates; confidence intervals unavailable.')

    b=pd.read_csv(PROCESSED/'barriers_household.csv')
    mapping={"Don't know how to use it":'Digital literacy',"Don't know what internet is":'Digital literacy',
             'Equipment cost too high':'Cost','Service cost too high':'Cost',
             'Not available in area':'Availability / supply','No electricity':'Availability / supply',
             'Do not need it':'No perceived need',"Available but doesn't meet needs":'No perceived need',
             'Have internet access elsewhere':'No perceived need','Lack of local content':'No perceived need'}
    b['group']=b.reason_no_internet_hh.map(mapping).fillna('Other')
    shares=b.groupby('group').households.sum();shares=(shares/shares.sum()).sort_values()
    fig,ax=plt.subplots(figsize=(8.5,4.4))
    ax.barh(shares.index,shares,color=BLUE);ax.xaxis.set_major_formatter(lambda x,_:f'{x:.0%}')
    ax.set_title('Reported main reasons for no internet at home',loc='left')
    ax.set_xlabel('Share of households without home internet')
    save(fig,'fig2_barriers.png','Household internet barriers do not establish causes of UPI exclusion or intervention effectiveness.')

    c=pd.read_csv(PROCESSED/'conditional_sector_gender.csv')
    fig,ax=plt.subplots(figsize=(8,4.7));x=np.arange(2)
    for offset,sex,color in [(-.18,'Female',ORANGE),(.18,'Male',BLUE)]:
        d=c[c.gender_name.eq(sex)].set_index('sector_name').loc[['Rural','Urban']]
        ax.bar(x+offset,d.conditional_rate,.36,label=sex,color=color)
    ax.set_xticks(x,['Rural','Urban']);ax.set_ylim(0,1);ax.legend(frameon=False)
    ax.yaxis.set_major_formatter(lambda x,_:f'{x:.0%}')
    ax.set_title('Online-banking capability among recent internet users',loc='left')
    save(fig,'fig3_conversion.png','Computed from respondent intersections. Point estimates, not causal effects; confidence intervals unavailable.')

    s=pd.read_csv(PROCESSED/'state_level.csv').sort_values('state',ascending=False)
    fig,ax=plt.subplots(figsize=(9,11));y=np.arange(len(s))
    ax.hlines(y,s.female_rate,s.male_rate,color='#cccccc',lw=2)
    ax.scatter(s.female_rate,y,label='Female',color=ORANGE,s=25)
    ax.scatter(s.male_rate,y,label='Male',color=BLUE,s=25)
    labels=s.state.where(s.matches_published_precision,s.state+' *')
    ax.set_yticks(y,labels);ax.set_xlim(0,1);ax.legend(frameon=False)
    ax.xaxis.set_major_formatter(lambda x,_:f'{x:.0%}')
    ax.set_xlabel('Share of persons aged 15+ reporting UPI capability')
    ax.set_title('State/UT capability by sex | Alphabetical order',loc='left')
    save(fig,'fig4_states.png','No confidence intervals: differences are not significance tests.\n* Himachal Pradesh: unresolved discrepancy with official online-banking rate; estimates provisional.')

    d=pd.read_csv(PROCESSED/'state_capability_vs_usage.csv')
    d=d[d.included_in_fit].sort_values('upi_capable_rate')
    fit=pd.read_csv(PROCESSED/'descriptive_fit.csv').iloc[0]
    fig,ax=plt.subplots(figsize=(9,6))
    ax.scatter(d.upi_capable_rate,d.txn_per_adult,color=BLUE,s=36)
    ax.plot(d.upi_capable_rate,d.fitted_classified_txn_per_adult,color=ORANGE,ls='--')
    ax.xaxis.set_major_formatter(lambda x,_:f'{x:.0%}')
    ax.set_xlabel('Survey UPI-capability rate, age 15+')
    ax.set_ylabel('Classified transactions / resident aged 15+, Q1 2025')
    ax.set_title(f'Exploratory association | {len(d)} states/UTs | Descriptive R² = {fit.r_squared:.3f}',loc='left')
    save(fig,'fig5_capability_vs_usage.png','38.1% of national volume unclassified; state coverage unknown. Himachal Pradesh omitted pending review.\nTransaction geography may differ from residence. The fit does not identify causes or intervention needs.')
    print('Five corrected figures generated.')

if __name__=='__main__':main()
