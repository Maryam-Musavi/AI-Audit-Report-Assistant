import pytest
from backend.services import finance_service as fs

if not fs.BLOCKS_JSON.exists():
    pytest.skip("blocks.json نیست؛ اول python -m scripts.build_blocks", allow_module_level=True)

BS = "صورت وضعیت مالی"
IS = "صورت سود و زیان"


def test_total_debt():
    v = fs.get_value("جمع بدهی‌ها", BS, period="1403/12/30")
    assert v["value"] == 449264642
    assert v["excel_row"] == 135
    assert not v["suspicious"]


def test_receivables_and_default_period_is_latest():
    v = fs.get_value("دریافتنی‌های تجاری و سایر دریافتنی‌ها", BS)
    assert v["value"] == 461592117


def test_previous_period():
    assert fs.get_value("جمع بدهی‌ها", BS, period="1402/12/29")["value"] == 356409510


def test_income_statement_negative_value():
    assert fs.get_value("بهای تمام شده درآمدهای عملیاتی", IS)["value"] == -4163384014


def test_duplicate_label_requires_section():
    with pytest.raises(fs.AmbiguousLabel):
        fs.get_value("سود(زیان) خالص")
    assert fs.get_value("سود(زیان) خالص", IS)["value"] == 209569140


def test_missing_label_raises_not_guesses():
    with pytest.raises(fs.LabelNotFound):
        fs.get_value("فروش اعتباری")


def test_unknown_period_raises():
    with pytest.raises(LookupError):
        fs.get_value("جمع بدهی‌ها", BS, period="1390/01/01")


def test_ratios():
    d = fs.compute_ratio("debt_ratio", "1403/12/30")
    assert d["value"] == pytest.approx(449264642 / 1093440777)
    c = fs.compute_ratio("current_ratio", "1403/12/30")
    assert c["value"] == pytest.approx(831685903 / 434324759)
    r = fs.compute_ratio("receivables_to_sales", "1403/12/30")
    assert r["value"] == pytest.approx(461592117 / 4425065684 * 100)
    m = fs.compute_ratio("net_profit_margin")
    assert m["value"] == pytest.approx(209569140 / 4425065684 * 100)


def test_every_ratio_is_computable():
    for name in fs.RATIOS:
        assert fs.compute_ratio(name)["value"] is not None
