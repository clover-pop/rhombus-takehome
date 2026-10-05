# Rhombus AI take-home: S3 to GCS pipeline, drift testing and validation

I built a cleaning pipeline in Rhombus AI with the AI builder only (S3 source, 9 cleaning steps, Google Cloud Storage destination, scheduled), then broke its input on purpose to see how the platform responds. This repo has the UI tests, API tests, a data validation script, every dataset, and one write-up per drift case.

**Important deviation:** the schedule never fired (details below), so every run, including the baseline, was started manually with the play button. I document this as a finding and did not hide it.

## 1. Setup and how to run

Requirements: Python 3.9+, an AWS bucket (source), a Google Cloud bucket and service account key (destination), and a Rhombus AI account.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
cp .env.example .env     # then fill in the values (the real .env is git-ignored)
```

`.env` holds: `S3_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`, `GCS_BUCKET`, `GOOGLE_APPLICATION_CREDENTIALS` (path to the service account key), `RHOMBUS_TOKEN` (a Bearer token copied from the browser's network tab) and `RHOMBUS_PROJECT_ID`.

The tests run against my own Rhombus account and project. To run them on another account, create the pipeline from `docs/pipeline-prompt.md`, then set the values above.

**Pipeline data:** `python datasets/generate_baseline.py` rebuilds the messy baseline (160 rows, 9 defect types, with a list of exactly which rows are affected). `python datasets/make_drifts.py` writes every drifted version.

**API tests** (`/api-tests/`): `python -m pytest api-tests -v -rx`. They need `RHOMBUS_TOKEN`. The token expires; if the run says it was rejected, copy a fresh one from the browser (DevTools, Network, any request to api.rhombusai.com, Authorization header) into `.env`.

**UI tests** (`/ui-tests/`, Playwright): log in once, then run.
1. Start Chrome with `--remote-debugging-port=9222 --user-data-dir=$HOME/chrome-rhombus-profile`, log in to Rhombus, open the project.
2. `python ui-tests/save_login_cdp.py` saves the session to `secrets/auth_state.json` (git-ignored).
3. `python -m pytest ui-tests -v -rx`. One test presses Run and takes about a minute; it requires the baseline file to be in S3.

No test uses a fixed sleep: they use Playwright's auto-waiting assertions, a handler for the "Ad Blocker Detected" modal, and bounded polling of GCS and the dashboard. `ui-tests/export_executions.py` reads the dashboard's execution table into `datasets/rhombus_executions.csv`.

**Data validation** (`/data-validation/`):
```bash
python data-validation/run_case.py <case_name> <dataset.csv>     # uploads to S3, you press Run, it downloads the new GCS output
python data-validation/validate.py <case_name> <output.csv> --input <dataset.csv> [--same-as other_outputs.csv]
python data-validation/compare_dates.py <output.csv>             # breaks date errors down by ambiguous and unambiguous
```
`validate.py` checks: schema (columns and order), row count, no duplicates, valid emails, full country names, ISO dates, plausible amounts (5 to 500), quantity of at least 1, trimmed title-case names, every value against what the nine rules should produce from the baseline, and determinism (`--same-as`). It exits with code 1 if any check fails. `run_case.py` always restores the baseline in S3 afterwards.

Latest test runs: `observations/evidence/api-tests-run-final.txt` (30 passed, 5 expected failures) and `observations/evidence/ui-tests-run-final.txt` (22 passed, 3 expected failures). Expected failures are marked `xfail` with the reason, and each one documents a bug I found.

## 2. Observations summary

All runs are in `docs/run-log.md` (with Rhombus execution numbers). Baseline: three runs gave identical content once sorted by order id (122 rows, all checks passed).

| Drift case | Change | Pipeline stopped? | Chatbot fix worked? | Severity | Details |
|---|---|---|---|---|---|
| Drop column | email removed | Yes, at orders_valid_email, nothing reached GCS | No: diagnosis wrong, edit did not stop the error | Low | [schema-drop-column](observations/schema-drop-column.md) |
| Rename column | country to country_name | Yes, at orders_country_std | Not applied (diagnosis partly right on the second try, with an invented explanation) | Low to medium | [schema-rename-column](observations/schema-rename-column.md) |
| Change type | amount_usd turned into text ("$124.47") | Yes, at orders_valid_amount, with "name 'TypeError' is not defined" | Not tested (diagnosis partly right) | Medium | [schema-type-change](observations/schema-type-change.md) |
| New column | loyalty_tier added | No: ran, extra column reached GCS, no warning | Not applicable | Medium | [schema-new-column](observations/schema-new-column.md) |
| All four combined | all of the above | Yes, at the first node that needs a missing column; the other changes were not mentioned | Not applicable (diagnosis wrong) | Medium | [schema-combined](observations/schema-combined.md) |
| Dollars to cents | amount_usd x 100 | No: ran, no warning | Not applicable | High | [semantic-cents](observations/semantic-cents.md) |
| Dates day-first | order_date as DD/MM/YYYY | No: ran, 42 of 49 ambiguous dates came out with month and day swapped | Not applicable | High | [semantic-dates-ddmm](observations/semantic-dates-ddmm.md) |
| Status labels swapped | shipped and delivered exchanged | No: ran, no warning (63 of 122 rows wrong) | Not applicable | Medium | [semantic-status-swap](observations/semantic-status-swap.md) |

Other write-ups: [baseline date handling](observations/baseline-date-handling.md), [baseline amount formatting](observations/baseline-amount-format.md), [schedule never fires](observations/schedule-not-triggering.md), [API returns 500 on invalid paging](observations/api-500-on-invalid-paging.md).

**Top three findings**
1. **Changes in meaning pass silently.** Cents (every amount 100x), day-first dates (42 of 49 ambiguous dates swapped) and swapped status labels all ran as normal successes, with no warning and no sign in the logs. Only checks against a reference (the baseline's expected values) caught them; format checks and input-versus-output checks passed.
2. **Scheduled runs never fire, and nothing says so.** The schedule shows "Active", yet over a day later the backend reports `last_run_at: null` and a `next_run_at` in the past, with no executions, no failure email and no skipped runs (captured from the schedules API). Every other run in this project was manual.
3. **The chatbot diagnoses from the pipeline, not the data.** In four failed cases it was never fully right: wrong twice, partly right twice. It edited the pipeline automatically, stated guesses as facts, and claimed a fix would work when it did not (the dropped-column error was unchanged after its edit). For the combined case, the backend's chat history shows no dataset attached and no data-reading tool used. Error messages are clear when the generated code happens to contain a guard (missing column) and confusing when it does not (the TypeError case).

Also found: the API returns HTTP 500 for zero or negative paging values; the log prints "completed successfully" after failed runs; two runs that executed nothing are recorded as successes; and the log's "Impact" figures are not real change counts.

## 3. Usability feedback

What helped most: the AI builder turned one detailed prompt into a working 9-step pipeline in under a minute, and its row counts matched the ones I calculated independently. Runs are fast (5 to 8 seconds), the dashboard is clear, and when a column was missing the error named the node and the column. Having the schedule and executions views in the same app made it easy to compare what should have happened with what did.

What was frustrating: a schedule that says "Active" but never runs, with a blank next-run time and no alert; the chatbot guessing and then editing a working pipeline without confirmation, with no way to duplicate the project or roll back; credits (50 free; one chatbot question cost 6, the cost is not shown before sending, and I was down to 3 credits after two days of use); a success message logged after failures; an "Ad Blocker Detected" pop-up in a browser with no ad blocker; and small things like "Rhombo" in the interface. To make it more useful, I would show the credit cost before sending, warn when a run's columns or types differ from the last successful run, let the chatbot read a data sample and ask before editing, and flag any schedule that misses its run time. Full notes are in `observations/usability-notes.txt`.

## 4. Demo video

TODO-REPLACE: add the link here.

## 5. Limitations and trade-offs

- **Manual runs only.** The schedule never produced a run (finding 2), so I triggered every run with the play button. The execution history shows only manual triggers.
- **Chatbot fixes:** I tested the fix for one of the four failed cases (dropped column). For the others I recorded its diagnosis only, because applying fixes would change the pipeline under test. I cleared the AI Builder chat history before the second renamed-column attempt and before the combined-case question; each observation file says what conditions applied to that question.
- **Fixture design:** the baseline is generated, with a file of exactly which rows have which defect, so validation compares against ground truth.
- **Tests change very little.** The Run test starts one pipeline run and writes one output file. The S3 empty-bucket test submits the form with no bucket and asserts that no source is created. The dialog tests are cancelled without saving, and no test deletes anything. I did not probe other accounts' resources.
- The UI tests check every stage of the journey on the pipeline I built with the AI builder (S3 source connected to my bucket, the 10-node AI-built pipeline, the GCS destination, the schedule, and a full Run whose output is validated), but they do not rebuild the pipeline from scratch. The build itself was done once, manually, by typing the prompt recorded in docs/pipeline-prompt.md into the AI builder.
- The optional bonus dashboard is not included.
