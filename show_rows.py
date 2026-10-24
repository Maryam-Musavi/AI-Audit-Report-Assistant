import json

WANT = [64, 68, 284, 287, 392, 407, 528]

blocks = json.load(open("blocks.json", encoding="utf-8"))
flat = [(b.get("title", ""), r) for b in blocks for r in b["rows"]]

for t, r in flat:
    if r["row"] in WANT:
        print("=" * 60)
        print("ردیف", r["row"], "| بلوک:", t[:60])
        i = flat.index((t, r))
        for t2, r2 in flat[max(0, i - 6): i + 1]:
            print(r2["row"], "|", " | ".join(str(c) for c in r2["cells"][:6]))
