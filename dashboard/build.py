"""Builds docs/index.html: a single-page dashboard made from the files in this repo.
(The page itself, with its styles and scripts, is dashboard/template.html.)

Run from the repo root:
    python ui-tests/export_executions.py     (refreshes datasets/rhombus_executions.csv from the Rhombus dashboard)
    python dashboard/build.py

Everything measured (runs, durations, outputs, validator results) is read from datasets/.
The heat map ratings are my own judgements from the write-ups in observations/. They live in HEATMAP below,
so anyone can read them, disagree with them and change them.
"""
import csv
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path.cwd()
REPO_URL = "https://github.com/clover-pop/rhombus-takehome"
SYDNEY = ZoneInfo("Australia/Sydney")
OUT_HTML = ROOT / "docs" / "index.html"
UI_RUNS_FROM = 16628  # unclaimed executions from here on come from the Playwright Run test


def blob(path):
    return REPO_URL + "/blob/main/" + path


# ---------------------------------------------------------------------------------------------
# Which executions belong to which scenario.
# Harness runs (data-validation/run_case.py) are matched automatically: each one is the first
# execution that started within 10 minutes after its upload to S3 (datasets/run_records.jsonl).
# Runs started by hand with no harness are listed in "manual".
# ---------------------------------------------------------------------------------------------
SCENARIOS = [
    dict(id="baseline_original", label="Baseline, original pipeline", group="baseline",
         evidence="docs/run-log.md",
         cases=["baseline_run1", "baseline_run2", "baseline_run3"],
         manual=[16380, 16381, 16382, 16383, 16419], validate="datasets/outputs/baseline_run1.csv"),
    dict(id="baseline_edited", label="Baseline, after the chatbot's edit", group="baseline",
         evidence="observations/schema-drop-column.md",
         cases=["baseline_after_chatbot_fix", "baseline_edit_run2", "baseline_edit_run3"], manual=[],
         validate="datasets/outputs/baseline_after_chatbot_fix.csv"),
    dict(id="drop_column", label="Dropped column (email)", group="schema",
         evidence="observations/schema-drop-column.md",
         cases=["drift_drop_column", "chatbot_drop_after_fix"], manual=[], validate=None),
    dict(id="rename_column", label="Renamed column (country)", group="schema",
         evidence="observations/schema-rename-column.md",
         cases=["drift_rename_column", "chatbot_rename_check"], manual=[], validate=None),
    dict(id="type_change", label="Type change (amount as text)", group="schema",
         evidence="observations/schema-type-change.md",
         cases=["drift_type_change"], manual=[], validate=None),
    dict(id="new_column", label="New column (loyalty_tier)", group="schema",
         evidence="observations/schema-new-column.md",
         cases=["drift_new_column"], manual=[], validate="datasets/outputs/drift_new_column.csv"),
    dict(id="combined", label="All four schema changes", group="schema",
         evidence="observations/schema-combined.md",
         cases=["drift_combined_schema"], manual=[], validate=None),
    dict(id="cents", label="Dollars become cents", group="semantic",
         evidence="observations/semantic-cents.md",
         cases=["drift_semantic_cents"], manual=[], validate="datasets/outputs/drift_semantic_cents.csv"),
    dict(id="dates", label="Dates turn day-first", group="semantic",
         evidence="observations/semantic-dates-ddmm.md",
         cases=["drift_semantic_dates_ddmm"], manual=[], validate="datasets/outputs/drift_semantic_dates_ddmm.csv"),
    dict(id="status_swap", label="Status labels swapped", group="semantic",
         evidence="observations/semantic-status-swap.md",
         cases=["drift_semantic_status_swap"], manual=[], validate="datasets/outputs/drift_semantic_status_swap.csv"),
    dict(id="cleared", label="Failed: nodes had lost their settings", group="other",
         evidence="observations/usability-notes.txt", cases=[], manual=[], validate=None),
    dict(id="ui_runs", label="Run button: UI test and manual re-runs", group="other",
         evidence="ui-tests/test_run_pipeline.py", cases=[], manual=[], validate=None),
    dict(id="unplanned", label="Unplanned runs", group="other",
         evidence="observations/usability-notes.txt", cases=[], manual=[16491, 16492, 16557], validate=None),
    dict(id="setup", label="First runs while building", group="other",
         evidence="docs/pipeline-prompt.md", cases=[], manual=[16345, 16373, 16374], validate=None),
]

# ---------------------------------------------------------------------------------------------
# Heat map: my ratings, one cell per drift case and question. level is good, partial, bad or na.
# ---------------------------------------------------------------------------------------------
HEAT_COLUMNS = [
    dict(id="noticed", label="Did Rhombus react?", hint="Did the run stop or warn when the data changed?"),
    dict(id="clarity", label="Did the error explain it?", hint="When it stopped, did the message point at the cause?"),
    dict(id="safe", label="Was GCS kept clean?", hint="Did only correct data reach the destination?"),
    dict(id="validator", label="Did my validator catch it?", hint="The checks in data-validation/validate.py."),
    dict(id="chatbot", label="Did the chatbot diagnose it?", hint="The built-in assistant, asked from the error with no hints."),
]


def cell(level, short, detail):
    return dict(level=level, short=short, detail=detail)


HEATMAP = [
    ("drop_column", [
        cell("good", "Stopped", "The run stopped at orders_valid_email and wrote nothing."),
        cell("good", "Named the column", "The error names the node and the missing column (email)."),
        cell("good", "Nothing written", "No output file reached GCS."),
        cell("na", "No output", "Nothing reached GCS, so there was nothing to validate."),
        cell("bad", "Wrong", "It blamed a stray space in a header. The column had been deleted. Its one-line edit left the error unchanged."),
    ]),
    ("rename_column", [
        cell("good", "Stopped", "The run stopped at orders_country_std and wrote nothing."),
        cell("partial", "Half the story", "It says country is missing but not that country_name replaced it."),
        cell("good", "Nothing written", "No output file reached GCS."),
        cell("na", "No output", "Nothing reached GCS, so there was nothing to validate."),
        cell("partial", "Partly right", "The second attempt found the country_name mismatch, then invented an edit history. The first attempt, with old chat history left in, was wrong."),
    ]),
    ("type_change", [
        cell("good", "Stopped", "The run stopped at orders_valid_amount and wrote nothing."),
        cell("bad", "Misleading", "The message is name 'TypeError' is not defined. It says nothing about amounts or dollar signs."),
        cell("good", "Nothing written", "No output file reached GCS."),
        cell("na", "No output", "Nothing reached GCS, so there was nothing to validate."),
        cell("partial", "Partly right", "It found the TypeError scope problem but missed the data change that triggered it."),
    ]),
    ("new_column", [
        cell("bad", "No warning", "The run completed as normal. Nothing said the schema had changed."),
        cell("na", "Nothing to explain", "There was no error."),
        cell("partial", "Extra column kept", "loyalty_tier reached GCS. The values are fine, but nobody reviewed the new column."),
        cell("good", "Caught", "The schema check flagged the extra column. The other checks passed."),
        cell("na", "Not asked", "There was no error to give it."),
    ]),
    ("combined", [
        cell("good", "Stopped", "The run stopped at the first node that needs a missing column."),
        cell("partial", "First problem only", "Only the country column is mentioned. The other three changes are not."),
        cell("good", "Nothing written", "No output file reached GCS."),
        cell("na", "No output", "Nothing reached GCS, so there was nothing to validate."),
        cell("bad", "Wrong", "It blamed header casing (Country against country) and named none of the four real changes."),
    ]),
    ("cents", [
        cell("bad", "No warning", "The run completed as normal. Nothing questioned amounts that were 100 times larger."),
        cell("na", "Nothing to explain", "There was no error."),
        cell("bad", "Wrong data", "Every amount reached GCS 100 times too large."),
        cell("good", "Caught", "The plausible-range check and the values-against-expected check failed. Checks that only compare with this run's own input passed."),
        cell("na", "Not asked", "There was no error to give it."),
    ]),
    ("dates", [
        cell("bad", "No warning", "The run completed as normal with valid-looking dates."),
        cell("na", "Nothing to explain", "There was no error."),
        cell("bad", "Wrong data", "42 of 49 ambiguous dates (day 12 or lower) came out with day and month swapped."),
        cell("good", "Caught", "The values-against-expected check failed. The date format check still passed."),
        cell("na", "Not asked", "There was no error to give it."),
    ]),
    ("status_swap", [
        cell("bad", "No warning", "The run completed as normal. Every value is a valid status, so a platform could fairly miss this."),
        cell("na", "Nothing to explain", "There was no error."),
        cell("bad", "Wrong data", "63 of 122 rows had shipped and delivered exchanged."),
        cell("good", "Caught", "The values-against-expected check failed. Every other check passed."),
        cell("na", "Not asked", "There was no error to give it."),
    ]),
]

CONSISTENCY_GROUPS = [
    ("Original pipeline, same baseline file, three runs", ["baseline_run1", "baseline_run2", "baseline_run3"]),
    ("After the chatbot's one-line edit, same baseline file, one run",
     ["baseline_after_chatbot_fix", "baseline_edit_run2", "baseline_edit_run3"]),
    ("Latest run started by the UI test (edited pipeline)", ["ui_run_test"]),
]

EXTRA_PICKER = ["drift_semantic_cents", "drift_semantic_dates_ddmm", "drift_semantic_status_swap"]

# Copied from the error text in the Rhombus logs (evidence is in observations/evidence/).
FAILURE_FINGERPRINTS = [
    dict(node="orders_valid_email", sha="5f40b5e32988", seen=["Dropped column run", "Re-run after the chatbot's edit"]),
    dict(node="orders_country_std", sha="b1bde1b05f09",
         seen=["Renamed column run", "All four changes run", "Re-run after the chatbot's edit"]),
    dict(node="orders_valid_amount", sha="214424711c89", seen=["Type change run"]),
]

RESOURCE_NOTES = [
    "Every run in this project was started by hand. The schedule never produced one.",
]


# ---------------------------------------------------------------------------------------------
def load_executions():
    path = ROOT / "datasets" / "rhombus_executions.csv"
    if not path.exists():
        sys.exit("datasets/rhombus_executions.csv is missing. Run: python ui-tests/export_executions.py")
    found = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            stamp = r["started"].replace("\u202f", " ").replace("\u00a0", " ").strip()
            started = datetime.strptime(stamp, "%m/%d/%Y, %I:%M:%S %p").replace(tzinfo=SYDNEY)
            nodes_text = r["nodes"].strip()
            nodes = int(nodes_text.split()[0]) if nodes_text[:1].isdigit() else 0
            status = r["status"].strip()
            outcome = "fail" if status == "Failure" else ("empty" if nodes == 0 else "ok")
            found[int(r["number"])] = dict(
                number=int(r["number"]), trigger=r["trigger"], status=status, nodes=nodes,
                duration_s=float(r["duration_s"]), started_dt=started, outcome=outcome,
                started=started.strftime("%d %b %H:%M"))
    return found


def load_jsonl(path):
    rows = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def assign_executions(executions, records):
    case_to_scenario = {c: s["id"] for s in SCENARIOS for c in s["cases"]}
    claimed = {}

    def claim(number, scenario_id, label):
        if number not in executions:
            print("warning: execution #" + str(number) + " is not in rhombus_executions.csv (" + label + ")")
        elif number in claimed:
            print("warning: execution #" + str(number) + " is claimed twice, keeping the first")
        else:
            claimed[number] = (scenario_id, label)

    for s in SCENARIOS:
        for number in s["manual"]:
            claim(number, s["id"], "started by hand")
    ordered = sorted(executions)
    for rec in records:
        sid = case_to_scenario.get(rec["case"])
        if not sid:
            print("note: run record '" + rec["case"] + "' is not part of any scenario, skipped")
            continue
        uploaded = datetime.fromisoformat(rec["uploaded_at"])
        for number in ordered:
            if number in claimed:
                continue
            gap = (executions[number]["started_dt"] - uploaded).total_seconds()
            if 0 <= gap <= 600:
                claim(number, sid, rec["case"])
                break
        else:
            print("warning: no execution found after the upload for case " + rec["case"])
    for number in ordered:
        if number not in claimed:
            if number >= UI_RUNS_FROM:
                failed = executions[number]["outcome"] == "fail" and number >= 16826
                claimed[number] = ("cleared", "node settings lost") if failed else ("ui_runs", "Run test or manual")
            else:
                print("note: execution #" + str(number) + " is not mapped to a scenario, filed under unplanned runs")
                claimed[number] = ("unplanned", "not mapped")
    return claimed


def validator_summary(results, output_path):
    if not output_path:
        return None
    match = [r for r in results if Path(r.get("output", "")).as_posix() == output_path]
    if not match:
        return None
    checks = match[-1]["results"]
    failed = [dict(name=c["check"], detail=c.get("detail", "")) for c in checks if c["status"] == "FAIL"]
    return dict(checks=len(checks), failed=failed)


def read_output(name):
    path = ROOT / "datasets" / "outputs" / (name + ".csv")
    if not path.exists():
        return None
    raw = path.read_bytes()
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    header, body = rows[0], rows[1:]
    content = "\n".join(sorted(",".join(r) for r in body))
    return dict(name=name, header=header, rows=body, kb=round(len(raw) / 1024, 1),
                sha_file=hashlib.sha256(raw).hexdigest(),
                sha_content=hashlib.sha256((",".join(header) + "\n" + content).encode()).hexdigest())


def build_consistency():
    groups, data_rows, columns = [], {}, None
    for title, names in CONSISTENCY_GROUPS:
        runs = []
        for n in names:
            info = read_output(n)
            if not info:
                print("note: datasets/outputs/" + n + ".csv not found, left out of the consistency section")
                continue
            columns = columns or info["header"]
            if info["header"] != columns:
                print("note: " + n + " has different columns, left out of the comparison picker")
            else:
                data_rows[n] = info["rows"]
            runs.append(dict(name=n, rows=len(info["rows"]), columns=len(info["header"]), kb=info["kb"],
                             sha_file=info["sha_file"][:12], sha_content=info["sha_content"][:12],
                             full_file=info["sha_file"], full_content=info["sha_content"]))
        if not runs:
            continue
        if len({r["full_file"] for r in runs}) == 1:
            verdict = "identical" if len(runs) > 1 else "single"
        elif len({r["full_content"] for r in runs}) == 1:
            verdict = "same_content"
        else:
            verdict = "different"
        groups.append(dict(title=title, runs=runs, verdict=verdict))
    for n in EXTRA_PICKER:
        info = read_output(n)
        if info and info["header"] == columns:
            data_rows[n] = info["rows"]

    cross = None
    if len(groups) >= 2:
        a, b = groups[0]["runs"][0], groups[1]["runs"][0]
        cross = dict(a=a["name"], b=b["name"], same=a["full_content"] == b["full_content"])
    for g in groups:
        for r in g["runs"]:
            del r["full_file"], r["full_content"]
    return dict(groups=groups, cross=cross, data=dict(columns=columns or [], files=data_rows))


def main():
    executions = load_executions()
    records = load_jsonl(ROOT / "datasets" / "run_records.jsonl")
    results = load_jsonl(ROOT / "datasets" / "validation_results.jsonl")
    claimed = assign_executions(executions, records)

    scenarios = []
    for s in SCENARIOS:
        runs = []
        for number, (sid, label) in sorted(claimed.items()):
            if sid != s["id"]:
                continue
            e = executions[number]
            runs.append(dict(number=number, started=e["started"], duration_s=e["duration_s"], nodes=e["nodes"],
                             status=e["status"], outcome=e["outcome"], trigger=e["trigger"], case=label))
        out_info = None
        if s["validate"]:
            info = read_output(Path(s["validate"]).stem)
            if info:
                out_info = dict(file=s["validate"], rows=len(info["rows"]), kb=info["kb"])
        scenarios.append(dict(
            id=s["id"], label=s["label"], group=s["group"], evidence=blob(s["evidence"]), executions=runs,
            validator=validator_summary(results, s["validate"]), output=out_info))

    known = {s["id"] for s in scenarios}
    heat_rows = []
    for sid, cells in HEATMAP:
        assert sid in known and len(cells) == len(HEAT_COLUMNS), "heat map row " + sid + " is malformed"
        label = next(s["label"] for s in scenarios if s["id"] == sid)
        heat_rows.append(dict(scenario=sid, label=label, cells=cells))

    all_runs = [r for s in scenarios for r in s["executions"]]
    payload = dict(
        generated=datetime.now(SYDNEY).strftime("%d %b %Y"),
        repo=REPO_URL,
        totals=dict(executions=len(all_runs),
                    first=min(all_runs, key=lambda r: r["number"])["started"] if all_runs else "",
                    last=max(all_runs, key=lambda r: r["number"])["started"] if all_runs else ""),
        scenarios=scenarios,
        heat=dict(columns=HEAT_COLUMNS, rows=heat_rows),
        consistency=build_consistency(),
        fingerprints=FAILURE_FINGERPRINTS,
        notes=RESOURCE_NOTES,
    )
    text = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    OUT_HTML.parent.mkdir(exist_ok=True)
    template = (Path(__file__).resolve().parent / "template.html").read_text(encoding="utf-8")
    OUT_HTML.write_text(template.replace("__DATA__", text), encoding="utf-8")
    print("wrote", OUT_HTML, "with", len(all_runs), "executions in", len(scenarios), "scenarios")


if __name__ == "__main__":
    main()
