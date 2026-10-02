# **Baseline: signup_date handling on load**

## What I uploaded
datasets/baseline.csv (160 rows) in S3 at input/baseline.csv. The S3 copy is identical to the local file (checked with diff). 15 rows have signup_date in a non-ISO format: 8 as "DD Mon YYYY" (for example 06 Jul 2025) and 7 as "YYYY/MM/DD" (for example 2024/06/12). The full list is in datasets/baseline_defects.json under signup_date_mixed_format.

## What I expected
The source node preview would show the original mixed formats and my pipeline rule (rule 4) would be the step that converts them to YYYY-MM-DD.

## What happened
The source node preview showed every signup_date as YYYY-MM-DD, before any of my rules ran. I spot-checked two of the 15 rows against the original values and both converted to the correct date:
- Order 1022: 06 Jul 2025 shown as 2025-07-06
- Order 1003: 2024/06/12 shown as 2024-06-12

When I asked the AI builder for per-rule row counts, it reported that rule 4 changed 0 rows because all 160 values were already in YYYY-MM-DD. It also offered a guess that the trim step might have handled edge cases.

## Conclusion
Rhombus appears to parse and normalise date strings when it loads the CSV, not in the pipeline. In this case the conversion was correct for the two rows I checked. The builder's report was accurate about what it saw but did not say that the conversion had happened earlier, and its explanation was a guess.

## Why it matters
- A cleaning rule can have nothing to do because of load-time parsing, so a "0 rows changed" report does not prove the rule works.
- Ambiguous formats (for example 03/04/2025) would have to be guessed at on load. This is relevant to my semantic drift tests (month/day swapped to day/month).

## Evidence
- evidence/baseline-source-preview.png

## Still to verify
Whether the other 13 rows also converted correctly (I checked 2 of 15).