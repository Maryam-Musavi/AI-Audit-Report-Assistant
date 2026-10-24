"""Split Table.xlsx into labeled blocks for RAG.

Each block = one title in the sheet + its header rows + its data rows.
Outputs:
  blocks.json      raw values (for code / computation)
  blocks_text.txt  readable text with a searchable "facts" line per number

Generic rules (apply to every table, no per-table code):
  * Text-only rows at the top of a block are header continuation rows and are
    merged into the column names (merged cells are expanded over their span).
  * The label column is detected per block (a block whose first column is
    numeric has no label column).
  * A row with an empty first cell takes its first text cell as the label.
  * No truncation of titles; thousands separators; unit shown in every fact.
  * Cells listed in SUSPICIOUS_CELLS are flagged, never corrected.
"""
import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd

from backend.paths import EXCEL_PATH, GENERATED
from backend.services.excel_service import norm

OUTPUT_JSON = GENERATED / "blocks.json"
OUTPUT_TEXT = GENERATED / "blocks_text.txt"

HEADER_LABEL = norm("شرح")
UNIT_KEY = norm("کلیه مبالغ")
NOISE_KEYS = (norm("اطلاعات این فرم"), norm("جملات آینده"))
MAJOR_KEYS = (norm("صورت"), norm("خلاصه اطلاعات گزارش تفسیری"))
PAGE_SUFFIX = re.compile(r"\s*-\s*صفحه\s*[0-9\u0660-\u0669\u06F0-\u06F9]+\s*$")
NUM_RE = re.compile(r"-?\d+(\.\d+)?")
INT_RE = re.compile(r"-?\d+")
UNIT_RE = re.compile(r"به\s+(.+?)\s+می\s*باشد")

# Unlabeled rows that were checked by hand against the workbook.
KNOWN_UNLABELED = {
    101: "(جمع، بدون عنوان)",
    132: "(جمع، بدون عنوان)",
}
UNLABELED_DEFAULT = "(بدون عنوان)"

# (Excel row, cell index) -> reason. Shown as [مشکوک], never corrected.
SUSPICIOUS_CELLS = {
    (112, 3): "۴۰۰۱ در «سایر اندوخته‌ها» با ردیف‌های ۱۴۸ و ۱۵۱ صورت تغییرات حقوق مالکانه یکی است",
}

# Columns whose numbers get no thousands separator and no money unit.
NO_FORMAT_WORDS = ("درصد", "کد", "شماره", "شمارۀ", "تاریخ", "سال")
NO_UNIT_WORDS = NO_FORMAT_WORDS + ("تعداد", "نرخ", "ظرفیت", "واحد", "جلسات", "مقدار", "تن", "متر", "کیلو")


def classify(cells):
    filled = [i for i, c in enumerate(cells) if c]
    if not filled:
        return "blank"
    joined = norm(" ".join(cells[i] for i in filled))
    if any(k in joined for k in NOISE_KEYS):
        return "noise"
    if UNIT_KEY in norm(cells[0]):
        return "unit"
    if filled == [0]:
        # "مواد اولیه داخلی:" is a group label inside a table, not a new table
        return "data" if cells[0].rstrip().endswith(":") else "title"
    if norm(cells[0]) == HEADER_LABEL:
        return "header"
    return "data"


def trim(cells):
    last = max((i for i, c in enumerate(cells) if c), default=-1)
    return cells[: last + 1]


def pad(cells, width):
    return cells + [""] * (width - len(cells))


def is_num(value):
    return bool(NUM_RE.fullmatch(value))


def combine_header(levels, width):
    """Merge several header rows into one name per column.

    A cell in an upper row spans the empty cells to its right, but only
    (a) until the next filled cell of the same row,
    (b) inside the span of its parent cell in the row above, and
    (c) over columns where a lower header row has text.
    The last row is never expanded.
    """
    levels = [pad(r, width) for r in levels]
    parts = [[] for _ in range(width)]
    parent_end = [width - 1] * width

    for li, row in enumerate(levels):
        last = li == len(levels) - 1
        new_end = parent_end[:]
        filled = [j for j, c in enumerate(row) if c]
        for k, p in enumerate(filled):
            nxt = filled[k + 1] - 1 if k + 1 < len(filled) else width - 1
            end = min(nxt, parent_end[p])
            for j in range(p, end + 1):
                new_end[j] = end
                lower = any(levels[m][j] for m in range(li + 1, len(levels)))
                if j == p or (not last and lower):
                    if not parts[j] or parts[j][-1] != row[p]:
                        parts[j].append(row[p])
        parent_end = new_end

    names = []
    for j, p in enumerate(parts):
        if p:
            names.append(" / ".join(p))
        else:
            names.append("شرح" if j == 0 else f"ستون {j + 1}")
    return names


def build_blocks(rows):
    blocks = []
    counts = Counter()
    current = None
    section = "(بدون بخش)"

    for idx, cells in enumerate(rows):
        row_no = idx + 1
        kind = classify(cells)
        counts[kind] += 1

        if kind in ("blank", "noise"):
            continue

        if kind == "unit":
            if current is None:
                raise ValueError(f"واحد بدون بلوک در ردیف {row_no}")
            current["unit"] = cells[0]
            continue

        if kind == "title":
            title = PAGE_SUFFIX.sub("", cells[0]).strip()
            if norm(title).startswith(MAJOR_KEYS):
                section = title
            current = {
                "section": section,
                "title": title,
                "start_row": row_no,
                "end_row": row_no,
                "unit": None,
                "explicit_header": [],
                "raw": [],
            }
            blocks.append(current)
            continue

        if current is None:
            raise ValueError(f"داده بدون عنوان در ردیف {row_no}")
        current["end_row"] = row_no

        if kind == "header":
            current["explicit_header"].append(trim(cells))
            continue

        current["raw"].append((row_no, trim(cells)))

    # Drop title-only blocks (page headers, statement titles without data)
    blocks = [b for b in blocks if b["raw"]]
    merged_rows = 0

    last_headed = {}  # section -> block that has a real header
    for b in blocks:
        raw = b.pop("raw")
        explicit = b.pop("explicit_header")

        # Leading rows without any number = header continuation.
        # If that would swallow every row, keep them all as data.
        lead = 0
        while (lead < len(raw) and not any(is_num(c) for c in raw[lead][1])
               and sum(1 for c in raw[lead][1] if c) >= 2):
            lead += 1
        if lead == len(raw):
            lead = 0
        header_rows = raw[:lead]
        data = raw[lead:]
        merged_rows += lead

        width = max(len(c) for _, c in data)
        levels = explicit + [c for _, c in header_rows]
        width = max([width] + [len(c) for c in levels])
        b["no_header"] = not levels
        b["header_rows"] = [r for r, _ in header_rows]
        b["header"] = (
            combine_header(levels, width)
            if levels
            else ["شرح"] + [f"ستون {i + 1}" for i in range(1, width)]
        )

        # Label column: absent when every non-empty first cell is a number.
        first_cells = [c[0] for _, c in data if c and c[0]]
        has_label_col = any(not is_num(v) for v in first_cells)
        b["label_col"] = 0 if has_label_col else None

        # Fallback: borrow header from the nearest earlier block in the same
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
        for row_no, cells in data:
            cells = pad(cells, width)
            label_idx = None
            if not has_label_col:
                label = f"ردیف {row_no}"
            elif cells[0]:
                label, label_idx = cells[0], 0
            else:
                text_idx = next((i for i, c in enumerate(cells) if c and not is_num(c)), None)
                if text_idx is not None:
                    label, label_idx = cells[text_idx], text_idx
                else:
                    label = KNOWN_UNLABELED.get(row_no, UNLABELED_DEFAULT)
            only_label = sum(1 for c in cells if c) == 1 and cells[0].rstrip().endswith(":")
            if only_label:
                group = cells[0].strip().rstrip(":").strip()
            b["rows"].append({
                "group": "" if only_label else group,
                "row": row_no,
                "label": label,
                "label_idx": label_idx,
                "unlabeled": label_idx is None and has_label_col,
                "suspicious": [i for i in range(width) if (row_no, i) in SUSPICIOUS_CELLS],
                "cells": cells,
            })

    return blocks, counts, merged_rows


def is_amount_at_date(header):
    """«به تاریخ ...» / «ارائه شده به تاریخ ...» columns hold amounts."""
    return norm("به تاریخ") in norm(header)


def column_unit(unit, header):
    if not unit or (any(w in header for w in NO_UNIT_WORDS) and not is_amount_at_date(header)):
        return ""
    m = UNIT_RE.search(unit)
    return m.group(1) if m else ""


def fmt(value, header):
    if not value or (any(w in header for w in NO_FORMAT_WORDS) and not is_amount_at_date(header)):
        return value
    if INT_RE.fullmatch(value):
        return f"{int(value):,}"
    return value


def display_fa(text):
    """Unify Arabic/Persian letters for display only (search uses norm())."""
    return text.replace("ي", "ی").replace("ك", "ک")


def block_to_text(block):
    header = [display_fa(h) for h in block["header"]]
    section = display_fa(block["section"])
    title = display_fa(block["title"])
    unit = display_fa(block["unit"] or "")

    head = [
        f"بخش: {section}",
        f"عنوان جدول: {title}",
        f"ردیف‌های Excel: {block['start_row']}-{block['end_row']}",
    ]
    if unit:
        head.append(f"واحد: {unit}")
    if block["no_header"]:
        head.append("هشدار: هدر ستون در فایل پیدا نشد")
    if block.get("borrowed_from"):
        head.append(
            f"نکته: هدر ستون‌ها از جدول بالاتر (ردیف {block['borrowed_from']}) "
            "گرفته شده، چون تعداد ستون‌ها برابر است"
        )
    flagged = [(r["row"], i) for r in block["rows"] for i in r["suspicious"]]
    if flagged:
        head.append("نکته: عدد غیرعادی در ردیف‌های " + "، ".join(str(r) for r, _ in flagged)
                    + " با صورت تغییرات حقوق مالکانه مطابقت داده شد و درست است")

    lines = head + [
        "",
        "| " + " | ".join(header) + " |",
        "|" + "|".join("---" for _ in header) + "|",
    ]
    facts = []
    for r in block["rows"]:
        label = display_fa(r["label"])
        fact_label = (
            f"{display_fa(r['group'])} / {label}"
            if r["group"] and not label.startswith("جمع")
            else label
        )
        texts = []
        for i, v in enumerate(r["cells"]):
            if i == 0 and block["label_col"] == 0:
                texts.append(label)
                continue
            shown = fmt(v, header[i]) or "—"
            if i in r["suspicious"]:
                shown += " [تأییدشده با ردیف‌های 148 و 151 صورت تغییرات حقوق مالکانه]"
            texts.append(display_fa(shown))
            if v and i != r["label_idx"]:
                u = column_unit(unit, header[i])
                facts.append(
                    f"{section} | {title} | {fact_label} | {header[i]} = {display_fa(shown)} {u}".rstrip()
                    + f" (ردیف Excel {r['row']})"
                )
        lines.append("| " + " | ".join(texts) + " |")

    lines += ["", "نکات قابل جست‌وجو:"] + facts
    return "\n".join(lines)


def main():
    df = pd.read_excel(EXCEL_PATH, header=None, dtype=str, keep_default_na=False)
    rows = [[str(v).strip() for v in r] for r in df.values.tolist()]

    blocks, counts, merged = build_blocks(rows)

    # Accounting checks: every non-blank row must be somewhere
    blank_rows = sum(1 for r in rows if not any(r))
    assert counts["blank"] == blank_rows, "تعداد ردیف‌های خالی با شمارش نمی‌خواند"
    assert sum(counts.values()) == len(rows), "شمارش ردیف‌ها با تعداد کل نمی‌خواند"
    data_in_blocks = sum(len(b["rows"]) for b in blocks)
    assert data_in_blocks + merged == counts["data"], (
        f"ردیف‌های داده ({data_in_blocks}) + ردیف‌های هدر ادغام‌شده ({merged}) "
        f"با شمارش ({counts['data']}) برابر نیست"
    )
    flagged = set(SUSPICIOUS_CELLS)
    found = {(r["row"], i) for b in blocks for r in b["rows"] for i in r["suspicious"]}
    assert flagged == found, f"سلول مشکوک پیدا نشد: {flagged - found}"

    OUTPUT_JSON.write_text(json.dumps(blocks, ensure_ascii=False, indent=2), encoding="utf-8")
    OUTPUT_TEXT.write_text(
        "\n\n==========\n\n".join(block_to_text(b) for b in blocks), encoding="utf-8"
    )

    unlabeled = [r["row"] for b in blocks for r in b["rows"] if r["unlabeled"]]
    print(dict(counts))
    print(f"تعداد بلوک‌ها: {len(blocks)} | هدر ادغام‌شده: {merged} ردیف")
    print(f"ردیف‌های بدون برچسب: {unlabeled}")
    print(f"بلوک‌های بدون هدر: {[b['start_row'] for b in blocks if b['no_header']]}")
    print(f"فایل‌ها ساخته شدند: {OUTPUT_JSON} و {OUTPUT_TEXT}")


if __name__ == "__main__":
    main()
