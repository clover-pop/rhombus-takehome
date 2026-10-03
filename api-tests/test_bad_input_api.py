import pytest

from api_helpers import HISTORY, SCHEDULES

KNOWN_500 = ("Known issue: the API returns HTTP 500 for this invalid input "
             "(see observations/api-500-on-invalid-paging.md)")
xfail_500 = pytest.mark.xfail(reason=KNOWN_500, strict=False)

BAD_SCHEDULE_PARAMS = [
    pytest.param({"page": 0, "page_size": 5}, marks=xfail_500, id="page_zero"),
    pytest.param({"page": -1, "page_size": 5}, marks=xfail_500, id="page_negative"),
    pytest.param({"page": 1, "page_size": 0}, id="page_size_zero"),
    pytest.param({"page": 1, "page_size": 10000}, id="page_size_huge"),
    pytest.param({"page": "abc", "page_size": 5}, id="page_not_a_number"),
]
BAD_HISTORY_PARAMS = [
    pytest.param({"limit": "abc"}, id="limit_not_a_number"),
    pytest.param({"limit": -5}, marks=xfail_500, id="limit_negative"),
    pytest.param({"limit": 10000}, id="limit_huge"),
]


def check_handled_cleanly(response):
    assert response.status_code < 500, "server error " + str(response.status_code) + " on bad input"
    assert "Traceback" not in response.text, "response leaks a stack trace"


@pytest.mark.parametrize("params", BAD_SCHEDULE_PARAMS)
def test_schedule_list_handles_bad_paging(api, params):
    check_handled_cleanly(api.get(SCHEDULES, params=params))


@pytest.mark.parametrize("params", BAD_HISTORY_PARAMS)
def test_history_handles_bad_limit(api, project_id, params):
    check_handled_cleanly(api.get(HISTORY.format(project_id=project_id), params=params))
