import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

# Fixed seed so same messy file is given every time
random.seed(42)

out_dir = Path(__file__).parent
num_rows = 150

first_names = ["Aarav", "Maya", "Liam", "Sofia", "Noah", "Priya", "Ethan", "Chloe",
               "Arjun", "Zoe", "Lucas", "Isla", "Kabir", "Ruby", "Oscar"]
last_names = ["Sharma", "Nguyen", "Smith", "Patel", "Brown", "Singh", "Wilson",
              "Lee", "Kumar", "Taylor", "Jones", "Gupta", "Evans", "Khan", "Clarke"]
countries = ["Australia", "United States", "India", "United Kingdom", "Canada"]
statuses = ["shipped", "pending", "cancelled", "delivered"]

# Messy versions of each country
bad_countries = {
    "Australia": "AUS",
    "United States": "USA",
    "India": "india",
    "United Kingdom": "U.K.",
    "Canada": "CANADA",
}

columns = ["order_id", "customer_name", "email", "signup_date", "order_date",
           "country", "amount_usd", "quantity", "status"]


def random_date():
    return date(2024, 1, 1) + timedelta(days=random.randint(0, 600))


# Build the clean rows first then mess them up afterwards
rows = []
for i in range(num_rows):
    first = random.choice(first_names)
    last = random.choice(last_names)
    rows.append({
        "order_id": 1000 + i,
        "customer_name": first + " " + last,
        "email": (first + "." + last + str(i) + "@example.com").lower(),
        "signup_date": random_date().isoformat(),
        "order_date": random_date().isoformat(),
        "country": random.choice(countries),
        "amount_usd": "%.2f" % random.uniform(5, 500),
        "quantity": random.randint(1, 10),
        "status": random.choice(statuses),
    })

# Shuffle the row positions and take a separate chunk for each defect so no row gets two problems at once
positions = list(range(num_rows))
random.shuffle(positions)

defects = {}  # defect name -> list of order_ids, used by the validation script later


def next_chunk(n):
    chunk = positions[:n]
    del positions[:n]
    return chunk


# Missing emails
chunk = next_chunk(8)
for i in chunk:
    rows[i]["email"] = ""
defects["missing_email"] = [rows[i]["order_id"] for i in chunk]

# Missing amounts
chunk = next_chunk(6)
for i in chunk:
    rows[i]["amount_usd"] = ""
defects["missing_amount"] = [rows[i]["order_id"] for i in chunk]

# Names in all caps or with extra spaces
chunk = next_chunk(12)
for n, i in enumerate(chunk):
    name = rows[i]["customer_name"]
    if n % 2 == 0:
        rows[i]["customer_name"] = name.upper()
    else:
        rows[i]["customer_name"] = "  " + name.lower() + "  "
defects["name_casing_or_spaces"] = [rows[i]["order_id"] for i in chunk]

# Country written differently
chunk = next_chunk(10)
for i in chunk:
    rows[i]["country"] = bad_countries[rows[i]["country"]]
defects["country_variants"] = [rows[i]["order_id"] for i in chunk]

# signup_date in other formats 
# order_date stays ISO so it can be used for the semantic drift tests later
chunk = next_chunk(15)
for n, i in enumerate(chunk):
    d = date.fromisoformat(rows[i]["signup_date"])
    if n % 2 == 0:
        rows[i]["signup_date"] = d.strftime("%d %b %Y")
    else:
        rows[i]["signup_date"] = d.strftime("%Y/%m/%d")
defects["signup_date_mixed_format"] = [rows[i]["order_id"] for i in chunk]

# Invalid emails
chunk = next_chunk(6)
for n, i in enumerate(chunk):
    if n % 2 == 0:
        rows[i]["email"] = "not-an-email"
    else:
        rows[i]["email"] = "john@@example.com"
defects["invalid_email"] = [rows[i]["order_id"] for i in chunk]

# Negative quantities
chunk = next_chunk(4)
for i in chunk:
    rows[i]["quantity"] = -abs(rows[i]["quantity"])
defects["negative_quantity"] = [rows[i]["order_id"] for i in chunk]

# Amount that isn't a number
chunk = next_chunk(4)
for i in chunk:
    rows[i]["amount_usd"] = "N/A"
defects["amount_not_a_number"] = [rows[i]["order_id"] for i in chunk]

# Duplicates copied from rows that haven't been messed with
chunk = next_chunk(10)
duplicates = [dict(rows[i]) for i in chunk]
defects["exact_duplicates"] = [rows[i]["order_id"] for i in chunk]

all_rows = rows + duplicates
random.shuffle(all_rows)

with open(out_dir / "baseline.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(all_rows)

summary = {
    "total_rows": len(all_rows),
    "unique_order_ids": num_rows,
    "defect_counts": {name: len(ids) for name, ids in defects.items()},
    "defect_order_ids": defects,
}
with open(out_dir / "baseline_defects.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print("wrote", len(all_rows), "rows to baseline.csv")
print(summary["defect_counts"])