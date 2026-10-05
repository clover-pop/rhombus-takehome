# Semantic drift: dollars become cents (amount_usd x 100)

## What I changed
Multiplied every numeric amount_usd value by 100 in datasets/drift_semantic_cents.csv (124.47 became 12447). Column names, types and row count are unchanged (160 rows, 9 columns). The header still says amount_usd. Uploaded to S3 as input/baseline.csv with data-validation/run_case.py and pressed Run manually.

## What I expected
The run would succeed with 122 rows, with amounts in the thousands, no warning from Rhombus, and my validator failing the amount checks. This prediction was written before running this case.

## What happened
The run succeeded (6:26:26 PM to 6:26:34 PM on 3 Oct, execution #16548. A file reached GCS with 122 rows and all 9 columns. Every amount was 100 times the baseline value (for example order 1093: 124.47 became 12447.0).

## Did Rhombus notice?
No. The log shows "Pipeline completed successfully", no warnings, and the amount step reports it modified 136 cells like a normal run. There is no check on whether values are plausible.

## Did my validation catch it?
Yes, with 2 of 22 checks failing:
- "rule: amount numeric and plausible (5 to 500)": 122 bad, e.g. 12447.0, 44130.0, 2697.0
- "values match expected: amount_usd": 122 of 122 differ, e.g. 1093: 124.47 -> 12447.0
The checks that compare the output only with this run's own input all passed (row counts, order IDs, schema), because both sides were in cents. Detecting this drift needs a reference to compare against: the baseline or a plausible range.

## What the logs said
Nothing unusual. Full transformation log in evidence/semantic-cents-success.txt.

## What the chatbot said
Not applicable: no error to give it.

## Severity
High. Nothing failed and nothing warned, but every financial value in the output is wrong by a factor of 100, and it landed in the destination as a successful run. A customer relying on the pipeline would only find out when a downstream report looked wrong.

## Evidence
- evidence/semantic-cents-dashboard-success.png
- evidence/semantic-cents-logs.png
- evidence/semantic-cents-success.txt
- evidence/semantic-cents-validation.txt
- datasets/outputs/drift_semantic_cents.csv
