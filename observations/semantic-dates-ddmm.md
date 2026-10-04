# Semantic drift: order_date changes from YYYY-MM-DD to DD/MM/YYYY

## What I changed
Rewrote every order_date in datasets/drift_semantic_dates_ddmm.csv from YYYY-MM-DD to day-first DD/MM/YYYY text (2024-08-02 became 02/08/2024). Same columns, same rows (160, 9 columns). Uploaded to S3 as input/baseline.csv with data-validation/run_case.py and pressed Run manually.

## What I expected
Rhombus parses dates when it loads a file (seen with signup_date in the baseline). Days above 12 can only be day-first, so those would be read correctly. For ambiguous dates (day 12 or lower, roughly 40% of rows) I expected some to be read month-first and silently swapped, with no warning. This prediction was written before running this case.

## What happened
The run succeeded (execution #16555) and a file reached GCS with 122 rows and 9 columns. order_date was converted to ISO format, but not always correctly:
- Ambiguous dates (day 12 or lower): 49 rows, 42 had month and day swapped (86%), 7 were unchanged (of which 7 have day equal to month, so a swap changes nothing).
- Unambiguous dates (day above 12): 73 rows, all correct.
Examples: order 1008: original 2024-08-02, output 2024-02-08. Order 1094: 2025-05-02 became 2025-02-05. Order 1131: 2024-12-05 became 2024-05-12.

## Did Rhombus notice?
No. The log shows a normal success, no warnings, and none of the eight pipeline steps touches order_date, which suggests the conversion happens when the file is loaded, before the pipeline runs. The pattern is consistent with slash dates being read month-first (US style) and falling back to day-first only when month-first is impossible. I have not seen the parser itself, so this is inferred.

## Did my validation catch it?
Yes, with 1 of 22 checks failing: "values match expected: order_date: 42 of 122 differ". The format check "order_date is YYYY-MM-DD" passed, because the swapped dates are still valid ISO dates. Detecting this needs a comparison against known-good values, not only format rules. data-validation/compare_dates.py breaks the errors down by ambiguous and unambiguous dates.

## Severity
High. The data looks valid, passes format checks, and lands in the destination as a successful run, but about a third of the rows (42 of 122) now have a wrong date. Nothing would flag it unless someone compared against the source.

## Evidence
- evidence/semantic-dates-validation.txt
- evidence/semantic-dates-comparison.txt
- evidence/semantic-dates-success.txt
- evidence/semantic-dates-logs.png
- evidence/semantic-dates-dashboard-success.png
- datasets/outputs/drift_semantic_dates_ddmm.csv
