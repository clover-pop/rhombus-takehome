| execution | scenario | trigger | started (Sydney) | duration | status | nodes | notes |
|-----------|----------|---------|------------------|----------|--------|-------|-------|
| #16345 | first run of the AI-built pipeline | manual | 2 Oct 13:55:51 | 1m 3s | success | 9 nodes | |
| #16373 | exploratory | manual | 2 Oct 16:09:11 | 4.4s | success | 10 nodes | |
| #16374 | exploratory | manual | 2 Oct 16:09:17 | 4.4s | success | 10 nodes | |
| #16380 | baseline (manual) | manual | 2 Oct 16:25:33 | 8.4s | success | 10 nodes | three play clicks within 9 seconds (#16380 to #16382) |
| #16381 | baseline (manual) | manual | 2 Oct 16:25:40 | 7.0s | success | 10 nodes | |
| #16382 | baseline (manual) | manual | 2 Oct 16:25:42 | 7.0s | success | 10 nodes | |
| #16383 | baseline (manual) | manual | 2 Oct 16:27:27 | 5.5s | success | 10 nodes | |
| #16419 | baseline (manual) | manual | 2 Oct 21:33:52 | 6.8s | success | 10 nodes | pressed while testing the schedule |
| #16426 | baseline_run1 | manual (harness) | 2 Oct 22:25:56 | 6.9s | success | 10 nodes | 122 rows, all validator checks passed |
| #16428 | baseline_run2 | manual (harness) | 2 Oct 22:27:12 | 6.9s | success | 10 nodes | identical to run 1 |
| #16429 | baseline_run3 | manual (harness) | 2 Oct 22:28:06 | 6.5s | success | 10 nodes | identical to run 1 |
| #16473 | drift_drop_column | manual (harness) | 3 Oct 10:34:33 | 4.9s | failure | 5 nodes | stopped at orders_valid_email |
| #16474 | drift_rename_column | manual (harness) | 3 Oct 11:13:31 | 3.6s | failure | 3 nodes | stopped at orders_country_std |
| #16479 | drift_type_change | manual (harness) | 3 Oct 12:47:03 | 4.8s | failure | 6 nodes | stopped at orders_valid_amount (TypeError not defined) |
| #16491 | accidental run | manual | 3 Oct 13:58:27 | 0.0s | success | none | executed nothing yet counted as a success |
| #16492 | accidental run | manual | 3 Oct 13:58:45 | 7.9s | success | 10 nodes | output deleted from GCS |
| #16493 | drift_new_column | manual (harness) | 3 Oct 14:00:23 | 6.7s | success | 10 nodes | loyalty_tier passed through to GCS |
| #16547 | drift_combined_schema | manual (harness) | 3 Oct 18:17:05 | 3.4s | failure | 3 nodes | stopped at orders_country_std |
| #16548 | drift_semantic_cents | manual (harness) | 3 Oct 18:26:27 | 6.9s | success | 10 nodes | amounts 100x too large, no warning |
| #16555 | drift_semantic_dates_ddmm | manual (harness) | 3 Oct 20:37:07 | 7.3s | success | 10 nodes | 42 of 49 ambiguous dates swapped |
| #16556 | drift_semantic_status_swap | manual (harness) | 3 Oct 21:54:13 | 7.6s | success | 10 nodes | 63 of 122 statuses wrong |
| #16557 | unknown | manual | 3 Oct 22:06:48 | 0.0s | success | none | executed nothing yet counted as a success |
| #16558 | chatbot_drop_after_fix | manual (harness) | 3 Oct 22:25:27 | 4.0s | failure | 5 nodes | same failure after the chatbot's edit |
| #16559 | baseline_after_chatbot_fix | manual (harness) | 3 Oct 22:26:28 | 7.8s | success | 10 nodes | identical to baseline_run1 |
| #16560 | chatbot_rename_check | manual (harness) | 3 Oct 23:38:53 | 4.1s | failure | 3 nodes | same failure after the chatbot's edit |
| #16628 | UI test: Run button | manual (Playwright) | 4 Oct 15:40:25 | 6.1s | success | 10 nodes | |
| #16632 | UI test: Run button | manual (Playwright) | 4 Oct 15:50:52 | 5.5s | success | 10 nodes | |

Scheduled runs: none ever appeared (see observations/schedule-not-triggering.md).
Source of this table: datasets/rhombus_executions.csv (exported from the dashboard).
