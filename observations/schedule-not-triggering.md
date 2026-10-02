# **Schedule never creates an execution**

## What I set up
- Pipeline: S3 source, 9 cleaning nodes, GCS data output (works when run manually)
- Schedule created from the project's Schedule tab, then deleted and recreated following the scheduling guide
- Frequencies tried: Hourly at minute 20, then Custom cron */20 * * * * (after which the card showed "Custom: */20 * * * *"), Hourly at minute 30, Hourly at minute 45
- Timezone: the create form did not show a timezone field that I could see, although the docs describe a read-only timezone field. I assume it used my browser's timezone (Sydney) but could not confirm.

## What I expected
According to the scheduling docs, a scheduled run behaves as if I clicked Run and every scheduled run creates an execution record (success or failure), with an email on failure. So I expected a new RhombusAI_output file in GCS at each trigger time and a row in the execution history.

## What happened
- The card showed an Active schedule with a "Next run" countdown. When the countdown reached zero it reset to the next interval.
- The pipeline execution history lists only manual runs. No scheduled run appears at all.
- The schedule's own Executions table was empty ("No results").
- No failure email arrived and nothing was marked failed.
- No new files appeared in GCS (refreshed repeatedly). The only files there came from pressing the play button manually.
- Credit balance did not change for scheduled triggers.
- Waited through [6-7] scheduled times over about [6] hours.

## Impact
High. The brief's baseline requires a successful scheduled run and the failure is silent as the UI says Active and counts down, but nothing runs and nothing reports an error. A customer relying on this would not find out that their data is not refreshing.

## What I did about it
Continued all tests in manual mode (pressing Run) and documented this as a deviation in the README.

## Evidence
- evidence/pipeline-execution-history-manual-only.png
- evidence/schedule-card-countdown.png
- evidence/bucket-manual-files.png

## Open questions
- Is a schedule on this account type or project supposed to run? (Docs do not mention restrictions.)
- Not tried: very short interval (*/5) diagnostic, changing the pipeline after creating the schedule.