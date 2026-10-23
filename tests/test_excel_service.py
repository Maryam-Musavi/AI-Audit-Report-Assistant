from pathlib import Path
import pytest
from excel_service import load_balance_sheet, get_total_debt, get_credit_sales

XLSX = Path(__file__).resolve().parent.parent / "Table.xlsx"


@pytest.fixture(scope="module")
def bs():
    return load_balance_sheet(str(XLSX))


def test_unit_and_dates(bs):
    assert "میلیون ریال" in bs["unit"]
    assert bs["dates"] == ["1403/12/30", "1402/12/29", "1402/01/01"]


def test_total_debt(bs):
    d = get_total_debt(bs)
    assert d["total"]["1403/12/30"] == 449264642
    assert d["total"]["1402/12/29"] == 356409510
    assert all(d["sum_check_ok"].values())


def test_credit_sales(bs):
    c = get_credit_sales(bs)
    assert c["trade_and_other_receivables"]["1403/12/30"] == 461592117
    assert c["long_term_receivables"]["1403/12/30"] == 0


def test_totals_balance(bs):
    r = bs["rows"]
    for d in bs["dates"]:
        assert r["جمع دارایی ها"]["values"][d] == r["جمع حقوق مالکانه و بدهی ها"]["values"][d]
