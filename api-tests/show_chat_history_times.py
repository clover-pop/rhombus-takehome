from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from api_helpers import BASE_URL, HISTORY, PROJECT_ID, TIMEOUT, TOKEN, parse_ts

response = requests.get(BASE_URL + HISTORY.format(project_id=PROJECT_ID),
                        params={"limit": 50, "structured": "true"},
                        headers={"Authorization": "Bearer " + TOKEN}, timeout=TIMEOUT)
print("HTTP", response.status_code)
for m in reversed(response.json()["history"]):
    when = parse_ts(m["created_at"]).astimezone(ZoneInfo("Australia/Sydney"))
    content = m["content"] if isinstance(m["content"], dict) else {}
    print(when.strftime("%d %b %H:%M:%S"), m["role"], "|", str(content.get("message", ""))[:70].replace("\n", " "))
