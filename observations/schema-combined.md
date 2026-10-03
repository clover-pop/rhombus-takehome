# Schema drift: all four changes together

## What I changed
datasets/drift_combined_schema.csv has all four schema changes at once: email dropped, country renamed to country_name, amount_usd turned into text ("$124.47"), and a new loyalty_tier column added. Uploaded to S3 as input/baseline.csv with data-validation/run_case.py and pressed Run manually.

## What I expected
The run would fail at orders_country_std, the first node in the chain that needs a missing column, and the error would mention only the country column, not the other changes. This prediction was written before running this case.

## What happened
The run failed at 6:17:08 PM on 3 Oct (started 6:17:04 PM, about 4 seconds), execution #16547. No output reached GCS. On the canvas, [describe the red nodes and what a downstream red node says when clicked].

## What the logs said
Pipeline failed at orders_country_std: LLM execution failed (code_sha=b1bde1b05f09): Column 'country' does not exist in input_df_1. The expanded JSON includes nodeId llm_node_2 and nodeLabel orders_country_std.
- Only the first failing node is reported. The dropped email column, the text amounts and the new column are not mentioned, so a user would find them one run at a time. (The email node comes after the country node in this pipeline, so I could not see whether it would also fail.)
- The code_sha for this node (b1bde1b05f09) is the same as in the renamed column run, which suggests generated code is reused between runs.

## What the chatbot said


## Did the fix work?


## Severity
Medium. The pipeline stopped and wrote nothing, which is safe. But the error hides the other three changes, so repairing the pipeline could take several failed runs, and the contradictory job-completed message is still logged after the failure.

## Evidence
- evidence/schema-combined-logs.png
- evidence/schema-combined-dashboard-failure.png
- evidence/schema-combined-error.txt
