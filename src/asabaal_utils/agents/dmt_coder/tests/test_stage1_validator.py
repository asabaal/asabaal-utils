from dmtcoder.stage1.validator import validate_spec
def test_validator_catches_missing():
    doc = {'spec':'X','version':'0.1.0','description':'d','functions':[{}]}
    rep = validate_spec(doc)
    assert not rep.passed and any('missing key' in m for m in rep.messages)
