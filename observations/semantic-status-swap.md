# Semantic drift: status labels swapped (shipped and delivered)

## What I changed
Exchanged the status values shipped and delivered in datasets/drift_semantic_status_swap.csv (every shipped became delivered and every delivered became shipped). pending and cancelled were left alone. Same columns and rows (160 rows, 9 columns), and every value is still a valid status. Uploaded to S3 as input/baseline.csv with data-validation/run_case.py and pressed Run manually.

## What I expected
The run would succeed and Rhombus would not notice, because every value is valid and the structure is unchanged. Only my validator, comparing against the expected output, would catch it. This prediction was written before running this case.

## What happened
The run succeeded (execution #16556) and a file reached GCS with 122 rows and 9 columns. 63 of the 122 rows had the wrong status (all the shipped and delivered rows). There were no warnings.

## Did Rhombus notice?
No. [Confirm from the log: normal success entries, warning counter 0.] I would not expect it to: nothing in the data is malformed, and detecting it would need a distribution comparison with earlier runs or business rules.

## Did my validation catch it?
Yes, with 1 of 22 checks failing: "values match expected: status: 63 of 122 differ, e.g. 1093: delivered -> shipped; 1057: shipped -> delivered". All other checks passed. Detecting this needs a reference to compare against.

## Severity
Medium. The wrong values land in the destination as a successful run and look completely normal. The platform could reasonably not detect it, so this is a gap in what the customer must monitor for themselves, more than a platform defect.

## Evidence
- evidence/semantic-status-success.txt
- evidence/semantic-status-logs.png
- evidence/semantic-status-dashboard-success.png
- evidence/semantic-status-validation.txt
- datasets/outputs/drift_semantic_status_swap.csv
