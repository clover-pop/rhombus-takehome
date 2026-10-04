import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

BASELINE = Path("datasets/baseline.csv")
RESULTS = Path("datasets/validation_results.jsonl")

EXPECTED_COLUMNS = ["order_id", "customer_name", "email", "signup_date",
                    "order_date", "country", "amount_usd", "quantity", "status"]
COUNTRY_MAP = {"AUS": "Australia", "USA": "United States", "india": "India",
               "U.K.": "United Kingdom", "CANADA": "Canada"}
ALLOWED_COUNTRIES = {"Australia", "United States", "India", "United Kingdom", "Canada"}
EMAIL_RE = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
ISO_RE = r"^\d{4}-\d{2}-\d{2}$"
# The baseline generator makes amounts between 5 and 500 dollars
AMOUNT_MIN, AMOUNT_MAX = 5, 500

results = []


def check(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    print("[" + status + "] " + name + (": " + detail if detail else ""))
    results.append({"check": name, "status": status, "detail": detail})


def skip(name, why):
    print("[SKIP] " + name + ": " + why)
    results.append({"check": name, "status": "SKIP", "detail": why})


def read(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def parse_date(s):
    for fmt in ("%Y-%m-%d", "%d %b %Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return "UNPARSEABLE"


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def expected_output():
    """What the nine cleaning rules should produce from the baseline file."""
    df = read(BASELINE).drop_duplicates().copy()
    for c in df.columns:
        df[c] = df[c].str.strip()
    df["customer_name"] = df["customer_name"].str.title()
    df["country"] = df["country"].replace(COUNTRY_MAP)
    df["signup_date"] = df["signup_date"].map(parse_date)
    keep = (df["email"].str.match(EMAIL_RE)
            & df["amount_usd"].map(is_number)
            & (df["quantity"].astype(int) >= 1))
    return df[keep]


def rule_check(out, name, column, is_ok):
    if column not in out.columns:
        skip(name, "column '" + column + "' not in output")
        return
    bad = out[~out[column].map(is_ok)]
    examples = bad[column].head(3).tolist()
    check(name, len(bad) == 0, "" if len(bad) == 0 else str(len(bad)) + " bad, e.g. " + str(examples))


def amount_ok(s):
    return is_number(s) and AMOUNT_MIN <= float(s) <= AMOUNT_MAX


def main():
    p = argparse.ArgumentParser()
    p.add_argument("case")
    p.add_argument("output")
    p.add_argument("--input", help="the dataset that was in S3 for this run")
    p.add_argument("--same-as", nargs="*", default=[], help="other outputs that should be identical")
    args = p.parse_args()

    out = read(args.output)
    golden = expected_output()
    print("case:", args.case, "| output rows:", len(out), "| expected rows:", len(golden))

    # 1. schema
    missing = [c for c in EXPECTED_COLUMNS if c not in out.columns]
    extra = [c for c in out.columns if c not in EXPECTED_COLUMNS]
    check("schema: columns match", not missing and not extra,
          "missing=" + str(missing) + " extra=" + str(extra))
    if not missing and not extra:
        check("schema: column order", list(out.columns) == EXPECTED_COLUMNS)

    # 2. row counts
    check("row count", len(out) == len(golden), "got " + str(len(out)) + ", expected " + str(len(golden)))
    if args.input:
        inp = read(args.input)
        check("output has no more rows than input", len(out) <= len(inp),
              "input " + str(len(inp)) + ", output " + str(len(out)))
        if "order_id" in out.columns and "order_id" in inp.columns:
            unknown = set(out["order_id"]) - set(inp["order_id"])
            check("every output order_id exists in input", not unknown, str(sorted(unknown)[:5]))

    # 3. cleaning rules applied (checks on the output alone)
    check("no duplicate rows", out.duplicated().sum() == 0, str(out.duplicated().sum()) + " duplicates")
    rule_check(out, "rule: valid emails only", "email", lambda s: bool(re.match(EMAIL_RE, s)))
    rule_check(out, "rule: country is a full name", "country", lambda s: s in ALLOWED_COUNTRIES)
    rule_check(out, "rule: signup_date is YYYY-MM-DD", "signup_date", lambda s: bool(re.match(ISO_RE, s)))
    rule_check(out, "rule: order_date is YYYY-MM-DD", "order_date", lambda s: bool(re.match(ISO_RE, s)))
    rule_check(out, "rule: amount numeric and plausible (5 to 500)", "amount_usd", amount_ok)
    rule_check(out, "rule: quantity is at least 1", "quantity", lambda s: s.lstrip("-").isdigit() and int(s) >= 1)
    rule_check(out, "rule: names trimmed and title case", "customer_name", lambda s: s == s.strip().title())

    # 4. values match what the baseline should have produced (catches silent changes)
    if "order_id" in out.columns:
        gone = set(golden["order_id"]) - set(out["order_id"])
        added = set(out["order_id"]) - set(golden["order_id"])
        check("same order_ids as expected", not gone and not added,
              "missing " + str(len(gone)) + ", unexpected " + str(len(added)))
        merged = golden.merge(out, on="order_id", suffixes=("_exp", "_out"))
        for col in EXPECTED_COLUMNS[1:]:
            if col not in out.columns:
                skip("values match expected: " + col, "column not in output")
                continue
            if col == "amount_usd":
                a = pd.to_numeric(merged[col + "_exp"], errors="coerce")
                b = pd.to_numeric(merged[col + "_out"], errors="coerce")
                differs = ~((a - b).abs() <= 0.005)
            else:
                differs = merged[col + "_exp"] != merged[col + "_out"]
            n = int(differs.sum())
            examples = [str(r["order_id"]) + ": " + str(r[col + "_exp"]) + " -> " + str(r[col + "_out"])
                        for _, r in merged[differs].head(3).iterrows()]
            check("values match expected: " + col, n == 0,
                  "" if n == 0 else str(n) + " of " + str(len(merged)) + " differ, e.g. " + "; ".join(examples))
    else:
        skip("values match expected", "no order_id column in output")

    # 5. determine
    for other in args.same_as:
        a = out.sort_values("order_id").reset_index(drop=True) if "order_id" in out.columns else out
        o = read(other)
        b = o.sort_values("order_id").reset_index(drop=True) if "order_id" in o.columns else o
        check("same content as " + Path(other).name, a.equals(b))

    fails = sum(1 for r in results if r["status"] == "FAIL")
    print("\nsummary:", len(results) - fails, "ok or skipped,", fails, "failed")
    with open(RESULTS, "a", encoding="utf-8") as f:
        f.write(json.dumps({"case": args.case, "output": args.output, "results": results}) + "\n")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
