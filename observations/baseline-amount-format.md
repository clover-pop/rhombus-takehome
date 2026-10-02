# **Baseline: amount_usd decimal formatting**

## What I changed
Nothing. Baseline run, no drift.

## What I expected
Rule 7 asked for amount_usd as a number with 2 decimal places, so 441.30 should stay 441.30.

## What happened
16 of 122 output amounts have fewer than 2 decimals (for example 441.30 became 441.3). All 122 values are numerically correct.

## Impact
Low. A text comparison against the input fails on these rows, so validation must compare numerically. A downstream consumer expecting fixed 2-decimal text would see a difference.

## Logs / chatbot
The builder's summary said valid values were rounded to 2 decimal places and did not mention the trailing zero.