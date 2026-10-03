# Schema drift: amount_usd changed from number to text ("$124.47")

## What I changed
Changed every non-empty, non-"N/A" amount_usd value in datasets/drift_type_change.csv from a plain number (124.47) to text with a dollar sign ($124.47). Same columns, same rows (160). Uploaded to S3 as input/baseline.csv with data-validation/run_case.py and pressed Run manually.

## What I expected
I expected the run to succeed with no warning. I predicted either that the dollar signs would make the amount rule drop most rows (far fewer than 122 in the output), or that the generated code would strip the "$" and match the baseline. 

## What happened
The run failed at the orders_valid_amount node (execution #16479, 12:47:03 to 12:47:08 PM on 3 Oct, 4.8s, dashboard shows "6 nodes" against 10 for successful runs). No output reached GCS. The dashboard marked it as a failure. On the canvas, the node orders_valid_amount went red(shown on the Canvas as Custom llm_node_5) the nodes before it succeeded and nothing after it ran.

## What the logs said
LLM execution failed (code_sha=214424711c89): name 'TypeError' is not defined. Full text in evidence/type-change-error.txt.
- Not helpful: the message does not mention amount_usd, the dollar signs or the data type. It reports a problem inside the generated code, so a user cannot tell that their data changed.
- Cause (from reading the generated code in the pipeline log): the amount node checks values with try: float(val) except (ValueError, TypeError). A value like "$124.47" makes float() raise ValueError, Python then evaluates the except clause, and the run stops with name 'TypeError' is not defined. This suggests the execution environment does not provide TypeError (not confirmed). The baseline never hit it because pandas reads "N/A" and empty cells as missing values, so float() was never called on them. If the handler had worked, every "$" value would have been treated as invalid and likely dropped silently.
- Same inconsistency as the earlier failures: a "Pipeline execution completed successfully" line is logged one second after the failure (3 of 3 failed runs so far).

## What the chatbot said


## Did the fix work?


## Severity
Medium. The pipeline stopped and wrote nothing, so no bad data reached GCS, which is the safe outcome. But the error points at an internal code problem instead of the changed data, so it is hard to diagnose, and the contradictory success message adds to the confusion.

## Evidence
- evidence/type-change-dashboard-failure.png
- evidence/type_change-logs.png
- evidence/type-change-error.txt
