from dmtcoder.stage1.runner import StageOneRunner
def test_integration_minimal(tmp_path):
    spec_path = tmp_path/'spec.yaml'
    spec_path.write_text('spec: X\nversion: 0.1.0\ndescription: d\nfunctions: []\n')
    rep = StageOneRunner.check(str(spec_path))
    assert rep.passed
