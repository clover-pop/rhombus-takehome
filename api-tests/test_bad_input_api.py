import pytest

from api_helpers import HISTORY, SCHEDULES

BAD_SCHEDULE_PARAMS = [
    {"page": 0, "page_size": 5},
    {"page": -1, "page_size": 5},
    {"page": 1, "page_size": 0},
    {"page": 1, "page_size": 10000},
    {"page": "abc", "page_size": 5},
]
BAD_HISTORY_PARAMS = [{"limit": "abc"}, {"limit": -5}, {"limit": 10000}]


def check_handled_cleanly(response):
    assert response.status_code < 500, "server error " + str(response.status_code) + " on bad input"
    assert "Traceback" not in response.text, "response leaks a stack trace"


@pytest.mark.parametrize("params", BAD_SCHEDULE_PARAMS)
def test_schedule_list_handles_bad_paging(api, params):
    check_handled_cleanly(api.get(SCHEDULES, params=params))


@pytest.mark.parametrize("params", BAD_HISTORY_PARAMS)
def test_history_handles_bad_limit(api, project_id, params):
    check_handled_cleanly(api.get(HISTORY.format(project_id=project_id), params=params))
