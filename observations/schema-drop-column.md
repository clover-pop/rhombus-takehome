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
Asked with Ask Chatbot on the 10:34:38 AM log entry, no hints added, while S3 held the healthy baseline file (not the dropped column file). Full reply in evidence/chatbot-drop-column-reply.txt.
- Diagnosis: wrong. It said the orders_trimmed node strips cell values but not column names, so a header like " email" (stray space) would not match. The real cause is that the email column was removed from the source. The error message gave no hint of whitespace.
- Confidence: it said "The root cause is clear" while its own explanation was conditional ("If the source CSV has a header like...").
- Action: it edited the pipeline automatically (one line added to orders_trimmed: target_df.columns = target_df.columns.str.strip()). The pre-filled message from the Ask Chatbot button says "Please help me fix", which invites an edit.
- It predicted "the error should be gone" after a re-run.
- Cost: 6 credits (39/50 to 33/50).

## Did the fix work?
No. After the chatbot edited orders_trimmed, I put the dropped column file back in S3 and ran again (started 10:25:27 PM, failed 10:25:32 PM). It failed at the same node, orders_valid_email, with the same message (Column 'email' does not exist in input_df_1) and the same code_sha (5f40b5e32988), so the email node was unchanged. The chatbot's prediction that the error would be gone was wrong. No output reached GCS. (evidence/chatbot-drop-column-rerun-logs.png)

Side effects: I then ran the normal baseline file through the edited pipeline. It produced 122 rows, all 23 validator checks passed, and the content was identical to baseline_run1 (evidence/chatbot-drop-column-baseline-check.txt). The edit did not break normal behaviour, but it did nothing for the problem and left a permanent change in the pipeline. After the edit, the failure log's nodeRef is a long hash instead of matching the node id as in earlier logs; I did not investigate why.

## Severity
Low for the drift handling: the pipeline stopped and wrote nothing, so no bad data reached GCS. The contradictory "completed successfully" line is a minor clarity issue.

## Evidence
- evidence/drop-column-logs.png
- evidence/drop-column-error.txt
- evidence/drop-column-dashboard-failure.png
