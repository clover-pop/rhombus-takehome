| run | scenario | trigger | started (Sydney) | duration | status | rows out | credits | notes |
|-----|----------|---------|------------------|----------|--------|----------|---------|-------|
| #16373 | exploratory | manual | 2 Oct 16:09:11 | 4.4s | success | | | |
| #16374 | exploratory | manual | 2 Oct 16:09:17 | 4.4s | success | | | |
| #16380 | baseline | manual | 2 Oct 16:25:33 | 8.4s | success | | | first GCS output; three play clicks within 9s |
| #16381 | baseline | manual | 2 Oct 16:25:40 | 7.0s | success | | | |
| #16382 | baseline | manual | 2 Oct 16:25:42 | 7.0s | success | | | |
| #16383 | baseline | manual | 2 Oct 16:27:27 | 5.5s | success | | | |
| #16419 | baseline | manual | 2 Oct 21:33:52 | 6.8s | success | | | pressed while testing the schedule |
| #16426 | baseline_run1 | manual (harness) | 2 Oct 22:25:56 | 6.9s | success | 122 | | validator: all checks passed |
| #16428 | baseline_run2 | manual (harness) | 2 Oct 22:27:12 | 6.9s | success | 122 | | identical to run1 |
| #16429 | baseline_run3 | manual (harness) | 2 Oct 22:28:06 | 6.5s | success | 122 | | identical to run1 |

Scheduled runs: none ever appeared in the execution history (see observations/schedule-not-triggering.md).
| #16479 | drift_type_change | manual (harness) | 3 Oct 12:47:03 | 4.8s | failure | none | | failed at orders_valid_amount; error is a NameError for TypeError in generated code || #? | accidental baseline run | manual | 3 Oct 13:58:27 | | success | | | pressed Run by mistake while the baseline was in S3; output deleted from GCS |
| #16491 | accidental baseline run | manual | 3 Oct 13:58:44 | | success | | | same; output deleted from GCS |
| #16492 | drift_new_column | manual (harness) | 3 Oct 14:00:22 | ~8s | success | 122 | | extra column loyalty_tier passed through to GCS |
| #? | drift_combined_schema | manual (harness) | 3 Oct 18:17:04 | ~4s | failure | none | | failed at orders_country_std; only the first missing column reported |
| #? | drift_semantic_cents | manual (harness) | 3 Oct 18:26:26 | ~8s | success | 122 | | amounts 100x too large, no warning from Rhombus; validator failed 2 checks |
| #? | drift_semantic_dates_ddmm | manual (harness) | 3 Oct | ~8s | success | 122 | | 42 of 49 ambiguous order_dates month/day swapped, no warning; validator failed 1 check |
