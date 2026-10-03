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
Asked from the 12:47:09 PM log entry with the history cleared, the drifted file in S3, and the message edited to say "do not change the pipeline". Reply in evidence/chatbot-type-change-reply.txt.
- Diagnosis: partly correct. It correctly said the immediate error is that TypeError is not defined in the node's execution environment. It did not connect this to the data change: amount_usd values now start with a "$", so float() fails and the generated except (ValueError, TypeError) clause is evaluated. It framed the error as a code-generation bug.
- It opened with "no pipeline inspection needed" and then guessed what the code looked like ("likely something like..."). The real code, visible in my pipeline logs, is different.
- Its example trigger ("N/A") is contradicted by my baseline: four N/A amounts ran successfully because pandas reads them as missing values before the code sees them.
- Suggested fix (not applied): import TypeError from builtins, or use pd.to_numeric(errors='coerce'). My prediction (untested): the second would turn every "$" amount into a missing value and the amount rule would drop those rows, so the run would succeed while silently losing data.
- It did not change the pipeline.

## Did the fix work?
Not tested for this case, for time. Only the dropped column fix was tested (it did not work).

## Severity
Medium. The pipeline stopped and wrote nothing, so no bad data reached GCS, which is the safe outcome. But the error points at an internal code problem instead of the changed data, so it is hard to diagnose, and the contradictory success message adds to the confusion.

## Evidence
- evidence/type-change-dashboard-failure.png
- evidence/type-change-logs.png
- evidence/type-change-error.txt
