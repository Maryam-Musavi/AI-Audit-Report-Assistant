import re
import pandas as pd

_FA_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_DATE = re.compile(r"\d{4}/\d{2}/\d{2}")

BALANCE_TITLE = "صورت وضعیت مالی"
BALANCE_END = "جمع حقوق مالکانه و بدهی ها"


def norm(s) -> str:
    s = str(s).translate(_FA_DIGITS)
    s = s.replace("ي", "ی").replace("ك", "ک").replace("ى", "ی")
    s = s.replace("\u200c", " ").replace("\u200f", " ")
    return re.sub(r"\s+", " ", s).strip()


def _num(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def load_balance_sheet(path: str, sheet=0) -> dict:
    df = pd.read_excel(path, sheet_name=sheet, header=None)
    labels = [norm(x) if str(x) != "nan" else "" for x in df[0]]

    title = norm(BALANCE_TITLE)
    start = head = None
    for i, lab in enumerate(labels):
        if lab != title:
            continue
        h = next((j for j in range(i, i + 6) if labels[j] == "شرح"), None)
        if h is not None:
            if start is not None:
                raise ValueError(f"بیش از یک ترازنامه پیدا شد (ردیف {start} و {i})")
            start, head = i, h
    if start is None:
        raise ValueError("ترازنامه (عنوان + ردیف «شرح») پیدا نشد")
    unit = next((labels[i] for i in range(start, head) if "میلیون ریال" in labels[i]), "")

    dates = {}
    for col in (1, 2, 3):
        m = _DATE.search(norm(df.iat[head, col]))
        if not m:
            raise ValueError(f"تاریخ ستون {col} پیدا نشد")
        dates[col] = m.group()

    end = labels.index(norm(BALANCE_END), head)
    rows = {}
    for i in range(head + 1, end + 1):
        name = labels[i]
        vals = {dates[c]: _num(df.iat[i, c]) for c in (1, 2, 3)}
        if not name or all(v is None for v in vals.values()):
            continue
        if name in rows:
            raise ValueError(f"برچسب تکراری در ترازنامه: {name} (ردیف {i})")
        rows[name] = {"row": i, "values": vals}

    return {"unit": unit, "dates": list(dates.values()), "rows": rows}


def _get(bs: dict, label: str) -> dict:
    key = norm(label)
    if key not in bs["rows"]:
        raise KeyError(f"ردیف پیدا نشد: {label}")
    return bs["rows"][key]


def get_total_debt(bs: dict) -> dict:
    total = _get(bs, "جمع بدهی ها")
    cur = _get(bs, "جمع بدهی های جاری")
    non = _get(bs, "جمع بدهی های غیرجاری")
    checks = {d: cur["values"][d] + non["values"][d] == total["values"][d] for d in bs["dates"]}
    return {
        "unit": bs["unit"],
        "total": total["values"],
        "current": cur["values"],
        "non_current": non["values"],
        "sum_check_ok": checks,
        "source_rows": {"total": total["row"], "current": cur["row"], "non_current": non["row"]},
    }


def get_credit_sales(bs: dict) -> dict:
    trade = _get(bs, "دریافتنی های تجاری و سایر دریافتنی ها")
    long_term = _get(bs, "دریافتنی های بلندمدت")
    return {
        "unit": bs["unit"],
        "trade_and_other_receivables": trade["values"],
        "long_term_receivables": long_term["values"],
        "source_rows": {"trade": trade["row"], "long_term": long_term["row"]},
        "note": (
            "فروش اعتباری مستقیم در گزارش نیامده. نزدیک‌ترین رقم مانده‌ی "
            "دریافتنی‌های تجاری و سایر دریافتنی‌ها در تاریخ ترازنامه است، "
            "نه کل فروش نسیه‌ی سال. این رقم شامل دریافتنی‌های غیرتجاری هم می‌شود."
        ),
    }


def balance_to_markdown(bs: dict) -> str:
    lines = [
        f"[صورت وضعیت مالی | {bs['unit']}]", "",
        "| شرح | " + " | ".join(bs["dates"]) + " |",
        "|---|" + "---|" * len(bs["dates"]),
    ]
    for name, r in bs["rows"].items():
        cells = ["" if r["values"][d] is None else f"{r['values'][d]:,}" for d in bs["dates"]]
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    return "\n".join(lines)
