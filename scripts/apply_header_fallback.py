"""Patch blocks_service.py (safe to re-run). From repo root:
    python -m scripts.apply_header_fallback

1. Header-less blocks borrow the header of the nearest earlier block in the
   same section, only when the column count is identical (never guess).
2. Columns like «به تاریخ ۱۴۰۳/۱۲/۳۰» hold amounts: they get separators and
   unit again (the word «تاریخ» alone used to switch formatting off).
3. Row 112 col 4 (4001): confirmed by rows 148 and 151 of the equity-change
   statement, so it is shown as [تأییدشده] instead of [مشکوک].
"""
from pathlib import Path

P = Path("backend/services/blocks_service.py")
s = P.read_text(encoding="utf-8")


def replace(old, new):
    assert s.count(old) == 1, f"الگو پیدا نشد:\n{old}"
    return s.replace(old, new)


if "borrowed_from" not in s:
    s = replace('''    for b in blocks:
        raw = b.pop("raw")
''', '''    last_headed = {}  # section -> block that has a real header
    for b in blocks:
        raw = b.pop("raw")
''')
    s = replace('''        b["rows"] = []
        group = ""
''', '''        # Fallback: borrow header from the nearest earlier block in the same
        # section, only if the column count is identical (never guess).
        b["borrowed_from"] = None
        if b["no_header"]:
            src = last_headed.get(b["section"])
            if src is not None and len(src["header"]) == width:
                b["header"] = list(src["header"])
                b["no_header"] = False
                b["borrowed_from"] = src["start_row"]
        else:
            last_headed[b["section"]] = b

        b["rows"] = []
        group = ""
''')
    s = replace('''    if block["no_header"]:
        head.append("هشدار: هدر ستون در فایل پیدا نشد")
''', '''    if block["no_header"]:
        head.append("هشدار: هدر ستون در فایل پیدا نشد")
    if block.get("borrowed_from"):
        head.append(
            f"نکته: هدر ستون‌ها از جدول بالاتر (ردیف {block['borrowed_from']}) "
            "گرفته شده، چون تعداد ستون‌ها برابر است"
        )
''')

if "def is_amount_at_date" not in s:
    s = replace('''def column_unit(unit, header):
    if not unit or any(w in header for w in NO_UNIT_WORDS):
        return ""''', '''def is_amount_at_date(header):
    """«به تاریخ ...» / «ارائه شده به تاریخ ...» columns hold amounts."""
    return norm("به تاریخ") in norm(header)


def column_unit(unit, header):
    if not unit or (any(w in header for w in NO_UNIT_WORDS) and not is_amount_at_date(header)):
        return ""''')
    s = replace('''    if not value or any(w in header for w in NO_FORMAT_WORDS):
        return value''', '''    if not value or (any(w in header for w in NO_FORMAT_WORDS) and not is_amount_at_date(header)):
        return value''')

if "[تأییدشده]" not in s:
    s = replace('''    (112, 3): "مقدار ۴۰۰۱ در ستون سوم «سایر اندوخته‌ها» با ستون‌های دیگر نمی‌خواند؛ باید با Codal چک شود",''',
                '''    (112, 3): "۴۰۰۱ در «سایر اندوخته‌ها» با ردیف‌های ۱۴۸ و ۱۵۱ صورت تغییرات حقوق مالکانه یکی است",''')
    s = replace('''                shown += " [مشکوک]"''', '''                shown += " [تأییدشده با ردیف‌های 148 و 151 صورت تغییرات حقوق مالکانه]"''')
    s = replace('''        head.append("هشدار: سلول مشکوک در ردیف‌های " + "، ".join(str(r) for r, _ in flagged))''',
                '''        head.append("نکته: عدد غیرعادی در ردیف‌های " + "، ".join(str(r) for r, _ in flagged)
                    + " با صورت تغییرات حقوق مالکانه مطابقت داده شد و درست است")''')

P.write_text(s, encoding="utf-8")
print("اعمال شد:", P)
