from dmtcoder.stage1.planner import build_plan
def test_plan_shapes():
    doc = {'spec':'ColorGen','version':'0.1.0','description':'d',
           'functions':[{'id':'CGN-001','name':'wave_to_color','signature':'wave_to_color(x) -> y',
                         'io':{'inputs':[{'name':'x','type':'np.ndarray'}],'output':{'type':'np.ndarray'}},
                         'behavior':[{'step':'a'}],'validation':[{'type':'exception','rule':'x'}],
                         'dmt':{'teach':{'lessons':[{'name':'l','demo':{'script':'notebooks/a.py','expects':[{'plot':'artifacts/plots/a.png'}]}}]}}}]}
    plan = build_plan(doc)
    kinds = {i.kind for i in plan.items}
    assert 'code_stub' in kinds and 'test_stub' in kinds and 'teach_stub' in kinds and 'doc_stub' in kinds
