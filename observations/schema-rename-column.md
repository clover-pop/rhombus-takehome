# Schema drift: renamed column (country to country_name)

## What I changed
Renamed the country column to country_name in datasets/drift_rename_column.csv (160 rows, 9 columns, same data). Uploaded to S3 as input/baseline.csv with data-validation/run_case.py and pressed Run manually.

## What I expected
I expected the pipeline to stop at the first node that uses the country column (the country standardisation step) instead of guessing that country_name was the same column.

## What happened
The run failed at 11:13:35 AM on 3 Oct (Sydney), execution #16474. The dashboard marked it as a failure. No output file reached GCS.
On the canvas, the node orders_country_std went red (shown on the Canvas as Custom llm_node_2) the nodes before it succeeded and nothing after it ran.

## What the logs said
Pipeline failed at orders_country_std: LLM execution failed (code_sha=b1bde1b05f09): Column 'country' does not exist in input_df_1. Full text in evidence/rename-column-error.txt.
- Clear: it names the node and the missing column.
- Not helpful: it does not mention that a similarly named column (country_name) exists.
- Same inconsistency as the dropped column case: a "Pipeline execution completed successfully" line is logged at the same second as the failure (2 of 2 failed runs so far).

## What the chatbot said
The chatbot confidently claimed that it fixed the error on the canvas by modifying the node logic to account for the rename, stating that the pipeline had recompiled and was live on the canvas.

## Did the fix work?
No, the claim was false. Running the renamed column file again after the edit (11:38:57 PM) failed at `orders_country_std` with the exact same error message and the same code hash (`code_sha=b1bde1b05f09`). Because the hash remained identical to the failure from before the chatbot's attempt, it proves the country node's code was never actually modified behind the scenes, contradicting the chatbot's story. (Evidence saved to `evidence/chatbot-rename-check-error.txt` and `evidence/chatbot-rename-check-logs.png`).

## Severity
Low to medium. The pipeline stopped and wrote nothing, so no bad data reached GCS. The error does not help locate the renamed column, and the contradictory success message is confusing.

## Evidence
- evidence/rename-column-logs.png
- evidence/rename-column-error.txt
- evidence/rename-column-dashboard-failure.png
- evidence/chatbot-rename-check-error.txt
- evidence/chatbot-rename-check-logs.png
