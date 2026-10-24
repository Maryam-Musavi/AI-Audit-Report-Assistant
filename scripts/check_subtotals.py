"""کنترل خودکار ردیف‌های «جمع» با blocks.json. فقط ناهماهنگی‌ها چاپ می‌شود."""
import json
import re
import sys

from backend.paths import GENERATED

MIN_ABS = 100  # جمع‌های خیلی کوچک/صفر خطا حساب نمی‌شوند
PERSIAN = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def parse(cell):
    """عدد سلول را برمی‌گرداند یا None. پرانتز/منفی = عدد منفی."""
    s = str(cell).translate(PERSIAN).strip().replace(",", "").replace("٬", "")
    if not s:
        return None
    neg = s.startswith("(") and s.endswith(")") or s.startswith("-")
    s = s.strip("()-").strip()
    if not re.fullmatch(r"\d+(\.\d+)?", s):
        return None
    v = float(s)
    return -v if neg else v


def is_total_row(r):
    label = r["label"].replace("ي", "ی").replace("ك", "ک")
    return label.startswith("جمع") or r.get("unlabeled")


def find_match(rows, i, j):
    """آیا ستون j ردیف i برابر جمع ردیف‌های بالاتر (پیوسته) است؟"""
    total = parse(rows[i]["cells"][j])
    cum = 0.0
    for k in range(i - 1, -1, -1):
        v = parse(rows[k]["cells"][j]) if j < len(rows[k]["cells"]) else None
        if v is None:
            continue
        cum += v
        if abs(cum - total) < 0.5:
            return rows[k]["row"]
    # حالت جمع کل: مجموع چند ردیف «جمع» قبلی (حداکثر ۸ تای نزدیک‌تر)
    vals = []
    for k in range(i - 1, -1, -1):
        if len(vals) >= 8:
            break
        if not is_total_row(rows[k]) or j >= len(rows[k]["cells"]):
            continue
        v = parse(rows[k]["cells"][j])
        if v is not None:
            vals.append((rows[k]["row"], v))
    for mask in range(1, 1 << len(vals)):
        pick = [vals[n] for n in range(len(vals)) if mask >> n & 1]
        if len(pick) >= 2 and abs(sum(v for _, v in pick) - total) < 0.5:
            return pick[-1][0]
    return None


def main():
    blocks = json.load(open(GENERATED / "blocks.json", encoding="utf-8"))
    ok = bad = skipped = 0
    problems = []
    for b in blocks:
        # ردیف‌های بلوک‌های قبلیِ همان بخش هم دیده می‌شوند
        prev = []
        for o in blocks:
            if o is b:
                break
            if o["section"] == b["section"]:
                prev += o["rows"]
        rows = prev + b["rows"]
        for i, r in enumerate(rows):
            if i < len(prev):
                continue
            if not is_total_row(r):
                continue
            cols = [j for j in range(len(r["cells"]))
                    if j != b["label_col"] and parse(r["cells"][j]) is not None
                    and abs(parse(r["cells"][j])) >= MIN_ABS]
            if not cols:
                skipped += 1
                continue
            matched = [j for j in cols if find_match(rows, i, j) is not None]
            if matched:
                ok += 1
            else:
                bad += 1
                problems.append((r["row"], r["label"], b["title"],
                                 [(b["header"][j] if j < len(b["header"]) else j,
                                   r["cells"][j]) for j in cols]))
    print(f"جمع‌های تأییدشده: {ok} | بدون تطابق: {bad} | رد شده (بدون عدد): {skipped}")
    for row, label, title, vals in problems:
        print(f"\nردیف {row} «{label}» [{title}]")
        for name, v in vals:
            print(f"   {name}: {v}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
