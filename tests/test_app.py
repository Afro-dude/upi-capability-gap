from pathlib import Path
from streamlit.testing.v1 import AppTest

APP=Path(__file__).resolve().parents[1]/'app.py'

def test_dashboard_interactions():
    app=AppTest.from_file(str(APP),default_timeout=30).run()
    assert not app.exception
    assert len(app.tabs)==5
    app.radio[0].set_value('State / UT').run()
    assert not app.exception
    next(x for x in app.selectbox if x.label=='State or union territory').set_value('Himachal Pradesh').run()
    assert not app.exception
    assert any('Source discrepancy' in w.value for w in app.warning)
    next(x for x in app.selectbox if x.label=='Scenario population').set_value('National demographic segment').run()
    assert not app.exception
    app.slider[0].set_value(0).run()
    assert not app.exception
    assert next(m.value for m in app.metric if m.label=='Hypothetical newly capable population')=='0'
    app.radio[0].set_value('National segments').run()
    next(x for x in app.multiselect if x.label=='Sector').set_value([]).run()
    assert not app.exception
    assert any('No groups meet' in m.value for m in app.info)
