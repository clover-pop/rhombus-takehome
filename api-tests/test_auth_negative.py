import pytest
import requests

from api_helpers import BASE_URL, CREDITS, HISTORY, PROFILE, PROJECT_ID, SCHEDULES, TIMEOUT

PATHS = [CREDITS, PROFILE, SCHEDULES + "?page=1&page_size=5"]
if PROJECT_ID:
    PATHS.append(HISTORY.format(project_id=PROJECT_ID) + "?limit=5&structured=true")

AUTH_CASES = {
    "no_header": {},
    "empty_bearer": {"Authorization": "Bearer "},
    "garbage_token": {"Authorization": "Bearer not-a-real-token"},
    "wrong_scheme": {"Authorization": "Basic dGVzdDp0ZXN0"},
}
DATA_KEYS = {"balance", "tier_info", "first_name", "last_name", "schedules", "history"}


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("case", list(AUTH_CASES))
def test_unauthenticated_requests_are_rejected(path, case):
    response = requests.get(BASE_URL + path, headers=AUTH_CASES[case], timeout=TIMEOUT)
    assert response.status_code in (401, 403), (
        case + " on " + path.split("?")[0] + " returned HTTP " + str(response.status_code)
    )
    assert "Traceback" not in response.text
    try:
        body = response.json()
    except ValueError:
        body = {}
    if isinstance(body, dict):
        leaked = DATA_KEYS & set(body)
        assert not leaked, "rejected response still contains data fields: " + str(leaked)
