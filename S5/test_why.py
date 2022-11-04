import S5.why as why
import pytest

@pytest.mark.parametrize("i",[i for i in range(30)])
def test_why(i):
    why()