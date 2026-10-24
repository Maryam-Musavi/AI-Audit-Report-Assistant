import json
import re
from itertools import combinations

TRANS = {ord(c): str(i) for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹")}
TRANS.update({ord(c): str(i) for i, c in enumerate("٠١٢٣٤٥٦٧٨٩")})

TOL = 0.5
MIN_ABS = 100
MAX_ITEMS = 15
LOOK_TOTALS = 60
SHOW_ROWS = list(range(96, 102)) + [112] + list(range(126, 133))
OUT = "check_totals2_report.txt"


def to_num(t):
    s = str(t).translate(TRANS).replace(",", "").replace("٬", "").strip()
    if not s:
        return None
    neg = (s.startswith("(") and s.endswith(")")) or s.startswith("-")
    s = s.strip("()-").strip()
    if not re.fullmatch(r"\d+(\.\d+)?", s):
        return None
    return -float(s) if neg else float(s)


def fa(t):
    return str(t).replace("ي", "ی").replace("ك", "ک").replace("ـ", "").strip()


def fmt(x):
    return f"{x:,.0f}"


def main():
    blocks = json.load(open("blocks.json", encoding="utf-8"))
    flat = []  # (block_idx, title, row_number, label, cells)
    for bi, b in enumerate(blocks):
        for r in b["rows"]:
            cells = r["cells"]
            flat.append((bi, fa(b.get("title", "")), r["row"],
                         fa(cells[0]) if cells else "", cells))

    def col(k, j):
        c = flat[k][4]
        return to_num(c[j]) if j < len(c) else None

    def prev_in_block(k, j):
        out = []
        for i in range(k - 1, -1, -1):
            if flat[i][0] != flat[k][0]:
                break
            v = col(i, j)
            if v is not None:
                out.append((i, v))
        return out[::-1]  # ترتیب صعودی

    # گذر ۱: جمع‌های بی‌عنوان (فقط داخل همان بلوک)
    totals = set()
    auto = {}
    for k, (bi, title, rown, label, cells) in enumerate(flat):
        if "جمع" in label:
            totals.add(k)
            continue
        if label:
            continue
        for j in range(1, len(cells)):
            v = col(k, j)
            if v is None or abs(v) < MIN_ABS:
                continue
            p = prev_in_block(k, j)
            hit = None
            for e in range(len(p) - 1, -1, -1):
                s = 0.0
                for st in range(e, max(-1, e - MAX_ITEMS), -1):
                    s += p[st][1]
                    if e - st >= 1 and abs(s - v) <= TOL:
                        hit = (flat[p[st][0]][2], flat[p[e][0]][2])
                        break
                if hit:
                    break
            if hit:
                totals.add(k)
                auto[k] = (j, hit)
                break

    lines = []
    ok = 0
    bad = 0

    for k in sorted(totals):
        bi, title, rown, label, cells = flat[k]
        name = label or "(بی‌عنوان)"
        col_msgs = []
        row_ok = False
        for j in range(1, len(cells)):
            v = col(k, j)
            if v is None or abs(v) < MIN_ABS:
                continue
            p = prev_in_block(k, j)
            # الف) از آخرین جمع تا همین‌جا
            seg = []
            for i, pv in reversed(p):
                if i in totals:
                    break
                seg.append((i, pv))
            seg = seg[::-1]
            cands = []  # (|diff|, diff, توضیح)
            if seg:
                s = sum(x[1] for x in seg)
                cands.append((abs(v - s), v - s,
                              f"از ردیف {flat[seg[0][0]][2]} تا {flat[seg[-1][0]][2]} (از آخرین جمع)"))
            # ب) پنجره پیوسته با کمترین اختلاف
            for e in range(len(p) - 1, max(-1, len(p) - 4), -1):
                s = 0.0
                for st in range(e, max(-1, e - MAX_ITEMS), -1):
                    s += p[st][1]
                    if e - st >= 1:
                        cands.append((abs(v - s), v - s,
                                      f"ردیف {flat[p[st][0]][2]} تا {flat[p[e][0]][2]}"))
            # ج) ترکیب چند جمع قبلی (بین بلوک‌ها)
            pt = []
            for i in range(k - 1, -1, -1):
                if flat[k][2] - flat[i][2] > LOOK_TOTALS:
                    break
                if i in totals:
                    tv = col(i, j)
                    if tv is not None:
                        pt.append((flat[i][2], tv))
            for n in (2, 3):
                for combo in combinations(pt, n):
                    s = sum(x[1] for x in combo)
                    cands.append((abs(v - s), v - s,
                                  "جمع‌های ردیف " + " + ".join(str(x[0]) for x in combo)))
            if not cands:
                continue
            best = min(cands, key=lambda c: c[0])
            if best[0] <= TOL:
                row_ok = True
                break
            col_msgs.append(f"   ستون {j}: مقدار {fmt(v)} | نزدیک‌ترین: {best[2]} | اختلاف {fmt(best[1])}")
        if row_ok:
            ok += 1
        else:
            bad += 1
            lines.append(f"ردیف {rown} «{name}» [{title}]")
            lines.extend(col_msgs or ["   (ستون عددی قابل مقایسه پیدا نشد)"])

    out = [f"جمع‌های تأییدشده: {ok} | بدون تطابق: {bad}", ""]
    out.append("--- بی‌عنوان ولی جمع (داخل بلوک):")
    for k, (j, (a, b)) in auto.items():
        out.append(f"ردیف {flat[k][2]}: = جمع ردیف {a} تا {b} (ستون {j})")
    out.append("")
    out.append("--- بدون تطابق (اختلاف کوچک = سلول مشکوک):")
    out.extend(lines)
    out.append("")
    out.append("--- ردیف‌های درخواستی:")
    for k, (bi, title, rown, label, cells) in enumerate(flat):
        if rown in SHOW_ROWS:
            out.append(f"{rown} | {label or '(بی‌عنوان)'} | " +
                       " | ".join(str(c) for c in cells[1:5]))

    text = "\n".join(out)
    print(text)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
