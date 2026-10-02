import csv
from pathlib import Path

here = Path(__file__).parent

with open(here / "baseline.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    columns = reader.fieldnames
    base_rows = list(reader)


def copy_rows():
    return [dict(r) for r in base_rows]


def save(name, cols, data):
    with open(here / name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(data)
    print("wrote", name, "-", len(data), "rows,", len(cols), "columns")


# ---------- schema drift ----------

def drop_email(cols, data):
    # email is used by the pipeline's validity rule
    cols = [c for c in cols if c != "email"]
    for r in data:
        del r["email"]
    return cols, data


def rename_country(cols, data):
    cols = ["country_name" if c == "country" else c for c in cols]
    for r in data:
        r["country_name"] = r.pop("country")
    return cols, data


def amount_to_text(cols, data):
    # amount_usd turns from a plain number into text like "$124.47"
    for r in data:
        if r["amount_usd"] not in ("", "N/A"):
            r["amount_usd"] = "$" + r["amount_usd"]
    return cols, data


def add_loyalty_tier(cols, data):
    tiers = ["bronze", "silver", "gold"]
    cols = cols + ["loyalty_tier"]
    for i, r in enumerate(data):
        r["loyalty_tier"] = tiers[i % 3]
    return cols, data


save_jobs = [
    ("drift_drop_column.csv", [drop_email]),
    ("drift_rename_column.csv", [rename_country]),
    ("drift_type_change.csv", [amount_to_text]),
    ("drift_new_column.csv", [add_loyalty_tier]),
    ("drift_combined_schema.csv", [drop_email, rename_country, amount_to_text, add_loyalty_tier]),
]

for name, steps in save_jobs:
    cols, data = list(columns), copy_rows()
    for step in steps:
        cols, data = step(cols, data)
    save(name, cols, data)


# ---------- semantic drift (same columns, different meaning) ----------

# 1. dollars become cents, header still says amount_usd
data = copy_rows()
for r in data:
    if r["amount_usd"] not in ("", "N/A"):
        r["amount_usd"] = str(int(round(float(r["amount_usd"]) * 100)))
save("drift_semantic_cents.csv", list(columns), data)

# 2. order_date goes from YYYY-MM-DD to DD/MM/YYYY (day first so ambiguous when day <= 12)
data = copy_rows()
for r in data:
    y, m, d = r["order_date"].split("-")
    r["order_date"] = d + "/" + m + "/" + y
save("drift_semantic_dates_ddmm.csv", list(columns), data)

# 3. status meanings swapped (shipped <-> delivered), nothing looks wrong structurally
data = copy_rows()
swap = {"shipped": "delivered", "delivered": "shipped"}
for r in data:
    r["status"] = swap.get(r["status"], r["status"])
save("drift_semantic_status_swap.csv", list(columns), data)