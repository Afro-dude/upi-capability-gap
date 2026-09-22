"""Structural and data integrity checks; Desktop visual/DAX checks are separate."""
import base64
import csv
import hashlib
import json
from pathlib import Path
import re
import zlib

ROOT=Path(__file__).resolve().parents[1]
PBI=ROOT/'powerbi'
MODEL=json.loads((PBI/'UPI.SemanticModel/model.bim').read_text(encoding='utf-8'))['model']
TABLES={t['name']:t for t in MODEL['tables']}

def embedded_rows(table):
    expression='\n'.join(table['partitions'][0]['source']['expression'])
    payload=re.search(r'Binary.FromText\("([A-Za-z0-9+/=]+)"',expression).group(1)
    return json.loads(zlib.decompress(base64.b64decode(payload),-15))

def test_embedded_snapshot_matches_every_export():
    manifest=json.loads((PBI/'aggregate_manifest.json').read_text())
    for item in manifest['tables']:
        path=ROOT/item['file']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
        table=TABLES[path.stem];columns={c['name']:i for i,c in enumerate(table['columns'])}
        rows=embedded_rows(table)
        with path.open(encoding='utf-8-sig',newline='') as f:
            records=list(csv.DictReader(f))
        assert len(rows)==len(records)==item['rows']
        for source,actual in zip(records,rows):
            for key,value in source.items():
                found=actual[columns[key]]
                if value=='':assert found is None
                elif key=='state_code':assert found==value.zfill(2)
                elif isinstance(found,bool):assert found==(value.lower()=='true')
                elif isinstance(found,(int,float)):assert found==float(value)
                else:assert found==value

def test_relationships_preserve_transaction_and_survey_scope():
    relationships=MODEL['relationships']
    assert all(r['crossFilteringBehavior']=='oneDirection' for r in relationships)
    assert {r['toTable'] for r in relationships if r['fromTable']=='fct_state'}=={'dim_state'}
    assert not any(r['fromTable'] in {'fct_npci_national','fct_conditional_national','scenario'} for r in relationships)
    for r in relationships:
        target=TABLES[r['toTable']];i=[c['name'] for c in target['columns']].index(r['toColumn'])
        keys=[row[i] for row in embedded_rows(target)]
        assert len(keys)==len(set(keys)) and None not in keys
        source=TABLES[r['fromTable']];j=[c['name'] for c in source['columns']].index(r['fromColumn'])
        assert {row[j] for row in embedded_rows(source)} <= set(keys)

def test_visual_fields_exist_and_fit_on_page():
    for p in (PBI/'UPI.Report/definition/pages').glob('*/visuals/*/visual.json'):
        visual=json.loads(p.read_text(encoding='utf-8'));pos=visual['position']
        assert 0<=pos['x'] and 0<=pos['y'] and pos['x']+pos['width']<=1440 and pos['y']+pos['height']<=900
        for role in visual['visual'].get('query',{}).get('queryState',{}).values():
            for projection in role['projections']:
                f=projection['field'];kind='Measure' if 'Measure' in f else 'Column';ref=f[kind]
                table=TABLES[ref['Expression']['SourceRef']['Entity']]
                assert ref['Property'] in {c['name'] for c in table['measures' if kind=='Measure' else 'columns']}

def test_scenario_has_no_state_slicer_and_supports_zero_to_full():
    assert embedded_rows(TABLES['scenario'])==[[n] for n in range(101)]
    page=PBI/'UPI.Report/definition/pages/04_whatif'
    assert 'dim_state' not in ''.join(p.read_text() for p in page.rglob('visual.json'))
    measures={m['name']:m['expression'] for m in TABLES['_Measures']['measures']}
    assert measures['Newly Capable (what-if)']=='[Scenario Baseline] * [Assumed Share]'
    assert measures['Capability Rate']=='DIVIDE([Capable Adults], [Adults])'
