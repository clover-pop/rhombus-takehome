import sys
from collections import Counter

import pandas as pd

if len(sys.argv) != 2:
    print("usage: python data-validation/compare_dates.py <output.csv>")
    sys.exit(1)

base = (pd.read_csv("datasets/baseline.csv", dtype=str, keep_default_na=False)
        .drop_duplicates("order_id").set_index("order_id"))
out = pd.read_csv(sys.argv[1], dtype=str, keep_default_na=False)

counts = {"ambiguous (day 12 or lower)": Counter(), "unambiguous (day above 12)": Counter()}
examples = []

for _, row in out.iterrows():
    oid = row["order_id"]
    if oid not in base.index:
        continue
    original = base.loc[oid, "order_date"]
    got = row["order_date"]
    y, m, d = original.split("-")

    swapped = y + "-" + d + "-" + m if int(d) <= 12 else None
    drifted = d + "/" + m + "/" + y

    if got == original:
        kind = "correct"
    elif swapped is not None and got == swapped:
        kind = "month and day swapped"
    elif got == drifted:
        kind = "left as DD/MM/YYYY text"
    else:
        kind = "other"

    group = "ambiguous (day 12 or lower)" if int(d) <= 12 else "unambiguous (day above 12)"
    counts[group][kind] += 1
    if kind != "correct" and len(examples) < 8:
        examples.append((oid, original, got, kind))

for group, c in counts.items():
    print(group + ":", dict(c) if c else "no rows")
print()
for oid, original, got, kind in examples:
    print("order", oid, "| original", original, "| output", got, "|", kind)
if not examples:
    print("every order_date matches the original")
