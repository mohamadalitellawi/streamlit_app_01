from app_module import calc_Mr
import pytest

def test_calc_Mr():
    latex_out, result = calc_Mr(100,100,0.9,240)
    assert result == pytest.approx(36_000_000.0)