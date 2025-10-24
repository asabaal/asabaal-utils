import pytest
def multiply_by_two(x):
    return x * 2
def test_multiply_by_two_basic_functionality():
    assert multiply_by_two(5) == 10
    assert multiply_by_two(0) == 0
    assert multiply_by_two(-3) == -6
def test_multiply_by_two_edge_cases():
    assert multiply_by_two(1) == 2
    assert multiply_by_two(-1) == -2
    assert multiply_by_two(1000000) == 2000000
    assert multiply_by_two(-1000000) == -2000000
def test_multiply_by_two_type_safety():
    assert multiply_by_two(2.5) == 5.0
    assert multiply_by_two(0.0) == 0.0
def test_multiply_by_two_error_conditions():
    with pytest.raises(TypeError):
        multiply_by_two("5")
    with pytest.raises(TypeError):
        multiply_by_two([1, 2, 3])
    with pytest.raises(TypeError):
        multiply_by_two(None)
    with pytest.raises(TypeError):
        multiply_by_two({1, 2, 3})