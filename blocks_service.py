"""Split Table.xlsx into labeled blocks for RAG.

Each block = one title in the sheet + its header row + its data rows.
Outputs:
  blocks.json      raw values (for code / computation)
  blocks_text.txt  readable text with a searchable "facts" line per number
"""
import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd

from excel_service import norm

EXCEL_PATH = Path("Table.xlsx")
OUTPUT_JSON = Path("blocks.json")
OUTPUT_TEXT = Path("blocks_text.txt")

HEADER_LABEL = norm("شرح")
UNIT_KEY = norm("کلیه مبالغ")
NOISE_KEYS = (norm("اطلاعات این فرم"), norm("جملات آینده"))
MAJOR_KEYS = (norm("صورت"), norm("خلاصه اطلاعات گزارش تفسیری"))
PAGE_SUFFIX = re.compile(r"\s*-\s*صفحه\s*[0-9\u0660-\u0669\u06F0-\u06F9]+\s*$")
INT_RE = re.compile(r"-?\d+")
UNLABELED = "[بدون برچسب در فایل]"


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
        return "title"
    if norm(cells[0]) == HEADER_LABEL:
        return "header"
    return "data"


def trim(cells):
    last = max((i for i, c in enumerate(cells) if c), default=-1)
    return cells[: last + 1]


def header_names(cells):
    names = trim(cells)
    return [names[0]] + [c if c else f"ستون {i + 1}" for i, c in enumerate(names[1:], start=1)]


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
                "header": None,
                "rows": [],
            }
            blocks.append(current)
            continue

        if current is None:
            raise ValueError(f"داده بدون عنوان در ردیف {row_no}")
        current["end_row"] = row_no

        if kind == "header":
            current["header"] = header_names(cells)
            continue

        cells_t = trim(cells)
        label = cells_t[0] if cells_t[0] else UNLABELED
        current["rows"].append({
            "row": row_no,
            "label": label,
            "unlabeled": not cells_t[0],
            "cells": cells_t,
        })

    # Drop title-only blocks (page headers, statement titles without data)
    blocks = [b for b in blocks if b["rows"]]

    # Finalize: fill missing header and pad all rows to the same width
    for b in blocks:
        width = max([len(b["header"] or [])] + [len(r["cells"]) for r in b["rows"]])
        if b["header"] is None:
            b["header"] = ["شرح"] + [f"ستون {i}" for i in range(1, width)]
            b["no_header"] = True
        else:
            b["no_header"] = False
        b["header"] = b["header"] + [f"ستون {i + 1}" for i in range(len(b["header"]), width)]
        for r in b["rows"]:
            r["cells"] = r["cells"] + [""] * (width - len(r["cells"]))

    return blocks, counts


def fmt(value, header):
    if not value or "درصد" in header:
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

    lines = head + [
        "",
        "| " + " | ".join(header) + " |",
        "|" + "|".join("---" for _ in header) + "|",
    ]
    facts = []
    for r in block["rows"]:
        label = display_fa(r["label"])
        texts = [label]
        for i, v in enumerate(r["cells"][1:], start=1):
            texts.append(fmt(v, header[i]) or "—")
            if v:
                facts.append(
                    f"{section} | {title} | {label} | "
                    f"{header[i]} = {fmt(v, header[i])} {unit}".rstrip()
                )
        lines.append("| " + " | ".join(texts) + " |")

    lines += ["", "نکات قابل جست‌وجو:"] + facts
    return "\n".join(lines)


def main():
    df = pd.read_excel(EXCEL_PATH, header=None, dtype=str, keep_default_na=False)
    rows = [[str(v).strip() for v in r] for r in df.values.tolist()]

    blocks, counts = build_blocks(rows)

    # Accounting checks
    blank_rows = sum(1 for r in rows if not any(r))
    assert counts["blank"] == blank_rows, "تعداد ردیف‌های خالی با شمارش نمی‌خواند"
    assert sum(counts.values()) == len(rows), "شمارش ردیف‌ها با تعداد کل نمی‌خواند"
    data_in_blocks = sum(len(b["rows"]) for b in blocks)
    assert data_in_blocks == counts["data"], (
        f"ردیف‌های داده در بلوک‌ها ({data_in_blocks}) با شمارش ({counts['data']}) برابر نیست"
    )

    OUTPUT_JSON.write_text(json.dumps(blocks, ensure_ascii=False, indent=2), encoding="utf-8")
    OUTPUT_TEXT.write_text(
        "\n\n==========\n\n".join(block_to_text(b) for b in blocks), encoding="utf-8"
    )

    unlabeled = sum(1 for b in blocks for r in b["rows"] if r["unlabeled"])
    print(dict(counts))
    print(f"تعداد بلوک‌ها: {len(blocks)} | ردیف بدون برچسب: {unlabeled}")
    for b in blocks:
        print(f"{b['start_row']}-{b['end_row']} | {b['section']} | {b['title']} | داده: {len(b['rows'])}")
    print(f"فایل‌ها ساخته شدند: {OUTPUT_JSON} و {OUTPUT_TEXT}")


if __name__ == "__main__":
    main()
