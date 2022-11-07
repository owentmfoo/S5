from S5.nonosquare import why
import pytest

@pytest.mark.parametrize("i",[i for i in range(30)])
def test_why(i):
    why()