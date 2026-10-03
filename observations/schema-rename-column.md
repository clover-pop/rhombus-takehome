# Schema drift: renamed column (country to country_name)

## What I changed
Renamed the country column to country_name in datasets/drift_rename_column.csv (160 rows, 9 columns, same data). Uploaded to S3 as input/baseline.csv with data-validation/run_case.py and pressed Run manually.

## What I expected
I expected the pipeline to stop at the first node that uses the country column (the country standardisation step) instead of guessing that country_name was the same column.

## What happened
The run failed at 11:13:35 AM on 3 Oct (Sydney), execution #16474. The dashboard marked it as a failure. No output file reached GCS.
On the canvas, the node orders_country_std went red(shown on the Canvas as Custom llm_node_2) the nodes before it succeeded and nothing after it ran.

## What the logs said
Pipeline failed at orders_country_std: LLM execution failed (code_sha=b1bde1b05f09): Column 'country' does not exist in input_df_1. Full text in evidence/rename-column-error.txt.
- Clear: it names the node and the missing column.
- Not helpful: it does not mention that a similarly named column (country_name) exists.
- Same inconsistency as the dropped column case: a "Pipeline execution completed successfully" line is logged at the same second as the failure (2 of 2 failed runs so far).

## What the chatbot said


## Did the fix work?


## Severity
Low to medium. The pipeline stopped and wrote nothing, so no bad data reached GCS. The error does not help locate the renamed column, and the contradictory success message is confusing.

## Evidence
- evidence/rename-column-logs.png
- evidence/rename-column-error.txt
- evidence/rename-column-dashboard-failure.png
