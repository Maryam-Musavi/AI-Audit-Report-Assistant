import json
import re

FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"
TRANS = {ord(c): str(i) for i, c in enumerate(FA_DIGITS)}
TRANS.update({ord(c): str(i) for i, c in enumerate(AR_DIGITS)})

TOL = 0.5        # تلورانس گرد کردن (میلیون ریال)
MIN_ABS = 100    # عددهای کوچک‌تر (درصد، تعداد) بررسی نمی‌شوند
LOOK_BACK = 30   # تا چند ردیف قبل جستجو شود
MAX_ITEMS = 12   # حداکثر تعداد اقلام در یک جمع


def to_num(text):
    s = str(text).translate(TRANS).replace(",", "").replace("٬", "").strip()
    if not s:
        return None
    neg = (s.startswith("(") and s.endswith(")")) or s.startswith("-")
    s = s.strip("()-").strip()
    if not re.fullmatch(r"\d+(\.\d+)?", s):
        return None
    v = float(s)
    return -v if neg else v


def label_of(cells):
    first = cells[0] if cells else ""
    return first.replace("ي", "ی").replace("ك", "ک").strip()


def find_window(prev, target):
    # prev: لیست (شماره_ردیف, مقدار) به ترتیب
    n = len(prev)
    for j in range(n):
        s = 0.0
        for i in range(j, max(-1, j - MAX_ITEMS), -1):
            s += prev[i][1]
            if j - i + 1 >= 2 and abs(s - target) <= TOL:
                return prev[i][0], prev[j][0]
    return None


def main():
    with open("blocks.json", encoding="utf-8") as f:
        blocks = json.load(f)

    flat = []
    for b in blocks:
        for r in b["rows"]:
            flat.append((b.get("title", ""), r))

    ok, auto, failed = 0, [], []

    for k, (title, r) in enumerate(flat):
        label = label_of(r["cells"])
        hit = None

        for j in range(1, len(r["cells"])):
            v = to_num(r["cells"][j])
            if v is None or abs(v) < MIN_ABS:
                continue
            prev = []
            for _, pr in flat[max(0, k - LOOK_BACK):k]:
                if j < len(pr["cells"]):
                    pv = to_num(pr["cells"][j])
                    if pv is not None:
                        prev.append((pr["row"], pv))
            found = find_window(prev, v)
            if found:
                hit = (j, found)
                break

        if hit and not label:
            j, (a, b_) = hit
            auto.append(f"ردیف {r['row']} ({title}): = جمع ردیف {a} تا {b_} (ستون {j})")
        elif "جمع" in label:
            if hit:
                ok += 1
            else:
                failed.append(f"ردیف {r['row']} «{label}»: جمعی با ردیف‌های قبل برابر نشد")

    print(f"جمع‌های درست: {ok}")
    print("\n--- بی‌عنوان ولی جمع است (برچسب بزنیم):")
    for x in auto:
        print(x)
    print("\n--- برچسب «جمع» دارد ولی تطابق ندارد (بررسی در Excel):")
    for x in failed:
        print(x)


if __name__ == "__main__":
    main()
