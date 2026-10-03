# Schema drift: new column (loyalty_tier added)

## What I changed
Added a loyalty_tier column (bronze, silver or gold) to the end of datasets/drift_new_column.csv. 160 rows, 10 columns, all other values unchanged. Uploaded to S3 as input/baseline.csv with data-validation/run_case.py and pressed Run manually.

## What I expected
The run would succeed and the extra column would pass through to GCS (10 columns in the output), with no warning. This prediction was made before running this case.

## What happened
The run succeeded (started 2:00:22 PM, completed 2:00:30 PM on 3 Oct, execution #16493). A file reached GCS with 122 rows and 10 columns, including loyalty_tier. The log warning counter stayed at 0. No message mentioned the new column.

## What the validator said
20 of 21 checks passed. The only failure was "schema: columns match: extra=['loyalty_tier']". Row count (122), duplicates, emails, countries, dates, amounts, quantities and values all matched the expected baseline output.

## What the logs said
Normal success entries. The "Applied 8 transformations" entry lists what each node did but never mentions loyalty_tier or any schema change. The only trace is indirect: every node reports output_column_count 10 (the baseline has 9), and the whitespace trimming node reports 800 cells modified (160 rows x 5), which likely means loyalty_tier was included in that step because its code loops over all text columns. Full log in evidence/new-column-transformations.json.

Other things noticed in this log:
- The "Impact" figures are not real change counts. The trim node reports 800 cells modified, but its code marks every text cell as modified without checking whether the value changed.
- The summary reports 555 affected rows for a 160-row file because per-step counts are added together.

## What the chatbot said
Not applicable: no error to give it.

## Did the fix work?
Not applicable.

## Severity
Medium. Nothing failed, so nobody is alerted, but a column that was never part of the pipeline reached the destination. If the new column held sensitive data, it would be exported without any review. Whether passing it through is the right behaviour depends on the customer, but the platform gave no signal that the schema had changed.

## Evidence
- evidence/new-column-logs.png
- evidence/new-column-success.txt
- datasets/outputs/drift_new_column.csv
