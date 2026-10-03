import os
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.environ.get("RHOMBUS_API_BASE", "https://api.rhombusai.com")
TOKEN = os.environ.get("RHOMBUS_TOKEN", "")
PROJECT_ID = os.environ.get("RHOMBUS_PROJECT_ID", "")
TIMEOUT = 20

CREDITS = "/api/accounts/users/credits"
PROFILE = "/api/accounts/users/profile"
SCHEDULES = "/api/dataset/analyzer/v2/pipeline/schedules/all"
HISTORY = "/api/dataset/analyzer/v2/projects/{project_id}/chat/history"


def parse_ts(value):
    """Parse an ISO timestamp such as 2026-10-02T11:39:51.782Z."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def utcnow():
    return datetime.now(timezone.utc)


class Api:
    def __init__(self, token):
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        self.session.headers["Authorization"] = "Bearer " + token

    def get(self, path, params=None):
        return self.session.get(BASE_URL + path, params=params, timeout=TIMEOUT)


def json_body(response, expected_status=200):
    assert response.status_code == expected_status, (
        "expected HTTP " + str(expected_status) + " but got " + str(response.status_code)
        + ": " + response.text[:200]
    )
    assert "json" in response.headers.get("content-type", "").lower(), "response is not JSON"
    return response.json()
