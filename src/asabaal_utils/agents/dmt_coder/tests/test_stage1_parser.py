from dmtcoder.stage1.parser import _sig_parts
def test_sig_parts():
    n, p, r = _sig_parts("f(a: int, b: str='x') -> float")
    assert n == 'f' and 'a:' in p and r == 'float'
