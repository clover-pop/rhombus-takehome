# Schema drift: all four changes together

## What I changed
datasets/drift_combined_schema.csv has all four schema changes at once: email dropped, country renamed to country_name, amount_usd turned into text ("$124.47"), and a new loyalty_tier column added. Uploaded to S3 as input/baseline.csv with data-validation/run_case.py and pressed Run manually.

## What I expected
The run would fail at orders_country_std, the first node in the chain that needs a missing column, and the error would mention only the country column, not the other changes. This prediction was written before running this case.

## What happened
The run failed at 6:17:08 PM on 3 Oct (started 6:17:04 PM, about 4 seconds), execution #16547. No output reached GCS. On the canvas, the orders_country_std node highlighted bright red showing a fatal error state. When a downstream node was clicked, the right-hand options panel displayed the global "Configuration Required" error message, locking access to further properties.

## What the logs said
Pipeline failed at orders_country_std: LLM execution failed (code_sha=b1bde1b05f09): Column 'country' does not exist in input_df_1. The expanded JSON includes nodeId llm_node_2 and nodeLabel orders_country_std.
- Only the first failing node is reported. The dropped email column, the text amounts and the new column are not mentioned, so a user would find them one run at a time. (The email node comes after the country node in this pipeline, so I could not see whether it would also fail.)
- The code_sha for this node (b1bde1b05f09) is the same as in the renamed column run, which suggests generated code is reused between runs.

## What the chatbot said
Asked from the 6:17:08 PM log entry with the message edited to say "do not change the pipeline". Conditions: history cleared and the combined file in S3. Reply in evidence/chatbot-combined-reply.txt.
- Diagnosis: wrong. It blamed a column name casing problem: it said the source header is probably "Country" (capital C) while the country node looks for "country". None of the four real changes (email dropped, country renamed to country_name, amount_usd as text, loyalty_tier added) was identified.
- The claim is contradicted by my files: the header in baseline.csv is lowercase "country", and every baseline output has lowercase headers, so no node changes header case (checked with head -1 on the datasets).
- The reply was written in hedged language ("may", "likely", "plausible") but ended with a firm conclusion about my file's contents, without checking the file.
- It correctly described the pipeline as it now stands (including the earlier orders_trimmed edit), so it read the pipeline but not the data.
- Inconsistency: in the renamed column test with the same node and error, the chatbot did find country_name. Here the file also contains country_name and it did not.
- It did not change the pipeline.

## Did the fix work?
Not applicable: no change was applied. It proposed normalising column names to lowercase or making the lookup case-insensitive, which would not help because the real problem is a renamed column.

## Extra evidence from the chat history API
The backend's record of my question (evidence/api-chat-history-combined.json) shows attached_datasets and dataset_refs empty, and the assistant's tool transcript lists only ToolSearch and inspect_pipeline. This is consistent with the chatbot reading the pipeline and never the data. (An empty attachment list alone does not prove it could not fetch data another way, but no data-reading tool was used.)

## Severity
Medium. The pipeline stopped and wrote nothing, which is safe. But the error hides the other three changes, so repairing the pipeline could take several failed runs, and the contradictory job-completed message is still logged after the failure.

## Evidence
- evidence/schema-combined-logs.png
- evidence/schema-combined-dashboard-failure.png
- evidence/schema-combined-error.txt
