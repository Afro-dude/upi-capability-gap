"""Build a portable PBIP/PBIR report from audited aggregates, without raw records.

Refresh loads the embedded, versioned aggregate snapshot. Re-run this builder
after updating the CSV exports; Desktop is required to validate and save PBIX.
"""
import base64
import csv
import hashlib
import json
from pathlib import Path
import uuid
import zlib

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'powerbi'
REPORT = OUT / 'UPI.Report'
MODEL = OUT / 'UPI.SemanticModel'
SCHEMA = 'https://developer.microsoft.com/json-schemas/fabric/'
BLUE, INK, MUTED, PAPER = '#21677A', '#173342', '#566875', '#F4F7F9'

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def sid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'upi-capability-gap/'+name))

TEXT = {'state','state_code','sector','sex','age_band','age_group_broad','region',
        'reason','barrier_group','variable','stage','month','period','review_status',
        'uncertainty_status','transaction_scope','comparison_label','allocation_rule',
        'highest_usage_state','interpretation','source_url','source_table','benchmark_interpretation'}
BOOL = {'unreliable','included_in_fit','matches_published_precision',
        'invariant_by_construction','uses_capability_in_allocation'}
INTEGER = {'age_sort','sex_sort','sector_sort','stage_sort','sample_n','n_fsu',
           'n_internet_users','state_count','assumed_percent','month_sort'}

def make_table(name, headers, rows):
    types={c:'string' if c in TEXT else 'boolean' if c in BOOL else
           'int64' if c in INTEGER else 'double' for c in headers}
    converted=[]
    for row in rows:
        vals=[]
        for c,v in zip(headers,row):
            t=types[c]
            if c=='state_code':v=str(v).zfill(2)
            vals.append(None if v=='' else str(v) if t=='string' else
                        str(v).lower()=='true' if t=='boolean' else
                        int(float(v)) if t=='int64' else float(v))
        converted.append(vals)
    packed=base64.b64encode(zlib.compress(json.dumps(converted,ensure_ascii=False).encode())[2:-4]).decode()
    # Enter Data-style M partition; the snapshot has no credentials or machine paths.
    mtypes={'string':'type text','boolean':'type logical','int64':'Int64.Type','double':'type number'}
    m=['let',f'    Rows = Json.Document(Binary.Decompress(Binary.FromText("{packed}", BinaryEncoding.Base64), Compression.Deflate)),',
       '    Data = Table.FromRows(Rows, '+json.dumps(headers).replace('[','{').replace(']','}')+'),',
       '    Typed = Table.TransformColumnTypes(Data, {'+', '.join('{"'+c+'", '+mtypes[types[c]]+'}' for c in headers)+'}, "en-US")',
       'in','    Typed']
    cols=[]
    sorts={'age_band':'age_sort','sector':'sector_sort','sex':'sex_sort','stage':'stage_sort','month':'month_sort'}
    for c in headers:
        col={'name':c,'dataType':types[c],'sourceColumn':c,'summarizeBy':'none','lineageTag':sid(name+'/'+c)}
        if sorts.get(c) in headers: col['sortByColumn']=sorts[c]
        if c.endswith('_rate') or c in {'share_of_adults','conditional_rate','unclassified_share_volume','unclassified_share_value'}:
            col['formatString']='0.0%'
        if types[c]=='int64': col['formatString']='#,0'
        cols.append(col)
    return {'name':name,'lineageTag':sid(name),'columns':cols,
            'partitions':[{'name':name,'mode':'import','source':{'type':'m','expression':m}}]}

MEASURES = {
 'Adults': ('SUM(fct_segment[adults])','#,0'),
 'Capable Adults': ('SUM(fct_segment[capable_adults])','#,0'),
 'Excluded Adults': ('[Adults] - [Capable Adults]','#,0'),
 'Capability Rate': ('DIVIDE([Capable Adults], [Adults])','0.0%'),
 'Sample Size': ('SUM(fct_segment[sample_n])','#,0'),
 'Displayed Capability Rate': ('IF([Sample Size] >= 30, [Capability Rate], BLANK())','0.0%'),
 'Adults (crore)': ('DIVIDE([Adults], 10000000)','0.0'),
 'Excluded (crore)': ('DIVIDE([Excluded Adults], 10000000)','0.0'),
 'Internet users unable to bank online (crore)': ('DIVIDE(SUM(fct_conditional_national[internet_users_not_online_capable]),10000000)','0.0'),
 'Indicator Share': ('SELECTEDVALUE(fct_funnel[share_of_adults])','0.0%'),
 'Households without internet': ('SUM(fct_barriers[households])','#,0'),
 'Barrier Share': ('DIVIDE([Households without internet], CALCULATE([Households without internet], REMOVEFILTERS(fct_barriers[reason]), REMOVEFILTERS(fct_barriers[barrier_group])))','0.0%'),
 'National Transactions (bn)': ('SUM(fct_npci_national[total_volume_mn])/1000','0.00'),
 'Classified Transactions (bn)': ('SUM(fct_npci_national[classified_volume_mn])/1000','0.00'),
 'Unclassified Transactions (bn)': ('SUM(fct_npci_national[unclassified_volume_mn])/1000','0.00'),
 'Unclassified Share': ('DIVIDE(SUM(fct_npci_national[unclassified_volume_mn]),SUM(fct_npci_national[total_volume_mn]))','0.0%'),
 'State Capability Rate': ('DIVIDE(SUM(fct_state[capable_adults]),SUM(fct_state[adults]))','0.0%'),
 'Classified Transactions per Resident 15+': ('DIVIDE(SUM(fct_state[txn_volume_mn])*1000000,SUM(fct_state[adults]))','0.0'),
 'State Review': ('IF(HASONEVALUE(dim_state[state]), SELECTEDVALUE(fct_state[review_status]), "Select a state to see its source check")',None),
 'Source Check': ('IF(HASONEVALUE(dim_state[state]), SELECTEDVALUE(fct_state[review_status]), "See Methods for source checks")',None),
 'Assumed Share': ('DIVIDE(SELECTEDVALUE(scenario[assumed_percent],10),100)','0%'),
 'Scenario Baseline': ('IF([Sample Size] >= 30, [Excluded Adults], BLANK())','#,0'),
 'Newly Capable (what-if)': ('[Scenario Baseline] * [Assumed Share]','#,0'),
 'Newly Capable (crore)': ('DIVIDE([Newly Capable (what-if)],10000000)','0.00'),
 'Monthly Unclassified Share': ('DIVIDE(SUM(fct_unclassified[unclassified_volume_mn]),SUM(fct_unclassified[total_volume_mn]))','0.0%'),
}

def model():
    tables=[]; manifest=[]
    for p in sorted((ROOT/'data/powerbi').glob('*.csv')):
        with p.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.reader(f); headers=next(reader); rows=list(reader)
        if p.stem=='fct_source_validation':
            states={r['state_code']:r['state'] for r in csv.DictReader((ROOT/'data/powerbi/dim_state.csv').open(encoding='utf-8-sig'))}
            ix=headers.index('state_code');headers.append('state')
            for row in rows:row.append(states[row[ix].zfill(2)])
        if p.stem=='fct_unclassified':
            headers.append('month_sort')
            for row in rows:row.append({'Jan':1,'Feb':2,'Mar':3}[row[0]])
        tables.append(make_table(p.stem,headers,rows))
        manifest.append({'file':str(p.relative_to(ROOT)).replace('\\','/'),'rows':len(rows),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    tables.append(make_table('scenario',['assumed_percent'],[[n] for n in range(101)]))
    measures=make_table('_Measures',['placeholder'],[[0]])
    measures['columns'][0]['isHidden']=True
    measures['measures']=[dict(name=n,expression=e,lineageTag=sid('measure/'+n),**({'formatString':fmt} if fmt else {})) for n,(e,fmt) in MEASURES.items()]
    tables.append(measures)
    global MEASURE_TABLE
    MEASURE_TABLE='_Measures'
    rel=[]
    for fact,dim,col in [('fct_segment','dim_state','state'),('fct_state','dim_state','state'),
                         ('fct_segment','dim_sector','sector'),('fct_barriers','dim_sector','sector'),
                         ('fct_segment','dim_age_band','age_band'),('fct_segment','dim_sex','sex')]:
        rel.append({'name':sid(fact+'/'+dim),'fromTable':fact,'fromColumn':col,'toTable':dim,
                    'toColumn':col,'fromCardinality':'many','toCardinality':'one','crossFilteringBehavior':'oneDirection','isActive':True})
    write(MODEL/'model.bim',{'name':'UPI Capability Gap','compatibilityLevel':1567,'model':{
        'culture':'en-US','defaultPowerBIDataSourceVersion':'powerBI_V3','sourceQueryCulture':'en-US',
        'tables':tables,'relationships':rel,'annotations':[{'name':'PBI_QueryOrder','value':json.dumps([t['name'] for t in tables])}],
        'dataAccessOptions':{'legacyRedirects':True,'returnErrorValuesAsNull':True}}})
    write(MODEL/'definition.pbism',{'$schema':SCHEMA+'item/semanticModel/definitionProperties/1.0.0/schema.json','version':'1.0','settings':{}})
    write(OUT/'aggregate_manifest.json',{'period':'Jan-Mar 2025','source':'Audited aggregate CSV exports','tables':manifest,
       'refresh':'Embedded aggregate snapshot. Regenerate with src/build_powerbi_project.py after rebuilding the CSV exports.'})

def literal(value):
    val=('true' if value else 'false') if isinstance(value,bool) else str(value)+'D' if isinstance(value,(int,float)) else "'"+value.replace("'","''")+"'"
    return {'expr':{'Literal':{'Value':val}}}

def color(value):return {'solid':{'color':literal(value)}}
def obj(**props):return [{'properties':props}]
def field(table,col,measure=False):
    return {('Measure' if measure else 'Column'):{'Expression':{'SourceRef':{'Entity':table}},'Property':col}}
def column(table,col,label=None):return {'field':field(table,col),'queryRef':table+'.'+col,'nativeQueryRef':col,**({'displayName':label} if label else {})}
def measure(name,label=None):return {'field':field(MEASURE_TABLE,name,True),'queryRef':MEASURE_TABLE+'.'+name,'nativeQueryRef':name,**({'displayName':label} if label else {})}

PAGES=[]; COUNT=0
def page(name,label,subtitle):
    PAGES.append(name)
    write(REPORT/'definition/pages'/name/'page.json',{'$schema':SCHEMA+'item/report/definition/page/2.0.0/schema.json',
       'name':name,'displayName':label,'displayOption':'FitToPage','width':1440,'height':900,
       'objects':{'background':obj(color=color(PAPER),transparency=literal(0))}})
    text(name,'heading',label,32,20,1376,47,28,INK,bold=True)
    text(name,'subtitle',subtitle,32,72,1376,42,12,MUTED)
    text(name,'footer','CMS-T & NPCI  •  Jan–Mar 2025  |  Weighted point estimates; sampling uncertainty is not quantified.',32,865,1376,25,10,MUTED)

def visual(page,name,kind,x,y,w,h,roles=None,title=None,objects=None,sort=None):
    global COUNT
    COUNT+=1
    v={'visualType':kind,'drillFilterOtherVisuals':True}
    if roles:
        v['query']={'queryState':{role:{'projections':projections} for role,projections in roles.items()}}
        if sort:v['query']['sortDefinition']={'sort':[{'field':sort['field'],'direction':'Ascending'}],'isDefaultSort':False}
    v['visualContainerObjects']={'background':obj(color=color('#FFFFFF'),transparency=literal(0)),
           'border':obj(show=literal(False)), 'visualHeader':obj(show=literal(False))}
    if title:v['visualContainerObjects']['title']=obj(show=literal(True),text=literal(title),fontColor=color(INK),fontSize=literal(12),alignment=literal('left'),titleWrap=literal(True))
    if objects:v['objects']=objects
    write(REPORT/'definition/pages'/page/'visuals'/name/'visual.json',{'$schema':SCHEMA+'item/report/definition/visualContainer/2.4.0/schema.json',
       'name':name,'position':{'x':x,'y':y,'width':w,'height':h,'z':COUNT*1000,'tabOrder':COUNT*1000},'visual':v})

def text(p,n,txt,x,y,w,h,size=12,c=MUTED,bold=False):
    paras=[{'textRuns':[{'value':line,'textStyle':{'fontFamily':'Segoe UI','fontSize':f'{size}pt','color':c,'fontWeight':'bold' if bold else 'normal'}}]} for line in txt.split('\n')]
    visual(p,n,'textbox',x,y,w,h,objects={'general':obj(paragraphs=paras)})

def card(p,n,m,title,x,y,w=326):
    visual(p,n,'card',x,y,w,112,{'Values':[measure(m)]},title,
           {'labels':obj(color=color(BLUE),fontSize=literal(30),labelDisplayUnits=literal(1)),
            'categoryLabels':obj(show=literal(False))})

def slicer(p,n,t,c,title,x,y,w=260):
    visual(p,n,'slicer',x,y,w,74,{'Values':[column(t,c)]},title,
       {'data':obj(mode=literal('Dropdown')),'header':obj(show=literal(False)),
        'selection':obj(singleSelect=literal(t=='scenario'),selectAllCheckboxEnabled=literal(t!='scenario'))})

def table(p,n,cols,title,x,y,w,h,sort=None):
    visual(p,n,'tableEx',x,y,w,h,{'Values':cols},title,
       {'grid':obj(rowPadding=literal(5),gridVertical=literal(False)),
        'columnHeaders':obj(fontSize=literal(10),fontColor=color(INK),backColor=color('#E6EFF2'),wordWrap=literal(True)),
        'values':obj(fontSize=literal(10),wordWrap=literal(True)),
        'total':obj(totals=literal(False))},sort)

def build_report():
    write(OUT/'UPI Capability Gap.pbip',{'$schema':SCHEMA+'pbip/pbipProperties/1.0.0/schema.json','version':'1.0',
       'artifacts':[{'report':{'path':'UPI.Report'}}],'settings':{'enableAutoRecovery':True}})
    write(REPORT/'definition.pbir',{'$schema':SCHEMA+'item/report/definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../UPI.SemanticModel'}}})
    write(REPORT/'definition/version.json',{'$schema':SCHEMA+'item/report/definition/versionMetadata/1.0.0/schema.json','version':'2.0.0'})
    write(REPORT/'definition/report.json',{'$schema':SCHEMA+'item/report/definition/report/3.0.0/schema.json','themeCollection':{},
           'settings':{'useStylableVisualContainerHeader':True,'exportDataMode':'AllowSummarized'}})
    p='01_survey';page(p,'Survey findings','India’s digital payments capability gap  /  Persons aged 15+  /  National overview')
    card(p,'capability','Capability Rate','Report being UPI-capable',32,127)
    card(p,'excluded','Excluded (crore)','Not UPI-capable · crore people',382,127)
    card(p,'online','Internet users unable to bank online (crore)','Internet users unable to bank online · crore',732,127)
    card(p,'adults','Adults (crore)','Survey population · crore people',1082,127)
    visual(p,'indicators','clusteredBarChart',32,261,690,500,{'Category':[column('fct_funnel','stage')],'Y':[measure('Indicator Share')]},'Access, use and capability',
           {'dataPoint':obj(defaultColor=color(BLUE)),'labels':obj(show=literal(True))},column('fct_funnel','stage'))
    visual(p,'barriers','clusteredBarChart',744,261,664,500,{'Category':[column('fct_barriers','reason')],'Y':[measure('Barrier Share')]},'Main reasons for no internet at home',
           {'dataPoint':obj(defaultColor=color('#A25B36'))},column('fct_barriers','reason'))
    text(p,'caveat','Separate prevalence indicators, not steps in a sequential funnel.\nHousehold internet barriers do not establish UPI-specific causes or intervention effects.',32,780,1376,64)
    p='02_explorer';page(p,'Capability explorer','Compare survey point estimates. Select filters below; small displayed groups are suppressed at n < 30.')
    for i,(t,c,label) in enumerate([('dim_state','state','State / UT'),('dim_sector','sector','Sector'),('dim_sex','sex','Sex'),('dim_age_band','age_band','Age')]):
        slicer(p,'filter_'+c,t,c,label,32+i*350,120,326)
    card(p,'rate','Displayed Capability Rate','UPI-capability rate · selected population',32,211,442)
    card(p,'sample','Sample Size','Respondents · selected population',496,211,442)
    card(p,'gap','Excluded (crore)','Not UPI-capable · crore people',960,211,448)
    visual(p,'age','clusteredColumnChart',32,345,620,356,{'Category':[column('dim_age_band','age_band')],'Series':[column('dim_sex','sex')],'Y':[measure('Displayed Capability Rate')]},'Capability by age and sex',sort=column('dim_age_band','age_band'))
    table(p,'states',[column('dim_state','state','State / UT'),measure('Displayed Capability Rate','UPI-capable'),measure('Sample Size','Sample n'),measure('Source Check','Source check')],
          'State comparisons · alphabetical',674,345,734,356,column('dim_state','state'))
    text(p,'limits','A sample threshold is a display rule, not a precision guarantee. Close point estimates are not significance tests.\nAll recorded sex categories contribute to totals. Source check details appear on the Methods page.',32,721,1376,80)
    p='03_npci';page(p,'NPCI · exploratory','Classified state transactions and survey capability are different measures. No demographic transaction estimates are inferred.')
    for i,(m,label) in enumerate([('National Transactions (bn)','National transactions · billion'),('Classified Transactions (bn)','Classified transactions · billion'),('Unclassified Transactions (bn)','Unclassified transactions · billion'),('Unclassified Share','National unclassified share')]):
        card(p,'metric_'+str(i),m,label,32+i*350,127)
    visual(p,'scatter','scatterChart',32,261,850,454,{'Category':[column('fct_state','state')],'X':[measure('State Capability Rate')],'Y':[measure('Classified Transactions per Resident 15+')],
         'Tooltips':[column('fct_state','review_status'),column('fct_state','transaction_scope')]},'Classified transactions per resident 15+ vs UPI capability',
         {'dataPoint':obj(defaultColor=color(BLUE)),'categoryAxis':obj(showAxisTitle=literal(True)),'valueAxis':obj(showAxisTitle=literal(True))})
    visual(p,'monthly','clusteredColumnChart',904,261,504,300,{'Category':[column('fct_unclassified','month')],'Y':[measure('Monthly Unclassified Share')]},'Unclassified share by month',sort=column('fct_unclassified','month'))
    text(p,'scope','38.1% of national volume has no state attribution.\nState-specific coverage is unknown.\nTransaction geography may differ from residence.',904,581,504,134,13)
    text(p,'caution','All 36 observed state points are shown, with source flags in tooltips. No fitted line or behavioural diagnosis is asserted here.\nRedistribution rules are assumptions; they do not recover missing state transactions or establish complete-volume rankings.',32,742,1376,90)
    p='04_whatif';page(p,'Population what-if','A transparent assumption applied to a survey population estimate. This is arithmetic, not an ML forecast.')
    for i,(t,c,label) in enumerate([('dim_sector','sector','Sector'),('dim_sex','sex','Sex'),('dim_age_band','age_band','Age'),('scenario','assumed_percent','Assumed share becoming capable (%)')]):
        slicer(p,'select_'+c,t,c,label,32+i*350,127,326)
    card(p,'baseline','Scenario Baseline','Baseline not UPI-capable · people',32,230,442)
    card(p,'assumption','Assumed Share','Applied assumption · default 10%',496,230,442)
    card(p,'result','Newly Capable (what-if)','Hypothetical newly capable · people',960,230,448)
    text(p,'formula','Estimated excluded population × assumed share',56,396,1300,66,27,BLUE,True)
    text(p,'explanation','Choose one assumed percentage from 0 to 100. With no single choice, the calculator uses 10%.\n\nThe result does not predict adoption, extra transactions, programme effectiveness or financial returns.\nThe baseline is a weighted survey estimate; its sampling uncertainty remains unquantified.\n\nScenario totals include all selected recorded sex categories. Groups with fewer than 30 respondents are blanked.\nState scenarios are intentionally unavailable while source and uncertainty limitations remain unresolved.',56,491,1290,284,15)
    p='05_methods';page(p,'Methods & source checks','A reproducible snapshot  /  Definitions, source reconciliation and limits')
    text(p,'methodnote','Survey: CMS-T, Jan–Mar 2025; age 15+; MLT/100 weights; NSS-region state codes. Q12 codes 1 and 3 identify UPI capability.\nConditional figures use respondent intersections. Sampling-frame/listing inputs needed for exact confidence intervals are unavailable.\nOnline-banking reconciliation matches 35/36 states at published precision; Himachal Pradesh differs by 1.8 percentage points.\nThe survey estimate is retained and flagged. This cross-check does not establish the accuracy of every derived measure.',32,119,1376,129,12)
    table(p,'validation',[column('fct_source_validation',c,label) for c,label in [('state','State / UT'),('computed_pct','Reproduced %'),('official_pct','Official %'),('difference_pp','Difference · pp'),('review_status','Review status')]],
          'Online-banking capability · official Table 12 cross-check',32,267,844,448,column('fct_source_validation','state'))
    table(p,'allocation',[column('fct_sensitivity',c,label) for c,label in [('allocation_rule','Rule'),('rank_agreement_with_excluded','Rank agreement'),('uses_capability_in_allocation','Uses capability')]],
          'Allocation assumptions · all 36 states',898,267,510,270)
    text(p,'allocationnote','Proportional and population allocations preserve per-adult ranks by construction. Capability/gap allocations build the tested relationship into the data. Neither validates actual missing-state coverage.',908,559,490,156,12)
    text(p,'sources','Sources: microdata.gov.in/NADA/index.php/catalog/239  •  NPCI owner-supplied Jan–Mar workbooks\nSee DATA_NOTES.md, docs/AUDIT.md and aggregate_manifest.json for definitions, provenance and source hashes.',32,743,1376,81,12)
    write(REPORT/'definition/pages/pages.json',{'$schema':SCHEMA+'item/report/definition/pagesMetadata/1.0.0/schema.json','pageOrder':PAGES,'activePageName':PAGES[0]})
    print(f'Built {len(PAGES)} pages and {COUNT} native visuals in {OUT}')

if __name__=='__main__':
    model();build_report()
