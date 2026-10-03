# Schema drift: dropped column (email)

## What I changed
Removed the email column from the source file (datasets/drift_drop_column.csv: 160 rows, 8 columns). I uploaded it to S3 as input/baseline.csv with data-validation/run_case.py and pressed Run manually in Rhombus.

## What I expected
The pipeline would fail at the email validation step (or carry on and let every row through).

## What happened
The run failed at 10:34:38 AM on 3 Oct (Sydney) execution #16473. The node orders_valid_email (shown on the canvas as "Custom llm_node_4") went red, the nodes before it succeeded, and nothing after it ran. No output file reached GCS.

## What the logs said
The error reads: Pipeline failed at orders_valid_email, LLM execution failed, Column 'email' does not exist in input_df_1. It is followed by a long block of generated code that is cut off in the log panel (full text in evidence/drop-column-error.txt).
- Clear: it names the node and the missing column.
- Confusing: at the same timestamp the log also shows "Pipeline execution completed successfully". The node name in the log (orders_valid_email) does not match the canvas label (llm_node_4).

## What the chatbot said
[to fill in once I test it]

## Did the fix work?
No. After the chatbot edited orders_trimmed, I put the dropped column file back in S3 and ran again (started 10:25:27 PM, failed 10:25:32 PM). It failed at the same node, orders_valid_email, with the same message (Column 'email' does not exist in input_df_1) and the same code_sha (5f40b5e32988), so the email node was unchanged. The chatbot's prediction that the error would be gone was wrong. No output reached GCS. (evidence/chatbot-drop-column-rerun-logs.png)

Side effects: I then ran the normal baseline file through the edited pipeline. It produced 122 rows, all 23 validator checks passed, and the content was identical to baseline_run1 (evidence/chatbot-drop-column-baseline-check.txt). The edit did not break normal behaviour, but it did nothing for the problem and left a permanent change in the pipeline. After the edit, the failure log's nodeRef is a long hash instead of matching the node id as in earlier logs; I did not investigate why.

## Severity
Low for the drift handling: the pipeline stopped and wrote nothing, so no bad data reached GCS. The contradictory "completed successfully" line is a minor clarity issue.

## Evidence
- evidence/drop-column-logs.png
- evidence/drop-column-error.txt
- evidence/drop-column-dashboard-failure.png
