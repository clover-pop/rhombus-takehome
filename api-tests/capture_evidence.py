import sys

import requests

from api_helpers import BASE_URL, CREDITS, HISTORY, PROFILE, PROJECT_ID, SCHEDULES, TIMEOUT, TOKEN

if not TOKEN:
    sys.exit("RHOMBUS_TOKEN is not set in .env")

auth = {"Authorization": "Bearer " + TOKEN}


def show(label, response):
    ctype = response.headers.get("content-type", "")
    body = response.text.strip().replace("\n", " ")[:200]
    print(label, "->", response.status_code, "|", ctype, "|", body)


print("== invalid paging and limits (each sent twice) ==")
history_path = HISTORY.format(project_id=PROJECT_ID)
cases = [
    ("schedules page=0 page_size=5", SCHEDULES, {"page": 0, "page_size": 5}),
    ("schedules page=-1 page_size=5", SCHEDULES, {"page": -1, "page_size": 5}),
    ("schedules page=1 page_size=0", SCHEDULES, {"page": 1, "page_size": 0}),
    ("schedules page=1 page_size=10000", SCHEDULES, {"page": 1, "page_size": 10000}),
    ("schedules page=abc page_size=5", SCHEDULES, {"page": "abc", "page_size": 5}),
    ("history limit=abc", history_path, {"limit": "abc"}),
    ("history limit=-5", history_path, {"limit": -5}),
    ("history limit=10000", history_path, {"limit": 10000}),
]
for label, path, params in cases:
    for attempt in (1, 2):
        show(label + " (try " + str(attempt) + ")",
             requests.get(BASE_URL + path, params=params, headers=auth, timeout=TIMEOUT))

print()
print("== missing or bad credentials ==")
auth_cases = {
    "no header": {},
    "empty bearer": {"Authorization": "Bearer "},
    "garbage token": {"Authorization": "Bearer not-a-real-token"},
    "wrong scheme": {"Authorization": "Basic dGVzdDp0ZXN0"},
}
paths = [CREDITS, PROFILE, SCHEDULES + "?page=1&page_size=5",
         history_path + "?limit=5&structured=true"]
for path in paths:
    for label, headers in auth_cases.items():
        show(path.split("?")[0].split("/api/")[-1] + " | " + label,
             requests.get(BASE_URL + path, headers=headers, timeout=TIMEOUT))
