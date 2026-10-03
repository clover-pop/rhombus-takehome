# API: HTTP 500 on invalid paging input

## What I tested
Read-only GET requests against my own account's endpoints, found in the browser's network tab, with deliberately invalid query parameters. A handful of requests, each sent twice. Nothing was changed on the server, and I did not try other users' resources.

## What I expected
Invalid input is rejected with a 4xx status (400 or 422) and a clear message, or is ignored or clamped with a 200. Never a 5xx.

## What happened
Three inputs returned HTTP 500 on both attempts:
- GET /api/dataset/analyzer/v2/pipeline/schedules/all?page=0&page_size=5
- GET /api/dataset/analyzer/v2/pipeline/schedules/all?page=-1&page_size=5
- GET /api/dataset/analyzer/v2/projects/{project_id}/chat/history?limit=-5

The other inputs were handled without a server error yielding specific validation responses:
- `page_size=0` clamped safely and returned **HTTP 200** with an empty schedules array payload.
- `page_size=10000` succeeded and returned **HTTP 200** alongside valid standard structural array values.
- `page=abc` was correctly rejected with **HTTP 422** indicating a Pydantic-style integer parsing compilation error.
- `limit=abc` was correctly rejected with **HTTP 422** indicating an invalid query string integer format.
- `limit=10000` was handled cleanly and rejected with **HTTP 422**, explicitly stating that the target input parameter should be less than or equal to a value boundary of 50.

Content of the 500 responses:
The response returned a content type of `text/html; charset=utf-8` containing a minimal generic template header block (`<!doctype html> <html lang="en"> <head> <title>Server Error (500)</title> </head> ...`). It does not leak any granular internal system database stack traces, python traceback details, or configuration environment parameters.

## Reproduce
curl -i -H "Authorization: Bearer \$RHOMBUS_TOKEN" "https://api.rhombusai.com/api/dataset/analyzer/v2/pipeline/schedules/all?page=0&page_size=5"
(RHOMBUS_TOKEN is a session token copied from the browser.) Or run: pytest api-tests/test_bad_input_api.py -v

## Severity
Low to medium. Zero or negative paging values are plausible mistakes for an API client, and they cause an unhandled server error instead of a validation error. I have no evidence of data exposure or wider impact, as the generic 500 HTML payload does not leak any active application deployment traces.

## Evidence
- evidence/api-bad-input-responses.txt
- evidence/api-tests-run.txt (the original run, with the three failures)
