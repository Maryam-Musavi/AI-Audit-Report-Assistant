"""جستجوی عمومی مقدار بر اساس برچسب + جدول نسبت‌ها (همه محاسبات با کد، نه LLM).

ورودی: data/generated/blocks.json (خروجی build_blocks).

قواعد:
  - برچسب باید دقیقاً (بعد از یکسان‌سازی حروف/فاصله) برابر باشد؛ حدس زدن نداریم.
  - نبودن برچسب یا تکراری بودن آن → خطا (با فهرست گزینه‌ها). هرگز عدد حدسی برنمی‌گردد.
  - سلول خالی/غیرعددی → خطا. صفر واقعی (0) مقدار معتبر است.
  - سلول «مشکوک» حذف یا اصلاح نمی‌شود؛ در نتیجه با suspicious=True می‌آید.

مثال:
    get_value("جمع بدهی‌ها", section="صورت وضعیت مالی", period="1403/12/30")
    compute_ratio("debt_ratio", period="1403/12/30")

اجرای مستقیم:
    python -m backend.services.finance_service value "جمع بدهی‌ها" --section "صورت وضعیت مالی"
    python -m backend.services.finance_service ratio debt_ratio
    python -m backend.services.finance_service ratios
"""
import argparse
import json
import re

from backend.paths import GENERATED
from backend.services.excel_service import norm

BLOCKS_JSON = GENERATED / "blocks.json"
_DATE = re.compile(r"\d{4}/\d{2}/\d{2}")
_INT = re.compile(r"-?\d+")


class LabelNotFound(LookupError):
    pass


class AmbiguousLabel(LookupError):
    pass


# ---------------------------------------------------------------- کمکی

def _key(text) -> str:
    """کلید مقایسه: یکسان‌سازی حروف/ارقام، حذف همهٔ فاصله‌ها و «:» انتهایی."""
    return norm(text).replace(" ", "").rstrip(":")


_cache = {}


def load_blocks(path=None):
    path = path or BLOCKS_JSON
    if path not in _cache:
        if not path.exists():
            raise FileNotFoundError(f"{path} پیدا نشد. اول بزنید: python -m scripts.build_blocks")
        _cache[path] = json.loads(path.read_text(encoding="utf-8"))
    return _cache[path]


def _section_unit(blocks, section):
    """واحد پولی بخش (بلوک‌های زیرمجموعه واحد ندارند و از بلوک اول بخش می‌گیرند)."""
    for b in blocks:
        if b["section"] == section and b.get("unit"):
            return norm(b["unit"])
    return None


def _num(cell):
    cell = (cell or "").strip()
    return int(cell) if _INT.fullmatch(cell) else None


def _pick_column(block, period, column):
    """ایندکس ستون مقدار؛ خطا اگر صفر یا چند ستون منطبق باشد."""
    header = block["header"]
    label_col = block.get("label_col") or 0
    cols = [i for i in range(len(header)) if i != label_col]

    if column is not None:
        want = _key(column)
        hit = [i for i in cols if want in _key(header[i])]
    else:
        if period is None:
            # آخرین تاریخ؛ ستون‌های «برآورد» هرگز پیش‌فرض نیستند
            dated = [(max(_DATE.findall(norm(header[i]))), i) for i in cols
                     if _DATE.search(norm(header[i])) and "برآورد" not in norm(header[i])]
            if not dated:
                raise LookupError(
                    f"جدول «{block['title']}» ستون تاریخ‌دار ندارد؛ پارامتر column را بدهید. "
                    f"ستون‌ها: {[header[i] for i in cols]}")
            period = max(d for d, _ in dated)
        period = norm(period)
        hit = [i for i in cols if period in norm(header[i]) and "برآورد" not in norm(header[i])]

    if not hit:
        raise LookupError(f"ستونی برای period={period!r} column={column!r} در «{block['title']}» نیست. "
                          f"ستون‌ها: {[header[i] for i in cols]}")
    if len(hit) > 1:
        raise AmbiguousLabel(f"چند ستون منطبق است؛ column را دقیق‌تر بدهید: {[header[i] for i in hit]}")
    return hit[0]


# ---------------------------------------------------------------- جستجوی عمومی

def find_rows(label, section=None, blocks=None):
    """همهٔ ردیف‌هایی که برچسبشان دقیقاً برابر است. section: نام بخش یا عنوان جدول (برابری دقیق)."""
    blocks = blocks if blocks is not None else load_blocks()
    want, sec = _key(label), (_key(section) if section else None)
    out = []
    for b in blocks:
        if sec and sec not in (_key(b["section"]), _key(b["title"])):
            continue
        for r in b["rows"]:
            if r["unlabeled"] or r["label_idx"] is None:
                continue
            if _key(r["label"]) == want:
                out.append((b, r))
    return out


def similar_labels(text, blocks=None, limit=10):
    """برای پیام خطا: برچسب‌هایی که شامل متن هستند."""
    blocks = blocks if blocks is not None else load_blocks()
    want = _key(text)
    seen = []
    for b in blocks:
        for r in b["rows"]:
            if not r["unlabeled"] and want and want in _key(r["label"]):
                item = f"{r['label']} [{b['title']}، ردیف {r['row']}]"
                if item not in seen:
                    seen.append(item)
    return seen[:limit]


def get_value(label, section=None, period=None, column=None, blocks=None):
    """مقدار یک برچسب در یک ستون. خروجی دیکشنری با مقدار و منبع (ردیف Excel)."""
    blocks = blocks if blocks is not None else load_blocks()
    hits = find_rows(label, section, blocks)

    if not hits:
        near = similar_labels(label, blocks)
        raise LabelNotFound(f"برچسب «{label}» (بخش={section}) پیدا نشد. نزدیک‌ها: {near}")
    if len(hits) > 1:
        where = [f"{b['section']} / {b['title']} (ردیف {r['row']})" for b, r in hits]
        raise AmbiguousLabel(f"برچسب «{label}» {len(hits)} بار آمده؛ section را مشخص کنید: {where}")

    block, row = hits[0]
    idx = _pick_column(block, period, column)
    cells = row["cells"]
    raw = cells[idx] if idx < len(cells) else ""
    value = _num(raw)
    if value is None:
        raise ValueError(f"سلول «{label}» در ستون «{block['header'][idx]}» عدد نیست (مقدار: {raw!r}، ردیف {row['row']})")

    return {
        "label": row["label"],
        "value": value,
        "column": block["header"][idx],
        "unit": _section_unit(blocks, block["section"]),
        "section": block["section"],
        "table": block["title"],
        "excel_row": row["row"],
        "suspicious": idx in row["suspicious"],
    }


# ---------------------------------------------------------------- جدول نسبت‌ها (داده، نه کد)
# هر نسبت = بالا (num) ÷ پایین (den) × scale. برای افزودن نسبت جدید فقط یک خط به RATIOS اضافه کنید.
# هر مرجع: (برچسب، بخش).

_BS = "صورت وضعیت مالی"
_IS = "صورت سود و زیان"

RATIOS = {
    "debt_ratio": {
        "name": "نسبت بدهی (جمع بدهی‌ها ÷ جمع دارایی‌ها)",
        "num": ("جمع بدهی‌ها", _BS), "den": ("جمع دارایی‌ها", _BS), "scale": 1,
        "note": "هر دو از ترازنامه در یک تاریخ.",
    },
    "current_ratio": {
        "name": "نسبت جاری (دارایی‌های جاری ÷ بدهی‌های جاری)",
        "num": ("جمع دارایی‌های جاری", _BS), "den": ("جمع بدهی‌های جاری", _BS), "scale": 1,
        "note": "هر دو از ترازنامه در یک تاریخ.",
    },
    "receivables_to_sales": {
        "name": "دریافتنی‌ها ÷ درآمد عملیاتی (درصد)",
        "num": ("دریافتنی‌های تجاری و سایر دریافتنی‌ها", _BS), "den": ("درآمدهای عملیاتی", _IS), "scale": 100,
        "note": "بالا: مانده پایان دوره (ترازنامه)، پایین: فروش کل سال (سود و زیان). "
                "فروش اعتباری جداگانه در گزارش نیست؛ این فقط یک شاخص تقریبی است.",
    },
    "net_profit_margin": {
        "name": "حاشیه سود خالص (سود خالص ÷ درآمد عملیاتی، درصد)",
        "num": ("سود(زیان) خالص", _IS), "den": ("درآمدهای عملیاتی", _IS), "scale": 100,
        "note": "هر دو از صورت سود و زیان همان دوره.",
    },
}


def compute_ratio(name, period=None, blocks=None):
    """نسبت را با کد حساب می‌کند و ورودی‌ها را هم برمی‌گرداند (برای نمایش منبع)."""
    if name not in RATIOS:
        raise KeyError(f"نسبت «{name}» تعریف نشده. موجود: {list(RATIOS)}")
    d = RATIOS[name]
    blocks = blocks if blocks is not None else load_blocks()

    num = get_value(d["num"][0], d["num"][1], period=period, blocks=blocks)
    den = get_value(d["den"][0], d["den"][1], period=period, blocks=blocks)
    if den["value"] == 0:
        raise ZeroDivisionError(f"مخرج «{den['label']}» صفر است؛ نسبت تعریف نمی‌شود.")

    value = num["value"] / den["value"] * d["scale"]
    return {
        "ratio": name,
        "name": d["name"],
        "value": value,
        "display": f"{value:,.2f}" + ("٪" if d["scale"] == 100 else ""),
        "numerator": num,
        "denominator": den,
        "note": d["note"],
        "suspicious": num["suspicious"] or den["suspicious"],
    }


# ---------------------------------------------------------------- CLI

def _print_value(v):
    flag = "  [مشکوک]" if v["suspicious"] else ""
    print(f"{v['label']} = {v['value']:,}  ({v['unit']})  | {v['table']} | {v['column']} | ردیف Excel {v['excel_row']}{flag}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("value")
    v.add_argument("label")
    v.add_argument("--section")
    v.add_argument("--period")
    v.add_argument("--column")
    r = sub.add_parser("ratio")
    r.add_argument("name")
    r.add_argument("--period")
    sub.add_parser("ratios")
    a = p.parse_args()

    if a.cmd == "ratios":
        for k, d in RATIOS.items():
            print(f"{k}: {d['name']}")
    elif a.cmd == "value":
        _print_value(get_value(a.label, a.section, a.period, a.column))
    else:
        res = compute_ratio(a.name, a.period)
        print(f"{res['name']} = {res['display']}")
        _print_value(res["numerator"])
        _print_value(res["denominator"])
        print("توضیح:", res["note"])


if __name__ == "__main__":
    main()
